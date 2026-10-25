"""Offline real systemd/polkit/helper reproduction; never run on the workstation."""
import base64
import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import pwd
import stat
import subprocess
import sys


def child(transport):
    assert os.getuid() == 1000
    sys.dont_write_bytecode = True
    root = Path('/usr/lib/family-connect')
    for directory in ('vendor', '.', 'clients/desktop'):
        sys.path.insert(0, str(root / directory))
    import backend
    import candidate_runtime
    from device_identity.friends import load_friends_identity
    from provisioning.friends_application import FriendsApplication
    from provisioning.friends_store import FriendsConfigurationStore
    backend.CANDIDATE_GUARD = candidate_runtime.installed_guard
    assert backend.system_component_status() == 'READY'
    identity = Path.home() / 'synthetic-identity'
    device = load_friends_identity(identity, create=True)
    fixture = json.loads(Path('/fixture/catalog.json').read_text())
    store = FriendsConfigurationStore(identity, device, base64.b64decode(fixture['anchor']))
    response = copy.deepcopy(fixture['vectors'][0]['reply'])
    response.update(device=device.reference, country='nl', address='10.83.0.2/32')
    verified = store.accept('nl', lambda *_: response)
    cache_before = hashlib.sha256((identity/'friends.configuration.json').read_bytes()).hexdigest()
    driver = backend.backend()
    application = FriendsApplication(store, driver)
    events = []
    requests = []
    original_call = backend._AuthorizationSession.call
    def call(session, kind, action, ident, data):
        requests.append(dict(kind=kind, action=action))
        try:
            return original_call(session, kind, action, ident, data)
        except Exception as error:
            events.append(dict(step='authorization', error=type(error).__name__, message=str(error)))
            raise
    backend._AuthorizationSession.call = call
    def observe(target, name, label):
        original = getattr(target, name)
        def wrapped(*args, **kwargs):
            events.append(dict(step=label, stage='enter'))
            try:
                result = original(*args, **kwargs)
            except Exception as error:
                events.append(dict(step=label, stage='failure', error=type(error).__name__, message=str(error)))
                raise
            events.append(dict(step=label, stage='return'))
            return result
        setattr(target, name, wrapped)
    observe(driver, 'connect', 'connect')
    observe(application.adapter, 'rollback', 'rollback')
    observe(application, '_write', 'journal-write')
    observe(backend.OperationLease, 'finish', 'finish')
    with backend.connection_operation() as lease:
        before = dict(lease.record)
    fetches = []
    def fetch():
        fetches.append(True)
        return verified
    try:
        application.connect(fetch, transport=transport)
        raise AssertionError('Transport unexpectedly started')
    except Exception as error:
        terminal = dict(error=type(error).__name__, message=str(error))
    journal_validation = None
    with store._locked() as directory:
        try:
            journal = application._read(directory)
        except ValueError as error:
            journal_validation = str(error)
            journal = json.loads((identity/'friends.application.json').read_text())
    operation = json.loads((backend.operation_directory()/'state.json').read_text())
    with backend.connection_operation(owner=application.owner):
        physical_lock_free = True
    assert hashlib.sha256((identity/'friends.configuration.json').read_bytes()).hexdigest() == cache_before
    print(json.dumps(dict(transport=transport, before=before, terminal=terminal, events=events,
                          requests=requests, fetches=len(fetches), journal_phase=journal['phase'],
                          generation=operation['generation'], pending=operation['pending'] is not None,
                          physical_user_lock_free=physical_lock_free, cache_preserved=True,
                          journal_validation_error=journal_validation)), flush=True)


def parent(transport):
    assert os.geteuid() == 0 and Path('/.dockerenv').exists()
    assert Path('/proc/1/comm').read_text().strip() == 'systemd'
    assert os.environ['FC_L032_HOST_NETNS'] != str(Path('/proc/self/ns/net').stat().st_ino)
    descriptor = os.open('/run/family-connect-transport.lock', os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW, 0o600)
    metadata = os.fstat(descriptor)
    assert metadata.st_uid == 0 and stat.S_IMODE(metadata.st_mode) == 0o600 and metadata.st_nlink == 1
    fcntl.flock(descriptor, fcntl.LOCK_EX|fcntl.LOCK_NB)
    def network():
        commands = [['ip','-j','link'], ['ip','-j','-4','route','show','table','all'],
                    ['ip','-j','-6','route','show','table','all'], ['ip','-j','-4','rule'],
                    ['ip','-j','-6','rule'], ['resolvectl','dns'], ['resolvectl','domain'],
                    ['nft','list','ruleset']]
        return [hashlib.sha256(subprocess.check_output(command)).hexdigest() for command in commands]
    before = network()
    user = pwd.getpwuid(1000)
    result = subprocess.run(['setpriv','--reuid','1000','--regid',str(user.pw_gid),'--init-groups',
                             '/usr/bin/python3','-I','-S',__file__,'child',transport],
                            env={**os.environ,'HOME':user.pw_dir,'PYTHONDONTWRITEBYTECODE':'1'},
                            capture_output=True,text=True,timeout=90)
    assert result.returncode == 0, result.stderr[-2000:]
    assert before == network()
    assert not any(Path('/sys/class/net').glob('fc*'))
    assert not Path('/run/family-connect-awg/active.json').exists()
    assert not Path('/run/family-connect-tcp/active').exists()
    os.close(descriptor)
    value=json.loads(result.stdout)
    value.update(successful_transport_starts=0,root_owner_count=0,tun_count=0,network_unchanged=True,root_fixture_released=True)
    print(json.dumps(value),flush=True)


if __name__ == '__main__':
    (child if sys.argv[1] == 'child' else parent)(sys.argv[2])
