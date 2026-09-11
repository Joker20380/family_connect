"""Run inside a disposable NET_ADMIN/TUN container; never changes host routes."""
import json
import os
from pathlib import Path
import signal
import socket
import struct
import subprocess
import sys
import time
import uuid

sys.path.insert(0,'/work/clients/desktop')
from profile_config import parse_tcp,tcp_config
from backend import probe_interface

def cmd(*args):
    p=subprocess.run(args,capture_output=True,text=True,timeout=20)
    if p.returncode:raise RuntimeError('Container check operation failed: '+args[0]+'; '+p.stderr.strip())
    return p.stdout

def main():
    profile=parse_tcp(Path('/keys/linux.conf').read_text())
    interface='fctcp12345678';process=None
    for priority,port in [('10500','51820'),('10501','51821')]:
        cmd('ip','rule','add','priority',priority,'ipproto','17','dport',port,'prohibit')
    for family in ('-4','-6'):
        cmd('ip',family,'rule','add','priority','10630','not','fwmark','64630','lookup','64630')
    try:
        config=tcp_config(profile,interface)
        config['log']={'loglevel':'debug','error':'/run/tcp-check.log'}
        Path('/run/client.json').write_text(json.dumps(config));os.chmod('/run/client.json',0o600)
        process=subprocess.Popen(['xray','run','-config','/run/client.json'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        for _ in range(100):
            if Path('/sys/class/net',interface).exists():break
            if process.poll() is not None:raise RuntimeError('Engine failed')
            time.sleep(.05)
        cmd('ip','address','add','10.79.0.2/32','dev',interface)
        cmd('ip','-6','address','add','fd79:92::2/128','dev',interface,'nodad')
        for family in ('-4','-6'):
            cmd('ip',family,'route','add','default','dev',interface,'table','64630')
        try:probe_interface(interface,profile['server'])
        except Exception:
            diagnostic=Path('/run/tcp-check.log').read_text()[-7000:]
            for key in ('id','public_key','short_id'):diagnostic=diagnostic.replace(profile[key],'[redacted]')
            print(diagnostic,file=sys.stderr)
            raise
        # DNS packet itself must traverse TUN/VLESS, not the Docker/host resolver.
        query=struct.pack('!6H',0xFC63,0x100,1,0,0,0)+b'\x07example\x03com\0'+struct.pack('!2H',1,1)
        with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as sock:
            sock.settimeout(10);sock.setsockopt(socket.SOL_SOCKET,socket.SO_BINDTODEVICE,interface.encode()+b'\0')
            sock.sendto(query,('1.1.1.1',53));answer=sock.recv(4096)
        ident,flags,questions,answers,_,_=struct.unpack('!6H',answer[:12])
        assert ident==0xFC63 and flags&0x8000 and not flags&15 and answers>0
        invalid=tcp_config({**profile,'id':str(uuid.uuid4())},interface)
        invalid['inbounds']=[{'listen':'127.0.0.1','port':1081,'protocol':'socks','settings':{'auth':'noauth'}}]
        Path('/run/invalid.json').write_text(json.dumps(invalid));os.chmod('/run/invalid.json',0o600)
        rejected=subprocess.Popen(['xray','run','-config','/run/invalid.json'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        try:
            for _ in range(100):
                assert rejected.poll() is None
                try:
                    with socket.create_connection(('127.0.0.1',1081),timeout=.2):break
                except OSError:time.sleep(.05)
            else:raise RuntimeError('Auth check listener unavailable')
            denied=subprocess.run(['curl','--disable','--noproxy','','--socks5-hostname','127.0.0.1:1081',
                '--silent','--fail','--max-time','5','https://1.1.1.1/cdn-cgi/trace'],capture_output=True,timeout=7)
            assert denied.returncode!=0,'Unregistered VLESS identity accepted'
        finally:rejected.terminate();rejected.wait(timeout=5)
        probe_interface(interface,profile['server'])
        print(json.dumps(dict(tun_https=True,dns_over_tcp=True,both_wg_udp_ports_blocked=True,
            unregistered_identity_rejected=True)),flush=True)
    finally:
        if process:
            process.terminate();process.wait(timeout=5)
        for family in ('-4','-6'):
            cmd('ip',family,'rule','del','priority','10630','not','fwmark','64630','lookup','64630')
        assert not Path('/sys/class/net',interface).exists()

if __name__=='__main__':main()
