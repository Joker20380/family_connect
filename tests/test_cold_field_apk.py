import zipfile

import pytest

from scripts.prepare_cold_field_apk import check_window, compare_payload, entries


def test_window_keeps_candidate_and_handoff_budgets():
    locator = dict(locator_sha256='a'*64, expires_at=1500)
    ready = dict(phase='LOCATOR_VERIFIED_SEED_CONNECTED', locator_sha256='a'*64, expires_at=1500, observed_at=1200)
    check_window(locator, ready, now=1201, handoff_seconds=60)
    for change in ({'observed_at': 1000}, {'locator_sha256': 'b'*64}, {'expires_at': 1501}, {'phase': 'STOPPED'}):
        with pytest.raises(ValueError):
            check_window(locator, dict(ready, **change), now=1201, handoff_seconds=60)
    with pytest.raises(ValueError):
        check_window(locator, ready, now=1241, handoff_seconds=60)


def test_signature_does_not_hide_changed_payload(tmp_path):
    source, signed = tmp_path/'source.apk', tmp_path/'signed.apk'
    with zipfile.ZipFile(source, 'w') as archive:
        archive.writestr('classes.dex', b'accepted')
        archive.writestr('assets/provisioning/nl-amsterdam-1.json', b'locator')
    for replacement in (False, True):
        with zipfile.ZipFile(signed, 'w') as archive:
            for name, raw in entries(source).items():
                archive.writestr(name, b'changed' if replacement and name == 'classes.dex' else raw)
            archive.writestr('META-INF/SIGNER.SF', b'signature')
        if replacement:
            with pytest.raises(ValueError):
                compare_payload(source, signed)
        else:
            compare_payload(source, signed)


def test_duplicate_zip_entries_rejected(tmp_path):
    apk = tmp_path/'duplicate.apk'
    with zipfile.ZipFile(apk, 'w') as archive:
        archive.writestr('classes.dex', b'one')
        with pytest.warns(UserWarning):
            archive.writestr('classes.dex', b'two')
    with pytest.raises(ValueError):
        entries(apk)
