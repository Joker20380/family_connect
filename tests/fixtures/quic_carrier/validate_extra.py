from lab import *
from records import complete_records

assert (WORK/'verification.json').exists(),'run after live collection and cleanup'
assert complete_records(b'{"done":true}\n{"tail":')==[{'done':True}]
assert complete_records(b'{"utf8":"\xd0')==[]
try:
    complete_records(b'{bad}\n')
except ValueError:
    pass
else:
    raise AssertionError('corrupt complete record accepted')
target=WORK/'extra-validation'
assert not target.exists()
shutil.copytree(SOURCE,target)
write(target/'labquic/resources_test.go',(FIX/'extra_tests/resources_test.go').read_text())
subprocess.run([TOOLS/'go/bin/gofmt','-w',str(target/'labquic/resources_test.go')],check=True)
with (WORK/'extra-validation.log').open('x') as log:
    subprocess.run([TOOLS/'go/bin/go','test','-p=1','-race','-v','-run','TestLabDeadlineExtensionAndClosedLifetimes','-count=1','-timeout=30s','./labquic'],cwd=target,env=environment(),stdout=log,stderr=subprocess.STDOUT,check=True)
assert inventory(SOURCE)==json.loads((WORK/'build.json').read_text())['source_inventory']
save(WORK/'extra-validation.json',dict(log_sha256=digest(WORK/'extra-validation.log'),test_sha256=digest(FIX/'extra_tests/resources_test.go'),runtime_source_unchanged=True,scope='local memory transport only; no new Telemost traffic',jsonl='partial byte/UTF8 lines deferred; corrupt complete lines rejected'))
