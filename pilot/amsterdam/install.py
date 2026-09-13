"""One-device native WG pilot. Run only on the explicitly authorized Amsterdam VPS.

Reads a client PUBLIC key from stdin. Gateway private key is generated on-server.
Refuses existing deployment paths; no client/signing secret inputs.
"""
import base64,json,os,subprocess,sys
from pathlib import Path

HOST='186.246.45.246'
ROOT=Path('/opt/apps/family_connect/amsterdam')
WG=Path('/etc/wireguard/fcams.conf')
FIREWALL=Path('/etc/systemd/system/family-connect-ams-firewall.service')
FORWARD=Path('/etc/sysctl.d/70-family-connect-ams.conf')

def run(*args):return subprocess.check_output(args,text=True).strip()
def write(path,value,mode=0o600):
    path.parent.mkdir(parents=True,exist_ok=True)
    fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,mode)
    with os.fdopen(fd,'w') as f:f.write(value)

def main():
    assert os.geteuid()==0,'root required'
    addresses=json.loads(run('ip','-j','-4','addr','show','dev','ens3'))
    assert any(a['local']==HOST for item in addresses for a in item['addr_info']),'wrong host'
    public=sys.stdin.read(256).strip();decoded=base64.b64decode(public,validate=True)
    assert len(decoded)==32 and any(decoded) and base64.b64encode(decoded).decode()==public,'invalid public key'
    assert not any(p.exists() for p in (ROOT,WG,FIREWALL,FORWARD)),'existing deployment; inspect before changing'
    assert not run('nft','list','tables'),'existing firewall; inspect before changing'
    baseline=dict(ipv4_forward=run('sysctl','-n','net.ipv4.ip_forward'),ipv6_forward=run('sysctl','-n','net.ipv6.conf.all.forwarding'))
    ROOT.mkdir(parents=True,mode=0o700)
    os.chmod(ROOT,0o700)
    write(ROOT/'baseline.json',json.dumps(baseline)+'\n')
    private=run('wg','genkey');write(ROOT/'server.key',private+'\n')
    server_public=subprocess.check_output(['wg','pubkey'],input=private+'\n',text=True).strip()
    write(ROOT/'server.pub',server_public+'\n',0o644)
    write(WG,f'[Interface]\nPrivateKey = {private}\nAddress = 10.79.0.1/24, fd79:92::1/64\nListenPort = 51820\nMTU = 1280\n\n[Peer]\nPublicKey = {public}\nAllowedIPs = 10.79.0.2/32, fd79:92::2/128\n')
    firewall='''table inet family_connect_ams {
 chain input {
  type filter hook input priority 0; policy accept;
  iifname "fcams" ip protocol icmp accept
  iifname "fcams" counter drop
 }
 chain forward {
  type filter hook forward priority 0; policy accept;
  iifname "fcams" meta nfproto ipv6 counter drop
  iifname "fcams" ct state invalid drop
  iifname "fcams" ip daddr { 0.0.0.0/8, 10.0.0.0/8, 100.64.0.0/10, 127.0.0.0/8, 169.254.0.0/16, 172.16.0.0/12, 192.168.0.0/16, 224.0.0.0/4, 240.0.0.0/4 } counter drop
  iifname "fcams" tcp dport 25 counter drop
  iifname "fcams" oifname "ens3" meta nfproto ipv4 counter accept
  iifname "fcams" counter drop
  oifname "fcams" ct state established,related counter accept
  oifname "fcams" counter drop
 }
}
table ip family_connect_ams_nat {
 chain postrouting {
  type nat hook postrouting priority srcnat; policy accept;
  ip saddr 10.79.0.0/24 oifname "ens3" masquerade
 }
}
'''
    write(ROOT/'firewall.nft',firewall,0o644)
    subprocess.run(['nft','--check','--file',str(ROOT/'firewall.nft')],check=True)
    write(FIREWALL,f'''[Unit]
Description=Family Connect Amsterdam pilot firewall
Before=wg-quick@fcams.service
[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/sbin/nft -f {ROOT}/firewall.nft
ExecStop=/usr/sbin/nft delete table inet family_connect_ams
ExecStop=/usr/sbin/nft delete table ip family_connect_ams_nat
[Install]
WantedBy=multi-user.target
''',0o644)
    write(Path('/etc/systemd/system/wg-quick@fcams.service.d/firewall.conf'),'[Unit]\nRequires=family-connect-ams-firewall.service\nAfter=family-connect-ams-firewall.service\n',0o644)
    write(FORWARD,'net.ipv4.ip_forward = 1\n',0o644)
    subprocess.run(['sysctl','-p',str(FORWARD)],check=True,stdout=subprocess.DEVNULL)
    subprocess.run(['systemctl','daemon-reload'],check=True)
    subprocess.run(['systemctl','enable','--now','wg-quick@fcams.service'],check=True)
    assert run('systemctl','is-active','wg-quick@fcams.service')=='active'
    print(json.dumps(dict(host=HOST,interface='fcams',port=51820,server_public_key=server_public,wireguard=run('wg','--version'),service='active',ipv6_egress=False)))

if __name__=='__main__':main()
