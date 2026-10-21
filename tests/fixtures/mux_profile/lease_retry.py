"""Run opt-in lease integration with new disposable ProductStore fixtures."""
import subprocess
from prepare import WORK, TOOLS, environment

env=environment()
env['FC_FAMILY_TEST_FIXTURES']=str(WORK/'disposable-lease-fixtures2')
with (WORK/'lease-profile-fixture-race.jsonl').open('x') as output:
    result=subprocess.run([TOOLS/'go/bin/go','test','-race','-json','-count=1','-run','TestCredit128TestLease|TestLease','./roombroker'],cwd=WORK/'carrier',env=env,stdout=output,stderr=subprocess.STDOUT,timeout=180)
print('LEASE_FIXTURE_EXIT',result.returncode)
raise SystemExit(result.returncode)
