"""Exercise existing persistent lease and denial tests at integrated RS32/Mux128."""

import json
import os
import shutil
import subprocess
import time
from prepare import ROOT, WORK, TOOLS, environment, write, digest


def main():
    os.umask(0o077)
    link = WORK / 'tests'
    if not link.exists():
        link.symlink_to(ROOT / 'tests', target_is_directory=True)
    fixture = WORK / ('security-fixtures-' + str(time.time_ns()))
    python = ROOT / 'state-client-build/field65-export16/telemost-admission-ownership-1/build/venv/bin/python'
    subprocess.run([python, '-m', 'pilot.telemost_family_fixture', '--out', fixture], cwd=ROOT, check=True, timeout=30)
    results = []
    for side, original in [('android', WORK / 'android-source/carrier'), ('gateway', WORK / 'gateway-source')]:
        source = WORK / ('security-' + side)
        if not source.exists():
            shutil.copytree(original, source)
            path = source / 'roombroker/lease_mux_test.go'
            text = path.read_text().replace('"github.com/Joker20380/family_connect/carrier/familysession"', '"github.com/Joker20380/family_connect/carrier/familysession"\n"github.com/Joker20380/family_connect/carrier/sessionprofile"')
            text = text.replace('familysession.Open(ctx, serverPipe, serverRaw, true)', 'speedLeaseOpen(ctx, serverPipe, serverRaw, true)').replace('familysession.Open(ctx, clientPipe, clientRaw, false)', 'speedLeaseOpen(ctx, clientPipe, clientRaw, false)')
            text += '''
func speedLeaseOpen(ctx context.Context, endpoint familysession.PacketEndpoint, raw []byte, server bool) (*familysession.Session,error) {
    profile,err:=sessionprofile.Parse(os.Getenv("SPEED_TEST_PROFILE"));if err!=nil{return nil,err}
    return familysession.OpenMuxReliable(profile.LocalWrite(ctx),endpoint,raw,server,profile!=sessionprofile.P0,profile.Reliable())
}
'''
            write(path,text)
        path = source / 'roombroker/lease_mux_test.go'
        text = path.read_text()
        if 'func speedExchangeLease(' not in text:
            text = text.replace('exchangeLease(fixture.ctx, fixture.client, fixture.id,', 'speedExchangeLease(test, fixture,')
            text += '''
func speedExchangeLease(test *testing.T, fixture *leaseMuxFixture, known LeaseReceipt, renew bool) (LeaseReceipt,time.Time,error) {
    test.Helper()
    deadline:=time.Now().Add(time.Second)
    stable:=0
    for stable<3 && time.Now().Before(deadline) {
        stats:=fixture.server.Stats()
        if stats.ActiveStreams==stats.ActiveSockets {stable++} else {stable=0}
        time.Sleep(5*time.Millisecond)
    }
    if stable<3 {test.Fatal("previous lease stream did not quiesce")}
    return exchangeLease(fixture.ctx,fixture.client,fixture.id,known,renew)
}
'''
            write(path,text)
        for profile in ('P0', 'P1', 'P2'):
            env = environment()
            env.update(FC_FAMILY_TEST_FIXTURES=str(fixture), SPEED_TEST_PROFILE=profile)
            log = WORK / (side + '-security-' + profile + '-' + str(time.time_ns()) + '.jsonl')
            with log.open('x') as output:
                result = subprocess.run([TOOLS / 'go/bin/go', 'test', '-race', '-json', '-count=1', '-timeout=120s', '-run', 'TestLease|TestProduct|TestMuxALPN', './roombroker', './familysession'], cwd=source, env=env, stdout=output, stderr=subprocess.STDOUT, timeout=240)
            results.append(dict(side=side, profile=profile, exit=result.returncode, log=log.name, sha256=digest(log)))
            (WORK / 'security-results.json').write_text(json.dumps(results, indent=2))
            print(json.dumps(results[-1]), flush=True)
    if any(result['exit'] for result in results):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
