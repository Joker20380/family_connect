"""Adverse-condition checks for the isolated lab, using only its synthetic peers."""
import base64
import os
from pathlib import Path
import time


def emit(event, **fields):
    import json
    print(json.dumps({'event': event, **fields}), flush=True)


def ping(run, *, size=None):
    args = ['ping', '-n', '-c', '1', '-W', '1']
    if size is not None:
        args += ['-M', 'do', '-s', str(size)]
    return run(args + ['10.90.0.1'], check=False)


def ready(run, timeout=30):
    start = time.monotonic()
    while time.monotonic() - start < timeout:
        if ping(run).returncode == 0:
            return round(time.monotonic() - start, 4)
    raise RuntimeError('Tunnel did not recover within bounded probe window')


def shape(run, namespace, loss):
    for ns, link in ((None, 'fc31c'), (namespace, 'fc31s')):
        run(['tc', 'qdisc', 'replace', 'dev', link, 'root', 'netem', 'delay', '35ms',
             'rate', '20mbit', 'loss', str(loss) + '%'], ns=ns)


def preflight(run, tool, namespace, client, server, directory):
    cfg = Path(directory) / (server + '.conf')
    original = cfg.read_text()
    trial = Path(directory) / 'negative.conf'
    def apply(text, expect_success):
        trial.write_text(text)
        os.chmod(trial, 0o600)
        result = run([tool, 'setconf', server, trial], ns=namespace, check=False)
        if (result.returncode == 0) != expect_success:
            raise RuntimeError('Unexpected profile validation result')
    try:
        for name, text in (
            ('header_padding_below_12', original.replace('S1 = 16', 'S1 = 11')),
            ('padding_above_tools_u16', original.replace('[Peer]', 'ContentPaddingAddition = 65536\n[Peer]')),
        ):
            apply(text, False)
            run([tool, 'setconf', server, cfg], ns=namespace)
            emit('negative_profile_rejected', case=name)
        lines = original.splitlines()
        wrong = '\n'.join('HeaderProtectionKey = ' + base64.b64encode(os.urandom(32)).decode()
                          if line.startswith('HeaderProtectionKey =') else line for line in lines) + '\n'
        apply(wrong, True)
        if ping(run).returncode == 0:
            raise RuntimeError('Wrong header key unexpectedly delivered data')
        stamps = run([tool, 'show', client, 'latest-handshakes']).stdout.decode().splitlines()
        if not stamps or any(int(line.split()[-1]) != 0 for line in stamps):
            raise RuntimeError('Wrong header key unexpectedly established handshake')
        emit('wrong_header_key', delivery=False, handshake=False, probe_seconds=1)
        run([tool, 'setconf', server, cfg], ns=namespace)
        emit('correct_key_recovery', seconds=ready(run))
        apply(original.replace('H4 = 4', 'H4 = 5'), True)
        if ping(run).returncode == 0:
            raise RuntimeError('Mismatched H4 unexpectedly delivered data')
        run([tool, 'setconf', server, cfg], ns=namespace)
        emit('mismatched_h4', delivery=False, recovery_seconds=ready(run))
        for mtu in (1280, 1200):
            for ns, interface in ((None, client), (namespace, server)):
                run(['ip', 'link', 'set', interface, 'mtu', str(mtu)], ns=ns)
            if ping(run, size=mtu-28).returncode != 0:
                raise RuntimeError('MTU boundary packet failed')
            excess = ping(run, size=mtu-27)
            if excess.returncode == 0 or b'message too long' not in (excess.stdout + excess.stderr).lower():
                raise RuntimeError('Expected local refusal above tunnel MTU')
            emit('mtu_boundary', mtu=mtu, maximum_payload=mtu-28, excess_locally_refused=True)
    finally:
        run([tool, 'setconf', server, cfg], ns=namespace)
        for ns, interface in ((None, client), (namespace, server)):
            run(['ip', 'link', 'set', interface, 'mtu', '1280'], ns=ns)
    ready(run)
    shape(run, namespace, 1)
    emit('loss_enabled', percent_each_direction=1, seeded=False)


def postflight(run, namespace, client, server, tool, engine, processes, directory, log, stop):
    shape(run, namespace, 100)
    try:
        if ping(run).returncode == 0:
            raise RuntimeError('Blackhole unexpectedly delivered packet')
    finally:
        shape(run, namespace, 0)
    emit('blackhole_recovery', seconds=ready(run), outage_probe_seconds=1)
    run(['ip', 'link', 'set', client, 'down'])
    run(['ip', 'link', 'set', client, 'up'])
    emit('client_link_cycle', seconds=ready(run))

    import subprocess
    stop(processes[-1])
    process = subprocess.Popen(['ip', 'netns', 'exec', namespace, str(engine), '-f', server],
        stdout=log, stderr=log, env={**os.environ, 'LOG_LEVEL': 'error', 'GOMAXPROCS': '1'})
    processes[-1] = process
    deadline = time.monotonic() + 5
    ipc = Path('/var/run/amneziawg') / (server + '.sock')
    while not ipc.exists():
        if process.poll() is not None or time.monotonic() > deadline:
            raise RuntimeError('Server engine failed to restart')
        time.sleep(0.02)
    run([tool, 'setconf', server, Path(directory)/(server+'.conf')], ns=namespace)
    run(['ip', 'addr', 'add', '10.90.0.1/24', 'dev', server], ns=namespace)
    run(['ip', 'link', 'set', server, 'mtu', '1280', 'up'], ns=namespace)
    emit('server_process_restart', recovery_seconds=ready(run, timeout=30))
    cfg = Path(directory)/(client+'.conf')
    original = cfg.read_text()
    accelerated = Path(directory)/'accelerated.conf'
    accelerated.write_text(original.replace('[Peer]', 'RekeyAfterTime = 5\nRejectAfterTime = 30\n[Peer]'))
    os.chmod(accelerated, 0o600)
    def handshake():
        return int(run([tool, 'show', client, 'latest-handshakes']).stdout.decode().split()[-1])
    try:
        run([tool, 'setconf', client, accelerated])
        ready(run)
        previous = handshake()
        if previous == 0:
            raise RuntimeError('No initial handshake for accelerated rekey')
        started = time.monotonic()
        while time.monotonic() - started < 18:
            time.sleep(1)
            ready(run)
            if handshake() > previous:
                emit('accelerated_rekey', elapsed_seconds=round(time.monotonic()-started,4), rekey_after_time=5)
                break
        else:
            raise RuntimeError('Accelerated rekey not observed')
    finally:
        run([tool, 'setconf', client, cfg])
    ready(run)
