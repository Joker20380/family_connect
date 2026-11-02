import importlib.util
import os
from pathlib import Path
import stat

import pytest

spec=importlib.util.spec_from_file_location('load_installer',Path(__file__).parents[1]/'deploy/server-load/install.py')
installer=importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


def test_monitor_directory_is_traversable_under_private_umask(tmp_path,monkeypatch):
    root=tmp_path/'monitor'
    monkeypatch.setattr(installer,'ROOT',root)
    previous=os.umask(0o077)
    try:
        installer.prepare_root()
        assert stat.S_IMODE(root.stat().st_mode)==0o755
        private=root/'state';private.mkdir(mode=0o700)
        root.chmod(0o700)
        installer.prepare_root()
        assert stat.S_IMODE(root.stat().st_mode)==0o755
        assert stat.S_IMODE(private.stat().st_mode)==0o700
    finally:os.umask(previous)


def test_monitor_directory_rejects_symlink(tmp_path,monkeypatch):
    private=tmp_path/'private';private.mkdir(mode=0o700)
    root=tmp_path/'monitor';root.symlink_to(private,target_is_directory=True)
    monkeypatch.setattr(installer,'ROOT',root)
    with pytest.raises(ValueError):installer.prepare_root()
    assert stat.S_IMODE(private.stat().st_mode)==0o700
