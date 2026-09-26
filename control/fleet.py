"""Operator-owned fleet inventory and pure admission planning.

No SSH, IP allocation, signing or VPN mutations happen here. Telemetry must come
from authenticated collectors, never the public dashboard. A plan is not a lease:
the issuer must reserve capacity and provision a peer before signing a config.
"""
import hashlib
import ipaddress
import json
import math
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator

from provisioning.models import FrozenModel, Identifier, Positive

MAX_REGISTRY_BYTES = 262144
Transport = Literal['wireguard', 'amneziawg', 'vless-reality']
Port = Annotated[int, Field(strict=True, ge=1, le=65535)]
Percent = Annotated[float, Field(ge=0, le=100, allow_inf_nan=False)]
Rate = Annotated[float, Field(ge=0, le=1e9, allow_inf_nan=False)]


def public_address(value):
    address = ipaddress.ip_address(value)
    if (str(address) != value or not address.is_global or address.is_multicast
            or getattr(address, 'scope_id', None) is not None
            or getattr(address, 'ipv4_mapped', None) is not None):
        raise ValueError('canonical public IP required')
    return value


class Endpoint(FrozenModel):
    transport: Transport
    version: Literal['1', '2.0', '3.1']
    address: str
    port: Port

    _address = field_validator('address')(public_address)

    @model_validator(mode='after')
    def version_matches(self):
        if self.version not in ({'2.0', '3.1'} if self.transport == 'amneziawg' else {'1'}):
            raise ValueError('transport version mismatch')
        return self

    @property
    def socket(self):
        return ('tcp' if self.transport == 'vless-reality' else 'udp', self.address, self.port)


class Gateway(FrozenModel):
    gateway_id: Identifier
    failure_domain: Identifier
    country: Annotated[str, Field(pattern=r'^[a-z]{2}$')]
    state: Literal['provisioning', 'active', 'draining', 'disabled']
    endpoints: Annotated[tuple[Endpoint, ...], Field(min_length=1, max_length=8)]
    tunnel_pool: str
    max_devices: Annotated[int, Field(strict=True, ge=1, le=1000000)]
    weight: Annotated[float, Field(gt=0, le=1000, allow_inf_nan=False)] = 1.0
    # This is an operator-approved admission budget, not a guessed NIC speed.
    egress_budget_mbps: Annotated[float, Field(gt=0, le=1e9, allow_inf_nan=False)]

    @field_validator('tunnel_pool')
    @classmethod
    def valid_pool(cls, value):
        network = ipaddress.ip_network(value, strict=True)
        allowed = [ipaddress.ip_network(x) for x in ('10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16')]
        if (network.version != 4 or not 16 <= network.prefixlen <= 29
                or str(network) != value or not any(network.subnet_of(x) for x in allowed)):
            raise ValueError('canonical private IPv4 pool /16 through /29 required')
        return value

    @model_validator(mode='after')
    def capacity_matches_pool(self):
        # Network, gateway and broadcast addresses are reserved.
        if self.max_devices > ipaddress.ip_network(self.tunnel_pool).num_addresses - 3:
            raise ValueError('device capacity exceeds address pool')
        return self


class Ingress(FrozenModel):
    ingress_id: Identifier
    failure_domain: Identifier
    address: str
    port: Port
    provider_public: str

    _address = field_validator('address')(public_address)

    @field_validator('provider_public')
    @classmethod
    def valid_provider(cls, value):
        import base64
        raw = base64.b64decode(value, validate=True)
        if len(raw) != 64 or raw == bytes(64) or base64.b64encode(raw).decode() != value:
            raise ValueError('canonical public Reticulum identity required')
        return value


class Registry(FrozenModel):
    schema_version: Literal[1]
    revision: Positive
    gateways: Annotated[tuple[Gateway, ...], Field(min_length=1, max_length=256)]
    control_ingresses: Annotated[tuple[Ingress, ...], Field(min_length=1, max_length=16)]

    @field_validator('schema_version', mode='before')
    @classmethod
    def exact_schema(cls, value):
        if type(value) is not int:
            raise ValueError('integer schema required')
        return value

    @model_validator(mode='after')
    def unique_inventory(self):
        for entries, attr in ((self.gateways, 'gateway_id'), (self.control_ingresses, 'ingress_id')):
            if len({getattr(x, attr) for x in entries}) != len(entries):
                raise ValueError('duplicate node ID')
        sockets = set()
        pools = []
        for gateway in self.gateways:
            network = ipaddress.ip_network(gateway.tunnel_pool)
            if any(network.overlaps(other) for other in pools):
                raise ValueError('overlapping tunnel pools')
            pools.append(network)
            for endpoint in gateway.endpoints:
                if endpoint.socket in sockets:
                    raise ValueError('duplicate listening socket')
                sockets.add(endpoint.socket)
        for ingress in self.control_ingresses:
            socket = ('tcp', ingress.address, ingress.port)
            if socket in sockets:
                raise ValueError('duplicate listening socket')
            sockets.add(socket)
        return self


def load_registry(raw):
    """Parse trusted operator input. This is deliberately not a client trust API."""
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_REGISTRY_BYTES:
        raise ValueError('invalid registry size')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate JSON field')
            result[key] = value
        return result
    def invalid_constant(_):
        raise ValueError('nonfinite JSON number')
    parsed = json.loads(raw, object_pairs_hook=unique, parse_constant=invalid_constant)
    return Registry.model_validate_json(json.dumps(parsed))


def validate_update(previous, candidate):
    """Keep durable node identities/pools; disabled records are tombstones.

    Moving a tunnel pool requires an explicit lease migration, not an inventory
    edit. Ingress rotation must retain an old address+pin during the overlap.
    """
    if candidate.revision <= previous.revision:
        raise ValueError('registry revision must increase')
    nodes = {node.gateway_id: node for node in candidate.gateways}
    for old in previous.gateways:
        new = nodes.get(old.gateway_id)
        if new is None or new.tunnel_pool != old.tunnel_pool or new.failure_domain != old.failure_domain:
            raise ValueError('node removal, relocation or pool change requires lease migration')
    def binding(ingress):
        return ingress.address, ingress.port, ingress.provider_public
    if not ({binding(x) for x in previous.control_ingresses}
            & {binding(x) for x in candidate.control_ingresses}):
        raise ValueError('control ingress rotation requires bootstrap overlap')
    return candidate


class Observation(FrozenModel):
    gateway_id: Identifier
    registry_revision: Positive
    observed_at: Annotated[int, Field(strict=True, ge=0)]
    # Ready only after peer API and data-plane probes, not merely ping/process up.
    ready_transports: tuple[Transport, ...]
    allocated_devices: Annotated[int, Field(strict=True, ge=0)]
    cpu_percent: Percent
    memory_percent: Percent
    tx_mbps: Rate


def rank_gateways(registry, observations, *, device, country, transport, version, now,
                  current=None, max_age=45, address_families=(4,)):
    """IDs for a new assignment; keep a healthy existing assignment, even draining.

    Missing/stale/wrong-revision observations never authorize new admissions.
    Empty output means no safe proposal; it is not a command to stop a live VPN.
    Capacity thresholds reserve 15% headroom. Weighted rendezvous spreads devices
    deterministically; adding a node does not reshuffle existing assignments.
    """
    if (type(now) is not int or now < 0 or type(max_age) is not int or not 1 <= max_age <= 300
            or type(device) is not str or not 1 <= len(device) <= 128
            or type(address_families) is not tuple or not address_families
            or any(type(v) is not int or v not in (4, 6) for v in address_families)
            or transport not in ('wireguard', 'amneziawg', 'vless-reality')
            or version not in ({'2.0', '3.1'} if transport == 'amneziawg' else {'1'})):
        raise ValueError('invalid admission request')
    samples = {}
    for sample in observations:
        if sample.gateway_id in samples:
            raise ValueError('ambiguous telemetry')
        samples[sample.gateway_id] = sample
    ranked = []
    retained = None
    for gateway in registry.gateways:
        if country is not None and gateway.country != country:
            continue
        if not any(e.transport == transport and e.version == version
                   and ipaddress.ip_address(e.address).version in address_families for e in gateway.endpoints):
            continue
        sample = samples.get(gateway.gateway_id)
        if (sample is None or sample.registry_revision != registry.revision
                or not 0 <= now - sample.observed_at <= max_age
                or transport not in sample.ready_transports
                or gateway.state not in ('active', 'draining')):
            continue
        if gateway.gateway_id == current:
            retained = gateway.gateway_id
            continue
        pressure = max(sample.cpu_percent / 100, sample.memory_percent / 100,
                       sample.tx_mbps / gateway.egress_budget_mbps)
        if (gateway.state != 'active' or sample.allocated_devices >= gateway.max_devices
                or pressure >= .85):
            continue
        headroom = min(1 - pressure, 1 - sample.allocated_devices / gateway.max_devices)
        digest = hashlib.sha256(json.dumps([device, gateway.gateway_id], separators=(',', ':')).encode()).digest()
        # Bounded integer fraction excludes both zero and one in binary64.
        unit = (int.from_bytes(digest[:6], 'big') + 1) / (2**48 + 1)
        score = -math.log(unit) / (gateway.weight * headroom)
        ranked.append((score, gateway.gateway_id))
    return ([retained] if retained else []) + [node for _, node in sorted(ranked)]
