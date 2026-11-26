import json
from pathlib import Path
import socket
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.control_ha_support_stopped import StoppedSupport


class Channel:
    def call(self, action, payload=None):
        with socket.socket(socket.AF_UNIX) as connection:
            connection.settimeout(10)
            connection.connect(sys.argv[3])
            connection.sendall(json.dumps(dict(action=action, payload=payload)).encode() + b'\n')
            response = json.loads(connection.makefile('rb').readline(65537))
            if 'error' in response:
                raise ValueError(response['error'])
            return response


class Interrupted(StoppedSupport):
    def readback(self, candidate, digest):
        Path(sys.argv[4]).write_text('snapshot-written-locks-held')
        time.sleep(60)
        return super().readback(candidate, digest)


Interrupted(sys.argv[1], sys.argv[2], Channel()).capture()
