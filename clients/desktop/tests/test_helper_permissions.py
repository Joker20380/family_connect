"""Real metadata/profile file modes must not depend on the calling GUI's umask."""
import importlib.util
import os
from pathlib import Path
import stat
import pytest

@pytest.mark.parametrize('name',['awg','tcp'])
@pytest.mark.parametrize('mask',[0o077,0o022,0o000])
def test_metadata_is_readable_and_profile_stays_private(tmp_path,monkeypatch,name,mask):
    path=Path(__file__).resolve().parents[2]/'linux'/f'{name}-helper.py'
    spec=importlib.util.spec_from_file_location('permissions_'+name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    monkeypatch.setattr(module,'ROOT',tmp_path)
    previous=os.umask(mask)
    try:
        for filename,mode in [('public.json',0o644),('private.conf',0o600)]:
            target=tmp_path/filename
            module.write(target,'synthetic',mode)
            assert stat.S_IMODE(target.stat().st_mode)==mode
            module.write(target,'replacement',mode)
            assert stat.S_IMODE(target.stat().st_mode)==mode
            assert target.read_text()=='replacement'
    finally:os.umask(previous)
