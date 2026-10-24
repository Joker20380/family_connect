"""Synthetic in-process operator service; no sockets, production identities or grants."""
import json
import time

import httpx

from control.friends.access import Access, Rejected
from control.friends.notices import device_request, NoticeDenied, NoticeConflict
from scripts.service_notices import Notices


class AnnouncementServer:
    def __init__(self, root, *, create=True):
        root.mkdir(parents=True, exist_ok=True)
        self.root = root
        self.access = Access(root / 'access.sqlite')
        if create:
            self.access.initialize()
        else:
            assert self.access.path.is_file()
        self.store = Notices(root / 'notices.sqlite')
        self.requests = []
        self.reject = self.lose_reply = False
        self.after_challenge = None

    def http(self):
        return httpx.Client(base_url='https://announcement.test.invalid', transport=httpx.MockTransport(self.route))

    def route(self, request):
        path = request.url.path
        self.requests.append(path)
        if request.method == 'GET' and path == '/downloads/family-connect-events-v2.json':
            return httpx.Response(200, stream=httpx.ByteStream(json.dumps(self.store.feed(version=2)).encode()))
        value = json.loads(request.content)
        try:
            if path == '/friends/challenge':
                result = self.access.challenge(**value)
                if self.after_challenge is not None and value['purpose'].startswith('notices-'):
                    self.after_challenge()
                return httpx.Response(200, json=result)
            if path == '/friends/activate':
                return httpx.Response(200, json=dict(device=self.access.complete(value, 'activate')['device'], status='active'))
            if path.startswith('/friends/chat/'):
                return httpx.Response(403)
            assert path.startswith('/friends/notices/device/')
            if self.reject:
                return httpx.Response(503)
            if path.endswith('/list'):
                deadline = time.monotonic() + 8
                while (self.root / 'hold-list').exists() and time.monotonic() < deadline:
                    time.sleep(.02)
            result = device_request(self.access, self.root / 'notices.sqlite', self.root / 'feed.json', path.rsplit('/', 1)[-1], value)
            lost = self.root / 'lose-reply'
            if self.lose_reply or lost.exists():
                self.lose_reply = False
                lost.unlink(missing_ok=True)
                raise httpx.ReadTimeout('synthetic lost reply')
            return httpx.Response(200, stream=httpx.ByteStream(json.dumps(result).encode()))
        except (Rejected, NoticeDenied):
            return httpx.Response(403, json={'error': 'private failure details'})
        except NoticeConflict:
            return httpx.Response(409)

    def close(self):
        self.store.db.close()
