"""Synthetic operator API behind the real chat D-Bus service; not packaged."""
import os
from pathlib import Path
import signal
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / 'clients/desktop'), str(ROOT)]

from gi.repository import GLib
from chat_daemon import ChatService
from chat_ui_check import MemoryKeyring
from messenger.tests.announcement_server import AnnouncementServer
from provisioning.chat_owner import ChatOwner
from provisioning.friends_owner import FriendsOwner


root = Path(sys.argv[1])
assert os.environ.get('DBUS_SESSION_BUS_ADDRESS')
server = AnnouncementServer(root / 'server', create=False)
friends = FriendsOwner(root / 'identity', root / 'anchor', http_factory=server.http)
owner = ChatOwner(root / 'chat', friends, keyring=MemoryKeyring())
service = ChatService(owner, online=lambda: True, activate=lambda _: None)
for signum in (signal.SIGTERM, signal.SIGINT):
    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signum, service.stop)
try:
    service.run()
finally:
    server.close()
