"""Bounded external Linux/AWG observations. Never imported by a web request."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time


def metric_command(arguments):
    reply = subprocess.run(arguments, capture_output=True, timeout=4, check=True)
    if len(reply.stdout) > 2_000_000:
        raise ValueError('METRIC_LIMIT')
    return reply.stdout.decode('utf-8')


def collect_metrics(source, expected_sha256, root=Path('/opt/apps/family_connect/friends-awg')):
    result = dict(schema=1, source=source, observed_at=int(time.time()), node=None,
                  awg_status='unavailable', devices=[], unknown_peers=None,
                  tcp_status='not_collected', mesh_status='not_collected')
    try:
        routes = json.loads(metric_command(['ip', '-j', 'route', 'show', 'default']))
        interfaces = {route['dev'] for route in routes if 'dev' in route}
        if len(interfaces) != 1:
            raise ValueError('AMBIGUOUS_INTERFACE')
        interface = interfaces.pop()
        if not re.fullmatch(r'[a-zA-Z0-9_.-]{1,32}', interface):
            raise ValueError('INVALID_INTERFACE')
        network = Path('/sys/class/net') / interface
        ticks = list(map(int, Path('/proc/stat').read_text().splitlines()[0].split()[1:9]))
        boot = hashlib.sha256(Path('/proc/sys/kernel/random/boot_id').read_bytes()).hexdigest()
        result['node'] = dict(boot=boot, interface=interface, ifindex=int((network/'ifindex').read_text()),
            rx=int((network/'statistics/rx_bytes').read_text()), tx=int((network/'statistics/tx_bytes').read_text()),
            cpu_total=sum(ticks), cpu_idle=ticks[3] + ticks[4],
            cpu_count=sum(line.startswith('cpu') and line[3:4].isdigit() for line in Path('/proc/stat').read_text().splitlines()))
    except (OSError, ValueError, KeyError, subprocess.SubprocessError):
        pass
    try:
        archive = root/'paid-transport.pyz'
        if not expected_sha256 or hashlib.sha256(archive.read_bytes()).hexdigest() != expected_sha256:
            raise ValueError('UNVERIFIED_BINDINGS')
        state_path = root/'transport-state.json'
        if state_path.stat().st_size > 8_000_000:
            raise ValueError('STATE_LIMIT')
        state = json.loads(state_path.read_text())
        if state['schema'] != 1 or state['node'] != source:
            raise ValueError('WRONG_NODE')
        mappings = {}
        for device, record in state['records'].items():
            public = record['decision']['public_key']
            if not re.fullmatch('[0-9a-f]{32}', device) or public in mappings:
                raise ValueError('AMBIGUOUS_BINDING')
            mappings[public] = device
        transfer = {}
        for line in metric_command([str(root/'awg'), 'show', 'fcopen31', 'transfer']).splitlines():
            public, received, sent = line.split()
            if public in transfer:
                raise ValueError('DUPLICATE_PEER')
            transfer[public] = (int(received), int(sent))
        handshakes = dict(line.split() for line in metric_command([str(root/'awg'), 'show', 'fcopen31', 'latest-handshakes']).splitlines())
        boot = hashlib.sha256(Path('/proc/sys/kernel/random/boot_id').read_bytes()).hexdigest()
        ifindex = int(Path('/sys/class/net/fcopen31/ifindex').read_text())
        result['devices'] = [dict(device=mappings[public], rx=values[0], tx=values[1],
            last_handshake=int(handshakes.get(public, 0)) or None, epoch=f'{boot}:{ifindex}')
            for public, values in transfer.items() if public in mappings]
        result.update(awg_status='ok', unknown_peers=len(set(transfer) - set(mappings)))
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        result.update(awg_status='unavailable', devices=[], unknown_peers=None)
    result['observed_at'] = int(time.time())
    return result
