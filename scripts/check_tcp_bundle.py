"""Filesystem install/rollback in disposable Docker; systemd calls explicitly stubbed."""
import hashlib,json,os,shutil,subprocess,tarfile
from pathlib import Path
assert Path('/.dockerenv').exists()
assert set(p.name for p in Path('/sys/class/net').iterdir())=={'lo'}
assert not Path('/usr/local/lib/family-connect-tcp').exists()
with tarfile.open('/bundle.tar.gz') as archive:
 for item in archive.getmembers():
  relative=Path(item.name)
  assert item.isfile() and not relative.is_absolute() and '..' not in relative.parts
  assert relative.parts[0]=='FamilyConnect-TCP-amd64'
  target=Path('/tmp/bundle')/relative;target.parent.mkdir(parents=True,exist_ok=True)
  target.write_bytes(archive.extractfile(item).read());target.chmod(item.mode&0o777)
bundle=Path('/tmp/bundle/FamilyConnect-TCP-amd64');mock=Path('/tmp/mock');mock.mkdir()
for name,body in {'resolvectl':'exit 0','pkexec':'exit 0','systemctl':'''echo "$1" >> /tmp/systemctl-calls
if [ "$1" = list-units ] && [ -e /tmp/active ]; then echo family-connect-tcp@test.service; fi
if [ "$1" = daemon-reload ] && [ -e /tmp/fail-reload ]; then rm /tmp/fail-reload; exit 1; fi
exit 0'''}.items():
 p=mock/name;p.write_text('#!/bin/sh\n'+body+'\n');p.chmod(0o755)
env={**os.environ,'PATH':str(mock)+':'+os.environ['PATH']}
def install(success):
 p=subprocess.run(['python3','-I',str(bundle/'install.py')],env=env,capture_output=True,text=True)
 assert (p.returncode==0)==success,p.stdout+p.stderr
 return p
install(True)
manifest=json.loads((bundle/'manifest.json').read_text())
installed=Path('/usr/local/lib/family-connect-tcp')
for src,name in [('bin/xray','xray'),('lib/helper','helper'),('lib/backend.py','backend.py'),('lib/profile_config.py','profile_config.py'),('lib/LICENSE','LICENSE')]:
 p=installed/name;assert hashlib.sha256(p.read_bytes()).hexdigest()==manifest['sha256'][src]
 assert p.stat().st_uid==0 and p.stat().st_mode&0o777==(0o755 if name in ('xray','helper') else 0o644)
assert subprocess.run([str(installed/'xray'),'version'],capture_output=True).returncode==0
profile=Path('/etc/family-connect/tcp/test.conf');profile.write_text('synthetic fixture, not a credential');profile.chmod(0o600)
original=(installed/'helper').read_bytes();before=len(list(Path('/var/backups/family-connect').iterdir()))
Path('/tmp/active').touch();install(False);Path('/tmp/active').unlink()
assert len(list(Path('/var/backups/family-connect').iterdir()))==before
(bundle/'lib/helper').write_bytes(original+b'\n# test upgrade\n')
install(False);assert (installed/'helper').read_bytes()==original
manifest['sha256']['lib/helper']=hashlib.sha256((bundle/'lib/helper').read_bytes()).hexdigest();(bundle/'manifest.json').write_text(json.dumps(manifest))
Path('/tmp/fail-reload').touch();install(False)
assert (installed/'helper').read_bytes()==original
install(True);assert (installed/'helper').read_bytes()==(bundle/'lib/helper').read_bytes()
assert profile.read_text()=='synthetic fixture, not a credential' and profile.stat().st_mode&0o777==0o600
for b in Path('/var/backups/family-connect').iterdir():
 assert b.stat().st_mode&0o777==0o700
 assert all(p.stat().st_mode&0o777==0o600 for p in b.iterdir())
assert set(Path('/tmp/systemctl-calls').read_text().splitlines())=={'list-units','daemon-reload'}
print(json.dumps({'fresh_install':True,'xray_exec':True,'root_modes':True,'active_refusal':True,'tamper_refusal':True,'failed_reload_rollback':True,'upgrade':True,'profile_preserved':True,'private_backups':True,'service_not_started':True,'systemd_stubbed':True}))
