"""Service-owned recovery intent; private material stays in a systemd-held memfd."""
import array
import fcntl
import json
import os
from pathlib import Path
import secrets
import select
import socket
import stat

import mesh_ipc as ipc
from mesh_system import command, private_read, private_write

NAME = 'fc-mesh-intent-v1'
LIMIT = 4096
SEALS = fcntl.F_SEAL_GROW | fcntl.F_SEAL_SHRINK | fcntl.F_SEAL_SEAL


class Notifier:
    def __init__(self, unit, counter=None, name=NAME):
        if name not in (NAME, 'fc-auto-intent-v1'):
            raise ValueError('Invalid recovery descriptor name')
        self.name = name
        self.address = os.environ.get('NOTIFY_SOCKET', '')
        if not self.address or self.address[0] not in ('/', '@'):
            raise ValueError('MESH service manager required')
        if self.address[0] == '@':
            self.address = '\0' + self.address[1:]
        self.counter = counter or (lambda: int(command('systemctl', 'show', unit,
            '--property=NFileDescriptorStore', '--value').stdout.strip()))

    def send(self, message, descriptors=()):
        with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as transport:
            transport.settimeout(2)
            transport.connect(self.address)
            ancillary = [(socket.SOL_SOCKET, socket.SCM_RIGHTS, array.array('i', descriptors))] if descriptors else []
            if transport.sendmsg([message.encode()], ancillary) != len(message.encode()):
                raise OSError('MESH manager notification failed')

    def barrier(self):
        reader, writer = os.pipe2(os.O_CLOEXEC | os.O_NONBLOCK)
        try:
            self.send('BARRIER=1', (writer,))
            os.close(writer)
            writer = None
            if not select.select([reader], [], [], 2)[0] or os.read(reader, 1) != b'':
                raise TimeoutError('MESH manager acknowledgment missing')
        finally:
            os.close(reader)
            if writer is not None:
                os.close(writer)

    def store(self, descriptor):
        self.send('FDSTORE=1\nFDPOLL=0\nFDNAME=' + self.name, (descriptor,))
        self.barrier()
        if self.counter() != 1:
            raise RuntimeError('MESH recovery descriptor was not retained')

    def remove(self):
        self.send('FDSTOREREMOVE=1\nFDNAME=' + self.name)
        self.barrier()

    def ready(self):
        self.send('READY=1')


class Intent:
    name, limit = NAME, LIMIT

    @staticmethod
    def validate(materials):
        ipc.validate_request(dict(schema=1, id=1, action='start', materials=materials))

    def __init__(self, path, uid, notifier=None, expected_owner=0):
        if type(uid) is not int or not 1 <= uid < 2**31:
            raise ValueError('Invalid MESH intent owner')
        self.path, self.uid, self.notifier = Path(path), uid, notifier
        self.expected_owner = expected_owner
        self.descriptor = None
        if notifier is not None and getattr(notifier, 'name', self.name) != self.name:
            raise ValueError('Recovery notifier contract mismatch')

    def read(self):
        if not self.path.exists():
            return None
        value = private_read(self.path, expected_owner=self.expected_owner)
        if (not isinstance(value, dict) or set(value) != {'schema', 'uid', 'generation', 'desired', 'recoveries'} or
                type(value['schema']) is not int or value['schema'] != 1 or type(value['uid']) is not int or value['uid'] != self.uid or
                type(value['desired']) is not bool or type(value['recoveries']) is not int or not 0 <= value['recoveries'] < 2**31 or
                not isinstance(value['generation'], str) or len(value['generation']) != 32 or
                any(part not in '0123456789abcdef' for part in value['generation'])):
            raise ValueError('Invalid MESH intent journal')
        return value

    def desired(self):
        value = self.read()
        return value is not None and value['desired']

    def begin(self, materials):
        self.validate(materials)
        if self.descriptor is not None or self.desired() or self.notifier is None:
            raise ValueError('MESH recovery owner is already active or unavailable')
        record = dict(schema=1, uid=self.uid, generation=secrets.token_hex(16), desired=True, recoveries=0)
        body = dict(schema=1, uid=self.uid, generation=record['generation'], materials=materials)
        raw = b'\1' + json.dumps(body, separators=(',', ':')).encode()
        if len(raw) > self.limit:
            raise ValueError('MESH recovery material exceeds limit')
        descriptor = os.memfd_create(self.name, os.MFD_CLOEXEC | os.MFD_ALLOW_SEALING)
        try:
            os.fchmod(descriptor, 0o600)
            if os.write(descriptor, raw) != len(raw):
                raise OSError('MESH recovery material incomplete')
            fcntl.fcntl(descriptor, fcntl.F_ADD_SEALS, SEALS)
            self.notifier.store(descriptor)
            private_write(self.path, record)
            self.descriptor = descriptor
        except BaseException:
            try:
                try:
                    os.pwrite(descriptor, b'\0', 0)
                finally:
                    self.notifier.remove()
            finally:
                os.close(descriptor)
            raise

    def inherited(self):
        process = os.environ.pop('LISTEN_PID', None)
        count = os.environ.pop('LISTEN_FDS', None)
        names = os.environ.pop('LISTEN_FDNAMES', None)
        if process is None and count is None and names is None:
            return None
        if process != str(os.getpid()) or count != '1' or names != self.name:
            raise ValueError('Invalid MESH inherited descriptor contract')
        descriptor = os.dup(3)
        os.close(3)
        os.set_inheritable(descriptor, False)
        return descriptor

    def recover(self, descriptor=None):
        self.descriptor = self.inherited() if descriptor is None else descriptor
        if self.descriptor is None:
            return None
        info = os.fstat(self.descriptor)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != self.expected_owner or info.st_nlink != 0 or
                stat.S_IMODE(info.st_mode) != 0o600 or not 1 < info.st_size <= self.limit or
                fcntl.fcntl(self.descriptor, fcntl.F_GET_SEALS) & SEALS != SEALS or
                os.readlink('/proc/self/fd/' + str(self.descriptor)) != '/memfd:' + self.name + ' (deleted)'):
            raise ValueError('Invalid MESH recovery memory descriptor')
        raw = os.pread(self.descriptor, self.limit + 1, 0)
        record = self.read()
        if raw[:1] == b'\0' or record is None or not record['desired']:
            if self.notifier is not None:
                self.notifier.remove()
            self.close()
            return None
        body = ipc.decode(raw[1:], self.limit)
        if (raw[:1] != b'\1' or set(body) != {'schema', 'uid', 'generation', 'materials'} or
                type(body['schema']) is not int or body['schema'] != 1 or type(body['uid']) is not int or body['uid'] != self.uid or
                body['generation'] != record['generation']):
            raise ValueError('MESH recovery memory does not match current intent')
        self.validate(body['materials'])
        record['recoveries'] = min(record['recoveries'] + 1, 2**31 - 1)
        private_write(self.path, record)
        return body['materials']

    def revoke(self):
        if self.descriptor is not None:
            if os.pwrite(self.descriptor, b'\0', 0) != 1:
                raise OSError('MESH recovery revocation failed')
            os.fsync(self.descriptor)
        record = self.read()
        if record is not None:
            private_write(self.path, dict(record, desired=False))

    def close(self):
        if self.descriptor is not None:
            os.close(self.descriptor)
            self.descriptor = None
