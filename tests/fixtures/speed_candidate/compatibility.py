"""Existing real old/new process fixture, loopback only; no product identities."""

import json
import os
import shutil
import subprocess
import time
from prepare import ROOT, WORK, ANDROID, GATEWAY, TOOLS, environment, write, digest


def main():
    os.umask(0o077)
    target = WORK / 'compatibility'
    target.mkdir(mode=0o700, exist_ok=True)
    original = (ROOT / 'tests/fixtures/mux_profile/cross_process_test.go').read_text()
    original = original.replace('"stats":mux.Stats(),', '"stats":mux.Stats(),"rs":secured.ReliabilityStats(),')
    cases = {'old-client': ANDROID / 'android-source/carrier', 'old-server': GATEWAY / 'candidate', 'new-client': WORK / 'android-source/carrier', 'new-server': WORK / 'gateway-source'}
    for name, baseline in cases.items():
        source = target / name
        if not source.exists():
            shutil.copytree(baseline, source)
        text = original
        if name.startswith('new'):
            text = text.replace('"github.com/Joker20380/family_connect/carrier/familysession"', '"github.com/Joker20380/family_connect/carrier/familysession"\n"github.com/Joker20380/family_connect/carrier/sessionprofile"')
            text = text.replace('secured,err:=familysession.OpenMux(ctx,&profilePacketConnection{Conn:connection},raw,server,os.Getenv("MUX_PROFILE_ENABLE")=="1")', '''profile,err:=sessionprofile.Parse(os.Getenv("SPEED_PROFILE"));if err!=nil {test.Fatal(err)}
secured,err:=familysession.OpenMuxReliable(profile.LocalWrite(ctx),&profilePacketConnection{Conn:connection},raw,server,os.Getenv("MUX_PROFILE_ENABLE")=="1",profile.Reliable())''')
            text = text.replace('want:=os.Getenv', '''limits:=secured.ReliabilityStats().Limits
var expected [4]int
if json.Unmarshal([]byte(os.Getenv("EXPECTED_LIMITS")),&expected)!=nil {test.Fatal("expected limits")}
if limits.LocalSend!=expected[0]||limits.LocalReceive!=expected[1]||limits.PeerReceive!=expected[2]||limits.EffectiveSend!=expected[3]||limits.LocalWriteCompletion!=(profile==sessionprofile.P2) {test.Fatal(limits,expected)}
want:=os.Getenv''')
        write(source / 'tcpforward/profile_cross_process_test.go', text)
        if not (target / (name + '.test')).exists():
            with (target / (name + '-build.log')).open('w') as output:
                subprocess.run([TOOLS / 'go/bin/go', 'test', '-c', '-race', '-o', target / (name + '.test'), './tcpforward'], cwd=source, env=environment(), stdout=output, stderr=subprocess.STDOUT, check=True, timeout=300)
        print('BUILT', name, flush=True)
    legacy, credit = 'family-connect-5n3-test-v1', 'family-connect-mux-credit128-v1'
    matrix = [
        ('old-old', 'old-client', 'old-server', 'P0', 'P0', legacy, None, None),
        ('old-new', 'old-client', 'new-server', 'P0', 'P1', credit, None, [32,32,16,16]),
        ('new-old', 'new-client', 'old-server', 'P1', 'P0', legacy, [32,32,16,16], None),
        ('new-P0', 'new-client', 'new-server', 'P0', 'P0', legacy, [8,16,16,8], [8,16,16,8]),
        ('new-P1', 'new-client', 'new-server', 'P1', 'P1', credit, [32,32,32,32], [32,32,32,32]),
        ('new-P2', 'new-client', 'new-server', 'P2', 'P2', credit, [32,32,32,32], [32,32,32,32]),
        ('return-P0', 'new-client', 'new-server', 'P0', 'P0', legacy, [8,16,16,8], [8,16,16,8]),
    ]
    results = []
    for name, client, server, client_profile, server_profile, alpn, client_limits, server_limits in matrix:
        directory = target / (name + '-' + str(time.time_ns()))
        directory.mkdir(mode=0o700)
        env = environment()
        env.update(MUX_PROFILE_FIXTURE=str(directory), MUX_PROFILE_ROLE='credentials')
        args = ['-test.run=^TestProfileCrossProcess$', '-test.v', '-test.timeout=30s']
        subprocess.run([target / 'new-server.test', *args], env=env, check=True, stdout=subprocess.DEVNULL)
        env.update(MUX_PROFILE_EXPECT=alpn, MUX_PROFILE_ENABLE='0' if server_profile == 'P0' else '1', MUX_PROFILE_ROLE='server', SPEED_PROFILE=server_profile, EXPECTED_LIMITS=json.dumps(server_limits))
        with (directory / 'server.log').open('x') as server_log, (directory / 'client.log').open('x') as client_log:
            process = subprocess.Popen([target / (server + '.test'), *args], env=env, stdout=server_log, stderr=subprocess.STDOUT)
            try:
                deadline = time.monotonic()+10
                while not (directory / 'ready.json').exists():
                    if process.poll() is not None or time.monotonic()>deadline:
                        raise RuntimeError('local fixture not ready')
                    time.sleep(.05)
                env.update(MUX_PROFILE_ROLE='client', MUX_PROFILE_ENABLE='1', SPEED_PROFILE=client_profile, EXPECTED_LIMITS=json.dumps(client_limits))
                result = subprocess.run([target / (client + '.test'), *args], env=env, stdout=client_log, stderr=subprocess.STDOUT, timeout=35)
                status = process.wait(timeout=35)
                results.append(dict(case=name, client_exit=result.returncode, server_exit=status, profile=alpn, directory=directory.name))
                (target / 'results.json').write_text(json.dumps(results, indent=2))
                assert result.returncode == status == 0, name
            finally:
                if process.poll() is None:
                    process.terminate(); process.wait(timeout=5)
                for identity in ('client.json', 'server.json'):
                    (directory / identity).unlink()
        print('PASS', name, alpn, flush=True)


if __name__ == '__main__':
    main()
