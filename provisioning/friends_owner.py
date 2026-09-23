"""Friends operations for the paired Linux frontend; no private data in UI results."""
import base64
from pathlib import Path
import httpx
from device_identity.friends import load_friends_identity
from .friends import FriendsClient
from .friends_store import FriendsConfigurationStore


class FriendsOwner:
    def __init__(self, path, anchor_path, *, http_factory=None):
        self.path=Path(path);self.anchor_path=Path(anchor_path)
        self.http_factory=http_factory or (lambda: httpx.Client(base_url='https://185.251.89.19:8443',timeout=12,follow_redirects=False))

    def _device(self, create=False):
        # Parent is application-owned persistent state, separate from versioned builds.
        if create:self.path.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
        return load_friends_identity(self.path,create=create)

    def activate(self, invitation):
        device=self._device(True)
        with self.http_factory() as http:FriendsClient(http,device).activate(invitation)

    def register(self, invitation_token=""):
        device=self._device(True)
        with self.http_factory() as http:return FriendsClient(http,device).register(invitation_token)

    def referral(self):
        device=self._device()
        with self.http_factory() as http:return FriendsClient(http,device).referral()

    def configuration(self,country):
        store=self._store()
        with self.http_factory() as http:
            client=FriendsClient(http,store.device)
            return store.accept(country,lambda floor,digest:client.configuration(country,store.anchor,floor=floor,previous_hash=digest)[0])

    def _store(self):
        device=self._device()
        raw=self.anchor_path.read_bytes()
        if len(raw)>128:raise ValueError('Invalid packaged anchor')
        anchor=base64.b64decode(raw.strip(),validate=True)
        return FriendsConfigurationStore(self.path,device,anchor)

    def connect(self,country,driver,*,transport="tcp"):
        from .friends_application import FriendsApplication
        return FriendsApplication(self._store(),driver).connect(lambda:self.configuration(country),transport=transport)

    def recover(self,driver):
        from .friends_application import FriendsApplication
        if not self.path.exists():return
        FriendsApplication(self._store(),driver).recover()
