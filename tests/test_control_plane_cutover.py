import importlib.util
import json
from pathlib import Path

import pytest


SOURCE = Path(__file__).resolve().parents[1] / 'deploy/friends/restricted/control_plane_cutover.py'
SPEC = importlib.util.spec_from_file_location('private_beta_cutover', SOURCE)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


@pytest.mark.parametrize('stage', ['before-prepare-commit', 'after-prepare-commit', 'before-file-0',
    'after-file-0', 'before-file-1', 'after-file-1', 'before-commit-receipt', 'after-commit-receipt'])
def test_interruption_resumes_forward_without_database_restore(tmp_path, stage):
    first, second, database = (tmp_path / name for name in ('api', 'policy', 'database'))
    first.write_bytes(b'old code')
    second.write_bytes(b'legacy')
    database.write_bytes(b'fixture CLEANED history floors revocations identity')
    first.chmod(0o600)
    second.chmod(0o600)
    writes = [(first, b'new code', 0o600), (second, b'v2', 0o600)]
    before = database.read_bytes()
    def fault(current):
        if current == stage:
            raise OSError('fixture interruption')
    cutover = MODULE.FileCutover(tmp_path / 'state', {'operation': 'one'}, fault=fault)
    with pytest.raises(OSError):
        cutover.apply(cutover.prepare(writes))
    resumed = MODULE.FileCutover(tmp_path / 'state', {'operation': 'one'})
    result = resumed.apply(resumed.prepare(writes))
    assert result['phase'] == 'FILES_COMMITTED'
    assert first.read_bytes() == b'new code' and second.read_bytes() == b'v2'
    assert resumed.apply(resumed.prepare(writes)) == result
    assert database.read_bytes() == before
    assert (tmp_path / 'state/before-0').read_bytes() == b'old code'


def test_unrecognized_partial_state_or_other_operation_never_overwritten(tmp_path):
    target = tmp_path / 'config'
    target.write_bytes(b'old')
    target.chmod(0o600)
    writes = [(target, b'new', 0o600)]
    cutover = MODULE.FileCutover(tmp_path / 'state', {'operation': 'one'})
    transaction = cutover.prepare(writes)
    target.write_bytes(b'unexpected concurrent state')
    with pytest.raises(ValueError):
        cutover.apply(transaction)
    assert target.read_bytes() == b'unexpected concurrent state'
    with pytest.raises(ValueError):
        MODULE.FileCutover(tmp_path / 'state', {'operation': 'two'}).prepare(writes)
    with pytest.raises(ValueError):
        cutover.prepare([(target, b'different inputs', 0o600)])


def test_symlink_is_rejected_without_target_change(tmp_path):
    real = tmp_path / 'real'
    real.write_bytes(b'untouched')
    link = tmp_path / 'link'
    link.symlink_to(real)
    with pytest.raises(ValueError):
        MODULE.FileCutover(tmp_path / 'state', {}).prepare([(link, b'unsafe', 0o600)])
    assert real.read_bytes() == b'untouched'
