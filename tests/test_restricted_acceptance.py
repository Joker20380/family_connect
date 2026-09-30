import copy
import importlib.util
from pathlib import Path

import pytest


SPEC = importlib.util.spec_from_file_location('restricted_acceptance', Path(__file__).resolve().parents[1] / 'pilot/android-restricted/acceptance.py')
ACCEPTANCE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ACCEPTANCE)


def evidence():
    return dict(prepared=[{'events': ['bootstrap_cache_stored']}], recovered=[{
        'events': ['bootstrap_normal_control_unavailable', 'bootstrap_cache_loaded',
                   'bootstrap_carrier_connected', 'bootstrap_family_auth', 'bootstrap_descriptor_received',
                   'bootstrap_closed_before_dedicated', 'dedicated_data_ready', 'vpn_packet_ready'],
        'packet': {'dns': 3, 'tcp_peak': 4, 'peak': 4, 'udp_denied': 1, 'ipv6_denied': 1,
                   'mux': {'MaxActiveStreams': 4, 'ReceiveHighWater': 16384, 'SendHighWater': 16384, 'RetainedHighWater': 262144},
                   'resources': {'carrier_send_queue': 0, 'carrier_receive_queue': 0}}}],
        gateway=[{'event': name} for name in ['bootstrap_seed_ready', 'bootstrap_family_auth', 'CREATING', 'CREATED',
                 'GATEWAY_JOINING', 'READY', 'CLIENT_ISSUED', 'bootstrap_handoff', 'family_auth', 'ACTIVE', 'dedicated_resources_closed']],
        browser=[{'controlled_content': True, 'vpn_active': True}] * 2,
        probes={'vpn_active': True, 'nxdomain': True, 'ipv6_failed_closed': True,
                'https': [{'status': 200, 'tls_verified': True}] * 2},
        failed={'vpn_active': True, 'session_failed': True, 'ordinary_tcp_failed': True, 'owner_reports_unavailable': True}, duration=540)


def test_complete_evidence_passes():
    ACCEPTANCE.validate(**evidence())


def test_auto_requires_real_normal_exhaustion_and_protected_underlay(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(SPEC.origin).parent))
    sample = evidence()
    sample['recovered'][0]['events'].remove('bootstrap_normal_control_unavailable')
    sample['recovered'][0].update(state=2, protect_ok=10, protect_denied=0, underlay_dns=4)
    events = []
    for candidate in ('awg', 'wg', 'tcp', 'restricted'):
        events.append(dict(event='candidate_attempted', candidate=candidate, state='CONNECTING'))
        events.append(dict(event='candidate_succeeded' if candidate == 'restricted' else 'candidate_failed',
                           candidate=candidate, category='TRANSPORT_UNAVAILABLE',
                           state='CONNECTED' if candidate == 'restricted' else 'CONNECTING'))
    ACCEPTANCE.validate(**sample, orchestrator=events)
    with pytest.raises(RuntimeError):
        ACCEPTANCE.validate(**sample, orchestrator=events[2:])
    sample['recovered'].append(copy.deepcopy(sample['recovered'][0]))
    sample['recovered'][-1]['events'] = []
    sample['recovered'][-1]['underlay_dns'] += 1
    with pytest.raises(RuntimeError, match='underlay DNS grew'):
        ACCEPTANCE.validate(**sample, orchestrator=events)


def test_route_parser_rejects_duplicate_owners():
    line = 'NetworkAgentInfo{ ni{VPN CONNECTED sessionId=Family Connect'
    assert not ACCEPTANCE.vpn_routes(line+'\n'+line, 'Family Connect')['active']


def test_debug_suffix_does_not_change_java_component_namespace():
    source = Path(SPEC.origin).read_text()
    assert "PACKAGE + '/com.familyconnect.app.RestrictedDiagnosticActivity'" in source
    assert "b'Error type' in result" in source


def test_combined_cellular_vpn_and_stale_requests():
    active = 'NetworkAgentInfo{ ni{VPN CONNECTED extra: } DnsAddresses: [ /10.79.0.1 ] 0.0.0.0/0 ::/0 Transports: CELLULAR|VPN sessionId=Family restricted diagnostic, bypassable=false Uids: <{0-99999}>'
    assert all(ACCEPTANCE.vpn_routes(active).values())
    assert not ACCEPTANCE.vpn_routes('NetworkRequest [ Transports: VPN ]')['active']


def test_localized_controlled_browser_content_and_network_errors():
    assert ACCEPTANCE.controlled_page('example.org Este dominio está destinado al uso en ejemplos de documentación', 'example.org')
    assert ACCEPTANCE.controlled_page('example.com Example Domain', 'example.com')
    assert not ACCEPTANCE.controlled_page('example.com ERR_CONNECTION_RESET Example Domain', 'example.com')
    assert not ACCEPTANCE.controlled_page('other.invalid Example Domain', 'example.com')


def test_locked_or_sleeping_phone_cannot_start_live_run():
    assert ACCEPTANCE.screen_ready('mIsShowing=false', 'mWakefulness=Awake')
    assert not ACCEPTANCE.screen_ready('mIsShowing=true', 'mWakefulness=Awake')
    assert not ACCEPTANCE.screen_ready('mIsShowing=false', 'mWakefulness=Asleep')


@pytest.mark.parametrize('missing', ['bootstrap_normal_control_unavailable', 'bootstrap_cache_loaded',
                                     'bootstrap_closed_before_dedicated', 'dedicated_data_ready', 'vpn_packet_ready'])
def test_missing_lifecycle_proof_rejected(missing):
    sample = evidence()
    sample['recovered'][0]['events'].remove(missing)
    with pytest.raises(RuntimeError):
        ACCEPTANCE.validate(**sample)


@pytest.mark.parametrize('field', ['vpn_active', 'session_failed', 'ordinary_tcp_failed', 'owner_reports_unavailable'])
def test_failure_must_remain_closed(field):
    sample = evidence()
    sample['failed'][field] = False
    with pytest.raises(RuntimeError):
        ACCEPTANCE.validate(**sample)


@pytest.mark.parametrize('field', ['dns', 'tcp_peak', 'udp_denied', 'ipv6_denied'])
def test_no_inferred_packet_success(field):
    sample = evidence()
    sample['recovered'][0]['packet'][field] = 0
    with pytest.raises(RuntimeError):
        ACCEPTANCE.validate(**sample)


def test_early_vpn_duplicate_and_short_smoke_rejected():
    for change in ('early', 'duplicate', 'short'):
        sample = copy.deepcopy(evidence())
        if change == 'early':
            sample['recovered'][0]['events'].reverse()
        elif change == 'duplicate':
            sample['recovered'][0]['events'].append('vpn_packet_ready')
        else:
            sample['duration'] = 30
        with pytest.raises(RuntimeError):
            ACCEPTANCE.validate(**sample)


def test_gateway_must_be_ready_before_descriptor_and_closed():
    for fault in ('early', 'cleanup'):
        sample = evidence()
        if fault == 'early':
            sample['gateway'][5], sample['gateway'][6] = sample['gateway'][6], sample['gateway'][5]
        else:
            sample['gateway'].pop()
        with pytest.raises(RuntimeError):
            ACCEPTANCE.validate(**sample)


@pytest.mark.parametrize('field,value', [('MaxActiveStreams', 33), ('ReceiveHighWater', 65537),
                                        ('SendHighWater', 16385), ('RetainedHighWater', 7 * 1024 * 1024)])
def test_native_resource_limits_are_acceptance_guards(field, value):
    sample = evidence()
    sample['recovered'][0]['packet']['mux'][field] = value
    with pytest.raises(RuntimeError):
        ACCEPTANCE.validate(**sample)
