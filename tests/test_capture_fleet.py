from copy import deepcopy
import fcntl
import json
import multiprocessing
import os
import socket
import time

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import pytest

from control import capture_fleet as fleet
from control.capture_gate import GateError, MARKER, initialize


class Barrier:
    def __init__(self, location):
        self.location, self.descriptor = location, None
        self.valid, self.enters, self.exits = True, 0, 0
        self.lease = os.urandom(32).hex()

    def __enter__(self):
        self.descriptor = os.open(self.location, os.O_CREAT | os.O_RDWR | os.O_CLOEXEC, 0o600)
        fcntl.flock(self.descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        self.enters += 1
        return self

    def check(self):
        assert self.descriptor is not None and self.valid, 'barrier lost'
        return self.lease

    def __exit__(self, *_):
        if self.descriptor is not None:
            os.close(self.descriptor)
            self.descriptor = None
            self.exits += 1


def setup(tmp_path, seconds=20):
    signers = {slot: Ed25519PrivateKey.generate() for slot in fleet.SLOTS}
    expected = dict(purpose=fleet.PURPOSE, operation=os.urandom(16).hex(), challenge=os.urandom(32).hex(),
        participants={slot: dict(public_key=signers[slot].public_key().public_bytes_raw().hex(),
            source_sha256='1' * 64, coverage_sha256='2' * 64, late_policy_sha256='3' * 64,
            boot=fleet.kernel(), journal=str(tmp_path / slot), files=['state.bin']) for slot in fleet.SLOTS})
    barriers = {slot: Barrier(tmp_path / (slot + '.lock')) for slot in fleet.SLOTS}
    counts = {slot: 0 for slot in fleet.SLOTS}
    files = {slot: {'state.bin': ('private fixture ' + slot).encode()} for slot in fleet.SLOTS}

    def capture(slot):
        counts[slot] += 1
        return files[slot]

    members = {slot: fleet.Participant(expected, slot, signers[slot], tmp_path / slot, barriers[slot],
                lambda slot=slot: capture(slot), seconds=seconds) for slot in fleet.SLOTS}
    return expected, members, barriers, counts, files


def request(member, phase, **payload):
    return dict(command=phase, operation=member.expected['operation'], payload=payload)


def ready_all(members):
    return {slot: member.run(request(member, 'HELD')) for slot, member in members.items()}


def capture_all(members, ready):
    return {slot: member.run(request(member, 'CAPTURED', ready=ready)) for slot, member in members.items()}


def roundtrip(expected, members, files):
    ready = ready_all(members)
    snapshots = capture_all(members, ready)
    manifest = fleet.verified_manifest(expected, ready, snapshots, files)
    seals = {slot: member.run(request(member, 'SEALED', snapshots=snapshots, manifest=manifest))
             for slot, member in members.items()}
    releases = {slot: member.run(request(member, 'RELEASED', seals=seals)) for slot, member in members.items()}
    return ready, snapshots, seals, releases


@pytest.fixture
def lab(tmp_path):
    values = setup(tmp_path)
    try:
        yield values
    finally:
        for member in values[1].values():
            member.abort('TEST_FINISHED')


def test_complete_causal_interval_exact_bytes_and_readonly_replay(lab):
    expected, members, barriers, counts, files = lab
    ready, snapshots, seals, releases = roundtrip(expected, members, files)
    result = fleet.verify_bundle(expected, ready, snapshots, seals, releases, files)
    assert result['result'] == 'CAUSAL_INTERVAL_AND_EXACT_SET_VERIFIED'
    assert result['capture_permitted'] is False and result['normal_resume'] == 'NOT_ATTESTED'
    for slot, member in members.items():
        assert member.run(request(member, 'HELD')) == ready[slot]
        assert member.run(request(member, 'CAPTURED', ready=ready)) == snapshots[slot]
        assert member.run(request(member, 'RELEASED', seals=seals)) == releases[slot]
        assert counts[slot] == barriers[slot].enters == barriers[slot].exits == 1


def test_no_shared_kernel_or_wall_clock_assumption(lab, monkeypatch):
    expected, members, _, _, files = lab
    monkeypatch.setattr(time, 'time', lambda: pytest.fail('wall clock consulted'))
    ready, snapshots, seals, releases = roundtrip(expected, members, files)
    assert fleet.verify_bundle(expected, ready, snapshots, seals, releases, files)['operation'] == expected['operation']
    assert 'held_since_ns' not in json.dumps(ready)


def test_lost_snapshot_response_replays_no_effect(lab):
    expected, members, _, counts, files = lab
    ready = ready_all(members)
    member = members['OWNER']
    first = member.run(request(member, 'CAPTURED', ready=ready))
    snapshots = capture_all(members, ready)
    assert first == snapshots['OWNER'] and counts['OWNER'] == 1
    fleet.verified_manifest(expected, ready, snapshots, files)


@pytest.mark.parametrize('missing', fleet.SLOTS)
def test_incomplete_participant_coverage_refuses_before_capture(lab, missing):
    _, members, _, counts, _ = lab
    ready = ready_all(members)
    del ready[missing]
    with pytest.raises(ValueError, match='FLEET_RECEIPT_COVERAGE'):
        members['OWNER'].run(request(members['OWNER'], 'CAPTURED', ready=ready))
    assert counts['OWNER'] == 0 and members['OWNER'].state == 'FAILED'


def test_barrier_lost_during_capture_is_terminal_and_keeps_partial(lab):
    _, members, barriers, _, files = lab
    ready = ready_all(members)
    member = members['OWNER']

    def late_completion():
        barriers['OWNER'].valid = False
        return files['OWNER']

    member.snapshot = late_completion
    with pytest.raises(ValueError, match='FLEET_BARRIER_LOST'):
        member.run(request(member, 'CAPTURED', ready=ready))
    assert (member.root / 'objects/state.bin').read_bytes() == files['OWNER']['state.bin']
    assert (member.root / 'failed.json').is_file() and not (member.root / 'captured.json').exists()
    barriers['OWNER'].valid = True
    with pytest.raises(ValueError, match='FLEET_TERMINAL_FAILURE'):
        member.run(request(member, 'CAPTURED', ready=ready))


def test_no_seal_after_lease_loss_and_no_partial_bundle(lab):
    expected, members, barriers, _, files = lab
    ready = ready_all(members)
    snapshots = capture_all(members, ready)
    manifest = fleet.verified_manifest(expected, ready, snapshots, files)
    barriers['NL1'].valid = False
    with pytest.raises(ValueError, match='FLEET_BARRIER_LOST'):
        members['NL1'].run(request(members['NL1'], 'SEALED', snapshots=snapshots, manifest=manifest))
    with pytest.raises(ValueError, match='FLEET_RECEIPT_COVERAGE'):
        fleet.verify_bundle(expected, ready, snapshots, {}, {}, files)


@pytest.mark.parametrize('mutation', ['bytes', 'extra', 'missing'])
def test_independent_reader_rejects_inexact_set(lab, mutation):
    expected, members, _, _, files = lab
    ready, snapshots, seals, releases = roundtrip(expected, members, files)
    changed = deepcopy(files)
    if mutation == 'bytes':
        changed['RU']['state.bin'] = b'altered'
    elif mutation == 'extra':
        changed['RU']['other.bin'] = b'extra'
    else:
        del changed['RU']
    with pytest.raises(ValueError, match='FLEET_(EXACT_BYTES|OBJECT_COVERAGE)'):
        fleet.verify_bundle(expected, ready, snapshots, seals, releases, changed)


@pytest.mark.parametrize('field', ['operation', 'challenge', 'coverage_sha256', 'source_sha256', 'late_policy_sha256'])
def test_other_operation_or_policy_is_rejected(lab, field):
    expected, members, _, _, files = lab
    ready, snapshots, seals, releases = roundtrip(expected, members, files)
    changed = deepcopy(expected)
    if field in ('operation', 'challenge'):
        changed[field] = '9' * len(changed[field])
    else:
        changed['participants']['OWNER'][field] = '9' * 64
    with pytest.raises(ValueError, match='FLEET_RECEIPT_BINDING'):
        fleet.verify_bundle(changed, ready, snapshots, seals, releases, files)


def test_forged_proof_and_replay_changed_are_rejected(lab):
    expected, members, _, _, _ = lab
    ready = ready_all(members)
    ready['RU']['body']['payload']['coverage'] = '7' * 64
    with pytest.raises(ValueError, match='FLEET_SIGNATURE'):
        fleet.prepared(ready, expected)
    with pytest.raises(ValueError, match='FLEET_REPLAY_CHANGED'):
        members['OWNER'].run(request(members['OWNER'], 'HELD', extra=True))


def test_incomplete_writers_and_late_policy_require_distinct_pins(lab):
    expected, _, _, _, _ = lab
    for name in ('coverage_sha256', 'late_policy_sha256'):
        changed = deepcopy(expected)
        del changed['participants']['OWNER'][name]
        with pytest.raises(ValueError, match='FLEET_MEMBER'):
            fleet.contract(changed)


def test_original_drain_still_refuses_uncertainty(tmp_path):
    gate = initialize(tmp_path / 'ordinary')
    marker = gate.directory / 'pending' / ('4' * 32)
    marker.write_bytes(MARKER)
    marker.chmod(0o600)
    before = (marker.read_bytes(), marker.stat())
    with pytest.raises(GateError, match='UNSETTLED_OPERATION'):
        with gate.drain(0.1):
            pytest.fail('historical uncertainty became drained')
    assert (marker.read_bytes(), marker.stat()) == before


def child_server(parent_descriptor, channel, expected, private_key, root, lock, seconds):
    os.close(parent_descriptor)
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    signer = Ed25519PrivateKey.from_private_bytes(private_key)
    member = fleet.Participant(expected, 'OWNER', signer, root, Barrier(lock),
                               lambda: {'state.bin': b'isolated'}, seconds=seconds)
    try:
        fleet.serve(member, channel.fileno(), channel.fileno())
    except ValueError:
        pass
    finally:
        channel.close()


@pytest.mark.parametrize('loss', ['eof', 'partial-frame', 'no-command'])
def test_dead_controller_or_stalled_frame_releases_real_kernel_lock(tmp_path, loss):
    expected, members, _, _, _ = setup(tmp_path)
    signer = Ed25519PrivateKey.generate()
    expected['participants']['OWNER']['public_key'] = signer.public_key().public_bytes_raw().hex()
    parent, child = socket.socketpair()
    root, lock = tmp_path / 'server', tmp_path / 'server.lock'
    expected['participants']['OWNER']['journal'] = str(root)
    process = multiprocessing.get_context('fork').Process(target=child_server, args=(parent.fileno(), child,
        expected, signer.private_bytes_raw(), root, lock, 1.0))
    process.start()
    child.close()
    try:
        fleet.send(parent.fileno(), dict(command='HELD', operation=expected['operation'], payload={}),
                   time.monotonic() + 2)
        response = fleet.receive(parent.fileno(), time.monotonic() + 2)
        assert fleet.verify_receipt(response, expected, 'OWNER', 'HELD')
        with lock.open('rb') as stream:
            with pytest.raises(BlockingIOError):
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            if loss == 'eof':
                parent.close()
            elif loss == 'partial-frame':
                parent.sendall(b'\x00\x00')
            process.join(timeout=4)
            assert process.exitcode == 0
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert fleet.document((root / 'failed.json').read_bytes())['result'] == 'FAILED'
        assert not (root / 'released.json').exists()
    finally:
        parent.close()
        if process.is_alive():
            process.kill()
        process.join(timeout=2)
        for member in members.values():
            member.abort('TEST_FINISHED')


def test_expired_before_start_never_captures(lab):
    _, members, _, counts, _ = lab
    member = members['OWNER']
    member.deadline = time.monotonic() - 1
    with pytest.raises(ValueError, match='FLEET_LEASE_EXPIRED'):
        member.run(request(member, 'HELD'))
    assert counts['OWNER'] == 0 and member.state == 'FAILED'


def test_cannot_reconstruct_or_reuse_durable_operation_directory(lab):
    expected, members, barriers, _, _ = lab
    member = members['OWNER']
    with pytest.raises(FileExistsError):
        fleet.Participant(expected, 'OWNER', member.signer, member.root, barriers['OWNER'], lambda: {})


def test_completed_operation_cannot_choose_another_journal_directory(lab):
    expected, members, barriers, _, files = lab
    roundtrip(expected, members, files)
    member = members['OWNER']
    with pytest.raises(ValueError, match='FLEET_JOURNAL_BINDING'):
        fleet.Participant(expected, 'OWNER', member.signer, member.root.with_name('replay-elsewhere'),
                          barriers['OWNER'], lambda: files['OWNER'])


def test_another_boot_cannot_resume_old_operation(lab, monkeypatch):
    expected, members, barriers, _, _ = lab
    member = members['OWNER']
    monkeypatch.setattr(fleet, 'kernel', lambda: '0' * 64)
    with pytest.raises(ValueError, match='FLEET_BOOT_BINDING'):
        fleet.Participant(expected, 'OWNER', member.signer, member.root, barriers['OWNER'], lambda: {})


def test_snapshot_bytes_changed_after_response_refuses_sealing(lab):
    expected, members, _, _, files = lab
    ready = ready_all(members)
    snapshots = capture_all(members, ready)
    manifest = fleet.verified_manifest(expected, ready, snapshots, files)
    member = members['NL2']
    (member.root / 'objects/state.bin').write_bytes(b'late changed snapshot')
    with pytest.raises(ValueError, match='FLEET_LOCAL_BYTES_CHANGED'):
        member.run(request(member, 'SEALED', snapshots=snapshots, manifest=manifest))


def test_snapshot_coverage_refuses_before_seal(lab):
    _, members, _, _, _ = lab
    ready = ready_all(members)
    member = members['NL2']
    member.snapshot = lambda: {'state.bin': b'valid', 'unexpected.bin': b'uncovered'}
    with pytest.raises(ValueError, match='FLEET_SNAPSHOT_COVERAGE'):
        member.run(request(member, 'CAPTURED', ready=ready))


def test_lost_barrier_during_response_replay_is_terminal(lab):
    _, members, barriers, _, _ = lab
    ready_all(members)
    barriers['RU'].valid = False
    with pytest.raises(ValueError, match='FLEET_BARRIER_LOST'):
        members['RU'].run(request(members['RU'], 'HELD'))
    assert members['RU'].state == 'FAILED'
    assert fleet.document((members['RU'].root / 'failed.json').read_bytes())['error_type'] == 'FLEET_BARRIER_LOST'


@pytest.mark.parametrize('raw', [b'{"a":1,"a":2}', b'{"a":NaN}', b'{ "a":1}', b''])
def test_strict_wire_documents(raw):
    with pytest.raises(ValueError):
        fleet.document(raw)
