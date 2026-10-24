"""Friends operations for the paired Linux frontend; no private data in UI results."""
import base64
import json
import os
import re
import stat
import time
import uuid
from pathlib import Path
import httpx
from device_identity.friends import load_friends_identity
from device_identity.device import _private_directory
from .friends import FriendsClient, FriendsError
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

    def configuration(self,country,driver=None):
        store=self._store()
        if driver is not None and hasattr(driver, 'normal_catalog'):
            store.merge_catalog_floor(driver.normal_catalog())
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
        return FriendsApplication(self._store(),driver).connect(lambda:self.configuration(country,driver),transport=transport)

    def connect_mesh(self, driver, profile="P0"):
        if profile not in ("P0", "P1"):
            raise ValueError("Unsupported MESH profile")
        store = self._store()
        material = dict(identity=base64.b64encode(store.device._identity.get_private_key()).decode("ascii"),
                        wireguard_public=store.device.wireguard_public_key,
                        anchor=base64.b64encode(store.anchor).decode("ascii"), profile=profile)
        try:
            state = driver.start_mesh(material)
            return dict(profile="fcmesh0", transport="mesh", requested_profile=profile,
                        state=state["state"], desired_connected=state["desired_connected"])
        finally:
            material.clear()

    def connect_auto(self, country, driver, profile="P0"):
        if country not in ('ru', 'nl') or profile not in ('P0', 'P1'):
            raise ValueError('Unsupported Auto selection')
        store = self._store()
        material = {}
        try:
            with store._locked() as directory:
                cache, (highest, _floor), saved = store._current(directory)
                material = dict(identity=base64.b64encode(store.device._identity.get_private_key()).decode('ascii'),
                    wireguard_public=store.device.wireguard_public_key,
                    wireguard_private=base64.b64encode(store.device._wireguard_key.private_bytes_raw()).decode('ascii'),
                    anchor=base64.b64encode(store.anchor).decode('ascii'), profile=profile, country=country,
                    normal_floors=[highest] if saved is not None else [reply['catalog'] for reply in cache.values()])
            state = driver.start_auto(material)
            return dict(state=state['state'], desired_connected=state['desired_connected'], selected=state.get('selected', ''))
        finally:
            material.clear()

    def has_existing_identity(self):
        try:
            self._device(False)
            return True
        except (OSError,ValueError):
            return False

    def cached_support_id(self):
        try:
            device = self._device(False)
            with _private_directory(self.path, create=False) as directory:
                descriptor = os.open('support.json', os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
                with os.fdopen(descriptor, 'rb') as source:
                    info = os.fstat(source.fileno())
                    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_nlink != 1 or stat.S_IMODE(info.st_mode) != 0o600:
                        return None
                    raw = source.read(1025)
                if len(raw) > 1024:
                    return None
                value = json.loads(raw, object_pairs_hook=FriendsClient._object)
                if (set(value) == {'schema', 'registration', 'device_support_id'} and type(value['schema']) is int and
                        value['schema'] == 1 and value['registration'] == device.reference and isinstance(value['device_support_id'], str) and
                        re.fullmatch(r'FC-[23456789ABCDEFGHJKMNPQRSTVWXYZ]{4}-[23456789ABCDEFGHJKMNPQRSTVWXYZ]{4}', value['device_support_id'])):
                    return value['device_support_id']
        except (OSError, ValueError, TypeError, FriendsError):
            pass
        return None

    def support_diagnostics(self, report, *, cancelled, registration):
        deadline = time.monotonic() + 15
        if cancelled():
            raise FriendsError('cancelled')
        device = self._device(False)
        if device.reference != registration:
            raise FriendsError('access_rejected')
        with self.http_factory() as http:
            return FriendsClient(http, device, cancelled=cancelled, deadline=deadline).support_diagnostics(report)

    def support_upload(self, snapshot, version_code):
        from .support import SupportConsent, SupportUpload
        device = self._device(False)
        def send(report, *, cancelled):
            return self.support_diagnostics(report, cancelled=cancelled, registration=device.reference)
        return SupportUpload(SupportConsent(self.path, device.reference), send, snapshot, version_code)

    def refresh_support_id(self, version, version_code):
        device = self._device(False)
        with self.http_factory() as http:
            support = FriendsClient(http, device).support_id('linux', version, version_code)
        raw = json.dumps(dict(schema=1, registration=device.reference, device_support_id=support), separators=(',', ':')).encode()
        with _private_directory(self.path, create=False) as directory:
            temporary = '.support-' + uuid.uuid4().hex
            descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=directory)
            try:
                with os.fdopen(descriptor, 'wb') as output:
                    output.write(raw)
                    output.flush()
                    os.fsync(output.fileno())
                os.replace(temporary, 'support.json', src_dir_fd=directory, dst_dir_fd=directory)
                os.fsync(directory)
            finally:
                try:os.unlink(temporary, dir_fd=directory)
                except FileNotFoundError:pass
        return support

    def recover(self,driver):
        from .friends_application import FriendsApplication
        if not self.path.exists():return
        FriendsApplication(self._store(),driver).recover()
