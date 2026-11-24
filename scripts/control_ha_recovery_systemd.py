"""Bounded transient recovery on an authorized host, never a production entrypoint."""
from pathlib import PurePosixPath
import re

from scripts.control_ha_recovery_cold import SHELL

PROPERTIES = (
    'DynamicUser=yes', 'PrivateNetwork=yes', 'PrivateDevices=yes', 'PrivateUsers=yes',
    'ProtectSystem=strict', 'ProtectHome=yes', 'NoNewPrivileges=yes', 'CapabilityBoundingSet=',
    'RestrictAddressFamilies=AF_UNIX', 'ProtectControlGroups=yes', 'ProtectKernelTunables=yes',
    'ProtectKernelModules=yes', 'ProtectProc=invisible', 'ProcSubset=pid',
    'MemoryMax=512M', 'MemorySwapMax=0', 'CPUQuota=25%', 'TasksMax=32', 'RuntimeMaxSec=600',
    'TimeoutStopSec=5', 'KillMode=control-group', 'Nice=19', 'IOSchedulingClass=idle',
    'UMask=0077', 'LimitCORE=0', 'MountAPIVFS=yes',
    'TemporaryFileSystem=/tmp:rw,nosuid,nodev,size=320M',
    'InaccessiblePaths=-/app -/root -/home -/opt/apps -/var/lib/docker',
)

INPUT = r'''import json,os,pathlib,stat,sys
assert os.getuid()!=0
status=dict(line.split(':',1) for line in pathlib.Path('/proc/self/status').read_text().splitlines() if ':' in line)
assert int(status['CapEff'].strip(),16)==0 and status['NoNewPrivs'].strip()=='1'
interfaces=[line.split(':',1)[0].strip() for line in pathlib.Path('/proc/self/net/dev').read_text().splitlines()[2:]]
assert interfaces==['lo']
assert not os.access('/opt/apps/family_connect',os.R_OK)
raw=sys.stdin.buffer.read(65537)
assert len(raw)<=65536
inputs=json.loads(raw)
roles=('stores','RU','node-RU','node-NL1','node-NL2','worker','mailbox')
assert set(inputs)=={role+suffix for role in roles for suffix in ('.key','.checkpoint.json')}
destination=pathlib.Path('/tmp/fc-custody'); destination.mkdir(mode=0o700)
for name,value in inputs.items():
    assert type(value) is str and len(value)<=8192
    body=bytes.fromhex(value) if name.endswith('.key') else value.encode()
    assert len(body)==32 if name.endswith('.key') else 0<len(body)<=8192
    descriptor=os.open(destination/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(descriptor,'wb') as output: output.write(body)
for role in roles:
    source=pathlib.Path('/fc-cipher')/(role+'.aesgcm')
    assert stat.S_ISREG(source.lstat().st_mode) and source.stat().st_size<128*1024*1024
    os.symlink(source,destination/source.name)
print(json.dumps(dict(isolation='PASS',uid=os.getuid(),caps=0,no_new_privs=True,interfaces=interfaces,activation=False)))
'''


def command(root, operation):
    path = PurePosixPath(root)
    if (str(path) != root or path.parts[:5] != ('/', 'opt', 'apps', 'family_connect', 'ha-recovery') or
            len(path.parts) != 6 or not re.fullmatch(r'[a-z0-9-]{8,64}', path.name) or
            not re.fullmatch(r'[a-z0-9-]{8,64}', operation)):
        raise ValueError('RECOVERY_SCOPE')
    properties = list(PROPERTIES) + ['RootDirectory=' + root + '/rootfs']
    mounts = {'kit.tar': '/tmp/fc-kit.tar', 'kit.checkpoint.json': '/tmp/fc-kit-checkpoint.json',
              'bootstrap.py': '/tmp/fc-kit-bootstrap.py', 'cipher': '/fc-cipher'}
    properties += ['BindReadOnlyPaths=' + root + '/' + source + ':' + target for source, target in mounts.items()]
    script = 'set -eu\numask 077\nmkdir /tmp/fc-work\n/usr/local/bin/python -I -c "$1"\n' + SHELL
    return ['/usr/bin/systemd-run', '--quiet', '--wait', '--pipe', '--collect',
            '--unit=fc-ha-recovery-' + operation, '--service-type=exec',
            *[argument for prop in properties for argument in ('--property', prop)],
            '--', '/bin/sh', '-c', script, 'fc-ha-offline', INPUT]
