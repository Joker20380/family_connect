import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import time


ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'state-client-build/mesh-perf-3b/cleanup-probe'
REMOTE = '/data/local/tmp/fc-mesh-perf3b-cleanup-20261018-1'
os.umask(0o077)


def run(arguments, timeout=20):
    return subprocess.check_output(arguments, text=True, stderr=subprocess.PIPE, timeout=timeout)


def main(baseline_path=None, probe_id='perf3b-cleanup-20261018'):
    OUT.mkdir(mode=0o700)
    assert re.fullmatch('[a-z0-9-]{1,80}',probe_id)
    baseline_path = baseline_path or ROOT/'state-client-build/mesh-perf-3b/receipts/final-continuation-readback.json'
    before = json.loads(baseline_path.read_bytes())
    pid = before['nl']['service']['MainPID']
    connectivity = run(['adb','shell','dumpsys','connectivity'])
    (OUT/'connectivity.txt').write_text(connectivity)
    vpn = [line for line in connectivity.splitlines() if line.strip().startswith('NetworkAgentInfo{') and 'ni{VPN' in line and 'OwnerUid: 10283' in line]
    assert len(vpn)==1 and 'Uids: <{0-99999}>' in vpn[0] and '10.79.0.1' in vpn[0]
    interface = re.search(r'InterfaceName: (\S+)',vpn[0]).group(1)
    assert run(['adb','shell','id','-u']).strip()=='2000'
    assert 'dev '+interface in run(['adb','shell','ip','route','get','1.1.1.1'])
    assert run(['adb','shell','pidof','com.familyconnect.app.friends']).strip()==before['phone']['process']
    run(['adb','shell','mkdir','-m','700',REMOTE])
    sampling = r'''
import json,subprocess,time
stop=time.monotonic()+35
while time.monotonic()<stop:
    raw=subprocess.check_output(['ss','-H','-tnp'],text=True,timeout=3)
    matches=[line for line in raw.splitlines() if 'pid=PID,' in line]
    print(json.dumps(dict(epoch=time.time(),sockets=matches)),flush=True)
    time.sleep(.1)
'''.replace('PID',pid)
    with (OUT/'gateway-sockets-private.jsonl').open('x') as sockets, (OUT/'sampler.stderr').open('x') as errors:
        sampler=subprocess.Popen(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','root@186.246.45.246',"python3 - <<'PY'\n"+sampling+'\nPY'],stdout=sockets,stderr=errors,text=True)
        time.sleep(1)
        fields=['http_code','http_version','ssl_verify_result','remote_ip','size_download','time_namelookup','time_connect','time_appconnect','time_starttransfer','time_total']
        arguments=['/system/bin/curl','-4','--http1.1','--noproxy','*','--retry','0','--connect-timeout','15','--max-time','30','--max-filesize','4096',
                   '-H','Accept-Encoding: identity','-H','Cache-Control: no-cache','--silent','--show-error','--output',REMOTE+'/body','--dump-header',REMOTE+'/headers',
                   '--write-out',''.join(key+'=%{'+key+'}\n' for key in fields),'https://www.cloudflare.com/cdn-cgi/trace?fc_probe='+probe_id]
        start=datetime.datetime.now(datetime.timezone.utc).isoformat()
        reply=subprocess.run(['adb','shell',shlex.join(arguments)],capture_output=True,text=True,timeout=40)
        (OUT/'curl.stdout').write_text(reply.stdout);(OUT/'curl.stderr').write_text(reply.stderr)
        metrics=dict(line.split('=',1) for line in reply.stdout.splitlines() if '=' in line)
        body=run(['adb','shell','cat',REMOTE+'/body'])
        headers=run(['adb','shell','cat',REMOTE+'/headers'])
        (OUT/'body-private.txt').write_text(body);(OUT/'headers.txt').write_text(headers)
        sampler.wait(timeout=40)
    socket_rows=[json.loads(line) for line in (OUT/'gateway-sockets-private.jsonl').read_text().splitlines()]
    matches=sum(any(metrics.get('remote_ip','INVALID')+':443' in entry for entry in row['sockets']) for row in socket_rows)
    encoding=[line.split(':',1)[1].strip() for line in headers.splitlines() if line.lower().startswith('content-encoding:')]
    result=dict(utc_start=start,purpose='post-abort production control only; no bulk baseline',
                phone_uid=2000,vpn_uid_range='0-99999',vpn_interface=interface,vpn_dns_matches_mesh=True,
                curl_exit=reply.returncode,http_status=metrics.get('http_code'),http_version=metrics.get('http_version'),tls_verify=metrics.get('ssl_verify_result'),
                body_bytes=int(float(metrics.get('size_download','0'))),observed_body_sha256=hashlib.sha256(body.encode()).hexdigest(),
                expected_nl_exit_observed='ip=186.246.45.246\n' in body,encoding=encoding or ['identity'],
                matching_production_pid_socket_samples=matches,sampler_exit=sampler.returncode,
                times_seconds={name:float(metrics[name]) for name in fields if name.startswith('time_') and name in metrics})
    result['control_pass']=(reply.returncode==0 and metrics.get('http_code')=='200' and metrics.get('ssl_verify_result')=='0'
                            and result['expected_nl_exit_observed'] and matches>0 and sampler.returncode==0 and not encoding)
    run(['adb','shell','rm','-f',REMOTE+'/body',REMOTE+'/headers'])
    run(['adb','shell','rmdir',REMOTE])
    result['phone_temporary_files_removed']=True
    with (OUT/'result.json').open('x') as handle:json.dump(result,handle,indent=2)
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
