"""Loopback-only integration peer with synthetic transport keys."""

import base64
import http.client
import importlib.util
import json
import os
from pathlib import Path
import sys
import time


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
mode, directory, port = sys.argv[1:4]
directory = Path(directory)
if mode == 'server':
    import RNS
    from provisioning.readiness_relay import ReadinessRelay
    directory.mkdir(mode=0o700)
    (directory / 'config').write_text('[reticulum]\nshare_instance = No\nenable_transport = No\n'
        '[logging]\nloglevel = 0\n[interfaces]\n[[loopback]]\nenabled = Yes\n'
        'type = TCPServerInterface\nlisten_ip = 127.0.0.1\nlisten_port = ' + port + '\n')
    RNS.Reticulum(configdir=str(directory), loglevel=0)
    specification = importlib.util.spec_from_file_location('provisioning._deployed_candidate',
        os.environ['FC_RNS_PROVIDER_SOURCE'])
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    identity = RNS.Identity()
    readiness = ReadinessRelay(lambda: http.client.HTTPConnection('127.0.0.1', int(sys.argv[4]), timeout=3))
    provider = module.ReticulumControlProvider(None, identity, readiness=readiness)
    print(base64.b64encode(identity.get_public_key()).decode(), flush=True)
    while True:
        provider.destination.announce()
        time.sleep(.2)
else:
    sys.path.insert(0, os.environ['FC_ANDROID_RNS_SOURCE'])
    from fc_rns_transport import Channel
    class Callbacks:
        def bindSocket(self, descriptor):
            return descriptor >= 0

        def cancelled(self):
            return False
    channel = Channel(str(directory), '127.0.0.1', int(port), sys.argv[4], Callbacks())
    try:
        print('READY', flush=True)
        for line in sys.stdin:
            request = json.loads(line)
            raw = json.dumps(request['body']).encode()
            response = channel.request(request['path'], base64.b64encode(raw).decode())
            print(base64.b64decode(response).decode(), flush=True)
    finally:
        channel.close()
