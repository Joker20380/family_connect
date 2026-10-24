"""Isolated support fixture: real identity/API handlers, synthetic VPN, no external HTTP."""
import json
import os
from pathlib import Path
import signal
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT/'clients/desktop'), str(ROOT)]

import httpx
from gi.repository import GLib
from chat_daemon import ChatService
from control.friends.access import Access, Rejected
from control.friends import diagnostics
from control.friends.referrals import RateLimited
from messenger.local import LocalError
from provisioning.friends_owner import FriendsOwner
from support_daemon import SupportSession


root = Path(sys.argv[1]).resolve()
access = Access(root/'registry.db')


def route(request):
    value = json.loads(request.content)
    try:
        if request.url.path == '/friends/challenge':
            return httpx.Response(200, json=access.challenge(**value))
        if request.url.path == '/friends/device/diagnostics':
            result = diagnostics.request(access, root/'snapshots.db', value)
            with (root/'stored.jsonl').open('a') as output:
                output.write(json.dumps(dict(report_id=result['report_id'], at=time.monotonic(), pid=os.getpid()))+'\n')
            return httpx.Response(200, json=result)
        raise AssertionError('No other network endpoint is permitted')
    except RateLimited:
        return httpx.Response(429)
    except Rejected:
        return httpx.Response(403)


friends = FriendsOwner(root/'device', root/'anchor', http_factory=lambda:
    httpx.Client(base_url='https://test.invalid', transport=httpx.MockTransport(route)))


class LockedChat:
    local = None

    def open(self, **kwargs):
        raise LocalError('keyring_unavailable')

    def close(self):
        pass


class NoNotifications:
    def __init__(self, activate):
        pass

    def close(self):
        pass


def snapshot():
    return json.loads((root/'sample.json').read_text())


support = SupportSession(friends, snapshot, 2011)
service = ChatService(LockedChat(), support=support, notifier=NoNotifications, online=lambda: False)
for signum in (signal.SIGTERM, signal.SIGINT):
    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signum, service.stop)
service.run()
