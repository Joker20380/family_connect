"""Fresh authenticated normal configuration; only signed floors are persisted."""
import base64
import hashlib
import json
import re
import time

from auto_policy import Failure, require, number
import mesh_ipc as ipc
from mesh_materials import NativeMaterials, MaterialsError, _bytes
from provisioning.friends_catalog import _verified_profile


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

    def validate(self, material, context):
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
