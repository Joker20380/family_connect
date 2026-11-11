"""Closed registry projection and opt-in support role for authenticated enrollment."""
import hashlib
import hmac
import json
import os
import re
import stat
import tempfile

from messenger.support import validate
from .chat import ChatAccess
from .chat_publishers import unique


def load(path):
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or not 0 < info.st_size <= 4096 or info.st_mode & 0o022:
        raise ValueError('Unsafe support configuration')
    document = json.loads(path.read_bytes(), object_pairs_hook=unique)
    fields = {'schema', 'sender_public', 'revision', 'enabled'}
    if (type(document) is not dict or type(document.get('schema')) is not int
            or document['schema'] not in (1, 2)
            or set(document) != (fields | {'sender_device'} if document['schema'] == 1 else fields)
            or (document['schema'] == 1 and (type(document['sender_device']) is not str
                or re.fullmatch('[0-9a-f]{32}', document['sender_device']) is None))
            or type(document['sender_public']) is not str or re.fullmatch('[0-9a-f]{128}', document['sender_public']) is None
            or type(document['revision']) is not int or not 1 <= document['revision'] <= 2**53 - 1
            or type(document['enabled']) is not bool):
        raise ValueError('Invalid support configuration')
    return document


def sender(database, document):
    if document['schema'] == 2:
        registered = database.execute('SELECT enabled FROM chat_service_senders WHERE public=?',
                                      (document['sender_public'],)).fetchone()
        if registered is None or not registered['enabled']:
            raise ValueError('Unregistered support service sender')
        return
    ChatAccess.active(database, document['sender_device'])
    registered = database.execute('SELECT public FROM chat_bindings WHERE device=?', (document['sender_device'],)).fetchone()
    if registered is None or registered['public'] != document['sender_public']:
        raise ValueError('Unregistered support sender')


def configuration(access, path, device, chat_public, expires):
    document = load(path)
    with access.db() as database:
        ChatAccess.active(database, device)
        sender(database, document)
        binding = database.execute('SELECT public FROM chat_bindings WHERE device=?', (device,)).fetchone()
        if binding is None or binding['public'] != chat_public:
            raise ValueError('Unregistered support binding')
    return validate(dict(schema=1, device=device, chat_public=chat_public,
                         sender_public=document['sender_public'], revision=document['revision'],
                         enabled=document['enabled'], expires_at=expires), device, chat_public, int(access.clock()))


def enroll(access, path, device, chat_public, expires):
    value = configuration(access, path, device, chat_public, expires)
    with access.db() as database:
        ChatAccess.active(database, device)
        binding = database.execute('SELECT public,support_sender FROM chat_bindings WHERE device=?', (device,)).fetchone()
        if (binding is None or binding['public'] != chat_public
                or binding['support_sender'] not in (None, value['sender_public'])):
            raise ValueError('Support enrollment identity changed')
        database.execute('UPDATE chat_bindings SET support_sender=? WHERE device=?', (value['sender_public'], device))
    return value


def bindings(access, key, path, node):
    if type(key) is not bytes or len(key) != 32:
        raise ValueError('Inventory HMAC key required')
    document = load(path)
    if (type(node) is not dict or set(node) != {'sequence', 'expires_at', 'host', 'port', 'public_key'}
            or type(node['sequence']) is not int or node['sequence'] < 1
            or type(node['expires_at']) is not int or not access.clock() < node['expires_at'] <= access.clock() + 120):
        raise ValueError('Fresh acknowledged mailbox lease required')
    with access.db() as database:
        sender(database, document)
        if database.execute('SELECT value FROM chat_sequence WHERE id=1').fetchone()[0] != node['sequence']:
            raise ValueError('Mailbox lease sequence mismatch')
        rows = database.execute('''SELECT d.device, c.public, c.support_sender, d.revoked,
            EXISTS(SELECT 1 FROM invites i WHERE i.device=d.device AND i.revoked=0) AS active
            FROM devices d LEFT JOIN chat_bindings c ON c.device=d.device ORDER BY d.device''').fetchall()
    return dict(schema=1, sequence=node['sequence'], expires_at=node['expires_at'], sender_public=document['sender_public'],
                node={name: value for name, value in node.items() if name != 'sequence'},
                devices=[dict(pseudonym=hmac.new(key, row['device'].encode(), hashlib.sha256).hexdigest(),
                              device=row['device'], public=row['public'],
                              state='revoked' if row['revoked'] or not row['active'] or not document['enabled'] else
                              'unregistered' if row['public'] is None else
                              'support_not_enrolled' if row['support_sender'] != document['sender_public'] else
                              'verified') for row in rows])


def publish(access, root, node):
    descriptor = os.open(root / 'support-inventory-hmac.key', os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as stream:
        info = os.fstat(stream.fileno())
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077
                or info.st_size != 32 or info.st_nlink != 1):
            raise ValueError('Private existing inventory HMAC key required')
        key = stream.read(33)
    document = bindings(access, key, root / 'chat-support.json', node)
    descriptor, temporary = tempfile.mkstemp(prefix='.support-bindings-', dir=root)
    try:
        with os.fdopen(descriptor, 'w') as stream:
            json.dump(document, stream, separators=(',', ':'))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, root / 'support-bindings.json')
        directory = os.open(root, os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
