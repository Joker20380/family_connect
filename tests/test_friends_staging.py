import copy
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import uuid

import pytest

from scripts import friends_staging as staging
from scripts import friends_staging_receiver as receiver

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def bundle(tmp_path):
    parent = tmp_path / 'inert' / 'attempt'
    parent.mkdir(parents=True, mode=0o700)
    source = tmp_path / 'artifact'
    source.write_bytes(bytes(range(256)) * 1024)
    manifest = [dict(artifact_id='native-check', source=str(source), bytes=source.stat().st_size, sha256=hashlib.sha256(source.read_bytes()).hexdigest(), mode=0o700)]
    request, sources = staging.prepare(manifest, 'ru', parent, 'operator')
    return dict(parent=parent, source=source, manifest=manifest, request=request, sources=sources, temporary=tmp_path)


def command(bundle, setup=''):
    code = 'import sys;sys.path.insert(0,' + repr(str(ROOT)) + ');from pathlib import Path;from scripts import friends_staging_receiver as receiver;' + setup + ';receiver.receive(Path(' + repr(str(bundle['parent'].parent)) + '))'
    return [sys.executable, '-I', '-B', '-c', code.replace(';;', ';')]


def run(bundle, setup='', sources=None, connect_seconds=2):
    evidence = bundle['temporary'] / uuid.uuid4().hex
    result = staging.transfer(bundle['request'], sources or bundle['sources'], evidence, transport=command(bundle, setup), connect_seconds=connect_seconds)
    assert json.loads((evidence / 'receipt.json').read_bytes()) == result
    return result


class SlowPath:
    def __init__(self, path, delay):
        self.path = path
        self.delay = delay

    def open(self, mode):
        self.stream = self.path.open(mode)
        self.calls = 0
        return self

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.stream.close()

    def read(self, size):
        self.calls += 1
        if self.calls > 1:
            time.sleep(self.delay)
        return self.stream.read(size)


def test_normal_ready_and_exact_inventory(bundle):
    result = run(bundle)
    assert result['state'] == 'READY'
    assert result['items'][0]['bytes_transferred'] == 262144
    assert result['items'][0]['remote_sha256_result']
    assert result['items'][0]['connect_end'] >= result['items'][0]['connect_start']
    assert receiver.inspect(bundle['parent'], 'operator', bundle['request'])['state'] == 'READY'
    assert (bundle['parent'] / 'operator/native-check').stat().st_mode & 0o777 == 0o700


def test_slow_valid_within_derived_deadline(bundle):
    result = run(bundle, sources=[SlowPath(bundle['source'], .03)])
    assert result['state'] == 'READY'
    assert result['elapsed_seconds'] < staging.budgets(262144)['transfer_seconds'] + 2


def test_connect_timeout_no_ready(bundle):
    result = run(bundle, setup='import time;time.sleep(2)', connect_seconds=.08)
    assert result['state'] == 'FAILED' and result['timeout_stage'] == 'connect'
    assert not (bundle['parent'] / 'operator').exists()


def test_mid_transfer_timeout_quarantines_and_safe_retry(bundle):
    bundle['request']['items'][0]['transfer_seconds'] = .15
    failed = run(bundle, sources=[SlowPath(bundle['source'], .3)])
    assert failed['state'] == 'PARTIAL' and failed['timeout_stage'] == 'transfer'
    assert failed['items'][0]['bytes_transferred'] > 0
    partial = list(bundle['parent'].glob('.operator.partial-*'))
    assert len(partial) == 1 and not (bundle['parent'] / 'operator').exists()
    assert not (partial[0] / receiver.RECEIPT).exists()
    original = (partial[0] / 'native-check').read_bytes()
    bundle['request']['items'][0]['transfer_seconds'] = 5
    bundle['request']['attempt'] = uuid.uuid4().hex
    assert run(bundle)['state'] == 'READY'
    assert (partial[0] / 'native-check').read_bytes() == original
    assert run(bundle)['final_event']['reused']


def test_remote_hash_mismatch_no_promotion(bundle):
    bundle['request']['items'][0]['sha256'] = '0' * 64
    result = run(bundle)
    assert result['state'] == 'PARTIAL' and result['exception_class'] == 'HashMismatch'
    assert not (bundle['parent'] / 'operator').exists()


def test_remote_validation_timeout(bundle):
    bundle['request']['items'][0]['validation_seconds'] = .05
    result = run(bundle, setup='import time;original=receiver.hash_file;receiver.hash_file=lambda path:(time.sleep(.3),original(path))[1]')
    assert result['state'] == 'PARTIAL' and result['timeout_stage'] == 'validation'
    assert not (bundle['parent'] / 'operator').exists()


def test_exit_after_promotion_before_receipt_is_unaccepted(bundle):
    result = run(bundle, setup='import os;original=receiver.promote;receiver.promote=lambda source,target:(original(source,target),os._exit(93))')
    assert result['state'] != 'READY'
    observation = receiver.inspect(bundle['parent'], 'operator', bundle['request'])
    assert observation == dict(state='PARTIAL', detail='COMPLETE_BUT_UNACCEPTED')
    assert run(bundle)['state'] != 'READY'


def test_two_attempts_cannot_corrupt_same_destination(bundle):
    other = copy.deepcopy(bundle)
    other['request']['attempt'] = uuid.uuid4().hex
    setup = 'import time;original=receiver.hash_file;receiver.hash_file=lambda path:(time.sleep(.3),original(path))[1]'
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda value: run(value, setup=setup), (bundle, other)))
    assert sum(result['state'] == 'READY' for result in results) == 1
    assert receiver.inspect(bundle['parent'], 'operator', bundle['request'])['state'] == 'READY'
    assert hashlib.sha256((bundle['parent'] / 'operator/native-check').read_bytes()).hexdigest() == bundle['request']['items'][0]['sha256']


def test_ready_reinspection_detects_tampering(bundle):
    assert run(bundle)['state'] == 'READY'
    (bundle['parent'] / 'operator/native-check').write_bytes(b'corrupted')
    with pytest.raises(receiver.HashMismatch):
        receiver.inspect(bundle['parent'], 'operator', bundle['request'])


@pytest.mark.parametrize('change', ['parent', 'destination', 'symlink', 'duplicate', 'oversized'])
def test_unsafe_paths_and_manifests_rejected(bundle, change):
    request = bundle['request']
    if change == 'parent':
        request['parent'] = str(bundle['temporary'])
    elif change == 'destination':
        request['destination'] = '../live'
    elif change == 'symlink':
        link = bundle['temporary'] / 'link'
        link.symlink_to(bundle['parent'], target_is_directory=True)
        request['parent'] = str(link)
    elif change == 'duplicate':
        request['items'] *= 2
    else:
        request['items'][0]['bytes'] = 2**30
    with pytest.raises(receiver.StagingError):
        receiver.validate(request, bundle['parent'].parent)


def test_local_wrong_pin_never_connects(bundle):
    bundle['manifest'][0]['sha256'] = '0' * 64
    with pytest.raises(ValueError, match='pin'):
        staging.prepare(bundle['manifest'], 'ru', bundle['parent'], 'operator')


def test_inspection_of_absent_destination_does_not_write(bundle):
    bundle['request']['inspect_only'] = True
    assert run(bundle)['state'] == 'PARTIAL'
    assert list(bundle['parent'].iterdir()) == []


def test_multiple_items_preserve_framing_and_inventory(bundle):
    second = dict(bundle['manifest'][0], artifact_id='provenance.json', mode=0o600)
    request, sources = staging.prepare(bundle['manifest'] + [second], 'ru', bundle['parent'], 'operator')
    bundle.update(request=request, sources=sources)
    result = run(bundle)
    assert result['state'] == 'READY' and len(result['items']) == 2
    assert all(item['bytes_transferred'] == 262144 for item in result['items'])


def test_connection_spawn_failure_has_durable_receipt(bundle):
    result = staging.transfer(bundle['request'], bundle['sources'], bundle['temporary'] / 'missing-ssh', transport=['/nonexistent/fc-staging-test'])
    assert result['state'] == 'FAILED' and result['exception_class'] == 'FileNotFoundError'


def test_bounded_source_command_and_strict_ssh_trust(bundle):
    argv = staging.command('ru')
    assert len(argv[-1]) < 45000
    assert 'StrictHostKeyChecking=yes' in argv and 'UpdateHostKeys=no' in argv
    assert 'ServerAliveInterval=5' in argv and 'ConnectTimeout=10' in argv
    assert str(bundle['source']) not in argv[-1]
