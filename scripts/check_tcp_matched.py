"""Controlled live traffic in a disposable container, never the host namespace."""
import re,threading,concurrent.futures,importlib.util,json,os,socket,struct,subprocess,sys,time
from pathlib import Path
sys.path.insert(0,'/desktop')
from profile_config import parse_tcp,tcp_config
from backend import probe_interface
spec=importlib.util.spec_from_file_location('helper','/fix/tcp-helper.py')
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
IDENT='fctcp12345678'
def dns(kind):
    query=struct.pack('!6H',0xfc65,0x100,1,0,0,0)+b'\x07example\x03com\0'+struct.pack('!2H',1,1)
    with socket.socket(socket.AF_INET,socket.SOCK_STREAM if kind=='dns_tcp' else socket.SOCK_DGRAM) as s:
        s.settimeout(3)
        if kind=='dns_direct':s.setsockopt(socket.SOL_SOCKET,socket.SO_MARK,64630)
        else:s.setsockopt(socket.SOL_SOCKET,socket.SO_BINDTODEVICE,IDENT.encode()+b'\0')
        if kind=='dns_tcp':
            s.connect(('1.1.1.1',53));s.sendall(struct.pack('!H',len(query))+query)
            def exact(n):
                data=b''
                while len(data)<n:
                    part=s.recv(n-len(data))
                    if not part:raise EOFError()
                    data+=part
                return data
            response=exact(struct.unpack('!H',exact(2))[0])
        else:s.sendto(query,('1.1.1.1',53));response=s.recv(4096)
    identity,flags,questions,answers,_,_=struct.unpack('!6H',response[:12])
    assert identity==0xfc65 and flags&0x8000 and not flags&15 and answers>0
def main():
    if not Path('/.dockerenv').is_file():raise RuntimeError('Disposable Docker container required')
    if set(p.name for p in Path('/sys/class/net').iterdir())!={'lo','eth0'}:raise RuntimeError('Unexpected network namespace')
    p=parse_tcp(Path('/keys/linux.conf').read_text());config=tcp_config(p,IDENT)
    config['inbounds'].append(dict(listen='127.0.0.1',port=10819,protocol='socks',settings={'auth':'noauth'}))
    path=Path('/run/client.json');path.write_text(json.dumps(config));path.chmod(0o600)
    h.check_routing_available();process=None;rows=[]
    samples=[];stop=threading.Event()
    def monitor():
        while not stop.is_set():
            raw=h.command('ss','-tin','dst',p['server'],check=False).stdout
            samples.append(dict(t=round(time.monotonic()-started,3),syn_sent=raw.count('SYN-SENT'),
                established=raw.count('ESTAB'),retrans=re.findall(r'\bretrans:(\d+/\d+)',raw),
                rto=re.findall(r'rto:(\d+)',raw)))
            stop.wait(.25)
    def probe(kind):
        start=time.monotonic()
        stamp=round(start-started,3)
        try:
            if kind.startswith('dns'):
                dns(kind)
                return dict(kind=kind,t=stamp,ok=True,seconds=round(time.monotonic()-start,3))
            args=['/usr/bin/curl','--disable','--noproxy','*','--silent','--show-error','--fail',
                '--connect-timeout','3','--max-time','5','--output','/dev/null',
                '--write-out','%{http_code} %{time_connect} %{time_appconnect} %{time_starttransfer} %{time_total}',
                'https://1.1.1.1/cdn-cgi/trace']
            if kind=='tun':args[2:2]=['--interface',IDENT]
            if kind=='socks':
                args[2:2]=['--socks5-hostname','127.0.0.1:10819']
                args[args.index('--noproxy')+1]=''
            r=subprocess.run(args,capture_output=True,text=True,timeout=7,
                **({'user':65534,'group':65534} if kind=='direct' else {}))
            values=r.stdout.split()
            return dict(kind=kind,t=stamp,ok=r.returncode==0 and values[0]=='200',code=r.returncode,
                http=values[0] if values else None,timing=values[1:],
                error=r.stderr.strip()[:250],seconds=round(time.monotonic()-start,3))
        except Exception as e:return dict(kind=kind,t=stamp,ok=False,error=type(e).__name__,seconds=round(time.monotonic()-start,3))
    started=time.monotonic();started_wall=time.time();watch=None
    try:
        process=subprocess.Popen(['xray','run','-config',str(path)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        for _ in range(100):
            if Path('/sys/class/net',IDENT).exists():break
            assert process.poll() is None;time.sleep(.05)
        h.command('ip','address','add','10.79.0.2/32','dev',IDENT)
        h.command('ip','-6','address','add','fd79:92::2/128','dev',IDENT,'nodad')
        h.install_routes(IDENT,p['server'])
        h.command('ip','rule','add','priority','10500','uidrange','65534-65534','lookup','main')
        route=json.loads(h.command('ip','-j','route','get','1.1.1.1','uid','65534').stdout)
        assert route[0]['dev']=='eth0'
        watch=threading.Thread(target=monitor);watch.start()
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
            for _ in range(24):
                rows.append(list(pool.map(probe,['direct','tun','socks','dns','dns_direct'])));print(json.dumps({'round':len(rows),'results':rows[-1]}),flush=True);time.sleep(2)
    finally:
        stop.set()
        if watch:watch.join(timeout=3)
        h.command('ip','rule','del','priority','10500','uidrange','65534-65534','lookup','main',check=False)
        try:h.remove_routes(IDENT,p['server'])
        finally:
            if process:process.terminate();process.wait(timeout=5)
    assert not Path('/sys/class/net',IDENT).exists()
    report={kind:dict(passed=sum(x['ok'] for row in rows for x in row if x['kind']==kind),total=len(rows)) for kind in ['direct','tun','socks','dns','dns_direct']}
    report['cleanup']=True
    report['failures']=[dict(round=i+1,**x) for i,row in enumerate(rows) for x in row if not x['ok']]
    report['started_wall']=started_wall
    report['tcp_samples']=samples
    report['timing_fields']=['connect','appconnect','starttransfer','total']
    Path('/results/matched.json').write_text(json.dumps({'summary':report,'rounds':rows},indent=2))
    print(json.dumps({k:v for k,v in report.items() if k!='tcp_samples'}),flush=True)
    if not all(x['ok'] for row in rows for x in row):raise SystemExit(1)
if __name__=='__main__':main()
