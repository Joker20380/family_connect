import difflib
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[4]
WORK = ROOT / 'state-client-build/tester-p1-cohort-20261023'
BASE = ROOT / 'state-client-build/p1-lifecycle-101-20261021'
PARENT = '3a0804cd3da63135dce387d1dff9afdc4588562186abea2e5d00da1d9f5c31ae'


def main():
    os.umask(0o077)
    helpers = runpy.run_path(str(ROOT / 'tests/fixtures/speed_candidate/prepare.py'))
    digest, write, replace = helpers['digest'], helpers['write'], helpers['replace']
    assert digest(BASE / 'gateway-speed') == PARENT
    source = WORK / 'gateway-source'
    assert not source.exists()
    shutil.copytree(BASE / 'gateway-source', source)
    inventory = {str(path.relative_to(source)): digest(path) for path in sorted(source.rglob('*')) if path.is_file()}
    write(WORK / 'parent-source-inventory.json', json.dumps(inventory, indent=2, sort_keys=True)+'\n')
    environment = helpers['environment']()
    go = helpers['TOOLS'] / 'go/bin/go'
    def run(name, arguments):
        with (WORK / name).open('x') as output:
            subprocess.run([go, *arguments], cwd=source, env=environment, stdout=output,
                           stderr=subprocess.STDOUT, check=True, timeout=360)
    build = ['build','-p=1','-trimpath','-buildvcs=false','-tags=fc_perf_diagnostic','-o']
    run('baseline-rebuild.log',build+[str(WORK/'gateway-baseline-reproduced'),'./cmd/bootstrap-broker'])
    assert digest(WORK / 'gateway-baseline-reproduced') == PARENT, 'BASELINE_REPRODUCTION_FAILED'
    replace(source/'roombroker/mux_policy_linux.go',
            'func muxOperatorValue(name string) (string, error) {',
            'func muxOperatorValue(name string) (string, error) {\n return muxOperatorValueLimit(name, 32)\n}\n\nfunc muxOperatorValueLimit(name string, limit int64) (string, error) {')
    replace(source/'roombroker/mux_policy_linux.go','io.LimitReader(file, 33)','io.LimitReader(file, limit+1)')
    replace(source/'roombroker/mux_policy_linux.go','len(raw) > 32','int64(len(raw)) > limit')
    replace(source/'roombroker/speed_policy_linux.go','"encoding/hex"','"encoding/hex"\n "strings"')
    replace(source/'roombroker/speed_policy_linux.go',
            'keyHash := sha256.Sum256(identity.PublicKey[:])\n\tif target != hex.EncodeToString(keyHash[:16]) {',
            '''targets, err := muxOperatorValueLimit("speed-targets", 99)
    if err != nil { return sessionprofile.P0, err }
    selected := map[string]bool{target:true}
    if targets != "" {
        if profile != sessionprofile.P1 { return sessionprofile.P0, Code("speed_profile_configuration") }
        members := strings.Split(targets, "\\n")
        if len(members) > 3 { return sessionprofile.P0, Code("speed_profile_configuration") }
        selected = make(map[string]bool, len(members))
        for _, member := range members {
            decoded, err := hex.DecodeString(member)
            if err != nil || len(decoded) != 16 || hex.EncodeToString(decoded) != member || selected[member] {
                return sessionprofile.P0, Code("speed_profile_configuration")
            }
            selected[member] = true
        }
        if !selected[target] { return sessionprofile.P0, Code("speed_profile_configuration") }
    }
    keyHash := sha256.Sum256(identity.PublicKey[:])
    if !selected[hex.EncodeToString(keyHash[:16])] {''')
    write(source/'roombroker/speed_group_test.go',Path(__file__).with_name('speed_group_test.go').read_text())
    changed = ['roombroker/mux_policy_linux.go','roombroker/speed_policy_linux.go','roombroker/speed_group_test.go']
    subprocess.run([go.parent/'gofmt','-w',*(source/name for name in changed)],check=True)
    final = {str(path.relative_to(source)): digest(path) for path in sorted(source.rglob('*')) if path.is_file()}
    assert sorted(name for name in final if final[name] != inventory.get(name)) == sorted(changed)
    write(WORK/'source-inventory.json',json.dumps(final,indent=2,sort_keys=True)+'\n')
    patch = ''.join(''.join(difflib.unified_diff((BASE/'gateway-source'/name).read_text().splitlines(True) if (BASE/'gateway-source'/name).exists() else [],(source/name).read_text().splitlines(True),fromfile='a/'+name,tofile='b/'+name)) for name in changed)
    write(Path(__file__).with_name('gateway-group.patch'),patch)
    vector = ROOT/'tests/vectors/bootstrap-timestamps.json'
    write(WORK/'tests/vectors/bootstrap-timestamps.json',vector.read_text())
    write(WORK/'test-fixture.json',json.dumps(dict(source=str(vector),sha256=digest(vector)),indent=2)+'\n')
    run('policy-tests.log',['test','-race','-tags=fc_perf_diagnostic','./roombroker','-run','TestSpeed|TestLifecycleOnly|TestPacketPacing','-count=1','-timeout=90s'])
    run('regression-tests.log',['test','-race','-tags=fc_perf_diagnostic','./roombroker','./familysession','./reliablestream','./tcpforward','./bootstrap','-count=1','-timeout=240s'])
    binary = WORK / 'gateway-group'
    run('gateway-build.log',build+[str(binary),'./cmd/bootstrap-broker'])
    receipt = dict(binary=str(binary),sha256=digest(binary),parent_sha256=PARENT,
                   baseline_reproduced=True,source_inventory_sha256=digest(WORK/'source-inventory.json'),
                   changed_files=changed,policy_tests_sha256=digest(WORK/'policy-tests.log'),
                   regression_tests_sha256=digest(WORK/'regression-tests.log'),deployed=False)
    write(WORK/'gateway-build.json',json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
