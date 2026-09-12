import base64
import hashlib
import json
import uuid
from types import SimpleNamespace

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from device_identity.device import DeviceIdentity
from provisioning import ack
from provisioning.configuration import (AUDIENCE, DOMAIN, LOCAL_KEY, ControlConfiguration,
    ConfigVerifier, ConfigError, issue_config)
from provisioning.envelope import ProvisioningRejected, public_identity
from provisioning.transaction import ControlJournal, ProvisioningCore
from provisioning.relay import ControlRelay, TestAdapter
from provisioning.application import BackendApplication


class Application:
    def __init__(self):
        self.active = 'baseline'
        self.applied = []
        self.restored = []
        self.health = True
        self.fail_apply = False
        self.fail_rollback = False

    def snapshot(self, previous=None):
        return dict(known=[self.active], active=[self.active])

    def apply(self, verified, baseline):
        self.applied.append(verified.digest)
        self.active = verified.digest
        if self.fail_apply:
            raise RuntimeError('secret transport exception')

    def healthy(self, verified):
        return self.health

    def rollback(self, staged, previous, baseline):
        if self.fail_rollback:
            raise RuntimeError('secret rollback exception')
        self.restored.append(staged.digest)
        self.active = baseline['active'][0] if baseline['active'] else None


@pytest.fixture
def environment(tmp_path):
    device = DeviceIdentity.generate()
    key = Ed25519PrivateKey.generate()
    anchor = key.public_key().public_bytes_raw()
    peer = DeviceIdentity.generate()
    wg = ('[Interface]\nPrivateKey = '+LOCAL_KEY+'\nAddress = 10.77.0.4/32\nDNS = 1.1.1.1\n'
        '[Peer]\nPublicKey = '+peer.wireguard_public_key+'\nEndpoint = 198.51.100.1:51820\nAllowedIPs = 0.0.0.0/0, ::/0\n')
    payload = dict(schema_version=2, config_id='config-1', revision=1, issued_at=1000, expires_at=4600,
        recipient=device.reference, audience=AUDIENCE, wireguard_public_key=device.wireguard_public_key,
        min_client_version='0.2.9', previous_config_hash=None, signer_key_id=hashlib.sha256(anchor).hexdigest(),
        gateways=[dict(gateway_id='gw1', endpoint='198.51.100.1', port=51820)],
        transport_profiles=[dict(profile_id='wg1', gateway_id='gw1', transport='wireguard', transport_version='1', config=wg)])
    verifier = ConfigVerifier(anchor=anchor, device=device, client_version='0.2.9')
    journal = ControlJournal(tmp_path / 'journal', verifier)
    journal.initialize()
    clock = [1000]
    application = Application()
    core = ProvisioningCore(journal=journal, application=application, device=device, clock=lambda: clock[0])
    relay = ControlRelay(tmp_path / 'relay', clock=lambda: clock[0])
    relay.initialize()
    env = SimpleNamespace(device=device, key=key, anchor=anchor, payload=payload, verifier=verifier,
        journal=journal, clock=clock, application=application, core=core, relay=relay)
    env.raw = signed(env)
    relay.publish(public=device.public_identity, wg=device.wireguard_public_key, sequence=1, envelope=env.raw)
    env.carrier = TestAdapter(relay, device)
    return env


def signed(env, changes=None, *, key=None):
    value = {**env.payload, **(changes or {})}
    # Test issuer intentionally signs malformed contracts for verifier cases.
    ciphertext = public_identity(base64.b64decode(env.device.public_identity)).encrypt(json.dumps(value).encode())
    return json.dumps(dict(ciphertext=base64.b64encode(ciphertext).decode(),
        signature=base64.b64encode((key or env.key).sign(DOMAIN+ciphertext)).decode()), separators=(',', ':')).encode()


def state(env):
    with env.journal._locked() as directory:
        return env.journal.read(directory)


def statuses(env):
    return [ack.verify(base64.b64decode(raw))['status'] for raw in state(env)['outbox']]


def test_offline_issue_and_full_lifecycle(environment):
    e = environment
    typed = ControlConfiguration.model_validate_json(json.dumps(e.payload))
    raw = issue_config(typed, recipient_public=base64.b64decode(e.device.public_identity), signing_key=e.key)
    assert e.verifier.verify(raw, now=1000).state.revision == 1
    assert e.core.refresh(e.carrier) == 'COMMITTED'
    record = state(e)
    assert record['phase'] == 'IDLE' and record['staged'] is None and not record['outbox']
    assert record['committed']['digest'] == hashlib.sha256(e.raw).hexdigest()
    with e.relay._db() as db:
        bodies = [ack.verify(bytes(row[0])) for row in db.execute('SELECT raw FROM acks')]
    assert {b['status'] for b in bodies} == {'RECEIVED', 'APPLIED', 'COMMITTED'}


@pytest.mark.parametrize('attack,category', [
    ('signature','SIGNATURE'), ('unknown','SIGNATURE'), ('tamper','SIGNATURE'),
    ('expiry','LEASE'), ('future','LEASE'), ('timestamps','STRUCTURE'), ('audience','TARGET'),
    ('recipient','TARGET'), ('schema','SCHEMA'), ('version','CLIENT_VERSION'), ('signer','SIGNER'),
    ('wgkey','TARGET'), ('profile','STRUCTURE'), ('awg31','UNSUPPORTED_TRANSPORT_VERSION'),
    ('boolschema','SCHEMA'), ('oversized','SIZE'), ('malformed','MALFORMED')])
def test_verification_fail_closed(environment, attack, category):
    e = environment
    changes = {}
    raw = e.raw
    if attack == 'unknown': raw = signed(e, key=Ed25519PrivateKey.generate())
    elif attack in ('signature', 'tamper'):
        outer = json.loads(raw)
        field = 'signature' if attack == 'signature' else 'ciphertext'
        content = bytearray(base64.b64decode(outer[field])); content[-1] ^= 1
        outer[field] = base64.b64encode(content).decode(); raw = json.dumps(outer).encode()
    elif attack == 'oversized': raw = bytes(65537)
    elif attack == 'malformed': raw = b'{}'
    else:
        if attack == 'expiry': changes = dict(expires_at=1000, issued_at=999)
        elif attack == 'future': changes = dict(issued_at=1001)
        elif attack == 'timestamps': changes = dict(expires_at=999)
        elif attack == 'audience': changes = dict(audience='other')
        elif attack == 'recipient': changes = dict(recipient='0'*32)
        elif attack == 'schema': changes = dict(schema_version=3)
        elif attack == 'boolschema': changes = dict(schema_version=True)
        elif attack == 'version': changes = dict(min_client_version='0.3.0')
        elif attack == 'signer': changes = dict(signer_key_id='0'*64)
        elif attack == 'wgkey': changes = dict(wireguard_public_key=DeviceIdentity.generate().wireguard_public_key)
        elif attack == 'profile': changes = dict(transport_profiles=[{**e.payload['transport_profiles'][0], 'config':'PostUp=evil'}])
        elif attack == 'awg31': changes = dict(transport_profiles=[{**e.payload['transport_profiles'][0],
            'transport':'amneziawg', 'transport_version':'3.1', 'config':'HeaderProtectionKey=never-downgrade'}])
        raw = signed(e, changes)
    with pytest.raises(ConfigError) as error:
        e.verifier.verify(raw, now=1000)
    assert error.value.category == category
    assert e.core.receive(raw) == 'REJECTED'
    assert not e.application.applied
    assert state(e)['committed'] is None and state(e)['floor'] == 0
    body = ack.verify(base64.b64decode(state(e)['outbox'][-1]))
    assert body['error'] == category and body['config_id'] is None and body['sequence'] == 0
    assert 'config' not in body and 'private' not in json.dumps(body).lower()


def test_replay_duplicates_previous_hash_and_bad_high_sequence(environment):
    e = environment
    assert e.core.receive(e.raw) == 'COMMITTED'
    assert e.core.receive(e.raw) == 'COMMITTED'
    assert len(e.application.applied) == 1
    assert e.core.receive(signed(e)) == 'REJECTED'  # same revision, different envelope
    high = signed(e, dict(revision=999), key=Ed25519PrivateKey.generate())
    assert e.core.receive(high) == 'REJECTED' and state(e)['floor'] == 1
    assert e.core.receive(signed(e, dict(revision=2, config_id='config-2'))) == 'REJECTED'
    second = signed(e, dict(revision=2, config_id='config-2', previous_config_hash=hashlib.sha256(e.raw).hexdigest()))
    assert e.core.receive(second) == 'COMMITTED'
    assert e.core.receive(e.raw) == 'REJECTED'
    assert len(e.application.applied) == 2 and state(e)['floor'] == 2


@pytest.mark.parametrize('failure', ['apply', 'health'])
def test_failure_restores_last_good_and_failed_duplicate_does_not_reapply(environment, failure):
    e = environment
    assert e.core.receive(e.raw) == 'COMMITTED'
    good = e.application.active
    e.application.fail_apply = failure == 'apply'
    e.application.health = failure != 'health'
    second = signed(e, dict(revision=2, config_id='config-2', previous_config_hash=good))
    assert e.core.receive(second) == 'ROLLED_BACK'
    assert e.application.active == good and state(e)['committed']['digest'] == good
    assert e.core.receive(second) == 'ROLLED_BACK' and len(e.application.applied) == 2
    assert statuses(e)[-1] == 'ROLLED_BACK'


@pytest.mark.parametrize('phase', ['STAGED', 'APPLYING', 'APPLIED_PENDING', 'COMMITTED'])
def test_crash_restart_is_deterministic(environment, monkeypatch, phase):
    e = environment
    write = e.journal._write
    def crash(directory, record):
        write(directory, record)
        if record['phase'] == phase or (phase == 'COMMITTED' and record['committed'] is not None):
            raise SystemExit('simulated power loss')
    with monkeypatch.context() as patch:
        patch.setattr(e.journal, '_write', crash)
        with pytest.raises(SystemExit):
            e.core.receive(e.raw)
    restarted = ProvisioningCore(journal=ControlJournal(e.journal.path, e.verifier),
        application=e.application, device=e.device, clock=lambda: e.clock[0])
    if phase == 'COMMITTED':
        assert restarted.recover() == 'IDLE'
        assert restarted.flush_acks(e.carrier)
        assert restarted.receive(e.raw) == 'COMMITTED'
        assert len(e.application.applied) == 1
    else:
        assert restarted.recover() == 'ROLLED_BACK'
        assert restarted.recover() == 'IDLE'
        assert e.application.active == 'baseline'
        assert restarted.receive(e.raw) == 'ROLLED_BACK'
        assert state(e)['committed'] is None


def test_rollback_failure_persists_intent_for_retry(environment):
    e = environment
    e.application.fail_apply = e.application.fail_rollback = True
    assert e.core.receive(e.raw) == 'FAILED'
    assert state(e)['phase'] == 'ROLLING_BACK'
    e.application.fail_rollback = False
    assert e.core.recover() == 'ROLLED_BACK'
    assert e.application.active == 'baseline'


def test_ack_retry_duplicate_and_carrier_failure_preserve_vpn(environment):
    e = environment
    assert e.core.receive(e.raw) == 'COMMITTED'
    pending = list(state(e)['outbox'])
    e.carrier.available = False
    assert not e.core.flush_acks(e.carrier)
    assert state(e)['outbox'] == pending
    with pytest.raises(OSError):
        e.core.refresh(e.carrier)
    assert e.application.active == hashlib.sha256(e.raw).hexdigest()
    e.carrier.available = True
    # Relay accepted but local process lost response; replay must deduplicate.
    e.carrier.send_ack(base64.b64decode(pending[0]))
    assert e.core.flush_acks(e.carrier)
    with e.relay._db() as db:
        assert db.execute('SELECT COUNT(*) FROM acks').fetchone()[0] == 3


def test_relay_replay_revoke_and_forged_ack(environment):
    e = environment
    from provisioning.auth import prove
    challenge = e.relay.challenge(public_identity=e.device.public_identity, wireguard_public_key=e.device.wireguard_public_key)
    proof = prove(e.device, challenge['challenge'])
    assert e.relay.fetch(proof) == e.raw
    with pytest.raises(ProvisioningRejected): e.relay.fetch(proof)
    e.core.receive(e.raw)
    raw = base64.b64decode(state(e)['outbox'][0])
    bad = json.loads(raw); bad['body']['status'] = 'FAILED'
    with pytest.raises(ProvisioningRejected): e.relay.acknowledge(json.dumps(bad).encode())
    e.relay.revoke(e.device.reference)
    with pytest.raises(ProvisioningRejected): e.carrier.receive()
    with pytest.raises(ProvisioningRejected): e.relay.acknowledge(raw)


def test_journal_corruption_and_clock_fail_closed(environment):
    e = environment
    e.core.receive(e.raw)
    e.clock[0] = 999
    with pytest.raises(ConfigError): e.core.receive(e.raw)
    (e.journal.path / 'cache.json').write_text('{}')
    with pytest.raises(ProvisioningRejected): e.core.recover()


def test_structured_logs_never_contain_profiles(environment, caplog):
    e = environment
    with caplog.at_level('INFO', logger='family_connect.control'):
        e.core.refresh(e.carrier)
    events = {r.control_event for r in caplog.records}
    assert {'control.config.verified','control.config.staged','control.config.applied',
        'control.config.committed','control.ack.sent'} <= events
    assert LOCAL_KEY not in caplog.text and e.payload['transport_profiles'][0]['config'] not in caplog.text


class Driver:
    def __init__(self):
        self.baseline = str(uuid.uuid4())
        self.inventory = {self.baseline: 'old'}
        self.live = {self.baseline}
        self.imported = []
    def profiles(self): return list(self.inventory.items())
    def active(self, ident): return ident in self.live
    def healthy(self, ident): return ident in self.live
    def connect(self, ident): self.live.add(ident)
    def disconnect(self, ident): self.live.discard(ident)
    def import_profile(self, path):
        from clients.desktop.profile_config import parse
        text = path.read_text(); parse(text)
        self.imported.append(text)
        ident = str(uuid.uuid4()); self.inventory[ident] = 'new'
        return ident


def test_backend_boundary_apply_and_crash_import_cleanup(environment):
    e = environment
    driver = Driver()
    application = BackendApplication(driver, e.device)
    baseline = application.snapshot()
    verified = e.verifier.verify(e.raw, now=1000)
    application.apply(verified, baseline)
    assert application.healthy(verified)
    assert len(driver.live) == 1 and driver.baseline not in driver.live
    assert LOCAL_KEY not in driver.imported[0]
    # New application instance has no in-memory imported ID, just durable baseline.
    BackendApplication(driver, e.device).rollback(verified, None, baseline)
    assert driver.live == {driver.baseline}
    BackendApplication(driver, e.device).rollback(verified, None, baseline)
    assert driver.live == {driver.baseline}


def test_real_rns_complete_lifecycle(tmp_path):
    import os
    from pathlib import Path
    import selectors
    import socket
    import subprocess
    import sys
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = str(sock.getsockname()[1])
    root = Path(__file__).resolve().parents[1]
    env = {**os.environ, 'PYTHONPATH': str(root), 'PYTHONDONTWRITEBYTECODE': '1'}
    command = [sys.executable, str(root / 'tests/reticulum_control_peer.py')]
    server = subprocess.Popen(command + ['server', str(tmp_path), port], cwd=root, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        with selectors.DefaultSelector() as selector:
            selector.register(server.stdout, selectors.EVENT_READ)
            assert selector.select(timeout=15), 'server startup timeout'
        assert server.stdout.readline().strip() == 'ready'
        result = subprocess.run(command + ['client', str(tmp_path), port], cwd=root, env=env,
            capture_output=True, text=True, timeout=55)
        assert result.returncode == 0, result.stderr
        assert 'RNS: commit, ACK, rollback, ACK, duplicate safe, last-good preserved' in result.stdout
    finally:
        server.terminate()
        try: server.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill(); server.communicate(timeout=5)


@pytest.mark.parametrize('transport', ['amneziawg', 'vless-reality'])
def test_existing_awg2_tcp_profile_parsers_reused(environment, transport):
    e = environment
    profile = dict(e.payload['transport_profiles'][0])
    profile['transport'] = transport
    if transport == 'amneziawg':
        profile['transport_version'] = '2.0'
        params = '\n'.join(['Jc = 4','Jmin = 40','Jmax = 70', 'S1 = 16','S2 = 32','S3 = 16','S4 = 16',
            'H1 = 100','H2 = 200','H3 = 300','H4 = 400'])
        profile['config'] = profile['config'].replace('[Peer]', params+'\n[Peer]')
    else:
        profile['config'] = json.dumps(dict(type='vless-reality-v1', server='198.51.100.1', port=51820,
            id=str(uuid.uuid4()), public_key=base64.urlsafe_b64encode(bytes(range(32))).decode().rstrip('='),
            server_name='example.com', short_id='abcd'))
    raw = signed(e, dict(transport_profiles=[profile]))
    assert e.verifier.verify(raw, now=1000).state.transport_profiles[0].transport == transport
    assert e.core.receive(raw) == 'COMMITTED'


def test_expired_last_good_never_reconnected_on_recovery(environment, monkeypatch):
    e = environment
    assert e.core.receive(e.raw) == 'COMMITTED'
    good = e.application.active
    second = signed(e, dict(config_id='config-2', revision=2, issued_at=2000, expires_at=5600,
        previous_config_hash=good))
    e.clock[0] = 2000
    def crash(*_): raise SystemExit()
    with monkeypatch.context() as patch:
        patch.setattr(e.application, 'healthy', crash)
        with pytest.raises(SystemExit): e.core.receive(second)
    e.clock[0] = 4600
    assert e.core.recover() == 'ROLLED_BACK'
    assert e.application.active is None
    assert state(e)['committed']['digest'] == good  # Evidence/floor retained.


def test_failed_commit_write_recovers_last_good(environment, monkeypatch):
    e = environment
    write = e.journal._write
    def fail_before_commit(directory, record):
        if record['committed'] is not None:
            raise OSError('disk write failed')
        write(directory, record)
    with monkeypatch.context() as patch:
        patch.setattr(e.journal, '_write', fail_before_commit)
        with pytest.raises(OSError): e.core.receive(e.raw)
    assert state(e)['phase'] == 'APPLIED_PENDING'
    assert e.core.recover() == 'ROLLED_BACK'
    assert e.application.active == 'baseline'


def test_stage_write_failure_never_applies(environment, monkeypatch):
    e = environment
    def fail(*_): raise OSError('disk write failed')
    with monkeypatch.context() as patch:
        patch.setattr(e.journal, '_write', fail)
        with pytest.raises(OSError): e.core.receive(e.raw)
    assert not e.application.applied and state(e)['phase'] == 'IDLE'


def test_outbox_backpressure_never_applies(environment):
    e = environment
    for i in range(59):
        assert e.core.receive(str(i).encode()) == 'REJECTED'
    with pytest.raises(ProvisioningRejected): e.core.receive(e.raw)
    assert not e.application.applied
    assert e.core.flush_acks(e.carrier)
    assert e.core.receive(e.raw) == 'COMMITTED'


def test_repeated_rollback_failures_do_not_exhaust_outbox(environment):
    e = environment
    e.application.fail_apply = e.application.fail_rollback = True
    assert e.core.receive(e.raw) == 'FAILED'
    for _ in range(70):
        e.clock[0] += 1
        assert e.core.recover() == 'FAILED'
    assert len(state(e)['outbox']) == 2
    e.application.fail_rollback = False
    assert e.core.recover() == 'ROLLED_BACK'


def test_real_backend_methods_are_application_boundary(environment, monkeypatch):
    # Exercise the actual LinuxTCP entry points; transport internals remain in
    # their existing unit/scoped platform suites. No privileged host operation.
    import sys
    from pathlib import Path
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / 'clients/desktop'))
    from backend import LinuxTCP
    import backend as backend_module
    monkeypatch.setattr(backend_module,'operation_directory',lambda:environment.journal.path.parent/'operations')
    e = environment
    simulated = Driver()
    calls = []
    for name in ('profiles', 'active', 'healthy', 'connect', 'disconnect', 'import_profile'):
        method = getattr(simulated, name)
        def observed(self, *args, _name=name, _method=method):
            calls.append(_name)
            return _method(*args)
        monkeypatch.setattr(LinuxTCP, name, observed)
    adapter = BackendApplication(LinuxTCP(), e.device)
    core = ProvisioningCore(journal=e.journal, application=adapter, device=e.device, clock=lambda: 1000)
    assert core.receive(e.raw) == 'COMMITTED'
    assert {'profiles', 'active', 'import_profile', 'disconnect', 'connect', 'healthy'} <= set(calls)
    assert state(e)['committed']['applied_at'] == 1000
    assert state(e)['committed']['runtime']['active'] == list(simulated.live)


def test_private_key_placeholder_cannot_be_hidden_in_comment(environment):
    e = environment
    profile = dict(e.payload['transport_profiles'][0])
    profile['config'] = profile['config'].replace(LOCAL_KEY, base64.b64encode(bytes(32)).decode()) + '# '+LOCAL_KEY+'\n'
    raw = signed(e, dict(transport_profiles=[profile]))
    assert e.core.receive(raw) == 'REJECTED'
    assert not e.application.applied


@pytest.mark.parametrize('phase',['STAGED','APPLYING','APPLIED_PENDING'])
def test_gui_blocked_until_control_journal_recovery(environment,monkeypatch,phase):
    from pathlib import Path
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]/'clients/desktop'))
    import backend
    e=environment
    monkeypatch.setattr(backend,'operation_directory',lambda:e.journal.path.parent/'operations')
    simulated=Driver()
    for name in ('profiles','active','healthy','connect','disconnect','import_profile'):
        method=getattr(simulated,name)
        monkeypatch.setattr(backend.LinuxTCP,name,lambda self,*a,_method=method:_method(*a))
    driver=backend.LinuxTCP()
    core=ProvisioningCore(journal=e.journal,application=BackendApplication(driver,e.device),device=e.device,clock=lambda:1000)
    write=e.journal._write
    def crash(directory,record):
        write(directory,record)
        if record['phase']==phase:raise SystemExit('crash')
    with monkeypatch.context() as patch:
        patch.setattr(e.journal,'_write',crash)
        with pytest.raises(SystemExit):core.receive(e.raw)
    with pytest.raises(backend.ConnectionBusy):
        with backend.connection_operation(mutate=True):pass
    recovered=ProvisioningCore(journal=e.journal,application=BackendApplication(driver,e.device),device=e.device,clock=lambda:1000)
    assert recovered.recover()=='ROLLED_BACK'
    with backend.connection_operation() as lease:assert lease.record['pending'] is None
    assert simulated.live=={simulated.baseline}
