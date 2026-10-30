from pathlib import Path

import pytest

from scripts.publisher_recovery_source import MEMBERS, directory_projection


def test_recovery_projection_rejects_unaccepted_atomic_store():
    with pytest.raises(ValueError, match='source mismatch'):
        directory_projection(b'approximate publisher source')


def test_recovery_projection_members_are_bounded():
    assert len(MEMBERS) == 6
    assert len(set(MEMBERS)) == len(MEMBERS)
    for name in MEMBERS:
        assert '..' not in Path(name).parts
        assert Path('carrier', name).is_file()
        assert name.startswith(('bootstrap/recovery_', 'cmd/publisher-recovery/'))
