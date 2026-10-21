"""Add128 counterparts of accepted persistent-lease and fresh-floor rejection tests."""

import subprocess
from prepare import WORK, TOOLS, environment

source=WORK/'carrier/roombroker/lease_mux_test.go'
text=source.read_text()
names=['TestLeaseRealFamilyMuxPersistentTCP','TestLeaseControlRevocationBeforeConfirmation']
parts=[]
for name in names:
    start=text.index('func '+name+'(')
    end=text.find('\nfunc ',start+5)
    body=text[start:end if end!=-1 else len(text)]
    body=body.replace(name,'TestCredit128'+name).replace('newLeaseMuxFixture(test, true)','newLeaseMuxProfileFixture(test, true, true)')
    body=body.replace('fixture := newLeaseMuxProfileFixture(test, true, true)', 'fixture := newLeaseMuxProfileFixture(test, true, true)\n\tif fixture.client.Stats().Window != 131072 || fixture.server.Stats().Window != 131072 { test.Fatal("profile not selected") }')
    parts.append(body)
addition='\n'.join(parts)
assert 'func TestCredit128TestLease' not in text
patch='*** Begin Patch\n*** Update File: '+str(source)+'\n@@\n'+''.join('+'+line+'\n' for line in addition.splitlines())+'*** End Patch\n'
subprocess.run(['apply_patch',patch],check=True)
subprocess.run([TOOLS/'go/bin/gofmt','-w',source],check=True)
with (WORK/'lease-profile-race.jsonl').open('x') as output:
    result=subprocess.run([TOOLS/'go/bin/go','test','-race','-json','-count=1','-run','TestCredit128TestLease','./roombroker'],cwd=WORK/'carrier',env=environment(),stdout=output,stderr=subprocess.STDOUT)
print('LEASE_PROFILE_EXIT',result.returncode)
raise SystemExit(result.returncode)
