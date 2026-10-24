"""Friends enrollment transport for desktop owners of an existing device identity.

This client cannot create keys, apply VPN profiles or grant entitlement locally.
The owner persists keys before using it, owns cancellation and keeps calls off the UI
thread. Server challenge consumption remains the authorization boundary.
"""
import ipaddress
import hashlib
import json
import re
import time


class FriendsError(Exception):
    """A stable public error code; never include server bodies or invitation tokens."""


class FriendsClient:
    LIMIT = 65536
    AUDIENCE = 'family-connect/enrollment/v1'

    def __init__(self, http_client, device, *, clock=time.time, cancelled=None, deadline=None):
        if http_client.base_url.scheme != 'https':
            raise ValueError('friends enrollment requires HTTPS')
        self.http = http_client
        self.device = device
        self.clock = clock
        self.cancelled = cancelled
        self.deadline = deadline

    def _check_request(self):
        if self.cancelled is not None and self.cancelled():
            raise FriendsError('cancelled')
        if self.deadline is not None and time.monotonic() >= self.deadline:
            raise FriendsError('timeout')

    @classmethod
    def from_linux_store(cls, http_client, path, *, create=False, clock=time.time):
        if http_client.base_url.scheme != 'https':
            raise ValueError('friends enrollment requires HTTPS')
        from device_identity.friends import load_friends_identity
        # Persist and validate the identity before returning anything able to send
        # an enrollment proof. Resume never falls back to creating replacement keys.
        device = load_friends_identity(path, create=create)
        return cls(http_client, device, clock=clock)

    @staticmethod
    def _object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate field')
            result[key] = value
        return result

    @staticmethod
    def _fields(value, fields):
        if type(value) is not dict or set(value) != set(fields.split()):
            raise FriendsError('invalid_response')

    @staticmethod
    def _integer(value, minimum=0):
        if type(value) is not int or value < minimum:
            raise FriendsError('invalid_response')
        return value

    @staticmethod
    def _constant(_):
        raise ValueError("non-finite JSON number")

    def _post(self, path, body, *, limit=None, notice_conflict=False, identity_encoding=False, rate_limit=False):
        deadline = time.monotonic() + 15
        try:
            self._check_request()
            headers = {'Accept-Encoding': 'identity'} if identity_encoding else None
            options = {} if self.deadline is None else dict(timeout=max(.001, self.deadline-time.monotonic()))
            with self.http.stream('POST', path, json=body, follow_redirects=False, headers=headers, **options) as response:
                self._check_request()
                if response.status_code == 429 and rate_limit:
                    raise FriendsError('rate_limited')
                if response.status_code == 409 and notice_conflict:
                    raise FriendsError('notice_conflict')
                if response.status_code in (401, 403, 409):
                    raise FriendsError('access_rejected')
                if response.status_code != 200:
                    raise FriendsError('service_unavailable')
                if identity_encoding and response.headers.get('Content-Encoding', '').strip().lower() not in ('', 'identity'):
                    raise FriendsError('invalid_response')
                raw = bytearray()
                for chunk in response.iter_bytes():
                    self._check_request()
                    if time.monotonic() > deadline:
                        raise FriendsError('service_unavailable')
                    if len(raw) + len(chunk) > (self.LIMIT if limit is None else limit):
                        raise FriendsError('invalid_response')
                    raw.extend(chunk)
            return json.loads(raw, object_pairs_hook=self._object,
                              parse_constant=self._constant)
        except FriendsError:
            raise
        except (ValueError, UnicodeError, RecursionError):
            raise FriendsError('invalid_response') from None
        except Exception as failure:
            self._check_request()
            if self.deadline is not None:
                from httpx import TimeoutException
                if isinstance(failure, TimeoutException):
                    raise FriendsError('timeout') from None
            raise FriendsError('service_unavailable') from None

    def _challenge(self, path, body, *, chat_public=None):
        response = self._post(path, body)
        fields = 'challenge expires_at audience'
        if chat_public is not None:
            fields += ' device chat_public'
        self._fields(response, fields)
        now = int(self.clock())
        expiry = self._integer(response['expires_at'], 1)
        if not now < expiry <= now + 120 or response['audience'] != self.AUDIENCE:
            raise FriendsError('invalid_response')
        if chat_public is not None and (response['device'] != self.device.reference
                                       or response['chat_public'] != chat_public):
            raise FriendsError('invalid_response')
        try:
            # The existing identity validates the nonce and signs the same binding as Android.
            proof = self.device.prove_transport_key(response['challenge'])
        except Exception:
            raise FriendsError('invalid_response') from None
        return response['challenge'], proof

    def _proof(self, purpose, invitation=''):
        _, proof = self._challenge('/friends/challenge', dict(
            public_identity=self.device.public_identity,
            wireguard_public_key=self.device.wireguard_public_key,
            purpose=purpose, invitation=invitation))
        return proof

    def activate(self, invitation):
        if type(invitation) is not str or len(invitation) > 128:
            raise FriendsError('invalid_invitation')
        normalized = invitation.strip().upper().replace('-', '')
        if normalized.startswith('FC'):
            normalized = normalized[2:]
        if not re.fullmatch('[0-9A-F]{32}', normalized):
            raise FriendsError('invalid_invitation')
        response = self._post('/friends/activate', self._proof('activate', invitation))
        self._fields(response, 'device status')
        if response['device'] != self.device.reference or response['status'] != 'active':
            raise FriendsError('invalid_response')
        return response

    def register(self, invitation_token=''):
        invitation = ''
        if invitation_token:
            if not re.fullmatch('[0-9a-f]{64}', invitation_token):
                raise FriendsError('access_rejected')
            claim = self._post('/friends/referral/claim', dict(token=invitation_token, request_id=self.device.reference))
            self._fields(claim, 'invitation status')
            if claim['status'] not in ('issued','activated') or not isinstance(claim['invitation'],str) or not re.fullmatch(r'FC-(?:[A-F0-9]{4}-){7}[A-F0-9]{4}',claim['invitation']):
                raise FriendsError('invalid_response')
            invitation = claim['invitation']
        response = self._post('/friends/activate', self._proof('activate', invitation))
        self._fields(response, 'device status')
        if response['device'] != self.device.reference or response['status'] != 'active':
            raise FriendsError('invalid_response')
        return response

    def referral(self):
        response = self._post('/friends/referral/issue', self._proof('refer'))
        self._fields(response, 'url pool_limit remaining')
        if (type(response['url']) is not str or not re.fullmatch(
                r'https://185\.251\.89\.19:8443/(?:invite|i)/#[0-9a-f]{64}', response['url'])
                or self._integer(response['pool_limit'], 1) != 500
                or self._integer(response['remaining']) > 500):
            raise FriendsError('invalid_response')
        return response

    def device_status(self):
        """Authenticated read-only recovery query. Never consumes an invitation."""
        proof = self._proof('status')
        response = self._post('/friends/device/status', proof)
        self._fields(response, 'device registered revoked active')
        if response['device'] != self.device.reference:
            raise FriendsError('invalid_response')
        for key in ('registered', 'revoked', 'active'):
            if type(response[key]) is not bool:
                raise FriendsError('invalid_response')
        return response

    def support_diagnostics(self, report):
        from .support import SupportSnapshot
        raw = SupportSnapshot.encode(report)
        response = self._post('/friends/device/diagnostics', dict(
            proof=self._proof('diagnostics:' + hashlib.sha256(raw.encode()).hexdigest()), report=raw),
            limit=1024, identity_encoding=True, rate_limit=True)
        self._fields(response, 'schema report_id stored_at')
        if type(response['schema']) is not int or response['schema'] != 1 or response['report_id'] != report['report_id']:
            raise FriendsError('invalid_response')
        self._integer(response['stored_at'], 1)
        if response['stored_at'] > SupportSnapshot.MAX_NUMBER:
            raise FriendsError('invalid_response')
        return response

    def support_id(self, platform, version, version_code):
        if (platform not in ('linux', 'windows') or type(version) is not str or
                not re.fullmatch(r'[0-9A-Za-z][0-9A-Za-z.+_-]{0,63}', version) or
                type(version_code) is not int or not 1 <= version_code <= 2147483647):
            raise FriendsError('invalid_input')
        response = self._post('/friends/device/support', dict(proof=self._proof('support'),
            platform=platform, app_version=version, version_code=version_code))
        self._fields(response, 'schema device_support_id')
        if (type(response['schema']) is not int or response['schema'] != 1 or
                not isinstance(response['device_support_id'], str) or not re.fullmatch(
                    r'FC-[23456789ABCDEFGHJKMNPQRSTVWXYZ]{4}-[23456789ABCDEFGHJKMNPQRSTVWXYZ]{4}', response['device_support_id'])):
            raise FriendsError('invalid_response')
        return response['device_support_id']

    def configuration(self, country, anchor, *, floor=0, previous_hash=None):
        """Fetch and verify; the owner must persist the response before VPN apply.

        Returns (response, verified profile). Both contain device credentials and
        belong in protected storage, never in a UI result or diagnostic log.
        """
        if type(country) is not str or country not in ('ru', 'nl'):
            raise FriendsError('invalid_input')
        from .friends_catalog import verify
        from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption
        response = self._post('/friends/configuration/' + country, self._proof(country))
        try:
            private = self.device._wireguard_key.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())
            verified = verify(response, anchor, self.device.reference, country, private,
                              floor=floor, previous_hash=previous_hash)
            return response, verified
        except Exception:
            raise FriendsError('invalid_response') from None

    def register_chat(self, chat):
        public = chat.profile()['public']
        if type(public) is not str or not re.fullmatch('[0-9a-f]{128}', public):
            raise FriendsError('invalid_input')
        nonce, proof = self._challenge('/friends/chat/challenge', dict(
            public_identity=self.device.public_identity,
            wireguard_public_key=self.device.wireguard_public_key,
            chat_public=public), chat_public=public)
        body = chat.enrollment_proof(self.device.reference, nonce)
        self._fields(body, 'chat_public chat_signature')
        if body['chat_public'] != public:
            raise FriendsError('invalid_input')
        response = self._post('/friends/chat/register', {**body, 'proof': proof})
        if type(response) is not dict:
            raise FriendsError('invalid_response')
        active = response.get('status') == 'active'
        self._fields(response, 'device chat_public status' + (' node' if active else ''))
        if (response['device'] != self.device.reference or response['chat_public'] != public
                or response['status'] not in ('active', 'pending-node')):
            raise FriendsError('invalid_response')
        if active:
            node = response['node']
            self._fields(node, 'sequence expires_at host port public_key')
            self._integer(node['sequence'], 1)
            now = int(self.clock())
            if not now < self._integer(node['expires_at'], 1) <= now + 120:
                raise FriendsError('invalid_response')
            try:
                if str(ipaddress.IPv4Address(node['host'])) != node['host']:
                    raise ValueError()
            except (ValueError, TypeError):
                raise FriendsError('invalid_response') from None
            if (self._integer(node['port'], 1) > 65535 or type(node['public_key']) is not str
                    or not re.fullmatch('[0-9a-f]{128}', node['public_key'])):
                raise FriendsError('invalid_response')
        return response
