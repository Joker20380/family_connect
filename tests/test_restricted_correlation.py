import copy
from pathlib import Path
import re

import pytest

from scripts import correlate_restricted as diagnostic


TAG = "ab" * 32
CONNECTION = "11111111-1111-1111-1111-111111111111"
INCIDENT = "22222222-2222-2222-2222-222222222222"
SUPPORT = "FC-YHQB-9VJN"


def entry(sequence=1, reason="NONE"):
    return dict(session_tag=TAG, sequence=sequence, timestamp_ms=1000 + sequence,
                stage="WEBSOCKET", state="ESTABLISHED", reason=reason, tx=1, rx=2,
                private_key="DO_NOT_EXPORT", room_url="DO_NOT_EXPORT", close_reason="DO_NOT_EXPORT")


def fixture():
    session = dict(session_tag=TAG, correlation_status="VALID", device_support_id=SUPPORT,
                   connection_id=CONNECTION, incident_id=INCIDENT,
                   lifecycle=dict(trace=[entry()]))
    return {"ring": {"restricted_session": session}}, [{"event": "restricted_trace", "trace": entry()}]


@pytest.mark.parametrize("lookup", [TAG, CONNECTION, INCIDENT, SUPPORT])
def test_lookup_from_every_identifier_and_privacy(lookup):
    client, server = fixture()
    result = diagnostic.correlate([client], server, lookup)
    assert result["sessions"][0]["correlation_proven"]
    assert not result["sessions"][0]["owner_lifecycle_complete"]
    assert "DO_NOT_EXPORT" not in str(result)


@pytest.mark.parametrize("tag", ["", "ab" * 16, "z" * 64, None])
def test_invalid_or_missing_tag_does_not_correlate(tag):
    client, server = fixture()
    client["ring"]["restricted_session"]["session_tag"] = tag
    if tag is None:
        assert not diagnostic.correlate([client], server, SUPPORT)["sessions"]
    else:
        with pytest.raises(ValueError):
            diagnostic.correlate([client], server, SUPPORT)


def test_ambiguous_binding_and_sequence_rejected():
    client, server = fixture()
    altered = copy.deepcopy(client)
    altered["ring"]["restricted_session"]["connection_id"] = INCIDENT
    with pytest.raises(ValueError, match="ambiguous"):
        diagnostic.correlate([client, altered], server, SUPPORT)
    server.append({"event": "restricted_trace", "trace": entry(reason="CARRIER_ERROR")})
    with pytest.raises(ValueError, match="conflicting"):
        diagnostic.correlate([client], server, SUPPORT)


def test_gaps_and_first_failure_separate_from_cleanup():
    client, server = fixture()
    server += [{"event": "restricted_trace", "trace": entry(2, "SIGNAL_WS_CLOSE")},
               {"event": "restricted_trace", "trace": entry(4, "RECOVERY_CLEANUP_FAILED")}]
    result = diagnostic.correlate([client], server, SUPPORT)["sessions"][0]
    assert result["first_server_failure"]["reason"] == "SIGNAL_WS_CLOSE"
    assert result["server_sequence_gaps"] and not result["correlation_proven"]


def test_native_android_operator_allowlists_match():
    root = Path(__file__).resolve().parents[1]
    native = (root / "carrier/sessiontrace/trace.go").read_text()
    android = (root / "clients/android/app/src/main/java/com/familyconnect/app/RestrictedTrace.java").read_text()
    for name in ("STAGES", "STATES", "REASONS"):
        expected = getattr(diagnostic, name)
        assert re.search(r"const " + name.title() + r' = "([^"]+)"', native)[1] == expected
        assert re.search(name + r'="([^"]+)"', android)[1] == expected
    assert re.search(r'const BrokerReasons = "([^"]+)"', native)[1] == diagnostic.BROKER_REASONS


@pytest.mark.parametrize('reason', ['RELIABLE_HANDSHAKE_TIMEOUT', 'RELIABLE_FRAME_TIMEOUT', 'RELIABLE_RETRY_EXHAUSTED'])
def test_reliable_first_failure_survives_cleanup_and_redaction(reason):
    client, server = fixture()
    first = entry(2, reason)
    first.update(stage='CARRIER', state='FAILED', reliable_pending=8, reliable_retries=8,
                 reliable_age_ms=9000, reliable_ack_age_ms=2000, reliable_progress_age_ms=9000,
                 reliable_ack_received=17, reliable_sacked=0, reliable_payload='DO_NOT_EXPORT')
    client['ring']['restricted_session']['lifecycle'].update(first_failure=first, trace=[entry(), first])
    close = dict(entry(3), stage='LOCAL_CLOSE', state='STARTED')
    server += [{'event': 'restricted_trace', 'trace': item} for item in (first, close, entry(4, 'FAMILY_TLS_ERROR'))]
    result = diagnostic.correlate([client], server, SUPPORT)['sessions'][0]
    assert result['first_client_failure'] == result['first_server_failure']
    assert result['first_client_failure']['reason'] == reason
    assert result['first_client_failure']['reliable_pending'] == 8
    assert result['first_client_failure']['reliable_sacked'] == 0
    assert result['first_client_failure']['reliable_ack_received'] == 17
    assert 'DO_NOT_EXPORT' not in str(result)


def test_large_sequence_is_bounded_and_broker_reason_preserved():
    client, server = fixture()
    server[0]["trace"]["sequence"] = 9007199254740991
    server[0]["trace"]["broker_reason"] = "provider_timeout"
    result = diagnostic.correlate([client], server, SUPPORT)["sessions"][0]
    assert result["server_sequence_gaps"]
    assert result["server"][0]["broker_reason"] == "provider_timeout"


def test_different_sessions_do_not_share_bindings():
    client, server = fixture()
    second = copy.deepcopy(client)
    session = second["ring"]["restricted_session"]
    session["session_tag"] = "cd" * 32
    session["lifecycle"]["trace"][0]["session_tag"] = session["session_tag"]
    session["connection_id"] = "33333333-3333-3333-3333-333333333333"
    assert len(diagnostic.correlate([client, second], server, SUPPORT)["sessions"]) == 2
    result = diagnostic.correlate([client, second], server, CONNECTION)["sessions"]
    assert len(result) == 1 and result[0]["session_tag"] == TAG
