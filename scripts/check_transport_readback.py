"""Bounded real AWG/Xray readback in an owned, network-none Docker namespace."""
import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import stat
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from control.friends import transport_gateway as module
from control.friends import transport_policy as policy


def command(arguments, **kwargs):
    return subprocess.run(arguments, check=True, capture_output=True, timeout=8, **kwargs).stdout


def main():
    os.umask(0o077)
    assert Path('/.dockerenv').exists(), 'OWNED_CONTAINER_REQUIRED'
    assert json.loads(command(['ip', '-j', 'link']))[0]['ifname'] == 'lo'
    assert len(json.loads(command(['ip', '-j', 'link']))) == 1, 'NETWORK_NONE_REQUIRED'
    interface = 'fcreadback0'
    processes = []
    report = dict(schema=1, scope='isolated real engine queries, not production traffic', cycles=6,
        source_sha=os.environ['FC_SOURCE_SHA'], native_sha256={name:hashlib.sha256(Path('/native',name).read_bytes()).hexdigest()
            for name in ('awg', 'amneziawg-go', 'xray')}, modes={})
    original_write, original_sync, original_replace = module.write, os.fsync, os.replace
    try:
        with tempfile.TemporaryDirectory(prefix='fc-readback-') as temporary:
            base = Path(temporary)
            root, tcp = base/'friends-awg', base/'friends-tcp'
            root.mkdir(); tcp.mkdir()
            for name in ('awg', 'amneziawg-go'): (root/name).symlink_to('/native/'+name)
            (tcp/'xray').symlink_to('/native/xray')
            awg = subprocess.Popen(['/native/amneziawg-go', '-f', interface], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            processes.append(awg)
            deadline = time.monotonic()+5
            while True:
                assert awg.poll() is None, 'AWG_EARLY_EXIT'
                try:
                    command(['/native/awg', 'show', interface])
                    break
                except subprocess.CalledProcessError:
                    assert time.monotonic() < deadline, 'AWG_START_DEADLINE'
                    time.sleep(.02)
            secret = base/'synthetic-awg-key'
            secret.write_bytes(command(['/native/awg', 'genkey']))
            command(['/native/awg', 'set', interface, 'private-key', str(secret)])
            public = base64.b64encode(b'p'*32).decode()
            device, identity = 'a'*32, '11111111-1111-4111-8111-111111111111'
            command(['/native/awg', 'set', interface, 'peer', public, 'allowed-ips', '10.254.253.2/32'])
            keys = command(['/native/xray', 'x25519']).decode().splitlines()
            private = next(line.split(':', 1)[1].strip() for line in keys if line.lower().startswith('private'))
            config = dict(log=dict(loglevel='none'), api=dict(tag='api', services=['HandlerService']),
                inbounds=[dict(tag='friends', listen='127.0.0.1', port=18443, protocol='vless',
                    settings=dict(decryption='none', clients=[dict(id=identity, email=device+'@family.test', flow='xtls-rprx-vision')]),
                    streamSettings=dict(network='tcp', security='reality', realitySettings=dict(
                        dest='127.0.0.1:19443', serverNames=['fixture.invalid'], privateKey=private, shortIds=['']))),
                    dict(tag='api', listen='127.0.0.1', port=18085, protocol='dokodemo-door', settings=dict(address='127.0.0.1'))],
                routing=dict(rules=[dict(type='field', inboundTag=['api'], outboundTag='api')]))
            module.write(tcp/'server.json', config)
            xray = subprocess.Popen(['/native/xray', 'run', '-config', str(tcp/'server.json')], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            processes.append(xray)
            deadline = time.monotonic()+5
            while True:
                assert xray.poll() is None, 'XRAY_EARLY_EXIT'
                try:
                    command(['/native/xray', 'api', 'inbounduser', '--server=127.0.0.1:18085', '-tag=friends'])
                    break
                except subprocess.CalledProcessError:
                    assert time.monotonic() < deadline, 'XRAY_START_DEADLINE'
                    time.sleep(.02)
            with sqlite3.connect(root/'peers.db') as database:
                database.execute('CREATE TABLE peers(id INTEGER PRIMARY KEY, public TEXT)')
                database.execute('INSERT INTO peers VALUES(1,?)', (public,))
            runtime = SimpleNamespace(ROOT=root, IFACE=interface, database=lambda:sqlite3.connect(root/'peers.db'),
                address=lambda index:'10.254.253.2/32', add_peer=lambda key,address:command(['/native/awg','set',interface,'peer',key,'allowed-ips',address]))
            spec = importlib.util.spec_from_file_location('collector', ROOT/'control_plane/apps/console/transport_collector.py')
            collector = importlib.util.module_from_spec(spec); spec.loader.exec_module(collector)
            archive = Path(module.__file__).read_bytes()
            (root/'paid-transport.pyz').write_bytes(archive)
            for mode in ('baseline', 'candidate'):
                configuration = dict(schema=1, profile=policy.PROFILE, node='gateway-ru', enabled=True)
                if mode == 'candidate': configuration['readback_mode'] = 'observations-v1'
                original_write(root/'transport-enforcement.json', configuration)
                now = int(time.time())
                original_write(root/'transport-state.json', dict(schema=1,node='gateway-ru',observed_at=now,records={}))
                decision = dict(device=device, public_key=public, tcp_id=identity, cohort=False, revision=0,
                    state='noncohort', identity_allowed=True, allowed=True, paid_until=None, grace_until=None,
                    observed_at=now, valid_until=now+120)
                gateway = module.Gateway(runtime, run=command)
                gateway.accept(dict(schema=1,profile=policy.PROFILE,node='gateway-ru',observed_at=now,decisions=[decision]))
                gateway.apply()
                counts = dict(engine_queries=0, durable_writes=0, file_fsync=0, directory_fsync=0, observations=0, collector_ok=0)
                def run(arguments):
                    counts['engine_queries'] += 1
                    return command(arguments)
                def write(path, value, *args):
                    counts['durable_writes'] += 1
                    return original_write(path,value,*args)
                def sync(descriptor):
                    counts['directory_fsync' if stat.S_ISDIR(os.fstat(descriptor).st_mode) else 'file_fsync'] += 1
                    return original_sync(descriptor)
                def replace(source, target):
                    counts['observations'] += target == gateway.observation_path
                    return original_replace(source,target)
                gateway.run = run
                module.write, os.fsync, os.replace = write, sync, replace
                try:
                    for iteration in range(report['cycles']):
                        gateway.apply()
                        observed = collector.collect_transport('gateway-ru', b'k'*32, hashlib.sha256(archive).hexdigest(), root)
                        assert observed['status'] == 'ok' and observed['devices'][0]['awg_allowed'] is True
                        assert observed['devices'][0]['tcp_allowed'] is True
                        if mode == 'candidate':
                            assert observed['observed_at'] == module.read(gateway.observation_path)['observed_at']
                        counts['collector_ok'] += 1
                finally:
                    module.write, os.fsync, os.replace = original_write, original_sync, original_replace
                expected = 12 if mode == 'baseline' else 0
                assert counts == dict(engine_queries=18, durable_writes=expected,file_fsync=expected,directory_fsync=expected,
                    observations=0 if mode == 'baseline' else 6,collector_ok=6), counts
                report['modes'][mode] = counts
    finally:
        for process in reversed(processes):
            process.terminate()
            try: process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill(); process.wait(timeout=3)
    report['owned_processes_reaped'] = all(process.poll() is not None for process in processes)
    print(json.dumps(report, sort_keys=True))


if __name__ == '__main__':
    main()
