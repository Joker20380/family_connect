"""Seal bounded bootstrap findings; never claim tester network or signed installation."""
import json
import subprocess
from prepare import ROOT, WORK, BASE, digest


def main():
    inputs=json.loads((WORK/'input-evidence.json').read_text())
    api=json.loads((WORK/'api-readback.json').read_text())
    journal=json.loads((WORK/'api-journal-scope.json').read_text())
    receipt=json.loads((WORK/'build/receipt.json').read_text())
    unsigned=json.loads((WORK/'unsigned-check.json').read_text())
    native_log=(WORK/'native-focused-tests.log').read_text()
    assert native_log.count('ok  ')==2 and 'FAIL' not in native_log
    assert receipt['tests']==175 and receipt['result']=='PASS_LOCAL_BUILD_JVM'
    assert unsigned['candidate']['sha256']==receipt['apk_sha256']
    signing=json.loads((WORK/'delivery/signing-receipt.json').read_text())
    signed_apk=WORK/'delivery/FamilyConnect-0.1.18-beta96-bootstrap.apk'
    assert signing['result']=='SIGNED_PRIVATE_BOOTSTRAP_FIELD_NOT_RUN'
    assert digest(signed_apk)==signing['signed']['sha256']
    assert signing['signed']['signer_sha256']==signing['baseline']['signer_sha256']
    assert signing['unsigned']['sha256']==receipt['apk_sha256']
    older=ROOT/'state-client-build/rtp-deadline-20261020/normal94/android-source'
    names=['FriendsRestricted','RestrictedBootstrap','RestrictedCache','FriendsAccessAndroid','FriendsReadinessProtocol',
           'ReadinessBootstrapRoute','ControlRnsAndroid','ChatNetworkAndroid','DiagnosticRing','RestrictedTunnelEngine']
    same={}
    for name in names:
        path='clients/android/app/src/main/java/com/familyconnect/app/'+name+'.java'
        assert (older/path).read_bytes()==(BASE/'android-source'/path).read_bytes()
        same[path]=digest(older/path)
    path='clients/android/app/src/main/python/fc_rns_transport.py'
    assert (older/path).read_bytes()==(BASE/'android-source'/path).read_bytes()
    same[path]=digest(older/path)
    record=dict(schema=1,support_id='FC-ZMVK-MM7C',inputs=inputs['inputs'],scopes=inputs['scopes'],
        deduplicated_events=inputs['unique_events'],historical_exact_cause='NOT_ESTABLISHED',
        historical_stage='FETCH_FAILED_FROM_RESTRICTED_BOOTSTRAP_REFRESH_EXCEPTION_BEFORE_NATIVE_BEGIN_READY',
        historical_missing='Transport exception/stage/route and cache validator/fingerprint at failed selection absent in94 export',
        server_receipts=api['receipts'],server_journal=journal,baseline94_and95_identical=same,
        local_defect='Python RNS socket availability error becomes generic PyException; challenge wraps INTERNAL with availability=false; valid cache not selected',
        fix='Typed availability only for failed socket bind/connect and explicit RNS wait deadline; existing validator chooses unexpired cache. Trust/auth/protocol/cancel remain terminal; no proof replay.',
        diagnostics='Bounded operation/stage/error/status/network generation, original connection scope, cache source/age/fingerprint/expiry/bundle validation and document expiry checks in ring and incident JSON',
        jvm_tests=175,python_bridge_tests=6,network_fixture='PASS_ACTUAL_JAVA_METHOD_WITH_ANDROID_STUBS_NOT_PHYSICAL',
        native_security_recovery='PASS_8_FOCUSED_NATIVE_TESTS_PLUS_SUBTESTS_WITH_RACE; unchanged native95, previous1011 checks retained; Java recovery tests rerun',
        native_focused_log_sha256=digest(WORK/'native-focused-tests.log'),
        unsigned=unsigned['candidate'],patch_sha256=receipt['patch_sha256'],native_sha256=receipt['native_sha256'],
        owner_validation='BASELINE95_READBACK_ONLY_CANDIDATE_NOT_INSTALLED',tester_cellular_validation='NOT_RUN',
        signing='SIGNED_PRIVATE_BOOTSTRAP_FIELD_NOT_RUN',signed=signing['signed'],signed_apk=str(signed_apk.relative_to(ROOT)),
        signing_receipt_sha256=digest(WORK/'delivery/signing-receipt.json'),
        private_tester_handoff='OWNER_REQUESTED_FILE_HANDOFF_NOT_CONFIRMED_RECEIVED_OR_INSTALLED',
        installation='NOT_RUN',public_release=False,pushed=False,
        current_gateway_sha256='272bbc3fed90bbcf740a58f812e93511c976c114e2190f2c8711b55fa0dfb0c4',current_profile='LEGACY64',credit128=False,
        remaining_dependency='Missing/expired/revoked/invalid cache still needs approved authenticated readiness refresh (direct HTTPS or existing RNS); seed cannot issue expired credentials. Live seed liveness not guaranteed by cached directory.',
        repaired_local_failures=['Initial RU query used Product DB instead of Friends DB; no writes',
            'Read-only receipt query corrected challenge_id to actual correlation column',
            'Gradle sandbox loopback blocked; rerun outside sandbox',
            'Exact source verifier required baseline95 Git metadata/work-tree binding; gate preserved',
            'Negative auth fixture corrected to actual challengeStatus401/403 ChallengeFailure shape; full suite rerun'])
    upgrade_path=WORK/'upgrade-receipt.json'
    if upgrade_path.exists():
        upgrade=json.loads(upgrade_path.read_text())
        assert upgrade['exit']==0 and upgrade['after']['code']==96
        assert upgrade['after']['apk_sha256']==signing['signed']['sha256']
        assert upgrade['before']['uid']==upgrade['after']['uid']
        record['installation']='OWNER_IN_PLACE95_TO96_VERIFIED'
        record['upgrade']=upgrade
        record['owner_validation']='INSTALLED96_UID_PRESERVED_POST_UPDATE_READY_CONNECT_NOT_RUN'
        after_identity=WORK/'identity-after.json'
        if after_identity.exists():
            before=json.loads((WORK/'identity-before.json').read_text())
            after=json.loads(after_identity.read_text())
            assert all(before[key]==after[key] for key in ('identity_bindings_sha256','support_id_sha256','owner_record_count'))
            assert not after['owner_revoked']
            record['owner_identity']='FRESH_SERVER_BINDINGS_AND_SUPPORT_UNCHANGED_DEVICE_PROOF_PENDING'
    (WORK/'result.json').write_text(json.dumps(record,indent=2))
    destination=ROOT/'docs/releases/2026-10-20-volgograd-mobile-bootstrap.evidence.json'
    operation='Add File: '+str(destination)+'\n'
    if destination.exists():operation='Update File: '+str(destination)+'\n@@\n'+''.join('-'+line+'\n' for line in destination.read_text().splitlines())
    subprocess.run(['apply_patch'],input='*** Begin Patch\n*** '+operation+''.join('+'+line+'\n' for line in json.dumps(record,indent=2).splitlines())+'*** End Patch\n',text=True,check=True)
    print(json.dumps(dict(local='PASS',historical='UNRESOLVED_TRANSPORT_CLASS',signed=signing['signed']['sha256'],installation=record['installation'],field='NOT_RUN',patch=receipt['patch_sha256'])))


if __name__=='__main__':main()
