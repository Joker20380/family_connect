"""Install a new isolated Amsterdam AWG3.1 pilot. Root; JSON stdin holds HPK.

Upload the two pinned binaries and lifecycle helper to --bundle first.
Refuses to overwrite any previous service/config; does not modify existing WG.
"""
from pathlib import Path
import argparse,base64,hashlib,json,os,shutil,subprocess
p=argparse.ArgumentParser();p.add_argument('--bundle',type=Path,required=True);a=p.parse_args()
BASE=Path('/opt/apps/family_connect/awg31-beta02');UNIT=Path('/etc/systemd/system/family-connect-awg31.service')
def run(*args,check=True):return subprocess.run(args,check=check,capture_output=True,text=True,timeout=30)
assert os.geteuid()==0 and not BASE.exists() and not UNIT.exists(),'Existing pilot preserved'
assert run('ip','link','show','fcawg31',check=False).returncode!=0
assert ':443 ' not in run('ss','-H','-lun').stdout
assert '10.80.0.' not in run('ip','-4','route','show','table','all').stdout
for family,table in [('inet','family_connect_awg31'),('ip','family_connect_awg31_nat')]:assert run('nft','list','table',family,table,check=False).returncode!=0
assert run('sysctl','-n','net.ipv4.ip_forward').stdout.strip()=='1'
expected={'amneziawg-go':'e7f00e47d6df853ade5dcd2fe79240f01ff897d75088c768316a444c27c87e0f','awg':'906d6795af1dd4adee7b11bf1e7fa133d4795c8a8d6e2099b34a026f810a3278'}
for name,digest in expected.items():assert hashlib.sha256((a.bundle/name).read_bytes()).hexdigest()==digest
payload=json.load(__import__('sys').stdin)
for key in ['client_public_key','header_protection_key']:assert len(base64.b64decode(payload[key],validate=True))==32
before=run('wg','show','fcams','allowed-ips').stdout
BASE.mkdir(mode=0o700)
for name in ['amneziawg-go','awg','awg31_service.py','LICENSE-go','LICENSE-tools']:
    shutil.copyfile(a.bundle/name,BASE/name);os.chmod(BASE/name,0o755 if name in expected else 0o600)
private=run('wg','genkey').stdout.strip()
public=subprocess.run(['wg','pubkey'],input=private,text=True,capture_output=True,check=True).stdout.strip()
params='Jc = 3\nJmin = 40\nJmax = 80\nS1 = 16\nS2 = 16\nS3 = 16\nS4 = 16\nH1 = 1\nH2 = 2\nH3 = 3\nH4 = 4\nHeaderProtectionKey = '+payload['header_protection_key']+'\nContentPaddingAddition = 0-32\nRandomTrailers = on\nDisableCookies = off\n'
def write(path,data,mode):
    with path.open('x') as f:os.fchmod(f.fileno(),mode);f.write(data)
write(BASE/'server.conf','[Interface]\nPrivateKey = '+private+'\nListenPort = 443\n'+params+'[Peer]\nPublicKey = '+payload['client_public_key']+'\nAllowedIPs = 10.80.0.2/32, fd80:92::2/128\n',0o600)
write(BASE/'firewall.nft','''table inet family_connect_awg31 {
 chain input { type filter hook input priority filter; policy accept;
  iifname "fcawg31" ip protocol icmp accept
  iifname "fcawg31" counter drop
 }
 chain forward { type filter hook forward priority filter; policy accept;
  iifname "fcawg31" meta nfproto ipv6 counter drop
  iifname "fcawg31" ct state invalid drop
  iifname "fcawg31" ip daddr { 0.0.0.0/8, 10.0.0.0/8, 100.64.0.0/10, 127.0.0.0/8, 169.254.0.0/16, 172.16.0.0/12, 192.168.0.0/16, 224.0.0.0/3 } counter drop
  iifname "fcawg31" tcp dport 25 drop
  iifname "fcawg31" oifname "ens3" meta nfproto ipv4 counter accept
  iifname "fcawg31" counter drop
  oifname "fcawg31" ct state established,related counter accept
  oifname "fcawg31" counter drop
 }
}
table ip family_connect_awg31_nat {
 chain postrouting { type nat hook postrouting priority srcnat; policy accept;
  ip saddr 10.80.0.0/24 oifname "ens3" masquerade
 }
}
''',0o600)
write(UNIT,f'''[Unit]
Description=Family Connect isolated Amsterdam AWG 3.1 pilot
After=network-online.target
Wants=network-online.target
[Service]
Type=simple
Environment=LOG_LEVEL=silent
UMask=0077
ExecStartPre=/usr/bin/python3 {BASE}/awg31_service.py firewall
ExecStart={BASE}/amneziawg-go -f fcawg31
ExecStartPost=/usr/bin/python3 {BASE}/awg31_service.py configure
ExecStopPost=/usr/bin/python3 {BASE}/awg31_service.py cleanup
Restart=on-failure
RestartSec=3
TimeoutStartSec=25
TimeoutStopSec=15
MemoryMax=192M
TasksMax=128
NoNewPrivileges=yes
ProtectHome=yes
[Install]
WantedBy=multi-user.target
''',0o644)
try:
    run('systemctl','daemon-reload');run('systemctl','start','family-connect-awg31.service')
    assert run('systemctl','is-active','family-connect-awg31.service').stdout.strip()=='active'
    assert run('wg','show','fcams','allowed-ips').stdout==before
    assert run(str(BASE/'awg'),'show','fcawg31','public-key').stdout.strip()==public
    run('systemctl','enable','family-connect-awg31.service')
except BaseException:
    run('systemctl','stop','family-connect-awg31.service',check=False)
    raise SystemExit('AWG pilot startup failed; service stopped, private files preserved')
print(json.dumps({'server_public_key':public,'client_public_key':payload['client_public_key'],'port':443,'ipv4':'10.80.0.2/32','interface':'fcawg31','old_wg_peers_preserved':True,'active':True,'binary_sha256':expected}))
