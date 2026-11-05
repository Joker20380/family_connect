import json
import socket

from credential_renewal import canonical, parse, require


class RuntimeReader:
    def __init__(self, path):
        self.path = str(path)

    def __call__(self, candidate):
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as channel:
            channel.settimeout(5)
            channel.connect(self.path)
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
            return parse(canonical(json.loads(response, object_pairs_hook=pairs)))
