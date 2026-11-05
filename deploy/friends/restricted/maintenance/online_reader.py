import json
import socket
import hashlib
from pathlib import Path
import stat
import struct

from credential_renewal import canonical, parse, require


class RuntimeReader:
    def __init__(self, path, *, expected_uid=None, expected_executable=None, service_state=None):
        self.path = str(path)
        self.expected_uid = expected_uid
        self.expected_executable = expected_executable
        self.service_state = service_state

    def verify_peer(self, channel):
        if self.service_state is None:
            return
        path = Path(self.path)
        require(path.is_absolute() and not path.is_symlink(), 'ONLINE_READER_PATH')
        metadata = path.lstat()
        require(stat.S_ISSOCK(metadata.st_mode) and metadata.st_uid == self.expected_uid
                and metadata.st_mode & 0o077 == 0, 'ONLINE_READER_CUSTODY')
        for parent in path.parents:
            metadata = parent.lstat()
            require(stat.S_ISDIR(metadata.st_mode) and metadata.st_uid == 0
                    and metadata.st_mode & 0o022 == 0, 'ONLINE_READER_CUSTODY')
        process, user, group = struct.unpack('3i', channel.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
        service = self.service_state()
        require(user == self.expected_uid and service['ActiveState'] == 'active'
                and process > 0 and service['MainPID'] == str(process), 'ONLINE_READER_PROCESS')
        with open('/proc/'+str(process)+'/exe', 'rb') as executable:
            require(hashlib.file_digest(executable, 'sha256').hexdigest() == self.expected_executable,
                    'ONLINE_READER_EXECUTABLE')

    def __call__(self, candidate):
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as channel:
            channel.settimeout(5)
            channel.connect(self.path)
            self.verify_peer(channel)
            channel.sendall(canonical(dict(candidate=candidate)) + b'\n')
            channel.shutdown(socket.SHUT_WR)
            response = bytearray()
            while len(response) <= 4096:
                chunk = channel.recv(4097-len(response))
                if not chunk:
                    break
                response.extend(chunk)
            require(len(response) <= 4096, 'ONLINE_RUNTIME_RECEIPT')
            def pairs(items):
                require(len({name for name, value in items}) == len(items), 'ONLINE_RUNTIME_RECEIPT')
                return dict(items)
            self.verify_peer(channel)
            return parse(canonical(json.loads(response, object_pairs_hook=pairs)))
