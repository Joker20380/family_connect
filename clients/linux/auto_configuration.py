"""Fresh authenticated normal configuration; only signed floors are persisted."""
import base64
from dataclasses import asdict, dataclass
import hashlib
import json
import re
import time

from auto_policy import Failure, require, number
import mesh_ipc as ipc
from mesh_materials import NativeMaterials, MaterialsError, _bytes
from provisioning.friends_catalog import _verified_profile


@dataclass(frozen=True)
class Target:
    provider: str
    reference: str
    country: str
    load: int | None = None

    def __post_init__(self):
        for value in (self.provider, self.reference):
            require(isinstance(value, str) and re.fullmatch('[a-z0-9][a-z0-9_.:-]{0,63}', value))
        require(isinstance(self.country, str) and re.fullmatch('[a-z]{2}', self.country))
        require(self.load is None or number(self.load, 0, 100))


@dataclass(frozen=True)
class Preference:
    provider: str
    target_reference: str
    transport: str
    requested_profile: str

    def __post_init__(self):
        for value in (self.provider, self.target_reference):
            require(isinstance(value, str) and re.fullmatch('[a-z0-9][a-z0-9_.:-]{0,63}', value))
        require(self.transport in ('', 'awg', 'tcp') and self.requested_profile in ('P0', 'P1'))


class TargetChoices:
    def __init__(self, targets, preference):
        self.selected_next = preference
        self.refresh(targets)
        self.select(preference)

    def refresh(self, targets):
        values = tuple(targets)
        require(0 < len(values) <= 256 and all(isinstance(target, Target) for target in values))
        require(len({(target.provider, target.reference) for target in values}) == len(values))
        self.targets = values

    def select(self, preference):
        require(isinstance(preference, Preference))
        require(any((target.provider, target.reference) == (preference.provider, preference.target_reference)
                    for target in self.targets))
        self.selected_next = preference

    def snapshot(self):
        return dict(targets=[asdict(target) for target in self.targets], selected_next=asdict(self.selected_next),
                    available=any((target.provider, target.reference) ==
                                  (self.selected_next.provider, self.selected_next.target_reference) for target in self.targets))


LEGACY_TARGETS = (Target('friends-legacy-v1', 'legacy-ru', 'ru'), Target('friends-legacy-v1', 'legacy-nl', 'nl'))


def legacy_target(country):
    require(country in ('ru', 'nl'))
    return next(target for target in LEGACY_TARGETS if target.country == country)


@dataclass(frozen=True)
class Assignment:
    target: Target
    owner_generation: str
    requested_profile: str
    sequence: int
    catalog_hash: str
    gateway_id: str | None = None

    def __post_init__(self):
        require(isinstance(self.target, Target))
        require(isinstance(self.owner_generation, str) and re.fullmatch('[a-f0-9]{32}', self.owner_generation))
        require(self.requested_profile in ('P0', 'P1') and number(self.sequence, 1))
        require(isinstance(self.catalog_hash, str) and re.fullmatch('[a-f0-9]{64}', self.catalog_hash))
        require(self.gateway_id is None if self.target.provider == 'friends-legacy-v1' else
                self.gateway_id is None or isinstance(self.gateway_id, str) and re.fullmatch('[a-zA-Z0-9_-]{1,64}', self.gateway_id))


@dataclass(frozen=True)
class AppliedSession:
    owner_generation: str
    transport: str
    requested_profile: str
    interface: str
    assignment: Assignment | None

    def __post_init__(self):
        require(isinstance(self.owner_generation, str) and re.fullmatch('[a-f0-9]{32}', self.owner_generation))
        require(self.transport in ('awg', 'tcp', 'restricted') and self.requested_profile in ('P0', 'P1'))
        require(isinstance(self.interface, str) and re.fullmatch('[a-zA-Z0-9_.-]{1,15}', self.interface))
        if self.transport == 'restricted':
            require(self.assignment is None)
        else:
            require(isinstance(self.assignment, Assignment) and self.assignment.owner_generation == self.owner_generation and
                    self.assignment.requested_profile == self.requested_profile)


class NativeConfiguration(NativeMaterials):
    OPTION = '--normal-stdio'
    MAX_REQUEST = 192 * 1024


def verified(reply, identifier, country, private):
    require(isinstance(reply, dict) and {'schema', 'id', 'ok', 'code'} <= set(reply))
    require(type(reply['schema']) is int and reply['schema'] == 1 and type(reply['id']) is int and reply['id'] == identifier)
    require(type(reply['ok']) is bool)
    if not reply['ok']:
        require(set(reply) == {'schema', 'id', 'ok', 'code'} and reply['code'] in ('CANCELLED', 'AUTH', 'CONFIGURATION', 'NETWORK', 'INTERNAL'))
        raise Failure(reply['code'])
    require(set(reply) == {'schema', 'id', 'ok', 'code', 'response', 'catalog', 'sequence', 'digest', 'public'})
    require(reply['code'] == 'AUTHENTICATED_RESPONSE' and number(reply['sequence'], 1))
    require(isinstance(reply['digest'], str) and re.fullmatch('[0-9a-f]{64}', reply['digest']))
    public = _bytes(reply['public'], size=64)
    require(isinstance(reply['response'], dict) and reply['response'].get('catalog') == reply['catalog'])
    catalog = reply['catalog']
    require(isinstance(catalog, dict) and set(catalog) == {'payload', 'signature'})
    payload = _bytes(catalog['payload'], maximum=8192)
    _bytes(catalog['signature'], size=64)
    require(hashlib.sha256(payload).hexdigest() == reply['digest'])
    profile = _verified_profile(reply['response'], payload, hashlib.sha256(public).hexdigest()[:32], country, private,
                                floor=reply['sequence'], previous_hash=reply['digest'])
    return profile


class NormalOwner:
    def __init__(self, storage, native=None):
        self.storage, self.native = storage, native or NativeConfiguration()
        self.summary = dict(stage='IDLE', code='NONE', durable=False)
        self._resolved, self._assignment = None, None

    def assignment(self, profile, generation, requested_profile):
        require(profile is not None and profile is self._resolved)
        require(isinstance(generation, str) and re.fullmatch('[a-f0-9]{32}', generation))
        require(requested_profile in ('P0', 'P1'))
        if self._assignment is None:
            self._assignment = Assignment(legacy_target(profile.country), generation, requested_profile, profile.sequence, profile.catalog_hash)
        require(self._assignment.owner_generation == generation and self._assignment.requested_profile == requested_profile)
        return self._assignment

    def validate(self, material, context):
        self._resolved, self._assignment = None, None
        request, reply = {}, {}
        try:
            context.check()
            floors = list(material['normal_floors'])
            require(len(floors) <= 2)
            raw = self.storage.read()
            if raw is not None:
                floors.append(ipc.decode(raw, 16384))
            request = dict(schema=1, id=1, action='validate', country=material['country'], floors=floors,
                **{key: material[key] for key in ('identity', 'wireguard_public', 'wireguard_private', 'anchor')})
            reply = self.native(request, context.cancel, context.deadline)
            context.check()
            require(isinstance(reply, dict) and type(reply.get('schema')) is int and reply['schema'] == 1 and
                    type(reply.get('id')) is int and reply['id'] == 1 and type(reply.get('ok')) is bool)
            if not reply['ok']:
                require(set(reply) == {'schema', 'id', 'ok', 'code'} and reply['code'] in ('CONFIGURATION', 'CANCELLED', 'INTERNAL'))
                raise Failure(reply['code'])
            require(set(reply) == {'schema', 'id', 'ok', 'code', 'public'} and reply['code'] == 'VALIDATED_MATERIAL')
            _bytes(reply['public'], size=64)
        except MaterialsError as error:
            raise Failure('CANCELLED' if error.code == 'CANCELLED' else 'INTERNAL') from None
        finally:
            request.clear()
            reply.clear()

    def resolve(self, material, country, private, seeds, underlying, context):
        self._resolved, self._assignment = None, None
        request, reply, inspected = {}, {}, {}
        try:
            context.check()
            require(country in ('ru', 'nl') and type(private) is bytes and len(private) == 32)
            require(isinstance(seeds, list) and len(seeds) <= 2 and all(isinstance(seed, dict) for seed in seeds))
            require(number(underlying, 1, 2**31-1))
            raw = self.storage.read()
            floors = list(seeds)
            if raw is not None:
                floors.append(ipc.decode(raw, 16384))
            self.summary = dict(stage='FETCHING', code='NONE', durable=False)
            request = dict(schema=1, id=1, action='fetch', identity=material['identity'],
                wireguard_public=material['wireguard_public'], wireguard_private=base64.b64encode(private).decode(),
                anchor=material['anchor'], country=country, floors=floors, underlying_index=underlying,
                budget_ms=min(30000, max(1, int((context.deadline-time.monotonic())*1000))))
            reply = self.native(request, context.cancel, context.deadline)
            request.clear()
            context.check()
            profile = verified(reply, 1, country, private)
            self.summary = dict(stage='PERSISTING_FLOOR', code='NONE', durable=False)
            raw = json.dumps(reply['catalog'], separators=(',', ':'), allow_nan=False).encode()
            require(len(raw) <= 16384)
            self.storage.write(raw)
            require(self.storage.read() == raw)
            context.check()
            request = dict(schema=1, id=2, action='inspect', public=reply['public'], anchor=material['anchor'], country=country,
                           floors=[ipc.decode(raw, 16384)], response=reply['response'])
            inspected = self.native(request, context.cancel, context.deadline)
            request.clear()
            context.check()
            checked = verified(inspected, 2, country, private)
            require(checked == profile and inspected['public'] == reply['public'] and inspected['catalog'] == reply['catalog'])
            self.summary = dict(stage='VERIFIED_READBACK', code='READY_FOR_PLATFORM', durable=True,
                                sequence=profile.sequence, country=country)
            self._resolved = profile
            return profile
        except MaterialsError as error:
            category = 'CANCELLED' if error.code == 'CANCELLED' else 'NETWORK' if error.code == 'DEADLINE' else 'INTERNAL'
            self.summary = dict(stage='FAILED', code=category, durable=False)
            raise Failure(category) from None
        except Failure as failure:
            self.summary = dict(stage='FAILED', code=failure.category, durable=False)
            raise
        except Exception:
            self.summary = dict(stage='FAILED', code='CONFIGURATION', durable=False)
            raise Failure('CONFIGURATION') from None
        finally:
            request.clear()
            reply.clear()
            inspected.clear()
