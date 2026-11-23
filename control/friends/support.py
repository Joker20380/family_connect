"""Closed registry projection and opt-in support role for authenticated enrollment."""
import hashlib
import hmac
import json
import os
import re
import stat
import tempfile

from messenger.support import validate
from .chat import ChatAccess, chat_transaction
from .chat_publishers import unique
from .pseudonyms import load as load_aliases, seal


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
    database = chat_transaction(database)
    if document['schema'] == 2:
        registered = database.service(document['sender_public'])
        if registered is None or not registered['enabled']:
            raise ValueError('Unregistered support service sender')
        return
    ChatAccess.active(database, document['sender_device'])
    registered = database.binding(document['sender_device'])
    if registered is None or registered['public'] != document['sender_public']:
        raise ValueError('Unregistered support sender')


def configuration(access, path, device, chat_public, expires):
    document = load(path)
    with access.read_enrollment() as enrollment:
        return _configuration(access, enrollment.chat(), document, device, chat_public, expires)


def _configuration(access, database, document, device, chat_public, expires):
    ChatAccess.active(database, device)
    sender(database, document)
    binding = database.binding(device)
    if binding is None or binding['public'] != chat_public:
        raise ValueError('Unregistered support binding')
    return validate(dict(schema=1, device=device, chat_public=chat_public,
                         sender_public=document['sender_public'], revision=document['revision'],
                         enabled=document['enabled'], expires_at=expires), device, chat_public, int(access.clock()))


def enroll(access, path, device, chat_public, expires):
    document = load(path)
    with access.enrollment() as enrollment:
        database = enrollment.chat()
        value = _configuration(access, database, document, device, chat_public, expires)
        binding = database.binding(device)
        if (binding is None or binding['public'] != chat_public
                or binding['support_sender'] not in (None, value['sender_public'])):
            raise ValueError('Support enrollment identity changed')
        database.enroll_support(device, value['sender_public'])
    return value


def bindings(access, key, path, node):
    if type(key) is not bytes or len(key) != 32:
        raise ValueError('Inventory HMAC key required')
    document = load(path)
    with access.read_enrollment() as enrollment:
        database = enrollment.chat()
        now = access.clock()
        if (type(node) is not dict or set(node) != {'sequence', 'expires_at', 'host', 'port', 'public_key'}
                or type(node['sequence']) is not int or node['sequence'] < 1
                or type(node['expires_at']) is not int or not now < node['expires_at'] <= now + 120):
            raise ValueError('Fresh acknowledged mailbox lease required')
        sender(database, document)
        if database.sequence() != node['sequence']:
            raise ValueError('Mailbox lease sequence mismatch')
        rows = database.support_bindings()
    return dict(schema=1, sequence=node['sequence'], expires_at=node['expires_at'], sender_public=document['sender_public'],
                node={name: value for name, value in node.items() if name != 'sequence'},
                devices=[dict(pseudonym=hmac.new(key, row['device'].encode(), hashlib.sha256).hexdigest(),
                              device=row['device'], public=row['public'],
                              state='revoked' if row['revoked'] or not row['active'] or not document['enabled'] else
                              'unregistered' if row['public'] is None else
                              'support_not_enrolled' if row['support_sender'] != document['sender_public'] else
                              'verified') for row in rows])


def publish(access, root, node):
    if access.enrollment_repository is not None:
        raise NotImplementedError('PostgreSQL support file publication requires fenced authority')
    descriptor = os.open(root / 'support-inventory-hmac.key', os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as stream:
        info = os.fstat(stream.fileno())
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077
                or info.st_size != 32 or info.st_nlink != 1):
            raise ValueError('Private existing inventory HMAC key required')
        key = stream.read(33)
    document = bindings(access, key, root / 'chat-support.json', node)
    aliases_path = root / 'pseudonym-aliases.json'
    if aliases_path.exists():
        document = seal(document, 'support', key, load_aliases(aliases_path))
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
