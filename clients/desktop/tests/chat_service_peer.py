"""Private session test worker; never packaged, no operator or live service access."""
import json
import os
from pathlib import Path
import signal
import sys
import time
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / 'clients/desktop'), str(ROOT)]

from gi.repository import GLib
from chat_daemon import ChatService
from device_identity.friends import load_friends_identity
from provisioning.chat_owner import ChatOwner
from provisioning.chat_transport import SystemMailbox


root = Path(sys.argv[1])
def offline():
    raise OSError('fixture has no external HTTP')
friends = SimpleNamespace(_device=lambda create: load_friends_identity(root / 'device', create=False), http_factory=offline)


class Owner(ChatOwner):
    def invoke(self, operation, **arguments):
        result = super().invoke(operation, **arguments)
        if operation == 'queue' and arguments.get('text') == 'synthetic-crash-after-commit':
            os._exit(17)
        return result

    def tick(self, **arguments):
        lease = root / 'node.json'
        if self.local is not None and self.carrier is None and lease.exists():
            node = json.loads(lease.read_text())
            if node['expires_at'] > time.time():
                self.carrier = self.local.attach_carrier(lambda chat: SystemMailbox(chat, node, self.runtime))
                self.node = node
        return super().tick(**arguments)


owner = Owner(root / 'chat', friends, events_fetcher=lambda _: [])
service = ChatService(owner, online=lambda: True,
    activate=lambda peer: (root / 'opened-peer').write_text(peer))
for signum in (signal.SIGTERM, signal.SIGINT):
    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signum, service.stop)
service.run()
