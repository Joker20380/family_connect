from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent / 'gateway-seed-supervisor-1'
GO = ROOT.parent / 'diag-source-freeze-1/resume-tools/go/bin/go'
FIXTURES = Path('/tmp/fc-seed-trigger-fixtures-fresh')


def prepare():
    target = ROOT / 'validation/carrier'
    shutil.copytree(ROOT / 'source/carrier', target, dirs_exist_ok=True)
    prior = BASE / 'validation/carrier'
    for relative in ('telemost/auth.go', 'telemost/session.go', 'telemost/signaling.go', 'telemost/rejoin_fixture.go', 'roombroker/rejoin_fixture.go'):
        text = (prior / relative).read_text()
        if relative == 'telemost/session.go':
            text = text.replace('type Session struct {', 'type Session struct {\n\tacceptanceBoundary', 1)
        if relative == 'telemost/signaling.go':
            text = text.replace('conn.SetReadLimit(wsReadLimit)', 'conn.SetReadLimit(wsReadLimit)\n\tconn, err = s.researchSignalingBoundary(conn)\n\tif err != nil { return err }', 1)
        (target / relative).write_text(text)
    shutil.copytree(prior / 'internal/rejoinfixture', target / 'internal/rejoinfixture', dirs_exist_ok=True)
    text = (prior / 'bootstrap/rejoin_capability_test.go').read_text()
    text = text.replace('//go:build sameroomfixture', '//go:build sameroomfixture && seedacceptance')
    text = text.replace('TestSupervisorRealPionContinuity', 'TestAcceptanceRealPionContinuity')
    text = text.replace('func TestAcceptanceRealPionContinuity(test *testing.T) {', '''func TestAcceptanceRealPionContinuity(test *testing.T) { acceptanceRealPion(test, false) }
func TestAcceptanceRealPionReceiptFailure(test *testing.T) { if os.Geteuid()==0 {test.Skip("permission fault requires non-root fixture")}; acceptanceRealPion(test, true) }
func acceptanceRealPion(test *testing.T, receiptFailure bool) {''')
    needle = '\tdefer cancel()\n\tpath := gatewayProfile(test)'
    replacement = '''\tdefer cancel()
    var err error
    controlDir:=test.TempDir(); os.Chmod(controlDir,0700)
    if os.Geteuid()==0 {controlDir,err=os.MkdirTemp("/run","fc-seed-acceptance-media-");if err!=nil{test.Fatal(err)};defer os.RemoveAll(controlDir)}
    binding,err:=acceptanceProcessBinding();if err!=nil{test.Fatal(err)}
    policy:=SeedAcceptanceConfig{Schema:1,Enabled:true,BinarySHA256:binding.BinarySHA256,Directory:controlDir,ExpiresAt:time.Now().Add(time.Minute)}
    var stopControl func()
    if os.Geteuid()==0 {policyRaw,_:=json.Marshal(policy);policyPath:=filepath.Join(controlDir,"policy.json");if os.WriteFile(policyPath,policyRaw,0600)!=nil{test.Fatal("root policy fixture")};ctx,stopControl,err=StartSeedAcceptance(ctx,policyPath)} else {ctx,stopControl,err=startSeedAcceptance(ctx,policy,binding,uint32(os.Geteuid()))}
    if err!=nil{test.Fatal(err)};defer stopControl()
    control:=ctx.Value(acceptanceContextKey{}).(*seedAcceptance)
    path := gatewayProfile(test)'''
    assert needle in text
    text = text.replace(needle, replacement, 1)
    needle = '\toldID, err := provider.CloseSeed(1011)\n\tif err != nil {\n\t\ttest.Fatal(err)\n\t}'
    replacement = '''\toldID:=provider.SeedIDForAcceptance()
    binding.Generation=1;binding.RoomHash=initial.PacketEndpoint.(*telemost.Session).ResearchRoomHash()
    command:=SeedAcceptanceCommand{Schema:1,Command:acceptanceCommand,Binding:binding,Nonce:fmt.Sprintf("%064x",time.Now().UnixNano()),ArmedAt:time.Now(),ExpiresAt:time.Now().Add(15*time.Second)}
    invalid:=command;invalid.Binding.Generation++
    invalidRaw,_:=json.Marshal(invalid)
    invalidConnection,err:=net.DialUnix("unix",nil,&net.UnixAddr{Name:control.listener.Addr().String(),Net:"unix"});if err!=nil{test.Fatal(err)}
    invalidConnection.SetDeadline(time.Now().Add(3*time.Second));invalidConnection.Write(invalidRaw);invalidConnection.CloseWrite();rejection,_:=io.ReadAll(invalidConnection);invalidConnection.Close()
    if string(rejection)!="REJECTED\\n" || initial.PacketEndpoint.(*telemost.Session).SignalingReadFailure().Kind!="" {test.Fatal("invalid command affected real seed")}
    if receiptFailure {if os.Chmod(controlDir,0500)!=nil{test.Fatal("receipt failure injection")};defer os.Chmod(controlDir,0700)}
    request,_:=json.Marshal(command)
    connection,err:=net.DialUnix("unix",nil,&net.UnixAddr{Name:control.listener.Addr().String(),Net:"unix"});if err!=nil{test.Fatal(err)}
    connection.SetDeadline(time.Now().Add(3*time.Second));connection.Write(request);connection.CloseWrite()
    response,_:=io.ReadAll(connection);connection.Close()
    if string(response)!="CONSUMED\\n"{test.Fatal("control rejected")}
'''
    assert needle in text
    text = text.replace(needle, replacement, 1)
    text = text.replace('\tpostDescriptor := bootstrapCached(secondRaw)', '''\tstopControl()
    if _,err:=os.Lstat(filepath.Join(controlDir,"seed-acceptance.sock"));!receiptFailure && !os.IsNotExist(err){test.Fatal("control not cleaned")}
    if control.consume(command,time.Now()){test.Fatal("replay after cleanup")}
    entries,_:=os.ReadDir(controlDir);readerSeen,recovered:=false,false
    for _,entry:=range entries {if entry.Name()=="policy.json"{continue};raw,_:=os.ReadFile(filepath.Join(controlDir,entry.Name()));var receipt SeedAcceptanceReceipt;if json.Unmarshal(raw,&receipt)==nil {readerSeen=readerSeen||receipt.ReaderObserved1011;recovered=recovered||receipt.RecoveryOutcome=="RECOVERED";encoded,_:=json.Marshal(receipt);test.Log("TRIGGER_RECEIPT",string(encoded))}}
    if !receiptFailure && (!readerSeen || !recovered){test.Fatal("missing independent trigger reader/recovery receipt")}
    if receiptFailure {if readerSeen || recovered {test.Fatal("receipt write failure not exercised")};os.Chmod(controlDir,0700);os.Remove(filepath.Join(controlDir,"seed-acceptance.sock"));test.Log("RECEIPT_FAILURE_PROTOCOL_CONTINUES true")}
    postDescriptor := bootstrapCached(secondRaw)''')
    (target / 'bootstrap/rejoin_capability_test.go').write_text(text)
    provider = target / 'internal/rejoinfixture/provider.go'
    provider.write_text(provider.read_text() + '''
func (provider *Provider) SeedIDForAcceptance() string {
    provider.mu.Lock();defer provider.mu.Unlock()
    for _,peer:=range provider.peers {if peer.label=="Family bootstrap gateway"{return peer.id}}
    return ""
}
''')
    subprocess.run([str(GO.with_name('gofmt')), '-w', str(target)], check=True)


def run(name, tree, pattern, packages, tags='', race=False, count=1):
    name = (sys.argv[2]+'-' if len(sys.argv)>2 else '') + name
    env = dict(os.environ, GOTOOLCHAIN='local', GOPROXY='off', GOSUMDB='off', GOCACHE='/tmp/fc-seed-read-gocache', FC_FAMILY_TEST_FIXTURES=str(FIXTURES), PYTHONDONTWRITEBYTECODE='1')
    assert not any(key.startswith('FC_TEST_LIVE') and value for key, value in env.items())
    command = [str(GO), 'test', '-json', '-count='+str(count), '-timeout=8m']
    if tags:
        command += ['-tags='+tags]
    if race:
        command += ['-race']
    command += ['-run', pattern] + packages
    started = time.time()
    source = {str(path.relative_to(tree)): hashlib.sha256(path.read_bytes()).hexdigest() for path in (tree / 'carrier').rglob('*.go')}
    with (ROOT / 'receipts' / (name+'.jsonl')).open('x') as output:
        result = subprocess.run(command, cwd=tree / 'carrier', env=env, stdout=output, stderr=subprocess.STDOUT, timeout=530)
    receipt = dict(command=command, exit_code=result.returncode, elapsed=time.time()-started, source=source)
    (ROOT / 'receipts' / (name+'.json')).write_text(json.dumps(receipt, indent=2)+'\n')
    print(name, result.returncode, round(receipt['elapsed'], 1), flush=True)
    return result.returncode


if __name__ == '__main__':
    if sys.argv[1] == 'prepare':
        prepare()
    elif sys.argv[1] == 'media':
        assert not FIXTURES.exists(), 'do not overwrite credentials'
        generator = ROOT.parent / 'gateway-same-room-rejoin-proof-1/source/pilot/telemost_family_fixture.py'
        subprocess.run(['/tmp/fc-lease-venv/bin/python', str(generator), '--out', str(FIXTURES)], env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(ROOT.parents[2])), check=True)
        sys.exit(run('media-first', ROOT / 'validation', '^TestAcceptanceRealPionContinuity$', ['./bootstrap'], 'seedacceptance,sameroomfixture'))
    elif sys.argv[1] == 'race':
        sys.exit(run('trigger-race3', ROOT / 'source', '^TestAcceptance', ['./telemost', './bootstrap'], 'seedacceptance', True, 3))
    elif sys.argv[1] == 'hardening':
        statuses={}
        statuses['trigger']=run('trigger-race3',ROOT/'source','^TestAcceptance',['./telemost','./bootstrap'],'seedacceptance',True,3)
        statuses['research_full']=run('full-research',ROOT/'source','.', ['./...'],'seedacceptance')
        (ROOT/'receipts/hardened-batch.json').write_text(json.dumps(statuses,indent=2)+'\n')
    elif sys.argv[1] == 'batch':
        security='^Test(NegativeAuthMandatory.*|Lease.*|ActiveExpiryRevocationAndGlobalBound|ExpiredLeaseAndBounds|StopSource.*|SeedRecovery.*|Fatal.*|Signaling.*|Supervisor.*)$'
        statuses={}
        statuses['trigger']=run('trigger-race3',ROOT/'source','^TestAcceptance',['./telemost','./bootstrap'],'seedacceptance',True,3)
        statuses['media']=run('media-race3',ROOT/'validation','^TestAcceptanceRealPion(Continuity|ReceiptFailure)$',['./bootstrap'],'seedacceptance,sameroomfixture',True,3)
        statuses['candidate_security']=run('security-candidate-race3',ROOT/'source',security,['./bootstrap','./telemost','./roombroker','./familysession','./cmd/bootstrap-broker'],'seedacceptance',True,3)
        statuses['baseline_security']=run('security-baseline-race3',BASE/'source',security,['./bootstrap','./telemost','./roombroker','./familysession','./cmd/bootstrap-broker'],'',True,3)
        statuses['baseline_full']=run('full-baseline',BASE/'source','.', ['./...'])
        statuses['public_full']=run('full-public',ROOT/'source','.', ['./...'])
        statuses['research_full']=run('full-research',ROOT/'source','.', ['./...'],'seedacceptance')
        (ROOT/'receipts'/((sys.argv[2]+'-' if len(sys.argv)>2 else '')+'batch.json')).write_text(json.dumps(statuses,indent=2)+'\n')
