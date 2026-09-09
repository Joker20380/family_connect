"""First telemetry contract: stable failure codes, never exception text.

This is deliberately not an event collector. Gateways, network dimensions and
identity references require separately validated registries before inclusion.
"""
from dataclasses import dataclass
from enum import StrEnum
import re


class FailureCode(StrEnum):
    CONTROL_UNREACHABLE = 'CONTROL_UNREACHABLE'
    CONTROL_AUTH_FAILED = 'CONTROL_AUTH_FAILED'
    PROVISIONING_UNAVAILABLE = 'PROVISIONING_UNAVAILABLE'
    PROVISIONING_SIGNATURE_INVALID = 'PROVISIONING_SIGNATURE_INVALID'
    PROVISIONING_EXPIRED = 'PROVISIONING_EXPIRED'
    PROVISIONING_DECRYPT_FAILED = 'PROVISIONING_DECRYPT_FAILED'
    PROVISIONING_SCHEMA_UNSUPPORTED = 'PROVISIONING_SCHEMA_UNSUPPORTED'
    DNS_FAILURE = 'DNS_FAILURE'
    ENDPOINT_UNREACHABLE = 'ENDPOINT_UNREACHABLE'
    HANDSHAKE_TIMEOUT = 'HANDSHAKE_TIMEOUT'
    HANDSHAKE_REJECTED = 'HANDSHAKE_REJECTED'
    TUNNEL_SETUP_FAILED = 'TUNNEL_SETUP_FAILED'
    ROUTE_APPLY_FAILED = 'ROUTE_APPLY_FAILED'
    CONNECTION_TIMEOUT = 'CONNECTION_TIMEOUT'
    CONNECTION_DROPPED = 'CONNECTION_DROPPED'
    TRANSPORT_UNAVAILABLE = 'TRANSPORT_UNAVAILABLE'
    UNKNOWN_NETWORK_FAILURE = 'UNKNOWN_NETWORK_FAILURE'


class Platform(StrEnum):
    LINUX = 'linux'
    ANDROID = 'android'
    WINDOWS = 'windows'


@dataclass(frozen=True, slots=True)
class FailureReport:
    code: FailureCode
    platform: Platform
    app_version: str

    def __post_init__(self):
        # Reject invalid direct construction too; annotations alone do not validate.
        if not isinstance(self.code, FailureCode) or not isinstance(self.platform, Platform):
            raise ValueError('invalid failure report classification')
        if type(self.app_version) is not str or not re.fullmatch(
            r'[0-9]{1,4}\.[0-9]{1,4}\.[0-9]{1,4}', self.app_version
        ):
            raise ValueError('invalid application version')

    @classmethod
    def from_dict(cls, value):
        # Never echo rejected values or underlying enum exceptions: they may
        # contain configuration, credentials or browsing data.
        if type(value) is not dict or set(value) != {'code', 'platform', 'app_version'}:
            raise ValueError('invalid failure report fields')
        if any(type(item) is not str for item in value.values()):
            raise ValueError('invalid failure report value type')
        try:
            code = FailureCode(value['code'])
            platform = Platform(value['platform'])
        except ValueError:
            raise ValueError('invalid failure report classification') from None
        return cls(code, platform, value['app_version'])

    def to_dict(self):
        return dict(code=self.code.value, platform=self.platform.value, app_version=self.app_version)
