"""Controlled live traffic in a disposable container, never the host namespace."""
import concurrent.futures,importlib.util,json,os,socket,struct,subprocess,sys,time
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
    def probe(kind):
        start=time.monotonic()
        try:
            if kind=='tun':probe_interface(IDENT,p['server'])
            elif kind.startswith('dns'):dns(kind)
            else:
                r=subprocess.run(['/usr/bin/curl','--disable','--noproxy','','--socks5-hostname','127.0.0.1:10819',
                    '--silent','--fail','--connect-timeout','3','--max-time','5','https://1.1.1.1/cdn-cgi/trace'],capture_output=True,text=True,timeout=7)
                assert r.returncode==0 and dict(line.split('=',1) for line in r.stdout.splitlines() if '=' in line).get('ip')==p['server']
            return dict(kind=kind,ok=True,seconds=round(time.monotonic()-start,3))
        except Exception as e:return dict(kind=kind,ok=False,error=type(e).__name__,seconds=round(time.monotonic()-start,3))
    try:
        process=subprocess.Popen(['xray','run','-config',str(path)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        for _ in range(100):
            if Path('/sys/class/net',IDENT).exists():break
            assert process.poll() is None;time.sleep(.05)
        h.command('ip','address','add','10.79.0.2/32','dev',IDENT)
        h.command('ip','-6','address','add','fd79:92::2/128','dev',IDENT,'nodad')
        h.install_routes(IDENT,p['server'])
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
            for _ in range(24):
                rows.append(list(pool.map(probe,['tun','socks','dns','dns_tcp','dns_direct'])));time.sleep(2)
    finally:
        try:h.remove_routes(IDENT,p['server'])
        finally:
            if process:process.terminate();process.wait(timeout=5)
    assert not Path('/sys/class/net',IDENT).exists()
    report={kind:dict(passed=sum(x['ok'] for row in rows for x in row if x['kind']==kind),total=len(rows)) for kind in ['tun','socks','dns','dns_tcp','dns_direct']}
    report['cleanup']=True
    report['failures']=[dict(round=i+1,**x) for i,row in enumerate(rows) for x in row if not x['ok']]
    print(json.dumps(report),flush=True)
    if not all(x['ok'] for row in rows for x in row):raise SystemExit(1)
if __name__=='__main__':main()
