import sys,subprocess,json
from pathlib import Path
assert sys.argv[1:] in (['up'],['down']);assert __import__('os').geteuid()==0
rule=['priority','10990','to','186.246.45.246/32','ipproto','tcp','dport','4242','lookup','main']
existing=json.loads(subprocess.check_output(['ip','-j','-4','rule'],text=True))
state=Path('/run/fc-amsterdam-reticulum-pilot-route.json')
if sys.argv[1]=='up':
 assert not state.exists() and not any(r['priority']==10990 for r in existing)
 state.write_text(json.dumps(existing));state.chmod(0o600)
 subprocess.run(['ip','-4','rule','add',*rule],check=True)
else:
 assert state.exists()
 subprocess.run(['ip','-4','rule','del',*rule],check=True)
 after=json.loads(subprocess.check_output(['ip','-j','-4','rule'],text=True));assert after==json.loads(state.read_text())
 state.unlink()
print('Scoped TCP relay route',sys.argv[1])
