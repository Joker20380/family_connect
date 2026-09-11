import subprocess,json,hashlib,tarfile,time,os
from pathlib import Path
result={'vm':True,'kernel':os.uname().release,'repository_present':False}
def run(*args):return subprocess.run(args,check=True,capture_output=True,text=True,timeout=700)
try:
 assert Path('/proc/1/comm').read_text().strip()=='systemd'
 assert run('systemd-detect-virt').stdout.strip() in ('qemu','kvm')
 assert not Path('/source').exists() and not Path('/usr/local/lib/family-connect-tcp-updater').exists()
 archive=Path('/opt/fc-setup.tar.gz');assert hashlib.sha256(archive.read_bytes()).hexdigest()=='c16c924cac52acc5d3555c38a5260b6f4cdc530b4484a831dc35a47dab025c17'
 root=Path('/tmp/setup');root.mkdir()
 with tarfile.open(archive) as a:a.extractall(root) # Independently pinned, operator-built test artifact.
 installer=root/'FamilyConnect-TCP-Setup-0.1.0/install.py'
 run('python3','-I',str(installer));result['standalone_bootstrap']=True
 broker=Path('/usr/local/lib/family-connect-tcp-updater/broker')
 run(str(broker),'install');result['public_signed_tcp_install']=True
 installed=json.loads(Path('/var/lib/family-connect-tcp-updates/installed.json').read_text())
 assert installed['version']=='0.1.0' and installed['sequence']==1
 result['tcp_version']=installed['version']
 run('/usr/local/lib/family-connect-tcp/xray','version');result['engine_exec']=True
 assert not run('systemctl','list-units','family-connect-tcp@*.service','--state=active,activating,deactivating','--no-legend','--plain').stdout.strip()
 assert not Path('/run/family-connect-tcp/active').exists()
 result['no_vpn_started']=True
 run('python3','-I',str(installer));result['bootstrap_reinstall']=True
 p=subprocess.run([str(broker),'install','/tmp/evil'],capture_output=True,timeout=30);assert p.returncode!=0
 result['arbitrary_argument_refused']=True
 assert broker.stat().st_uid==0 and broker.stat().st_mode&0o777==0o755
 result['root_modes']=True;result['passed']=True
except Exception as error:
 result.update(passed=False,error_type=type(error).__name__,error=str(error)[:400])
finally:
 print('FC_VM_RESULT '+json.dumps(result),flush=True)
 subprocess.run(['systemctl','poweroff'],capture_output=True,timeout=30)
