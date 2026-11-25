from pathlib import Path
import runpy


def test_authenticated_wire_old_links_late_identification_and_captured_callback(tmp_path):
    fixture = Path(__file__).resolve().parents[2] / 'tests/fixtures/mailbox_links_system.py'
    result = runpy.run_path(str(fixture))['qualify'](tmp_path)
    assert result['authenticated_rns'] and result['controller_sigkill']
    assert result['reopened_native_rows'] == 3
    assert not result['restart_protected'] and not result['activation_ready']
