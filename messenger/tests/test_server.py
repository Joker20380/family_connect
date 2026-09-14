from pathlib import Path
import os
import pytest
from messenger.server import unique,validate_volume,read_owned


def test_duplicate_settings_rejected():
    with pytest.raises(ValueError):unique([('allowed_public',[]),('allowed_public',[])])


def test_unmounted_directory_cannot_be_used_as_spool(tmp_path):
    with pytest.raises(ValueError,match='not mounted'):validate_volume(tmp_path,'0'*32)


def test_symlink_volume_and_operator_file_refused(tmp_path):
    link=tmp_path/'link';link.symlink_to(tmp_path,target_is_directory=True)
    with pytest.raises(ValueError):validate_volume(link,'0'*32)
    target=tmp_path/'file';target.write_text('not a key')
    alias=tmp_path/'alias';alias.symlink_to(target)
    with pytest.raises(OSError):read_owned(alias,128)
