"""Root lifecycle helper for the isolated, fixed fcawg31 pilot service."""
from pathlib import Path
import subprocess,sys,time
BASE=Path('/opt/apps/family_connect/awg31-beta02')
IFACE='fcawg31'
def run(*args,check=True):return subprocess.run(args,check=check,capture_output=True,text=True,timeout=15)
if sys.argv[1]=='firewall':
    prefix=''
    for family,table in [('inet','family_connect_awg31'),('ip','family_connect_awg31_nat')]:
        if run('nft','list','table',family,table,check=False).returncode==0:prefix+=f'delete table {family} {table}\n'
    subprocess.run(['nft','-f','-'],input=prefix+(BASE/'firewall.nft').read_text(),text=True,capture_output=True,check=True,timeout=15)
elif sys.argv[1]=='configure':
    for _ in range(100):
        if Path('/run/amneziawg/fcawg31.sock').exists():break
        time.sleep(.1)
    else:raise SystemExit('AWG IPC readiness timeout')
    run(str(BASE/'awg'),'setconf',IFACE,str(BASE/'server.conf'))
    run('ip','address','replace','10.80.0.1/24','dev',IFACE)
    run('ip','-6','address','replace','fd80:92::1/64','dev',IFACE)
    run('ip','link','set',IFACE,'mtu','1280','up')
elif sys.argv[1]=='cleanup':
    run('ip','link','delete',IFACE,check=False)
    for family,table in [('inet','family_connect_awg31'),('ip','family_connect_awg31_nat')]:run('nft','delete','table',family,table,check=False)
else:raise SystemExit('Unknown action')
