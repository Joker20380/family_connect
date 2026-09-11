"""Operator-only live TCP test in a fresh systemd container; never put profiles in CI."""
import subprocess,json,time,hashlib,tarfile
from pathlib import Path
assert Path('/.dockerenv').exists(), 'Disposable Docker container required'
result={'systemd_stubbed':False,'environment':'Debian 12 Docker, private network/cgroup, shared host kernel'}
def run(*args,ok=True,input=None):
 p=subprocess.run(args,input=input,capture_output=True,text=True,timeout=60)
 if ok and p.returncode:raise RuntimeError(args[0]+' failed exit '+str(p.returncode))
 return p
assert Path('/proc/1/comm').read_text().strip()=='systemd'
assert run('systemctl','is-active','systemd-resolved').stdout.strip()=='active'
result['real_systemd_resolved']=True
helper='/usr/local/lib/family-connect-tcp/helper'
installer='/tmp/FamilyConnect-TCP-amd64/install.py'
assert not Path(helper).exists()
run('python3','-I',installer)
result['fresh_corrected_install']=True
ident=run(helper,'import',input=Path('/keys/linux.conf').read_text()).stdout.strip()
unit='family-connect-tcp@'+ident+'.service'
profile=Path('/etc/family-connect/tcp')/(ident+'.conf')
digest=hashlib.sha256(profile.read_bytes()).hexdigest()
def rules():return [json.loads(run('ip','-j',f,'rule','show').stdout) for f in ('-4','-6')]
baseline=rules()
def clean():
 assert not Path('/sys/class/net',ident).exists()
 assert not Path('/run/family-connect-tcp/active').exists()
 assert rules()==baseline
 for f in ('-4','-6'):
  assert not any(str(r.get('table'))=='64630' for r in json.loads(run('ip','-j',f,'route','show','table','all').stdout))
def health():
 run(helper,'up',ident)
 assert run('systemctl','is-active',unit).stdout.strip()=='active'
 run('resolvectl','query','--interface='+ident,'example.com')
 # Use resolved's real stub for ordinary application DNS in this disposable container.
 Path('/etc/resolv.conf').write_text('nameserver 127.0.0.53\n')
 run('getent','ahostsv4','example.com')
 for _ in range(3):
  out=run('curl','--noproxy','*','--interface',ident,'--fail','--silent','--max-time','15','https://api.ipify.org').stdout.strip()
  assert out=='185.251.89.19','unexpected egress'
try:
 clean();health();result['start_dns_https']=True
 before=len(list(Path('/var/backups/family-connect').iterdir()))
 p=run('python3','-I',installer,ok=False)
 assert p.returncode!=0 and 'Finish TCP cleanup first' in p.stdout
 assert len(list(Path('/var/backups/family-connect').iterdir()))==before
 result['active_install_refused']=True
 run(helper,'down',ident);clean();result['normal_stop_cleanup']=True
 run('python3','-I',installer)
 assert hashlib.sha256(profile.read_bytes()).hexdigest()==digest and profile.stat().st_mode&0o777==0o600
 result['reinstall_profile_preserved']=True
 health();result['restart_dns_https']=True
 run('systemctl','kill','--kill-who=main','--signal=KILL',unit)
 for _ in range(100):
  if run('systemctl','show',unit,'-p','ActiveState','--value').stdout.strip() in ('failed','inactive'):break
  time.sleep(.2)
 clean();result['sigkill_execstoppost_cleanup']=True
finally:
 run('systemctl','stop',unit,ok=False)
 clean();result['final_cleanup']=True
 Path('/tmp/acceptance-result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
