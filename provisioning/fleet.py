"""Operator-supplied profile pins for the existing control configuration issuer."""
import ipaddress
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator
from clients.desktop.profile_config import AWG_FIELDS, AWG31_FIELDS, validate_awg
from provisioning.models import FrozenModel, GatewayCandidate


class ProfileBinding(FrozenModel):
    transport: Literal['wireguard', 'amneziawg']
    version: Literal['1', '2.0', '3.1']
    server_public: str
    dns: Annotated[tuple[str, ...], Field(min_length=1, max_length=3)]
    mtu: Annotated[int, Field(strict=True, ge=1280, le=1500)] = 1280
    parameters: dict[str, str] = Field(default_factory=dict, repr=False)

    @field_validator('server_public')
    @classmethod
    def key(cls, value):
        return GatewayCandidate.valid_key(value)

    @model_validator(mode='after')
    def valid(self):
        for address in self.dns:
            ip = ipaddress.ip_address(address)
            if str(ip) != address or ip.is_unspecified or ip.is_multicast or ip.is_loopback:
                raise ValueError('invalid DNS')
        if self.transport == 'wireguard':
            if self.version != '1' or self.parameters:
                raise ValueError('invalid WG binding')
        else:
            allowed = AWG_FIELDS | (AWG31_FIELDS if self.version == '3.1' else set())
            if self.version not in ('2.0', '3.1') or set(self.parameters) - allowed:
                raise ValueError('invalid AWG binding')
            if any(len(value) > 2048 or '\n' in value or '\r' in value for value in self.parameters.values()):
                raise ValueError('invalid AWG parameter')
            if self.version == '3.1' and not AWG31_FIELDS <= set(self.parameters):
                raise ValueError('incomplete AWG 3.1 binding')
            validate_awg(self.parameters)
        return self
