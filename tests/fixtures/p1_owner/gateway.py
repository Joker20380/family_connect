"""Prepare/test/build the owner-scoped observation delta; never deploy implicitly."""
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[3]
WORK=ROOT/'state-client-build/p1-owner-acceptance-20261021'
BASE=ROOT/'state-client-build/speed-candidate-20261021'


def main():
    os.umask(0o077)
    helpers=runpy.run_path(str(ROOT/'tests/fixtures/speed_candidate/prepare.py'))
    write,replace,digest=helpers['write'],helpers['replace'],helpers['digest']
    build=json.loads((BASE/'gateway-build.json').read_text())
    assert build['sha256']=='ae527cbd0b93a5d34d10af1a5424cdf8254d79e253c9994a57520408614ce1dd'
    assert digest(BASE/'gateway-speed')==build['sha256']
    seal=json.loads((BASE/'source-seal.json').read_text())
    assert all(digest(BASE/'gateway-source'/name)==expected for name,expected in seal['gateway-protected'].items())
    source=WORK/'gateway-source';assert not source.exists()
    shutil.copytree(BASE/'gateway-source',source)
    runpy.run_path(str(Path(__file__).with_name('prepare.py')))['instrument'](source)
    write(source/'tcpforward/mux_lifecycle_test.go',Path(__file__).with_name('mux_lifecycle_test.go').read_text())
    replace(source/'roombroker/gateway.go','config := tcpforward.MuxConfig{','config := tcpforward.MuxConfig{Lifecycle: lifecyclePolicy(gateway.identity),')
    path=source/'roombroker/speed_policy_linux.go'
    write(path,path.read_text()+'''
func lifecyclePolicy(identity Identity) bool {
    target, err := muxOperatorValue("speed-target")
    keyHash := sha256.Sum256(identity.PublicKey[:])
    return err == nil && target == hex.EncodeToString(keyHash[:16])
}
''')
    path=source/'roombroker/speed_policy_other.go'
    write(path,path.read_text()+'\nfunc lifecyclePolicy(identity Identity) bool { return false }\n')
    write(source/'roombroker/lifecycle_policy_test.go','''package roombroker

import (
    "crypto/sha256"
    "encoding/hex"
    "os"
    "path/filepath"
    "testing"
)

func TestLifecycleOnlyExistingOwnerTarget(test *testing.T) {
    directory:=test.TempDir();os.Chmod(directory,0700);test.Setenv("FC_DIAGNOSTIC_CONTROL_DIR",directory)
    var owner,other Identity;owner.PublicKey[0]=1;other.PublicKey[0]=2
    hash:=sha256.Sum256(owner.PublicKey[:]);path:=filepath.Join(directory,"speed-target")
    if err:=os.WriteFile(path,[]byte(hex.EncodeToString(hash[:16])),0600);err!=nil {test.Fatal(err)}
    if !lifecyclePolicy(owner) || lifecyclePolicy(other) {test.Fatal("observer escaped owner scope")}
    os.Chmod(path,0644)
    if lifecyclePolicy(owner) {test.Fatal("unsafe operator file accepted")}
}
''')
    go=helpers['TOOLS']/'go/bin/go';env=helpers['environment']();env['GOCACHE']=str(BASE/'go-cache')
    changed=[path for path in source.rglob('*.go') if not (BASE/'gateway-source'/path.relative_to(source)).exists() or digest(path)!=digest(BASE/'gateway-source'/path.relative_to(source))]
    subprocess.run([go.parent/'gofmt','-w',*changed],check=True)
    with (WORK/'gateway-local-tests.log').open('x') as output:
        subprocess.run([go,'test','-race','-tags=fc_perf_diagnostic','./tcpforward','./sessiondiag','./roombroker','-run','TestLife|TestMux|TestLifecycle|TestSpeedPolicy','-count=1','-timeout=180s'],cwd=source,env=env,stdout=output,stderr=subprocess.STDOUT,check=True,timeout=210)
    binary=WORK/'gateway-speed'
    with (WORK/'gateway-build.log').open('x') as output:
        subprocess.run([go,'build','-p=1','-trimpath','-buildvcs=false','-tags=fc_perf_diagnostic','-o',binary,'./cmd/bootstrap-broker'],cwd=source,env=env,stdout=output,stderr=subprocess.STDOUT,check=True,timeout=600)
    (WORK/'gateway-build.json').write_text(json.dumps(dict(binary=str(binary),sha256=digest(binary),parent_sha256=build['sha256'],deployed=False,observation_only=True),indent=2))
    print('BUILT_NOT_DEPLOYED',digest(binary))


if __name__=='__main__':main()
