"""First installation of an unpublished ordinary gateway; no catalog or MESH actions."""

import base64
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import pwd
import re
import secrets
import stat
import subprocess
import sys

ROOT = Path('/opt/apps/family_connect')
STATE = Path('/var/lib/family-connect-ordinary-install')
UNITS = ('family-connect-friends-tcp.service', 'family-connect-friends-awg.service')
NATIVE = {
    'amneziawg-go': 'e7f00e47d6df853ade5dcd2fe79240f01ff897d75088c768316a444c27c87e0f',
    'awg': '906d6795af1dd4adee7b11bf1e7fa133d4795c8a8d6e2099b34a026f810a3278',
    'xray': '4f7a4436f86798bbb5c875014e352021a1673710a45e170ccc507c5f59341940',
}
EXCLUDED = {'185.251.89.19', '185.10.158.212', '186.246.45.246', '186.246.51.201'}
SYSCTL = Path('/etc/sysctl.d/90-family-connect-ordinary.conf')
SNI = 'www.cloudflare.com'


def require(condition):
    if not condition:
        raise ValueError('standby node precondition rejected')


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def command(argv, **kwargs):
    result = subprocess.run(argv, capture_output=True, timeout=90, **kwargs)
    require(result.returncode == 0)
    return result.stdout


def regular(path):
    for parent in (path, *path.parents):
        require(not parent.is_symlink())
    info = path.lstat()
    require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_uid == os.geteuid())
    return path.read_bytes()


def write(path, raw, mode=0o600, gid=0):
    for parent in path.parents:
        require(parent.is_dir() and not parent.is_symlink())
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode)
    with os.fdopen(descriptor, 'wb') as output:
        os.fchmod(output.fileno(), mode)
        os.fchown(output.fileno(), os.geteuid(), gid)
        output.write(raw)
        output.flush()
        os.fsync(output.fileno())
    descriptor = os.open(path.parent, os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def manifest_check(value, directory, target):
    require(set(value) == {'schema', 'target', 'operation_id', 'source_commit', 'files'})
    require(value['schema'] == 1 and value['target'] == target and target not in EXCLUDED)
    require(str(ipaddress.IPv4Address(target)) == target and ipaddress.IPv4Address(target).is_global)
    require(bool(re.fullmatch('[a-z0-9-]{16,80}', value['operation_id'])))
    require(bool(re.fullmatch('[0-9a-f]{40}', value['source_commit'])))
    require(set(value['files']) == {*NATIVE, 'awg-gateway.py', 'standby-node.py'})
    for name, expected in value['files'].items():
        require(bool(re.fullmatch('[0-9a-f]{64}', expected)))
        require(hashlib.sha256(regular(directory / name)).hexdigest() == expected)
        require(name not in NATIVE or expected == NATIVE[name])


def material(target):
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey

    awg = X25519PrivateKey.generate()
    tcp = X25519PrivateKey.generate()
    def raw_private(key):
        return key.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw,
                                 serialization.NoEncryption())
    def raw_public(key):
        return key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    def url(raw):
        return base64.urlsafe_b64encode(raw).decode().rstrip('=')
    parameters = ('Jc = 4\nJmin = 40\nJmax = 70\nS1 = 81\nS2 = 93\nS3 = 17\nS4 = 23\n'
                  'H1 = 1\nH2 = 2\nH3 = 3\nH4 = 4\nHeaderProtectionKey = ' +
                  base64.b64encode(secrets.token_bytes(32)).decode() + '\nContentPaddingAddition = 0-32\n')
    awg_server = ('[Interface]\nPrivateKey = ' + base64.b64encode(raw_private(awg)).decode() +
                  '\nListenPort = 51823\n' + parameters).encode()
    short_id = secrets.token_hex(8)
    tcp_server = dict(log=dict(loglevel='none'), api=dict(tag='api', services=['HandlerService']),
        inbounds=[dict(tag='friends', listen='0.0.0.0', port=443, protocol='vless',
            settings=dict(clients=[], decryption='none'), streamSettings=dict(network='tcp', security='reality',
                realitySettings=dict(show=False, dest=SNI + ':443', xver=0, serverNames=[SNI],
                                     privateKey=url(raw_private(tcp)), shortIds=[short_id]))),
            dict(tag='api', listen='127.0.0.1', port=18085, protocol='dokodemo-door',
                 settings=dict(address='127.0.0.1'))],
        outbounds=[dict(protocol='freedom', tag='direct'), dict(protocol='blackhole', tag='blocked')],
        routing=dict(rules=[dict(type='field', inboundTag=['api'], outboundTag='api'),
            dict(type='field', ip=['0.0.0.0/8', '10.0.0.0/8', '127.0.0.0/8', '169.254.0.0/16',
                 '172.16.0.0/12', '192.168.0.0/16', '224.0.0.0/4', '::1/128', 'fc00::/7', 'fe80::/10'],
                 outboundTag='blocked')]))
    template = dict(country='nl', tcp=dict(type='vless-reality-v1', server=target, port=443,
        id='DEVICE_CREDENTIAL', server_name=SNI, public_key=url(raw_public(tcp)), short_id=short_id),
        awg='[Interface]\nPrivateKey = LOCAL_DEVICE_KEY\nAddress = ASSIGNED_ADDRESS\n'
        'DNS = 1.1.1.1\nMTU = 1280\n' + parameters + '\n[Peer]\nPublicKey = ' +
        base64.b64encode(raw_public(awg)).decode() + '\nEndpoint = ' + target +
        ':51823\nAllowedIPs = 0.0.0.0/0, ::/0\nPersistentKeepalive = 25\n')
    return awg_server, canonical(tcp_server), template


def units():
    common = ('[Unit]\nAfter=network-online.target\nWants=network-online.target\n'
              'StartLimitIntervalSec=120\nStartLimitBurst=5\n[Service]\nUMask=0077\n'
              'Restart=on-failure\nRestartSec=3\nNoNewPrivileges=true\nProtectHome=true\n'
              'PrivateTmp=true\nMemoryMax=256M\nTasksMax=128\nStandardOutput=null\nStandardError=null\n')
    tail = '[Install]\nWantedBy=multi-user.target\n'
    tcp = (common + 'User=fc-friends\nGroup=fc-friends\nProtectSystem=strict\n'
           'ProtectKernelTunables=true\nProtectControlGroups=true\n'
           'RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX\n'
           'CapabilityBoundingSet=CAP_NET_BIND_SERVICE\nAmbientCapabilities=CAP_NET_BIND_SERVICE\n'
           'ExecStart=/opt/apps/family_connect/friends-tcp/xray run -config '
           '/opt/apps/family_connect/friends-tcp/server.json\n' + tail)
    awg = (common + 'User=root\nGroup=root\nProtectSystem=full\nKillMode=mixed\nTimeoutStopSec=90\n'
           'ExecStart=/usr/bin/python3 /opt/apps/family_connect/friends-awg/awg-gateway.py run\n' + tail)
    return dict(zip(UNITS, (tcp.encode(), awg.encode())))


def application_root():
    for parent in (*reversed(ROOT.parents), ROOT):
        if not parent.exists():
            parent.mkdir(mode=0o755)
            parent.chmod(0o755)
        require(not parent.is_symlink() and parent.is_dir() and parent.stat().st_uid == 0)
        require(stat.S_IMODE(parent.stat().st_mode) & 0o022 == 0)
        require(stat.S_IMODE(parent.stat().st_mode) & 0o005 == 0o005)


def preflight(target):
    require(os.geteuid() == 0 and target not in EXCLUDED)
    addresses = json.loads(command(['ip', '-j', '-4', 'address']))
    require(any(entry['local'] == target for interface in addresses for entry in interface['addr_info']))
    require('VERSION_ID="24.04"' in Path('/etc/os-release').read_text())
    require(command(['uname', '-m']).strip() == b'x86_64')
    require(not Path('/run/reboot-required').exists())


def prepare(manifest, directory):
    require(not STATE.exists() and not STATE.is_symlink())
    require(not SYSCTL.exists() and not SYSCTL.is_symlink())
    for name in ('friends-awg', 'friends-tcp'):
        require(not (ROOT / name).exists() and not (ROOT / name).is_symlink())
    for name in UNITS:
        require(not Path('/etc/systemd/system', name).exists())
        require(command(['systemctl', 'show', name, '--property=LoadState', '--value']).strip() == b'not-found')
    for family in ('-lnt', '-lnu'):
        listeners = command(['ss', '-H', family]).decode().splitlines()
        require(not any(line.split()[3].rsplit(':', 1)[-1] in ('443', '51823', '18085') for line in listeners))
    routes = json.loads(command(['ip', '-j', '-4', 'route']))
    subnet = ipaddress.IPv4Network('10.83.0.0/16')
    require(not any(subnet.overlaps(ipaddress.IPv4Network(entry['dst'], strict=False))
                    for entry in routes if entry.get('dst') not in (None, 'default')))
    external = next(entry['dev'] for entry in routes if entry.get('dst') == 'default')
    require(bool(re.fullmatch('[a-zA-Z0-9_-]{1,15}', external)))
    require(subprocess.run(['ip', 'link', 'show', 'fcopen31'], capture_output=True).returncode != 0)
    require(b'FCFRIENDS31' not in command(['iptables-save']))
    STATE.mkdir(mode=0o700)
    write(STATE / 'intent.json', canonical(manifest))
    write(STATE / 'previous-forwarding', Path('/proc/sys/net/ipv4/ip_forward').read_bytes())
    try:
        account = pwd.getpwnam('fc-friends')
    except KeyError:
        command(['useradd', '--system', '--no-create-home', '--shell', '/usr/sbin/nologin', 'fc-friends'])
        account = pwd.getpwnam('fc-friends')
    require(account.pw_shell == '/usr/sbin/nologin' and account.pw_uid != 0)
    application_root()
    awg_root, tcp_root = ROOT / 'friends-awg', ROOT / 'friends-tcp'
    awg_root.mkdir(mode=0o700)
    tcp_root.mkdir(mode=0o750)
    os.chown(tcp_root, 0, account.pw_gid)
    os.chmod(tcp_root, 0o750)
    for name in NATIVE:
        destination = tcp_root if name == 'xray' else awg_root
        write(destination / name, regular(directory / name), mode=0o555)
    write(awg_root / 'awg-gateway.py', regular(directory / 'awg-gateway.py'), mode=0o444)
    awg, tcp, template = material(manifest['target'])
    write(awg_root / 'server.conf', awg)
    write(awg_root / 'settings.json', canonical(dict(network='10.83.0.0/16', address='10.83.0.1/16', external=external)))
    write(tcp_root / 'server.json', tcp, mode=0o640, gid=account.pw_gid)
    command(['runuser', '-u', 'fc-friends', '--', str(tcp_root / 'xray'), 'run', '-test', '-config', str(tcp_root / 'server.json')])
    write(STATE / 'template.json', canonical(template))
    for name, raw in units().items():
        write(Path('/etc/systemd/system', name), raw, mode=0o644)
    command(['systemd-analyze', 'verify', *[str(Path('/etc/systemd/system', name)) for name in UNITS]])
    command(['systemctl', 'daemon-reload'])
    write(STATE / 'prepared.json', canonical(dict(result='PREPARED_UNPUBLISHED', manifest_sha256=hashlib.sha256(canonical(manifest)).hexdigest())))


def service_status():
    return {name: dict(line.split('=', 1) for line in command(['systemctl', 'show', name,
        '--property=ActiveState,SubState,NRestarts,MainPID']).decode().splitlines()) for name in UNITS}


def start():
    regular(STATE / 'prepared.json')
    require(not (STATE / 'admitted').exists())
    require(not (STATE / 'start-intent').exists())
    write(STATE / 'start-intent', b'START_REQUESTED\n')
    write(SYSCTL, b'net.ipv4.ip_forward=1\n', mode=0o644)
    try:
        command(['sysctl', '-p', str(SYSCTL)])
        for name in UNITS:
            command(['systemctl', 'enable', '--now', name])
        status = service_status()
        require(all(value['ActiveState'] == 'active' and value['NRestarts'] == '0' for value in status.values()))
        write(STATE / 'started.json', canonical(status))
    except Exception:
        stop()
        raise


def stop():
    regular(STATE / 'intent.json')
    require(not (STATE / 'admitted').exists())
    for name in reversed(UNITS):
        command(['systemctl', 'disable', '--now', name])
    if SYSCTL.exists():
        require(regular(SYSCTL) == b'net.ipv4.ip_forward=1\n')
        SYSCTL.unlink()
    previous = regular(STATE / 'previous-forwarding').strip()
    require(previous in (b'0', b'1'))
    command(['sysctl', '-w', 'net.ipv4.ip_forward=' + previous.decode()])


def main():
    require(sys.argv[1:] == [])
    request = json.loads(sys.stdin.buffer.read(4097))
    require(set(request) == {'action', 'manifest_sha256'})
    require(request['action'] in ('prepare', 'start', 'stop', 'status', 'template'))
    directory = Path(__file__).resolve().parent
    raw = regular(directory / 'manifest.json')
    require(hashlib.sha256(raw).hexdigest() == request['manifest_sha256'])
    manifest = json.loads(raw)
    manifest_check(manifest, directory, manifest['target'])
    preflight(manifest['target'])
    if request['action'] == 'prepare':
        prepare(manifest, directory)
    else:
        require(regular(STATE / 'intent.json') == canonical(manifest))
        if request['action'] == 'start':
            start()
        elif request['action'] == 'stop':
            stop()
        elif request['action'] == 'template':
            sys.stdout.buffer.write(regular(STATE / 'template.json'))
            return
    print(canonical(dict(result='UNPUBLISHED', operation_id=manifest['operation_id'],
        action=request['action'], units=service_status(), catalog_publications=0, mesh='UNCHANGED')).decode())


if __name__ == '__main__':
    os.umask(0o077)
    try:
        main()
    except Exception:
        print('{"result":"STANDBY_REQUIRES_RECONCILIATION"}')
        sys.exit(1)
