import json
from pathlib import Path
import pytest

from scripts.verify_desktop_reference import MANIFEST, digest, local_path, verify


def test_gtk_connection_state_labels_are_exact_reference_text():
    import ast
    root=Path(__file__).resolve().parents[1]
    tree=ast.parse((root/'clients/desktop/app.py').read_text())
    assignment=next(item for item in tree.body if isinstance(item,ast.Assign) and
                    any(isinstance(target,ast.Name) and target.id=='STATE_LABELS' for target in item.targets))
    labels=ast.literal_eval(assignment.value)
    contract=json.loads((root/'clients/shared/android106-ui.json').read_text())
    for state,key in {'DISCONNECTED':'off','CONNECTING':'connecting','CONNECTED':'on',
                      'RESTORING':'restoring','STOPPING':'ui_disconnecting','FAILED':'unable_connect'}.items():
        assert labels[state]==tuple(contract['strings'][language][key] for language in ('ru','en'))
    assignment=next(item for item in tree.body if isinstance(item,ast.Assign) and
                    any(isinstance(target,ast.Name) and target.id=='NAV_LABELS' for target in item.targets))
    labels=ast.literal_eval(assignment.value)
    for page,key in {'status':'dashboard_status','messenger':'dashboard_chats',
                     'route':'dashboard_route_short','settings':'dashboard_settings_short'}.items():
        assert labels[page]==tuple(contract['strings'][language][key] for language in ('ru','en'))


def test_readiness_semantic_port_uses_exact_accepted_sources():
    root = Path(__file__).resolve().parents[1]
    reference = json.loads((root / MANIFEST).read_text())
    contract = json.loads((root / 'clients/shared/desktop-readiness106.json').read_text())
    for path, expected in contract['source_files'].items():
        assert reference['android_ui_and_handlers'][path] == expected
    capsule = local_path(root, reference['reference']['source'])
    for path, expected in contract['rns_source_files'].items():
        assert digest(local_path(capsule, path)) == expected
    for path in contract['implementation'].values():
        assert local_path(root, path).is_file()
    assert contract['invariants']['profiles'] == ['P0', 'P1']
    assert not contract['invariants']['native_proposal_is_durable']


def test_supported_shared_sources_match_accepted_inventory():
    assert verify()["result"] == "PASS"


def test_restricted_chat_contract_has_exact_services_and_bounds():
    from scripts.verify_desktop_reference import ROOT
    contract = json.loads((ROOT / 'clients/shared/android106-chat.json').read_text())
    reference = json.loads((ROOT / MANIFEST).read_text())
    assert contract['source_inventory_sha256'] == reference['reference']['source_inventory_sha256']
    assert contract['services'] == ['chat-api', 'chat-mailbox']
    assert contract['api_paths'] == ['/friends/chat/challenge', '/friends/chat/register']
    assert contract['maximum_leases'] == 8 and contract['maximum_session_service_streams'] == 4
    assert contract['authorization_statuses'] == [400, 401, 403] and contract['conflict_status'] == 409
    assert (contract['request_bytes'], contract['response_bytes'], contract['maximum_duration_ms']) == (8192, 16384, 30000)
    assert contract['redirects'] is False and contract['proxy_environment'] is False
    assert contract['api_origin'] == 'https://185.251.89.19:8443'
    for path in contract['implementation']:
        assert local_path(ROOT, path).is_file()


@pytest.mark.parametrize("name", ["../escape", "/etc/passwd", "carrier/../../escape", "..\\escape"])
def test_manifest_paths_cannot_escape(tmp_path, name):
    with pytest.raises(ValueError):
        local_path(tmp_path, name)


def test_manifest_rejects_symlink_escape(tmp_path):
    (tmp_path / "link").symlink_to(tmp_path.parent)
    with pytest.raises(ValueError):
        local_path(tmp_path, "link/escape")


def test_source_drift_is_not_a_match(tmp_path):
    source = tmp_path / "core.go"
    source.write_text("package core\n")
    manifest = tmp_path / MANIFEST
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps({"schema": 1, "build_tags": [], "desktop_adaptations": {},
                                    "shared_sources": {"core.go": {"sha256": digest(source)}}}))
    assert verify(tmp_path)["result"] == "PASS"
    source.write_text("package changed\n")
    assert verify(tmp_path)["failures"] == ["core.go"]
    source.unlink()
    assert verify(tmp_path)["failures"] == ["core.go"]


def test_experimental_build_tags_are_rejected(tmp_path):
    manifest = tmp_path / MANIFEST
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps({"schema": 1, "build_tags": ["fc_messenger_lab"]}))
    with pytest.raises(ValueError):
        verify(tmp_path)


def test_visual_contract_is_reproducible_when_capsule_is_available():
    from scripts.extract_desktop_contract import extract
    from scripts.verify_desktop_reference import ROOT

    manifest = json.loads((ROOT / MANIFEST).read_text())
    if not (ROOT / manifest["reference"]["source"]).exists():
        pytest.skip("reference capsule is not distributed in CI")
    contract = json.loads((ROOT / "clients/shared/android106-ui.json").read_text())
    assert extract() == contract
    assert contract["palette"]["background"] == "#071211"
    assert contract["navigation"] == ["home", "messenger", "route", "settings"]
