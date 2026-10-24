import base64
import copy
import hashlib
import json
import os
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'clients/linux'))
from auto_configuration import NormalOwner, verified
from auto_policy import Context, Failure
from mesh_materials import CacheStore

FIXTURE = json.loads((ROOT / 'tests/fixtures/desktop-friends-catalog-v2.json').read_text())
PUBLIC = b'x' * 64
PRIVATE = base64.b64decode(FIXTURE['wireguard_key'])


def response(identifier=1):
    reply = copy.deepcopy(FIXTURE['vectors'][0]['reply'])
    reply['device'] = hashlib.sha256(PUBLIC).hexdigest()[:32]
    payload = base64.b64decode(reply['catalog']['payload'])
    return dict(schema=1, id=identifier, ok=True, code='AUTHENTICATED_RESPONSE', response=reply,
                catalog=reply['catalog'], sequence=2, digest=hashlib.sha256(payload).hexdigest(),
                public=base64.b64encode(PUBLIC).decode())


@pytest.fixture
def setup(tmp_path):
    tmp_path.chmod(0o700)
    storage = CacheStore(tmp_path, 1000, expected_owner=os.getuid())
    calls = []

    def native(request, cancel, deadline):
        calls.append(copy.deepcopy(request))
        return response(request['id'])

    owner = NormalOwner(storage, native)
    material = dict(identity=base64.b64encode(b'a' * 64).decode(), anchor=FIXTURE['anchor'],
                    wireguard_public=base64.b64encode(b'w' * 32).decode())
    yield owner, storage, material, calls
    storage.close()


def test_fresh_fetch_then_profile_validation_then_durable_native_readback(setup):
    owner, storage, material, calls = setup
    profile = owner.resolve(material, 'nl', PRIVATE, [], 2, Context(30000))
    assert profile.country == 'nl' and profile.sequence == 2
    assert [call['action'] for call in calls] == ['fetch', 'inspect']
    assert calls[0]['underlying_index'] == 2 and 0 < calls[0]['budget_ms'] <= 30000
    assert calls[0]['wireguard_private'] == FIXTURE['wireguard_key']
    assert calls[1]['floors'] == [response()['catalog']]
    assert json.loads(storage.read()) == response()['catalog']
    assert b'tcp_id' not in storage.read() and FIXTURE['wireguard_key'].encode() not in storage.read()
    assert owner.summary == dict(stage='VERIFIED_READBACK', code='READY_FOR_PLATFORM', durable=True, sequence=2, country='nl')
    assert FIXTURE['wireguard_key'] not in repr(profile)


@pytest.mark.parametrize('category', ['AUTH', 'NETWORK', 'CONFIGURATION', 'CANCELLED', 'INTERNAL'])
def test_cached_catalog_is_only_a_floor_never_offline_access(setup, category):
    owner, storage, material, calls = setup
    cached = json.dumps(response()['catalog']).encode()
    storage.write(cached)
    seen = []

    def fail(request, cancel, deadline):
        seen.append(request['floors'])
        return dict(schema=1, id=request['id'], ok=False, code=category)

    owner.native = fail
    with pytest.raises(Failure, match=category):
        owner.resolve(material, 'nl', PRIVATE, [response()['catalog']], 2, Context(30000))
    assert len(seen) == 1 and len(seen[0]) == 2
    assert storage.read() == cached and not owner.summary['durable']


def test_cancel_before_persistence_and_after_floor_commit(setup, monkeypatch):
    owner, storage, material, calls = setup
    context = Context(30000)

    def cancel_fetch(request, cancel, deadline):
        cancel.set()
        return response()

    owner.native = cancel_fetch
    with pytest.raises(Failure, match='CANCELLED'):
        owner.resolve(material, 'nl', PRIVATE, [], 2, context)
    assert storage.read() is None
    owner.native = lambda request, cancel, deadline: response(request['id'])
    context = Context(30000)
    write = storage.write

    def cancel_commit(raw):
        write(raw)
        context.cancel.set()

    monkeypatch.setattr(storage, 'write', cancel_commit)
    with pytest.raises(Failure, match='CANCELLED'):
        owner.resolve(material, 'nl', PRIVATE, [], 2, context)
    assert storage.read() is not None and not owner.summary['durable']


@pytest.mark.parametrize('damage', ['digest', 'public', 'sequence', 'code', 'unknown', 'type', 'catalog'])
def test_worker_response_never_bypasses_profile_or_exact_schema_checks(damage):
    reply = response()
    if damage == 'digest': reply['digest'] = '0' * 64
    elif damage == 'public': reply['public'] = base64.b64encode(b'y' * 64).decode()
    elif damage == 'sequence': reply['sequence'] = 3
    elif damage == 'code': reply['code'] = 'CONNECTED'
    elif damage == 'unknown': reply['shell'] = 'bad'
    elif damage == 'type': reply['id'] = True
    else: reply['catalog'] = dict(payload='AA==', signature='AA==')
    with pytest.raises(ValueError):
        verified(reply, 1, 'nl', PRIVATE)


def test_signed_but_unsafe_profile_still_fails_before_floor_write(setup):
    owner, storage, material, calls = setup
    unsafe = response()
    payload = json.loads(base64.b64decode(unsafe['catalog']['payload']))
    payload['gateways'][0]['awg'] += 'PostUp = dangerous\n'
    raw = json.dumps(payload).encode()
    unsafe['catalog']['payload'] = base64.b64encode(raw).decode()
    unsafe['digest'] = hashlib.sha256(raw).hexdigest()
    owner.native = lambda *args: copy.deepcopy(unsafe)
    with pytest.raises(Failure, match='CONFIGURATION'):
        owner.resolve(material, 'nl', PRIVATE, [], 2, Context(30000))
    assert storage.read() is None


def test_readback_mismatch_never_applies_or_reverts_advanced_floor(setup):
    owner, storage, material, calls = setup

    def mismatch(request, cancel, deadline):
        reply = response(request['id'])
        if request['action'] == 'inspect': reply['response']['tcp_id'] = '22222222-2222-4222-8222-222222222222'
        return reply

    owner.native = mismatch
    with pytest.raises(Failure, match='CONFIGURATION'):
        owner.resolve(material, 'nl', PRIVATE, [], 2, Context(30000))
    assert storage.read() is not None and not owner.summary['durable']
