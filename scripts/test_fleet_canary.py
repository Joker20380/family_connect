"""Opt-in native integration. Only new, internal Docker resources are mutable."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import signal
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
IMAGE = 'family-connect-fleet-canary:local'
LABEL = 'family-connect.isolated-canary'
SOURCES = ('pilot/fleet_canary.py', 'pilot/fleet-canary/Dockerfile', 'scripts/test_fleet_canary.py')


def call(arguments, *, payload=None, timeout=60, check=True):
    result = subprocess.run(arguments, input=payload, capture_output=True, timeout=timeout)
    if check and result.returncode:
        raise RuntimeError('isolated canary command failed; no raw command output disclosed')
    return result


def inspect(kind, identifier, run=call):
    return json.loads(run(['docker', kind, 'inspect', identifier]).stdout)[0]


def verify_container(info, prefix, networks, role):
    config = info['HostConfig']
    if (info['Config']['Labels'].get(LABEL) != prefix or config['Privileged']
            or config.get('PidMode') or config.get('IpcMode') == 'host'
            or config.get('Binds') or config.get('PortBindings') or not config['ReadonlyRootfs']
            or set(info['NetworkSettings']['Networks']) != set(networks)
            or any(mount['Type'] != 'tmpfs' for mount in info['Mounts'])
            or config.get('CapDrop') != ['ALL']):
        raise RuntimeError('container isolation gate rejected')
    expected = {'NET_BIND_SERVICE'} | ({'NET_ADMIN'} if role != 'origin' else set())
    if {name.removeprefix('CAP_') for name in config['CapAdd']} != expected:
        raise RuntimeError('unexpected container capabilities')
    if config.get('SecurityOpt') != ['no-new-privileges:true']:
        raise RuntimeError('no-new-privileges missing')
    devices = config.get('Devices') or []
    expected_devices = [] if role == 'origin' else [dict(PathOnHost='/dev/net/tun',
        PathInContainer='/dev/net/tun', CgroupPermissions='rwm')]
    if devices != expected_devices:
        raise RuntimeError('unexpected host device')


def cleanup(prefix, run=call):
    failures = []
    for kind, list_command in [('container', ['docker', 'ps', '-aq']), ('network', ['docker', 'network', 'ls', '-q'])]:
        try:
            found = run(list_command + ['--filter', 'label=' + LABEL + '=' + prefix], check=False)
        except (OSError, subprocess.SubprocessError):
            failures.append(kind + '-discovery')
            continue
        if found.returncode:
            failures.append(kind + '-discovery')
            continue
        for identifier in found.stdout.decode().split():
            try:
                info = inspect(kind, identifier, run)
                labels = info['Config']['Labels'] if kind == 'container' else info['Labels']
                if labels.get(LABEL) != prefix:
                    raise RuntimeError('cleanup ownership mismatch')
                command = ['docker', 'rm', '-f', identifier] if kind == 'container' else ['docker', 'network', 'rm', identifier]
                if run(command, check=False).returncode:
                    failures.append(kind + '-removal')
            except (RuntimeError, OSError, KeyError, ValueError, subprocess.SubprocessError):
                failures.append(kind + '-inspection')
        try:
            remaining = run(list_command + ['--filter', 'label=' + LABEL + '=' + prefix], check=False)
        except (OSError, subprocess.SubprocessError):
            failures.append(kind + '-remaining')
            continue
        if remaining.returncode or remaining.stdout.strip():
            failures.append(kind + '-remaining')
    return failures


def execute(report, run=call):
    prefix = 'fc-dataplane-canary-' + secrets.token_hex(6)
    if not re.fullmatch(r'fc-dataplane-canary-[a-f0-9]{12}', prefix):
        raise RuntimeError('invalid run identity')
    receipt = dict(schema=1, result='FAIL', run_id=prefix, production_writes=0,
        production_credentials_read=False, production_node_acceptance='NOT_RUN',
        source_sha256={name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in SOURCES},
        started_at=datetime.now(timezone.utc).isoformat())
    descriptor = os.open(report, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'w') as output:
        try:
            receipt['phase'] = 'image'
            image = inspect('image', IMAGE, run)['Id']
            receipt['image_id'] = image
            network_ids = {}
            receipt['phase'] = 'create-networks'
            for suffix in ('entry', 'egress'):
                name = prefix + '-' + suffix
                network_ids[suffix] = run(['docker', 'network', 'create', '--internal',
                    '--label', LABEL + '=' + prefix, name]).stdout.decode().strip()
                info = inspect('network', network_ids[suffix], run)
                if not info['Internal'] or info['Labels'].get(LABEL) != prefix:
                    raise RuntimeError('network isolation gate rejected')
            containers = {}
            receipt['phase'] = 'create-containers'
            for role, initial_network in [('origin', 'egress'), ('gateway', 'entry'), ('client', 'entry')]:
                command = ['docker', 'run', '-d', '--name', prefix + '-' + role,
                    '--label', LABEL + '=' + prefix, '--network', prefix + '-' + initial_network,
                    '--read-only', '--cap-drop', 'ALL', '--cap-add', 'NET_BIND_SERVICE',
                    '--security-opt', 'no-new-privileges:true', '--pids-limit', '128', '--memory', '384m',
                    '--tmpfs', '/run:mode=755', '--tmpfs', '/tmp:mode=1777']
                if role != 'origin':
                    command += ['--cap-add', 'NET_ADMIN', '--device', '/dev/net/tun']
                if role == 'gateway':
                    command += ['--sysctl', 'net.ipv4.ip_forward=1']
                containers[role] = run(command + [image]).stdout.decode().strip()
            run(['docker', 'network', 'connect', network_ids['egress'], containers['gateway']])
            details = {}
            receipt['phase'] = 'verify-isolation'
            for role, identifier in containers.items():
                info = inspect('container', identifier, run)
                networks = [prefix + '-egress'] if role == 'origin' else [prefix + '-entry']
                if role == 'gateway':
                    networks += [prefix + '-egress']
                verify_container(info, prefix, networks, role)
                details[role] = info['NetworkSettings']['Networks']
            observed = run(['docker', 'exec', containers['client'], 'sha256sum', '/canary.py']).stdout.decode().split()[0]
            if observed != receipt['source_sha256']['pilot/fleet_canary.py']:
                raise RuntimeError('stale canary image')

            def inner(role, action, document):
                result = run(['docker', 'exec', '-i', containers[role], 'python3', '/canary.py', action],
                    payload=json.dumps(document).encode(), timeout=150, check=False)
                if result.returncode:
                    try:
                        value = json.loads(result.stdout)
                        stage = value.get('stage', 'unknown')
                        if type(stage) is str and re.fullmatch(r'[a-z-]{1,40}', stage):
                            receipt['failed_stage'] = role + ':' + stage
                    except ValueError:
                        pass
                    raise RuntimeError('isolated inner gate failed')
                return json.loads(result.stdout)

            origin = details['origin'][prefix + '-egress']['IPAddress']
            receipt['phase'] = 'origin'
            certificate = inner('origin', 'origin', dict(address=origin))
            document = dict(origin=origin, gateway=details['gateway'][prefix + '-entry']['IPAddress'],
                egress=details['gateway'][prefix + '-egress']['IPAddress'], certificate=certificate)
            receipt['phase'] = 'gateway'
            client = inner('gateway', 'gateway', document)
            receipt['phase'] = 'client'
            receipt['checks'] = inner('client', 'client', client)
            counts = json.loads(run(['docker', 'exec', containers['origin'], 'cat', '/run/fc-canary/counts.json']).stdout)
            if counts['dns'] < 2 or counts['https'] != 2:
                raise RuntimeError('origin evidence mismatch')
            receipt['origin_counts'] = counts
            receipt['phase'] = 'completed'
            receipt['result'] = 'ISOLATED_NATIVE_DATA_PLANE_PASS'
        except (RuntimeError, OSError, ValueError, KeyError, subprocess.SubprocessError, KeyboardInterrupt) as error:
            receipt['result'] = 'FAIL'
            receipt['failure_type'] = type(error).__name__
        finally:
            failures = cleanup(prefix, run)
            receipt['cleanup'] = 'PASS' if not failures else 'FAIL'
            if failures:
                receipt['result'] = 'FAIL'
                receipt['cleanup_failures'] = failures
            receipt['finished_at'] = datetime.now(timezone.utc).isoformat()
            json.dump(receipt, output, indent=2)
            output.write('\n')
    return receipt


def main():
    parser = argparse.ArgumentParser(description='Isolated AWG3.1/REALITY canary; no production targets or identities')
    parser.add_argument('--build', action='store_true')
    parser.add_argument('--report', required=True, type=Path)
    args = parser.parse_args()
    os.umask(0o077)

    def interrupted(signum, frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, interrupted)
    if args.build:
        with tempfile.TemporaryDirectory(prefix='fc-canary-source-') as temporary:
            folder = Path(temporary)
            (folder / 'Dockerfile').write_bytes((ROOT / 'pilot/fleet-canary/Dockerfile').read_bytes())
            (folder / 'fleet_canary.py').write_bytes((ROOT / 'pilot/fleet_canary.py').read_bytes())
            call(['docker', 'build', '-t', IMAGE, str(folder)], timeout=300)
    receipt = execute(args.report)
    print(json.dumps(receipt))
    return 0 if receipt['result'] == 'ISOLATED_NATIVE_DATA_PLANE_PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
