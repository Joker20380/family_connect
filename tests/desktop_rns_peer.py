"""Loopback-only RNS fixture; bootstrap overrides exist only in this test process."""
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import socket
import sys
import time
import types
import zipimport

mode, archive, directory = sys.argv[1:]
root = Path(directory)

PATHS = tuple('/friends/restricted-readiness' + suffix for suffix in ('/challenge', '', '/ack-challenge', '/ack'))


def server():
    config = root / 'server'
    config.mkdir()
    with socket.socket() as reserve:
        reserve.bind(('127.0.0.1', 0))
        port = reserve.getsockname()[1]
    (config / 'config').write_text('[reticulum]\nshare_instance = No\nenable_transport = No\n'
        '[logging]\nloglevel = -1\n[interfaces]\n[[loopback]]\nenabled = Yes\n'
        'type = TCPServerInterface\nlisten_ip = 127.0.0.1\nlisten_port = ' + str(port) + '\n')
    RNS.Reticulum(configdir=str(config), loglevel=-1)
    identity = RNS.Identity()
    destination = RNS.Destination(identity, RNS.Destination.IN, RNS.Destination.SINGLE,
                                  'family_connect', 'control', 'v1')
    def respond(path, data, request_id, remote_identity, requested_at):
        assert path in PATHS and isinstance(data, bytes) and len(data) <= 8192
        with (root / 'requests.jsonl').open('a') as output:
            output.write(json.dumps(dict(path=path, size=len(data), sha256=hashlib.sha256(data).hexdigest())) + '\n')
        payload = bytes(range(256)) * 256 if path == PATHS[1] else data
        return json.dumps(dict(status=200, body=base64.b64encode(payload).decode()), separators=(',', ':')).encode()
    for path in PATHS:
        destination.register_request_handler(path, respond, allow=RNS.Destination.ALLOW_ALL, auto_compress=False)
    public = dict(port=port, provider=base64.b64encode(identity.get_public_key()).decode())
    (root / 'public.json').write_text(json.dumps(public))
    print('READY', flush=True)
    while True:
        destination.announce()
        time.sleep(0.5)


def client():
    specification = importlib.util.spec_from_file_location('desktop_rns_test_worker', runtime / 'fc_rns_worker.py')
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    bootstrap = json.loads((root / 'public.json').read_text())
    module.HOST, module.PORT, module.PROVIDER = '127.0.0.1', bootstrap['port'], bootstrap['provider']
    binds = []
    class LoopbackCallbacks(module.Callbacks):
        def __init__(self, index, deadline, stop):
            self.index, self.deadline, self.stop = index, deadline, stop
        def bindSocket(self, descriptor):
            binds.append(descriptor >= 0)
            return descriptor >= 0 and module.HOST == '127.0.0.1' and not self.cancelled()
    module.Callbacks = LoopbackCallbacks
    sys.argv = [archive, '--stdio']
    result = module.main()
    (root / 'client-result.json').write_text(json.dumps(dict(exit_code=result, binds=binds,
        crypto_provider=RNS.Cryptography.Provider.backend())))
    return result


launcher = types.ModuleType('desktop_rns_test_launcher')
exec(zipimport.zipimporter(archive).get_code('__main__'), launcher.__dict__)
with launcher.unpack(archive) as runtime:
    sys.path.insert(0, str(runtime))
    import RNS
    if mode == 'server':
        server()
    elif mode == 'client':
        sys.exit(client())
    else:
        raise SystemExit(64)
