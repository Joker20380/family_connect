"""Strict immutable desired state. No transport private keys are accepted."""
import base64
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, IPvAnyAddress, IPvAnyInterface, field_validator, model_validator

Positive = Annotated[int, Field(strict=True, ge=1, le=2**63 - 1)]
Identifier = Annotated[str, Field(pattern=r'^[a-zA-Z0-9_-]{1,64}$')]


class FrozenModel(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True, strict=True, hide_input_in_errors=True)


class GatewayCandidate(FrozenModel):
    gateway_id: Identifier
    provider_id: Identifier
    region: Annotated[str, Field(pattern=r'^[A-Z]{2}$')]
    asn: Annotated[int, Field(strict=True, ge=1, le=4294967295)] | None = None
    transport: Literal['wireguard']
    endpoint: IPvAnyAddress
    port: Annotated[int, Field(strict=True, ge=1, le=65535)]
    public_key: str

    @field_validator('public_key')
    @classmethod
    def valid_key(cls, value):
        try:
            raw = base64.b64decode(value, validate=True)
        except ValueError:
            raise ValueError('invalid public key') from None
        if len(raw) != 32 or raw == bytes(32) or base64.b64encode(raw).decode() != value:
            raise ValueError('invalid public key')
        return value

    @field_validator('endpoint')
    @classmethod
    def routable_endpoint(cls, value):
        if value.is_unspecified or value.is_multicast or value.is_loopback:
            raise ValueError('invalid gateway endpoint')
        return value


class NetworkProvisioningState(FrozenModel):
    schema_version: Literal[1]
    revision: Positive
    recipient: Annotated[str, Field(pattern=r'^[0-9a-f]{32}$')]
    issued_at: Positive
    expires_at: Positive
    entitlement_id: Identifier
    entitlement_revision: Positive
    wireguard_public_key: str
    addresses: Annotated[tuple[IPvAnyInterface, ...], Field(min_length=1, max_length=2)]
    dns: Annotated[tuple[IPvAnyAddress, ...], Field(min_length=1, max_length=3)]
    gateways: Annotated[tuple[GatewayCandidate, ...], Field(min_length=1, max_length=8)]

    @field_validator('schema_version', mode='before')
    @classmethod
    def integer_schema(cls, value):
        if type(value) is not int:
            raise ValueError('invalid schema version')
        return value

    @field_validator('wireguard_public_key')
    @classmethod
    def valid_key(cls, value):
        return GatewayCandidate.valid_key(value)

    @model_validator(mode='after')
    def valid_state(self):
        if not 0 < self.expires_at - self.issued_at <= 86400:
            raise ValueError('invalid authorization lease')
        if len({g.gateway_id for g in self.gateways}) != len(self.gateways):
            raise ValueError('duplicate gateway')
        if len({a.version for a in self.addresses}) != len(self.addresses):
            raise ValueError('duplicate address family')
        for address in [*(a.ip for a in self.addresses), *self.dns]:
            if address.is_unspecified or address.is_multicast or address.is_loopback:
                raise ValueError('invalid tunnel address')
        return self
