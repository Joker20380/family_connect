"""Carrier-independent control configuration using the existing offline anchor.

Encrypted to the existing device identity. A distinct signature domain separates
configuration authority from the app-update catalog; no new signing root or TOFU.
"""
import base64
import hashlib
import json
import re
from dataclasses import dataclass
from typing import Annotated, Literal

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from pydantic import Field, field_validator, model_validator

from clients.desktop.profile_config import parse, parse_tcp, AWG_FIELDS
from clients.desktop.updates import version
from .envelope import MAX_ENVELOPE_BYTES, ProvisioningRejected, _unique_fields, public_identity
from .models import FrozenModel, GatewayCandidate, Identifier, Positive

DOMAIN = b'family-connect/control-config/v1\x00'
AUDIENCE = 'family-connect/control-config/v1'
LOCAL_KEY = 'LOCAL_DEVICE_KEY'
Digest = Annotated[str, Field(pattern=r'^[0-9a-f]{64}$')]


class ConfigError(ProvisioningRejected):
    def __init__(self, category):
        self.category = category
        super().__init__(category)


class ControlGateway(FrozenModel):
    gateway_id: Identifier
    endpoint: str
    port: Annotated[int, Field(strict=True, ge=1, le=65535)]

    @field_validator('endpoint')
    @classmethod
    def valid_endpoint(cls, value):
        import ipaddress
        address = ipaddress.ip_address(value)
        GatewayCandidate.routable_endpoint(address)
        if str(address) != value:
            raise ValueError('noncanonical endpoint')
        return value


class TransportProfile(FrozenModel):
    profile_id: Identifier
    gateway_id: Identifier
    transport: Literal['wireguard', 'amneziawg', 'vless-reality']
    transport_version: Literal['1', '2.0', '3.1']
    config: Annotated[str, Field(min_length=1, max_length=16384, repr=False)]

    def parsed(self):
        if self.transport == 'vless-reality':
            value = parse_tcp(self.config)
            if value['id'] == '00000000-0000-0000-0000-000000000000' or not any(base64.urlsafe_b64decode(value['public_key']+'=')):
                raise ValueError('invalid TCP credential')
            return value
        # Only the local device can supply a WG private key, never the issuer.
        sentinel = base64.b64encode(bytes(32)).decode()
        fields = parse(self.config.replace(LOCAL_KEY, sentinel), allow_awg=self.transport == 'amneziawg')
        if (fields['Interface']['PrivateKey'] != sentinel or self.config.count(LOCAL_KEY) != 1 or
                not re.search(r'^\s*PrivateKey\s*=\s*LOCAL_DEVICE_KEY\s*(?:#.*)?$', self.config, re.MULTILINE)):
            raise ValueError('local device key binding required')
        return fields

    @model_validator(mode='after')
    def valid_profile(self):
        expected = {'wireguard': {'1'}, 'amneziawg': {'2.0', '3.1'}, 'vless-reality': {'1'}}
        if self.transport_version not in expected[self.transport]:
            raise ValueError('transport version mismatch')
        if self.transport_version == '3.1':
            # A future runtime/parser must explicitly add support. Never interpret
            # AWG 3.1 as 2.0 or silently drop its header/timing protection settings.
            raise ConfigError('UNSUPPORTED_TRANSPORT_VERSION')
        fields = self.parsed()
        if self.transport == 'amneziawg' and not AWG_FIELDS.intersection(fields['Interface']):
            raise ValueError('AWG parameters required')
        return self


class ControlConfiguration(FrozenModel):
    schema_version: Literal[2]
    config_id: Identifier
    revision: Positive
    issued_at: Positive
    expires_at: Positive
    recipient: Annotated[str, Field(pattern=r'^[0-9a-f]{32}$')]
    audience: Literal['family-connect/control-config/v1']
    wireguard_public_key: str
    min_client_version: str
    previous_config_hash: Digest | None
    signer_key_id: Digest
    gateways: Annotated[tuple[ControlGateway, ...], Field(min_length=1, max_length=8)]
    transport_profiles: Annotated[tuple[TransportProfile, ...], Field(min_length=1, max_length=8, repr=False)]

    @field_validator('schema_version', mode='before')
    @classmethod
    def integer_schema(cls, value):
        if type(value) is not int:
            raise ValueError('invalid schema')
        return value

    @field_validator('wireguard_public_key')
    @classmethod
    def valid_key(cls, value):
        return GatewayCandidate.valid_key(value)

    @field_validator('min_client_version')
    @classmethod
    def valid_version(cls, value):
        version(value)
        return value

    @model_validator(mode='after')
    def valid_configuration(self):
        if not 0 < self.expires_at - self.issued_at <= 86400:
            raise ValueError('invalid lease')
        gateways = {g.gateway_id: g for g in self.gateways}
        if len(gateways) != len(self.gateways):
            raise ValueError('duplicate gateway')
        if len({p.profile_id for p in self.transport_profiles}) != len(self.transport_profiles):
            raise ValueError('duplicate profile')
        for profile in self.transport_profiles:
            gateway = gateways.get(profile.gateway_id)
            if gateway is None:
                raise ValueError('unknown gateway')
            parsed = profile.parsed()
            if profile.transport == 'vless-reality':
                host, port = parsed['server'], parsed['port']
            else:
                host, port = parsed['Peer']['Endpoint'].rsplit(':', 1)
                host, port = host.strip('[]'), int(port)
            if host != gateway.endpoint or port != gateway.port:
                raise ValueError('gateway/profile mismatch')
        return self


@dataclass(frozen=True, repr=False)
class VerifiedConfiguration:
    state: ControlConfiguration
    envelope: bytes
    digest: str


def issue_config(state, *, recipient_public, signing_key):
    """Offline only. Runtime providers do not import or call this function."""
    recipient = public_identity(recipient_public)
    if (state.recipient != recipient.hash.hex() or state.signer_key_id !=
            hashlib.sha256(signing_key.public_key().public_bytes_raw()).hexdigest()):
        raise ValueError('signer or recipient mismatch')
    ciphertext = recipient.encrypt(state.model_dump_json().encode())
    raw = json.dumps(dict(ciphertext=base64.b64encode(ciphertext).decode(),
        signature=base64.b64encode(signing_key.sign(DOMAIN + ciphertext)).decode()),
        separators=(',', ':')).encode()
    if len(raw) > MAX_ENVELOPE_BYTES:
        raise ValueError('oversized configuration')
    return raw


class ConfigVerifier:
    def __init__(self, *, anchor, device, client_version):
        self.signer = Ed25519PublicKey.from_public_bytes(anchor)
        self.key_id = hashlib.sha256(anchor).hexdigest()
        self.device = device
        self.client_version = version(client_version)

    def verify(self, raw, *, now):
        if type(now) is not int or now < 0:
            raise ConfigError('CLOCK')
        if type(raw) is not bytes or len(raw) > MAX_ENVELOPE_BYTES:
            raise ConfigError('SIZE')
        try:
            outer = json.loads(raw, object_pairs_hook=_unique_fields)
            if type(outer) is not dict or set(outer) != {'ciphertext', 'signature'}:
                raise ValueError()
            ciphertext = base64.b64decode(outer['ciphertext'], validate=True)
            self.signer.verify(base64.b64decode(outer['signature'], validate=True), DOMAIN + ciphertext)
        except InvalidSignature:
            raise ConfigError('SIGNATURE') from None
        except (ValueError, TypeError, KeyError, UnicodeError, RecursionError):
            raise ConfigError('MALFORMED') from None
        try:
            plain = self.device._identity.decrypt(ciphertext)
            value = json.loads(plain, object_pairs_hook=_unique_fields)
            if type(value) is not dict:
                raise ValueError()
            if type(value.get('schema_version')) is not int or value['schema_version'] != 2:
                raise ConfigError('SCHEMA')
            if value.get('audience') != AUDIENCE or value.get('recipient') != self.device.reference:
                raise ConfigError('TARGET')
            if value.get('signer_key_id') != self.key_id:
                raise ConfigError('SIGNER')
            profiles = value.get('transport_profiles')
            if type(profiles) is list and any(type(p) is dict and p.get('transport') == 'amneziawg'
                    and p.get('transport_version') == '3.1' for p in profiles):
                raise ConfigError('UNSUPPORTED_TRANSPORT_VERSION')
            state = ControlConfiguration.model_validate_json(plain)
        except ConfigError:
            raise
        except (ValueError, TypeError, KeyError, UnicodeError, RecursionError):
            raise ConfigError('STRUCTURE') from None
        if state.wireguard_public_key != self.device.wireguard_public_key:
            raise ConfigError('TARGET')
        if not state.issued_at <= now < state.expires_at:
            raise ConfigError('LEASE')
        if version(state.min_client_version) > self.client_version:
            raise ConfigError('CLIENT_VERSION')
        return VerifiedConfiguration(state, raw, hashlib.sha256(raw).hexdigest())
