"""Seal redacted support receipts, without controlling phone/services or uploading."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
WORK = ROOT / 'state-client-build/support-cadence99-20261021'
PRIOR = ROOT / 'state-client-build/support-automation-20261021'
sys.path.insert(0, str(ROOT / 'tests/fixtures/speed_candidate'))
from prepare import write, digest


def main():
    build = json.loads((WORK / 'build/receipt.json').read_text())
    signing = json.loads((WORK / 'delivery/signing-receipt.json').read_text())
    install = json.loads((WORK / 'install-receipt.json').read_text())
    verification = json.loads((WORK / 'verification-connected.json').read_text())
    online = json.loads((WORK / 'online-repeat-summary.json').read_text())
    phone = json.loads((WORK / 'owner-final.json').read_text())
    state = json.loads((WORK / 'final99-readback.json').read_text())
    inventory = json.loads((WORK / 'build/source-inventory.json').read_text())
    assert all(digest(WORK / 'android-source' / name) == expected for name, expected in inventory.items())
    assert state['phone']['apk_sha256'] == signing['signed']['sha256']
    assert state['phone']['native_sha256'] == build['native_sha256']
    assert phone['version_code'] == state['phone']['code'] == 99
    session = phone['restricted_session']
    profile = [row['diagnostic'] for row in verification['gateway']['records'] if row['event'] == 'session_profile']
    assert len(profile) == 1 and profile[0]['session_tag'] == session['session_tag']
    fields = ('session_tag','speed_profile','mux_profile','mux_window','reliable_limits','protocol_errors','protocol_error_reasons','terminal_reason','retransmissions','retry_bytes')
    artifact = WORK / 'delivery/FamilyConnect-0.1.18-beta99-support.apk'
    paths = [WORK / name for name in (
        'build/receipt.json','build/source-inventory.json','delivery/signing-receipt.json',
        'install-intent.json','install-receipt.json','control-profile.json','control-connect.json',
        'verification-connected.json','online-repeat-summary.json','owner-final.json',
        'final99-readback.json','final-python-tests.log')]
    paths += [PRIOR / name for name in ('verification-p0.json','verification-p0-startup.json',
                                       'owner-followup.json','owner-later.json','online-http-statuses.json')]
    result = dict(schema=1, date='2026-10-21', scope='owner support automation, not speed admission',
                  android=dict(version_code=99, version=signing['signed']['version'],
                               installed=True, public_or_tester_distribution=False,
                               apk_path=str(artifact.relative_to(ROOT)), sha256=signing['signed']['sha256'],
                               signer_sha256=signing['signed']['signer_sha256'],
                               native_sha256=build['native_sha256'], native_identical_to98=True,
                               source_inventory=build['source_inventory'],
                               update_interval_utc=[install['before']['utc'],install['after']['utc']]),
                  tests=dict(jvm=build['tests'], python=41, native='unchanged98; prior focused race retained'),
                  android_final={key:phone.get(key) for key in ('state','restricted_readiness','vpn_capture_open','network_class')},
                  session={key:session.get(key) for key in fields},
                  gateway_startup={key:profile[0].get(key) for key in fields if key in profile[0]},
                  gateway_final=state['gateway'],
                  identity_preserved=verification['identity_preserved'],
                  online=online,
                  resource_sample=state['android_resources'],
                  safety=dict(no_new_bulk_speed_load=True, no_task_gateway_restart=True,
                              no_security_state_change=True, http_unchanged_since98=True,
                              other_clients_not_enrolled=True, no_push_or_public_release=True),
                  limits=['98 UNAVAILABLE cause unknown; cooldown bug proven locally, not retroactively attributed',
                          'unknown_stream branch is not proof of frame provenance, harm or historical17 cause',
                          'short observation, not all-day availability or automatic network-loss recovery',
                          'online relies on live native statistics; desktop uploaders not shipped',
                          'USB one-hour/process-local consent; online separate seven-day opt-in'],
                  evidence_sha256={str(path.relative_to(ROOT)):digest(path) for path in paths})
    write(WORK / 'manifest.json', json.dumps(result, indent=2) + '\n')
    write(ROOT / 'docs/releases/2026-10-21-owner-support-automation.evidence.json', json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(result='SEALED', version=99, online=online['result'],
                         source_inventory=build['source_inventory'], sha256=digest(WORK / 'manifest.json'))))


if __name__ == '__main__':
    main()
