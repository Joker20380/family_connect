"""Bounded phone-side HTTP1.1 measurement; no payload streaming over ADB."""

import concurrent.futures
import datetime
import json
import os
import re
import shlex
import subprocess
import sys
import threading
import time

from prepare import APK, GATEWAY, ROOT, WORK
from journal import reassemble, performance_lines

sys.path.insert(0, str(ROOT/'tests/fixtures/mesh_throughput_trace'))
from correlate import reconstruct


def export_gate(path):
    rows=[]
    for line in path.read_text().splitlines():
        try: rows.append(json.loads(line))
        except json.JSONDecodeError: pass
    journal,join_errors=reassemble(row['raw'] for row in rows if row['kind']=='journal')
    snapshots,errors=reconstruct(performance_lines(journal))
    errors+=join_errors
    useful=[row for row in snapshots if row['performance'].get('Window') and row['performance'].get('Mux') and row['performance'].get('Trace') and any(point['kind']=='data_carrier_written' for point in row['performance']['Trace']['points'])]
    return dict(snapshots=len(snapshots),useful=len(useful),errors=errors,
                sockets_seen=any(row.get('sockets') for row in rows),sessions=sorted({row['session_tag'] for row in useful}))


def adb(command, timeout=25):
    return subprocess.run(['adb','shell',command],capture_output=True,text=True,timeout=timeout)


def topology():
    result=adb('dumpsys connectivity');result.check_returncode()
    lines=[line for line in result.stdout.splitlines() if line.strip().startswith('NetworkAgentInfo{') and 'ni{VPN' in line and 'OwnerUid: 10283' in line]
    assert len(lines)==1 and 'Uids: <{0-99999}>' in lines[0] and '10.79.0.1' in lines[0]
    value={key:re.search(pattern,lines[0])[1] for key,pattern in dict(interface=r'InterfaceName: (\S+)',underlay=r'UnderlyingNetworks: \[([^\]]*)\]').items()}
    assert 'dev '+value['interface'] in adb('ip route get 1.1.1.1').stdout
    return value


def main():
    os.umask(0o077)
    label=sys.argv[1];assert re.fullmatch('[a-z0-9-]+',label)
    expected=sys.argv[2] if len(sys.argv)>2 else GATEWAY
    assert re.fullmatch('[a-f0-9]{64}',expected)
    rounds=int(sys.argv[3]) if len(sys.argv)>3 else 1
    assert rounds in (1,2)
    target=WORK/label;target.mkdir(mode=0o700,exist_ok=False)
    initial=topology()
    apk=adb('pm path com.familyconnect.app.friends').stdout.strip().removeprefix('package:')
    assert adb('sha256sum '+shlex.quote(apk)).stdout.split()[0]==APK
    remote="""
import datetime,hashlib,json,subprocess
from pathlib import Path
from cryptography import x509
state=dict(line.split('=',1) for line in subprocess.check_output(['systemctl','show','family-connect-restricted-bootstrap.service','-p','MainPID,InvocationID,ActiveState'],text=True).splitlines())
assert state['ActiveState']=='active'
assert hashlib.sha256((Path('/proc')/state['MainPID']/'exe').read_bytes()).hexdigest()=='EXPECTED'
expiry=x509.load_pem_x509_certificate(json.loads(Path('/opt/apps/family_connect/friends-restricted/gateway.json').read_text())['certificate'].encode()).not_valid_after_utc
assert (expiry-datetime.datetime.now(datetime.timezone.utc)).total_seconds()>900
print(json.dumps(state))
""".replace('EXPECTED',expected)
    gateway=json.loads(subprocess.check_output(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=8','root@186.246.45.246','python3 -B -'],input=remote,text=True,timeout=25))
    (target/'preflight.json').write_text(json.dumps(dict(gateway=gateway,topology=initial,sha256=expected,utc=datetime.datetime.now(datetime.timezone.utc).isoformat())))
    start=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    collector=r"""
import json,os,select,subprocess,sys,time
from pathlib import Path
pid='PID';invocation='INVOCATION'
print(json.dumps(dict(kind='origin',pid=pid,invocation=invocation,clock_ticks=os.sysconf('SC_CLK_TCK'))),flush=True)
journal=subprocess.Popen(['journalctl','--file=/var/log/journal/*/system.journal','--no-pager','--all','--output-fields=MESSAGE,_STREAM_ID,_PID,_SYSTEMD_INVOCATION_ID,_LINE_BREAK,__REALTIME_TIMESTAMP','--since','START','-f','-o','json','_SYSTEMD_INVOCATION_ID='+invocation],stdout=subprocess.PIPE,bufsize=0)
stop=time.monotonic()+600;size=0;next_sample=0;buffer=b''
try:
 while time.monotonic()<stop and size<67108864:
  readable,_,_=select.select([sys.stdin,journal.stdout],[],[],.1)
  if sys.stdin in readable and not sys.stdin.readline():break
  if journal.stdout in readable:
   data=os.read(journal.stdout.fileno(),65536)
   if not data:break
   size+=len(data);buffer+=data
   while b'\n' in buffer:
    line,buffer=buffer.split(b'\n',1);print(json.dumps(dict(kind='journal',raw=line.decode('utf8','replace'))),flush=True)
  if time.monotonic()>=next_sample:
   sockets=subprocess.check_output(['ss','-H','-tnp','state','all','( dport = :443 )'],text=True,timeout=3)
   print(json.dumps(dict(kind='sample',epoch=time.time(),monotonic=time.monotonic(),stat=(Path('/proc')/pid/'stat').read_text(),status=(Path('/proc')/pid/'status').read_text(),sockets=[line for line in sockets.splitlines() if 'pid='+pid+',' in line])),flush=True)
   next_sample=time.monotonic()+1
finally:
 journal.terminate()
 try: journal.wait(timeout=2)
 except subprocess.TimeoutExpired: journal.kill();journal.wait(timeout=2)
 print(json.dumps(dict(kind='end',cap_reached=size>=67108864,partial_bytes=len(buffer))),flush=True)
""".replace("pid='PID'",'pid='+repr(gateway['MainPID'])).replace("invocation='INVOCATION'",'invocation='+repr(gateway['InvocationID'])).replace("'START'",repr(start))
    assert "'_SYSTEMD_INVOCATION_ID='" in collector
    compile(collector,'<bounded-collector>','exec')
    output=(target/'capture-private.jsonl').open('x');errors=(target/'capture.stderr').open('x')
    process=subprocess.Popen(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=8','root@186.246.45.246','python3 -B -c '+shlex.quote(collector)],stdin=subprocess.PIPE,stdout=output,stderr=errors)
    remote_root='/data/local/tmp/fc-queue-'+label+'-20261019'
    adb('umask 077; mkdir '+remote_root).check_returncode()
    records=[];lock=threading.Lock();stop=threading.Event();parallel=[]
    fields=('http_code','http_version','ssl_verify_result','remote_ip','local_port','num_connects','size_download','time_namelookup','time_connect','time_appconnect','time_starttransfer','time_total')
    def request(name,size):
        base=remote_root+'/'+name
        args=['/system/bin/curl','-4','--http1.1','--noproxy','*','--retry','0','--connect-timeout','15','--max-time','150','--max-filesize',str(size),'-H','Accept-Encoding: identity','-H','Cache-Control: no-cache','--silent','--show-error','--output',base+'.body','--dump-header',base+'.headers','--write-out',''.join(key+'=%{'+key+'}\n' for key in fields),'https://speed.cloudflare.com/__down?bytes='+str(size)]
        command='umask 077; read uptime rest < /proc/uptime; echo BEGIN=$uptime; '+shlex.join(args)+'; result=$?; read uptime rest < /proc/uptime; echo END=$uptime; echo CURL_EXIT=$result; if test -f '+base+'.body; then echo BODY_BYTES=$(wc -c < '+base+'.body); echo BODY_SHA256=$(sha256sum '+base+'.body | cut -d " " -f 1); fi; echo HEADER_BEGIN; cat '+base+'.headers'
        began=time.time();response=adb(command,170)
        (target/(name+'.stdout')).write_text(response.stdout);(target/(name+'.stderr')).write_text(response.stderr)
        text,_,headers=response.stdout.partition('HEADER_BEGIN')
        metrics=dict(line.split('=',1) for line in text.splitlines() if '=' in line)
        header_map={key.strip().lower():value.strip() for key,value in (line.split(':',1) for line in headers.splitlines() if ':' in line)}
        valid=response.returncode==0 and metrics.get('CURL_EXIT')=='0' and metrics.get('http_code')=='200' and metrics.get('ssl_verify_result')=='0' and metrics.get('http_version')=='1.1' and int(metrics.get('BODY_BYTES','0'))==size and float(metrics.get('size_download','0'))==size and header_map.get('content-encoding','identity').lower() in ('','identity') and header_map.get('cf-cache-status','').upper() not in ('HIT','STALE','UPDATING') and float(header_map.get('age','0'))==0
        record=dict(name=name,intended_bytes=size,start_epoch=began,end_epoch=time.time(),metrics=metrics,headers=header_map,valid=valid)
        if valid:record['mbit_s']=size*8/float(metrics['time_total'])/1e6
        else:stop.set()
        with lock:
            records.append(record)
            with (target/'requests.jsonl').open('a') as handle:handle.write(json.dumps(record)+'\n')
        adb('rm -f '+base+'.body '+base+'.headers').check_returncode()
        print(json.dumps({key:record[key] for key in ('name','valid','mbit_s') if key in record}),flush=True)
        return record
    try:
        for attempt in range(100):
            assert process.poll() is None,'COLLECTOR_FAILED_BEFORE_TRAFFIC'
            if (target/'capture-private.jsonl').stat().st_size:break
            time.sleep(.1)
        assert (target/'capture-private.jsonl').stat().st_size,'COLLECTOR_EMPTY_BEFORE_TRAFFIC'
        if expected!=GATEWAY:
            for attempt in range(120):
                assert process.poll() is None,'COLLECTOR_FAILED_WAITING_FOR_RECOVERY'
                gate=export_gate(target/'capture-private.jsonl')
                if gate['useful']:break
                time.sleep(1)
            (target/'pretraffic-session-gate.json').write_text(json.dumps(gate,indent=2))
            assert gate['useful'],'AUTO_RECOVERY_NOT_READY_NO_TRAFFIC'
        request('small',65536)
        if expected!=GATEWAY and not stop.is_set():
            gate={}
            for attempt in range(50):
                assert process.poll() is None,'COLLECTOR_FAILED_AFTER_SMALL'
                gate=export_gate(target/'capture-private.jsonl')
                if gate['useful'] and gate['sockets_seen']:break
                time.sleep(.2)
            (target/'small-export-gate.json').write_text(json.dumps(gate,indent=2))
            assert gate['useful'] and gate['sockets_seen'],'SMALL_EXPORT_NOT_PROVEN_NO_BULK'
        for number in range(rounds):
            if stop.is_set():break
            assert process.poll() is None,'COLLECTOR_FAILED_NO_MORE_BULK'
            assert topology()==initial
            request('single-'+str(number),2097152)
            if stop.is_set():break
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                pair=list(pool.map(lambda index:request('parallel-'+str(number)+'-'+str(index),2097152),range(2)))
            if all(item['valid'] for item in pair):
                wall=max(float(item['metrics']['END']) for item in pair)-min(float(item['metrics']['BEGIN']) for item in pair)
                parallel.append(dict(bytes=4194304,wall_seconds=wall,aggregate_mbit_s=4194304*8/wall/1e6))
        time.sleep(3)
    finally:
        process.stdin.close();process.wait(timeout=15);output.close();errors.close()
        adb('rmdir '+remote_root)
        result=dict(gateway_sha256=expected,gateway=gateway,requests=records,parallel=parallel,topology_stable=topology()==initial,
                    application_bytes=sum(int(item['metrics'].get('BODY_BYTES','0')) for item in records),capture_exit=process.returncode)
        (target/'result.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(dict(label=label,requests=len(records),failures=sum(not item['valid'] for item in records),parallel=parallel)),flush=True)


if __name__=='__main__':main()
