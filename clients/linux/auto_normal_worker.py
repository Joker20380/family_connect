"""Root-only, inherited-lease bridge to fixed existing AWG/TCP helpers."""
import fcntl
import importlib.machinery
import importlib.util
import ipaddress
import json
import os
from pathlib import Path
import stat
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from auto_guard import DIRECTORY, candidate, integer, objects, policy
from auto_normal import unlink_durable
from auto_policy import require
from backend import privileged_transport_start
from mesh_system import private_read
import mesh_ipc as ipc
from profile_config import MAX_PROFILE


def trusted(path, directory=False):
    info = path.lstat()
    require(info.st_uid == 0 and not info.st_mode & 0o022 and
            (stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode) and info.st_nlink == 1))
    return info


class Lease:
    def __init__(self, descriptor):
        require(os.geteuid() == 0 and type(descriptor) is int and descriptor >= 3)
        self.directory, self.lock = DIRECTORY, descriptor
        info = trusted(DIRECTORY, True)
        require(stat.S_IMODE(info.st_mode) == 0o700)
        expected = trusted(DIRECTORY / 'lock')
        actual = os.fstat(descriptor)
        require((actual.st_dev, actual.st_ino) == (expected.st_dev, expected.st_ino) and
                stat.S_IMODE(actual.st_mode) == 0o600)
        probe = os.open(DIRECTORY / 'lock', os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK)
        try:
            try:
                fcntl.flock(probe, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                pass
            else:
                raise ValueError('Auto lease is not held')
        finally:
            os.close(probe)
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        self.record = private_read(DIRECTORY / 'guard.json')
        self._owned()

    def _owned(self):
        require(self.record == private_read(DIRECTORY / 'guard.json') and self.record['pending'] is None)
        require(set(self.record) == {'schema', 'uid', 'generation', 'current', 'pending'} and
                type(self.record['schema']) is int and self.record['schema'] == 1 and integer(self.record['uid'], 1, 2**31-1))
        objects(self.record['generation'], policy(**self.record['current']))
        normal = private_read(DIRECTORY / 'normal.json')
        require(set(normal) == {'schema', 'uid', 'generation', 'selected'} and type(normal['schema']) is int and normal['schema'] == 1 and
                normal['uid'] == self.record['uid'] and normal['generation'] == self.record['generation'])
        require(normal['selected'] == candidate(**normal['selected']) and normal['selected']['kind'] in ('awg', 'tcp'))
        selected = self.record['current']['selected']
        require(self.record['current']['mode'] == 'blocked' or selected == normal['selected'])
        self.normal = normal


def load_helper(kind):
    directory = Path('/usr/local/lib/family-connect-'+kind)
    for parent in (directory, *directory.parents):
        trusted(parent, True)
    path = directory / 'helper'
    trusted(path)
    loader = importlib.machinery.SourceFileLoader('fc_auto_'+kind, str(path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def expected_metadata(lease):
    selected = lease.normal['selected']
    return dict(id=selected['interface'], owner=0, endpoint=selected['endpoint'], primary=None,
                auto_generation=lease.normal['generation'])


def installed(helper, lease):
    selected = lease.normal['selected']
    path = helper.ROOT / (selected['interface']+'.json')
    if not os.path.lexists(path):
        require(not os.path.lexists(helper.ROOT / (selected['interface']+'.conf')))
        return False
    require(json.loads(helper.read(path)) == expected_metadata(lease))
    return True


def temporary_path(lease, path):
    return path.with_name('.auto-'+lease.normal['generation']+'-'+path.name)


def write_owned(helper, lease, path, text, mode):
    temporary = temporary_path(lease, path)
    if os.path.lexists(temporary):
        helper.read(temporary, private=mode == 0o600)
        unlink_durable(temporary)
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode)
    try:
        with os.fdopen(descriptor, 'w') as stream:
            os.fchmod(stream.fileno(), mode)
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.lexists(temporary):
            helper.read(temporary, private=mode == 0o600)
            unlink_durable(temporary)


def forget_temporaries(helper, lease, path, metadata):
    for target, private in ((path, True), (metadata, False)):
        temporary = temporary_path(lease, target)
        if os.path.lexists(temporary):
            helper.read(temporary, private=private)
            unlink_durable(temporary)


def execute(lease, request, helper):
    require(set(request) == {'schema', 'operation', 'profile'} and type(request['schema']) is int and request['schema'] == 1)
    operation, profile = request['operation'], request['profile']
    require(operation in ('install', 'up', 'down', 'forget', 'health') and isinstance(profile, str))
    require(len(profile.encode()) <= MAX_PROFILE and (operation == 'install' or not profile))
    lease._owned()
    selected, mode = lease.normal['selected'], lease.record['current']['mode']
    require(mode in (('ready',) if operation == 'health' else ('probe',) if operation in ('install', 'up') else ('blocked',)))
    if operation in ('install', 'up', 'health'):
        require(lease.record['current']['selected'] == selected)
    trusted(helper.ROOT, True)
    kind, identifier = selected['kind'], selected['interface']
    path, metadata = helper.ROOT / (identifier+'.conf'), helper.ROOT / (identifier+'.json')
    if operation in ('install', 'up'):
        trusted(Path(helper.BIN) / ('amneziawg-go' if kind == 'awg' else 'xray'))
        if kind == 'awg':
            trusted(Path(helper.BIN) / 'awg')
            trusted(Path(helper.BIN) / 'awg-quick')
    if operation == 'install':
        require(not installed(helper, lease) and not Path('/sys/class/net', identifier).exists())
        if kind == 'awg':
            text = helper.validate(profile, allow_awg=True, allow_awg31=helper.supports_awg31())
            fields = helper.parse(text, allow_awg=True, allow_awg31=helper.supports_awg31())
            require(bool(set(fields['Interface']) & helper.AWG_FIELDS))
            endpoint, port = fields['Peer']['Endpoint'].rsplit(':', 1)
            text = helper.quick_flags(text, native=True)
        else:
            fields = helper.parse_tcp(profile)
            endpoint, port = fields['server'], fields['port']
            text = json.dumps(fields)
        require(candidate(kind, identifier, str(ipaddress.IPv4Address(endpoint)), int(port)) == selected)
        write_owned(helper, lease, metadata, json.dumps(expected_metadata(lease)), 0o644)
        write_owned(helper, lease, path, text, 0o600)
        require(installed(helper, lease) and helper.read(path, private=True) == text)
        return
    present = installed(helper, lease)
    if not present:
        require(operation in ('down', 'forget') and not Path('/sys/class/net', identifier).exists())
        if operation == 'forget':
            forget_temporaries(helper, lease, path, metadata)
        return
    if operation == 'forget':
        require(not Path('/sys/class/net', identifier).exists())
        if kind == 'awg':
            require(not os.path.lexists('/run/family-connect-awg/active.json'))
        if kind == 'tcp':
            require(not os.path.lexists(helper.RUN / 'active') and not os.path.lexists(helper.RUN / (identifier+'.json')))
        if os.path.lexists(path):
            helper.read(path, private=True)
            unlink_durable(path)
        forget_temporaries(helper, lease, path, metadata)
        unlink_durable(metadata)
    elif operation == 'health':
        if kind == 'awg':
            helper.healthy(identifier, selected['endpoint'])
        else:
            helper.probe_interface(identifier, selected['endpoint'])
    elif operation == 'down' and not os.path.lexists(path):
        require(not Path('/sys/class/net', identifier).exists())
        if kind == 'tcp':
            require(not os.path.lexists(helper.RUN / 'active'))
    else:
        previous = sys.argv
        try:
            sys.argv = ['helper', operation, identifier]
            helper.execute()
        finally:
            sys.argv = previous


def main():
    require(len(sys.argv) == 2 and sys.argv[1].isdigit())
    lease = Lease(int(sys.argv[1]))
    request = ipc.decode(sys.stdin.buffer.read(MAX_PROFILE*2+1025), MAX_PROFILE*2+1024)
    kind = lease.normal['selected']['kind']
    helper = load_helper(kind)
    try:
        with privileged_transport_start(kind, auto_guard=lease):
            execute(lease, request, helper)
    except RuntimeError:
        return 2 if request.get('operation') in ('up', 'health') else 1
    finally:
        request.clear()
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception:
        sys.exit(1)
