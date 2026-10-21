from pathlib import Path
import runpy


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'tests/fixtures/support_automation'


def test_historical98_replay_does_not_follow_mutable_current_uploader():
    prepare = runpy.run_path(str(FIXTURE / 'prepare.py'))
    source = prepare['frozen_file'](prepare['JAVA'] / 'SupportAutomation.java')
    assert source.endswith('\n')
    assert 'nextUpload=now+60000' in source
    assert 'SupportUploadSchedule' not in source
    for name in ('SupportSnapshot.java', 'SupportAccess.java', 'OwnerSupportProvider.java'):
        assert 'package com.familyconnect.app;' in prepare['frozen_file'](prepare['JAVA'] / name)


def test99_delta_does_not_modify_transport_or_security_identity():
    patch = (FIXTURE / 'android98-to99.patch').read_text()
    paths = [line.removeprefix('+++ b/') for line in patch.splitlines() if line.startswith('+++ b/')]
    assert len(paths) == 5
    assert all(path.startswith('clients/android/') for path in paths)
    assert not any(word in path for path in paths for word in ('Identity', 'Bootstrap', 'Recovery', 'SpeedProfile'))
    assert 'versionCodeOverride = 99' in patch
