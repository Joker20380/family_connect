"""Mailbox authority custody only; no message spool, service start or membership refresh."""
import base64
import fcntl
import ipaddress
import os
from pathlib import Path
import signal
import stat
import time

from scripts import control_ha_file_custody as custody
from scripts.control_ha_installed_inventory import Reader
from scripts.control_ha_live_sqlite import require

ROOT = Path('/opt/apps/family_connect/mailbox-pilot')
SECONDS = 0.25
FILES = ('accept_membership.py', 'settings.json', 'bootstrap.json', 'members.json', 'node.identity',
         'state/.volume-id', 'state/rns/config', 'app/messenger/membership.py', 'app/messenger/server.py')
PINS = {'accept_membership.py': '7e575dd6d3f030b1fc5e6398491088ad5e5a29a99331c14afa99f0d20f2d0023',
        'app/messenger/membership.py': 'a0c7513ceed6e58e83026066db5b3d01a595c408424185e9ebc8e21bd89cc4b4',
        'app/messenger/server.py': '01c4d94b9bce9b7137c4f9cc25eba3046bd57ac41f81ff683ad317a6b323077c'}


def capture(root=ROOT):
    reader = Reader()
    for name, expected in PINS.items():
        require(custody.digest(reader.raw(root / name)) == expected, 'MAILBOX_SOURCE_CHANGED')
    require(signal.getsignal(signal.SIGALRM) == signal.SIG_DFL and
            signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0), 'ALARM_NOT_EXCLUSIVE')
    started = time.monotonic()
    signal.setitimer(signal.ITIMER_REAL, SECONDS)
    try:
        with reader.opened(root / '.members.lock') as descriptor:
            info = os.fstat(descriptor)
            require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_size == 0, 'MAILBOX_LOCK')
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            document = custody.capture(dict(slot='NL1', files={name: str(root / name) for name in FILES}, trees={}))
            reader.verify()
        elapsed = time.monotonic() - started
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
    require(elapsed < SECONDS, 'MAILBOX_DEADLINE')
    return document, dict(barrier_seconds=elapsed, deadline_seconds=SECONDS,
                          document_sha256=custody.digest(custody.encoded(document)),
                          dispatcher_fence=False, activation=False, message_spool=False)


def validate(document):
    import RNS
    from messenger.membership import validate as membership
    import json
    custody.validate(document)
    require(document['plan']['slot'] == 'NL1' and set(document['entries']) == set(FILES), 'MAILBOX_SCOPE')
    files = {name: base64.b64decode(entry['body'], validate=True) for name, entry in document['entries'].items()}
    for name, expected in PINS.items():
        require(custody.digest(files[name]) == expected, 'MAILBOX_SOURCE_CHANGED')
    settings = json.loads(files['settings.json'], object_pairs_hook=custody.pairs)
    bootstrap = json.loads(files['bootstrap.json'], object_pairs_hook=custody.pairs)
    members = membership(json.loads(files['members.json'], object_pairs_hook=custody.pairs), document['finished_at_ns'] / 1e9)
    require(type(settings) is dict and set(settings) == {'volume_id', 'public_key', 'allowed_public'} and
            type(settings['volume_id']) is str and len(settings['volume_id']) == 32 and
            bytes.fromhex(settings['volume_id']).hex() == settings['volume_id'] and
            files['state/.volume-id'].decode().strip() == settings['volume_id'], 'MAILBOX_VOLUME')
    require(type(settings['allowed_public']) is list and 1 <= len(settings['allowed_public']) <= 100 and
            len(set(settings['allowed_public'])) == len(settings['allowed_public']) and
            all(type(value) is str and len(value) == 128 and bytes.fromhex(value).hex() == value
                for value in settings['allowed_public']), 'MAILBOX_STATIC_MEMBERS')
    require(len(files['node.identity']) == 64, 'MAILBOX_IDENTITY')
    identity = RNS.Identity.from_bytes(files['node.identity'])
    require(identity is not None and identity.get_public_key().hex() == settings['public_key'], 'MAILBOX_KEY_BINDING')
    require(type(bootstrap) is dict and set(bootstrap) == {'server', 'port', 'public_key', 'destination'} and
            bootstrap['server'] == str(ipaddress.IPv4Address(bootstrap['server'])) and
            type(bootstrap['port']) is int and 1 <= bootstrap['port'] <= 65535 and
            bootstrap['public_key'] == settings['public_key'] and
            bootstrap['destination'] == RNS.Destination.hash(identity, 'lxmf', 'propagation').hex(), 'MAILBOX_BOOTSTRAP')
    return dict(result='MAILBOX_AUTHORITY_READBACK_PASS', files=len(files), sequence=members['sequence'],
                dynamic_members=len(members['public_keys']), static_members=len(settings['allowed_public']),
                activation=False, dispatcher_fence=False, message_spool=False)
