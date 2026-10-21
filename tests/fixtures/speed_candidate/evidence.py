"""Index existing local receipts and every retained attempt; no network or tests."""

import datetime
import json
from prepare import ROOT, WORK, FIXTURE, digest, write


def load(name):
    return json.loads((WORK / name).read_text())


def log_summary(path):
    records = []
    unparsed = 0
    for line in path.read_text().splitlines():
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            unparsed += 1
    return dict(
        path=str(path.relative_to(WORK)), sha256=digest(path), bytes=path.stat().st_size,
        test_pass=sum(row.get('Action') == 'pass' and bool(row.get('Test')) for row in records),
        test_fail=sum(row.get('Action') == 'fail' and bool(row.get('Test')) for row in records),
        test_skip=sum(row.get('Action') == 'skip' and bool(row.get('Test')) for row in records),
        failed_names=sorted({row.get('Test', row.get('Package', '')) for row in records if row.get('Action') == 'fail'}),
        non_json_lines=unparsed,
    )


def main():
    phase_names = ('original96','P0a','P1a','P2a','P2b','P1b','P0b')
    assert sorted(path.name for path in WORK.glob('phase-*')) == sorted('phase-'+phase for phase in phase_names), 'Reconcile any additional physical phases explicitly'
    baseline = load('baseline.json')
    build = load('build/receipt.json')
    gateway = load('gateway-build.json')
    unsigned = WORK / 'build/android/app/outputs/apk/privateBeta/app-privateBeta-unsigned.apk'
    assert digest(unsigned) == build['apk_sha256']
    assert digest(WORK / 'gateway-speed') == gateway['sha256']
    entry, final = load('entry-readback.json'), load('final-readback.json')
    assert entry['gateway']['sha256'] == final['gateway']['sha256'] == baseline['gateway_sha256']
    signing=load('delivery/signing-receipt.json')
    signed=WORK/'delivery/FamilyConnect-0.1.18-beta97-speed.apk'
    assert digest(signed)==signing['signed']['sha256']
    current=load('owner-p0-final-readback.json')
    assert current['phone']['apk_sha256']==signing['signed']['sha256']
    assert current['gateway']['sha256']==gateway['sha256']
    assert current['gateway']['state']['InvocationID']==load('p0b-ended-readback.json')['gateway']['state']['InvocationID']
    assert current['gateway']['state']['InvocationID']!=load('p0b-preflight-readback.json')['gateway']['state']['InvocationID']
    assert current['gateway']['operator']['speed-profile']=='P0'
    original=load('phase-original96/normalized.json')
    requests=[dict(phase=phase,**json.loads(line)) for phase in phase_names for line in (WORK/('phase-'+phase)/'requests.jsonl').read_text().splitlines()]
    p0=load('phase-P0a/phase-analysis.json')
    analyses={phase:load('phase-'+phase+'/phase-analysis.json') for phase in phase_names}
    contrasts = {}
    for kind,pairs in (('q1',(('P1a','P2a'),('P1b','P2b'))),
                       ('windows',(('P0a','P1a'),('P0b','P1b'))),
                       ('cumulative',(('P0a','P2a'),('P0b','P2b'))),
                       ('original_new_p0',(('original96','P0a'),('original96','P0b')))):
        contrasts[kind] = []
        for reference,candidate in pairs:
            before,after = analyses[reference],analyses[candidate]
            values = {}
            for index,name in enumerate(('single_goodput_percent','aggregate_goodput_percent')):
                base,value = before['cells'][index]['completed_goodput_mbit_s'],after['cells'][index]['completed_goodput_mbit_s']
                values[name] = (value/base-1)*100 if base is not None and value is not None else None
            contrasts[kind].append(dict(reference=reference,candidate=candidate,**values,
                latency_percent={probe:{metric:(after['latency'][probe][metric]/before['latency'][probe][metric]-1)*100
                    for metric in ('median_seconds','max_seconds')} for probe in ('idle','loaded')},
                phase_exceptions={phase:load('phase-'+phase+'/summary.json')['phase_exception'] for phase in (reference,candidate)},
                clean_acceptance=False,scope='descriptive different-session observations only; P0b single completed before renewal but its parallel failed; partial aggregate excluded; protocol/closure limitations retained'))
    actual_bytes=sum(record['delivered_bytes'] for record in analyses.values())
    renewal=load('RU-p0b-state-change.json')['records']['renewal-coordinator/transaction.json']
    profile_delta=load('p0b-profile-delta-archive.json')
    assert renewal['state']=='COMMITTED' and renewal['operation_id']==profile_delta['operation_id']
    assert current['gateway']['profile_sha256']==profile_delta['after_sha256']
    assert renewal['before']['NL']['files']['gateway.json']==profile_delta['before_sha256']
    assert [field['name'] for field in profile_delta['fields'] if not field['unchanged']]==['certificate','revocations']
    transitions=[json.loads(line) for line in (WORK/'transitions/private/deploy-NL.jsonl').read_text().splitlines()]
    deployment=next(record for record in transitions if record.get('result')=='EXECUTABLE_TRANSITION_VERIFIED')
    summaries = {name: load(name) for name in (
        'checks-focused.json', 'checks-queue.json', 'checks-suite.json',
        'compatibility/results.json', 'head32-results.json', 'security-results.json',
        'final-checks.json', 'busy-repeat.json', 'sign-check.json', 'transitions/prepared.json', 'cleanup.json',
        'phone-connected-readback.json', 'identity-original.json', 'ui-gate.json', 'upgrade-receipt.json',
        'identity-before.json', 'identity-after.json', 'policy-p0a-prepared.json',
        'transitions/receipts/before-readiness.json', 'transitions/receipts/candidate-ready-readiness.json',
    )}
    logs = [log_summary(path) for path in sorted(WORK.glob('*.jsonl'))]
    build_logs = []
    for path in sorted(list((WORK / 'build').glob('*.log'))+list((WORK/'superseded-ui/build').glob('*.log'))):
        text = path.read_text()
        status = 'BUILD_SUCCESSFUL' if 'BUILD SUCCESSFUL' in text else 'BUILD_FAILED' if 'FAILURE:' in text else 'LOG_ONLY_SEE_RECEIPT'
        build_logs.append(dict(path=str(path.relative_to(WORK)), sha256=digest(path), status=status))
    data = dict(
        schema='family-connect.android-speed-candidate.v1',
        prepared_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        state='CYCLE_CLOSED_WITH_LIMITATIONS; FINAL_P0_CONFIRMED_BOTH_ENDS; NO_PRODUCT_ADMISSION_OR_MORE_OWNER_ACTIONS',
        workdir=str(WORK.relative_to(ROOT)),
        exact_baseline=baseline,
        source_seal=load('source-seal.json'),
        build={name: build[name] for name in ('version', 'version_code', 'apk_sha256', 'native_sha256', 'tests', 'source_inventory', 'signing', 'installed', 'distributed')},
        build_receipt_scope='unsigned build-time receipt; signing/install/current runtime are separate verified records',
        unsigned_apk_path=str(unsigned.relative_to(ROOT)),
        signed_apk_path=str(signed.relative_to(ROOT)), signed_apk_sha256=signing['signed']['sha256'],
        signing=signing,
        connected_observation=load('observation-p0a-connected.json'),
        operator_corrections=load('operator-corrections.json'),
        initial_p0_policy=load('policy-p0a-bounded-target.json'),
        final_next_session_p0_policy=load('policy-p0b-prepared.json'),
        final_next_session_p0_observation_sha256=digest(WORK/'observation-p0b-prepared.json'),
        next_session_p1_policy=load('policy-p1a-prepared.json'),
        reverse_next_session_p1_policy=load('policy-p1b-prepared.json'),
        supplementary_observation_failures=[load('p1b-delivered-observation-attempt1.json'),load('p1b-delivered-observation-attempt2.json')],
        supplementary_observation_recovery=dict(sha256=digest(WORK/'observation-p1b-delivered.json'),
            since_utc=load('observation-p1b-delivered.json')['gateway']['since_utc'],
            input_bytes=load('observation-p1b-delivered.json')['gateway']['input_bytes'],
            parser_errors=load('observation-p1b-delivered.json')['gateway']['parser_errors'],limits_unchanged=True),
        next_session_p2_policy=load('policy-p2a-prepared.json'),
        post_export_receipts={path.name:load(path.name) for path in sorted(WORK.glob('post-*.json'))},
        p0_consistency_review=load('p0-integration-audit.json'),
        p0_post_export_sha256=digest(WORK/'android-p0a-post.json'),
        p0_applied_scope_sha256=digest(WORK/'scope-P0a.json'),
        p0_post_gateway_observation_sha256=digest(WORK/'observation-p0a-after.json'),
        current_owner_applied_profile='P0_BOTH_ENDS_CONFIRMED_AFTER_RENEWAL; ANDROID_CONNECTED_READY_ERRORS17_IN_NEW_SESSION; NOT_CLEAN_ADMISSION',
        final_owner_receipt=load('owner-p0-final-receipt.json'),
        p0b_android_history=load('post-P0b-owner-p0-final.json'),
        p0b_applied_scope_sha256=digest(WORK/'scope-P0b.json'),
        p0b_post_renewal_observation_sha256=digest(WORK/'observation-p0b-final-state.json'),
        p1b_applied_scope_sha256=digest(WORK/'scope-P1b.json'),
        p1b_post_export=load('post-P1b-p1b-post.json'),
        p1b_closure=load('post-P1b-p0b-preflight.json'),
        p2_applied_scope_sha256=digest(WORK/'scope-P2a.json'),
        p2_preload_protocol_errors=load('scope-P2a.json')['android_diagnostic']['protocol_errors'],
        p2_post_export=load('post-P2a-p2a-post.json'),
        p2a_closure=load('post-P2a-p2b-preflight.json'),
        p2b_post_export=load('post-P2b-p2b-post.json'),
        p2b_closure=load('post-P2b-p1b-preflight.json'),
        q1_order_matched_contrasts=contrasts['q1'],
        windows_order_matched_contrasts=contrasts['windows'],
        cumulative_order_matched_contrasts=contrasts['cumulative'],
        original_new_p0_contrasts=contrasts['original_new_p0'],
        p2_reverse_gate=dict(status='P2B_DELIVERED_POST0_THEN_LATE_ANDROID2_GATEWAY1_EXHAUSTION_NOT_CLEAN',
                             load_started=True,policy_changed=False,restart=False,
                             scope_sha256=digest(WORK/'scope-P2b.json'),
                             android_preload_errors=load('scope-P2b.json')['android_diagnostic']['protocol_errors'],
                             rationale='New tag, actual both-end limits and Q1, initial Android/server errors0; all15 bodies delivered; P2a errors and late exhaustion retained, not erased by repeat'),
        delivery_qualification=dict(P0a='LATE_ANDROID4_GATEWAY3_NOT_CLEAN',
                                    P1a='GATEWAY_WHOLE_SESSION3_AND_POST_DELIVERY_EXHAUSTION_NOT_CLEAN',
                                    P2a='ANDROID1_TO10_AND_GATEWAY_TERMINAL1_POST_DELIVERY_EXHAUSTION_NOT_CLEAN',
                                    P2b='DELIVERED_ANDROID_POST0_THEN_LATE2_GATEWAY1_EXHAUSTION_NOT_CLEAN',
                                    P1b='DELIVERED_ANDROID_POST_ERRORS0_TO1_GATEWAY_TERMINAL3_AND_EXHAUSTION_NOT_CLEAN',
                                    P0b='13_OF15_COMPLETE; SINGLE_COMPLETE; PARALLEL_TWO_PARTIAL_EXIT18; SCHEDULED_RENEWAL_INTERRUPTION; NOT_CLEAN'),
        operator_tests_sha256=digest(WORK/'operator-tests.log'),
        helper_tests_sha256=digest(WORK/'operator-and-scope-tests.log'),
        observation_helper_tests=dict(path='observer-filter-tests.log',sha256=digest(WORK/'observer-filter-tests.log'),passed=6,
                                      scope='local operator/scope tests and generated journal script with/without UTC filter; no live payload'),
        final_accounting_tests=dict(path='final-accounting-tests.log',sha256=digest(WORK/'final-accounting-tests.log'),passed=9,
            prior_attempt_sha256=digest(WORK/'partial-accounting-tests.log'),meter_unchanged=True,
            scope='partial bodies never become completed goodput; existing bounded journal continuation parser; no product or failure-handling change'),
        p0b_initial_line_parser=dict(path='phase-P0b/line-parser-attempt.json',sha256=digest(WORK/'phase-P0b/line-parser-attempt.json'),
            errors=load('phase-P0b/line-parser-attempt.json')['parse_errors'],recovered_with_existing_bounded_parser=True),
        superseded_ui=dict(signing=load('superseded-ui/delivery/signing-receipt.json'),installed=False,
                           reason='Profile selector was on MainActivity rather than actual FriendsActivity; fixed before any install',
                           current_tests=190, current_launcher='FriendsActivity', native_unchanged=True),
        gateway_build=gateway,
        gateway_deployment=deployment,
        startup_readiness=dict(first_check='FAILED_PUBLICATION_TIMESTAMP_1_15_SECONDS_AFTER_PROCESS_START',
                               retry='PASS_AFTER_STARTUP_WITH_IDENTICAL_STRICT_GATES',
                               gates_weakened=False,restart_count=1,renewal_forced=False),
        runtime=dict(entry=entry, pre_install_final=final, current=current,
                     mutations_by_this_task=['owner signed in-place97 install','approved shared gateway executable transition', 'owner-targeted next-session P0 then P1 then P2 then P1 then P0 files'],
                     external_epoch_changed=True, external_cause='UNKNOWN',
                     reported_process_start_utc='2026-10-21T11:41:02Z',
                     profile_change_interval=[entry['utc'], final['utc']],
                     transport_flags_equal=entry['gateway']['operator'] == final['gateway']['operator']),
        p0b_external_state_change=dict(operation_id=renewal['operation_id'],state=renewal['state'],gate=renewal['gate'],
            first_cause=renewal['first_cause'],profile_delta=profile_delta,binary_unchanged=True,
            trigger='existing scheduled credential renewal; service result and COMMITTED coordinator receipt agree',
            load_overlap='after completed single, during both parallel responses; no new load after abort',
            systemd_events={role:[dict(epoch_us=row['__REALTIME_TIMESTAMP'],message=row['MESSAGE'])
                for journal in load(role+'-p0b-state-change.json')['journals'].values()
                for row in journal['rows'] if row.get('_PID')=='1'] for role in ('NL','RU')},
            receipt_hashes={name:digest(WORK/name) for name in ('NL-p0b-state-change.json','RU-p0b-state-change.json','p0b-profile-delta-archive.json')},
            first_profile_probe=dict(result='ACTIVE_OWNER_FILE_ABSENT_AFTER_NORMAL_ARCHIVE; READ_ONLY_RETRY_USED_EXISTING_ARCHIVE',
                stderr_sha256=digest(WORK/'p0b-profile-delta.stderr')),renewal_forced=False,timers_changed=False,rollback=False,
            earlier_1141_event_still_unexplained=True),
        profiles=dict(
            P0=dict(local_send=8, local_receive=16, expected_peer_receive=16, expected_effective_send=8, mux='LEGACY64', mux_bytes=65536, q1=False),
            P1=dict(local_send=32, local_receive=32, expected_peer_receive=32, expected_effective_send=32, mux='CREDIT128', mux_bytes=131072, q1=False),
            P2=dict(local_send=32, local_receive=32, expected_peer_receive=32, expected_effective_send=32, mux='CREDIT128', mux_bytes=131072, q1=True),
        ),
        common=dict(carrier='L', timebase='A0', post_frame_delay_ms=2, packing=False, fec=False, new_pacing=False,
                    quic=False, payload_bytes=16384, rto_ms=1000, max_retries=8, max_age_ms=20000),
        local_summary_receipts=summaries,
        all_go_attempts=logs,
        all_build_attempt_logs=build_logs,
        artifacts={str(path.relative_to(ROOT)): digest(path) for path in sorted(FIXTURE.iterdir()) if path.is_file()},
        q1_reproducer=dict(window=32, test_only_rto_ms=30, local_writer_hold_ms=340,
                           Q0=dict(attempts=9, premature_retries=8, terminal='recovery_exhausted'),
                           Q1=dict(attempts=1, premature_retries=0, byte_exact=True, terminal=''),
                           scope='local bound Pion, Android and gateway; not a live speed result'),
        known_non_green=dict(
            bootstrap_negative_assertions='Reproduced on exact accepted96; rejection remains enforced; not patched for green logs',
            busy_repeat=dict(accepted96=dict(passed=12, failed=8), candidate97=dict(passed=12, failed=8)),
            all_suites_pass=False,
        ),
        static_extra_payload_and_ring_bytes_per_endpoint={'16_streams': 1703936, '32_streams': 2752512, '64_streams': 4849664},
        physical=dict(status='SEVEN_PHASES_ATTEMPTED; SIX_COMPLETE_AND_P0B13_OF15; NO_RETRY_OR_CLEAN_ACCEPTANCE', attempts=requests,
                      original_control=original,new_p0a=p0,application_bytes=actual_bytes,new_live_test_media_bytes=None,
                      application_bytes_scope='received body bytes including partial; reservation is not refunded on failures',
                      complete_response_bytes=sum(record['complete_response_bytes'] for record in analyses.values()),
                      partial_response_bytes=sum(record['partial_response_bytes'] for record in analyses.values()),
                      successful_responses=sum(record['valid'] for record in analyses.values()),
                      phase_analyses=analyses,
                      reserved_bytes=sum(load(path.name)['intended_bytes'] for path in WORK.glob('traffic-*-reservation.json')),
                      application_budget_bytes=64 << 20, bulk_request_deadline_seconds=150,
                      planned_order=['P0a', 'P1a', 'P2a', 'P2b', 'P1b', 'P0b'],
                      main_phase_reserved_bytes=(8 << 20) + 12 * 1024,
                      baseline_new_p0_difference_review_fraction=.15,
                      repeated_single_gain_min_fraction=.20, aggregate_regression_review_fraction=.10,
                      small_median_or_max_regression_review_fraction=.20, q1_speed_regression_review_fraction=.10,
                      probes_per_phase=dict(idle=6, loaded=6, bytes=1024),
                      origin_sha256_contract=False, observed_body_sha256=True, p99_claim=False),
        recovery=dict(local_lease_renewal_expiry_revocation='PASS_BOUNDED_FIXTURES', automatic_physical_network_loss='NOT_RUN', overnight='NOT_RUN',
            live_maintenance='PROVEN_RENEWAL_INTERRUPTED_P0B; NEW_P0_SESSION_CONFIRMED_BOTH_ENDS; ANDROID_CONNECTED_READY_ERRORS17; NOT_PROOF_OF_AUTOMATIC_NETWORK_LOSS_RECOVERY'),
        results=dict(EXACT_BASELINE='FRESH_96_734_READBACK_AND_ORIGINAL_TUN_CONTROL',
                     INTEGRATED_COMPONENTS='P0_P1_P2_IMPLEMENTED_SEALED', OLD_NEW_COMPATIBILITY='7_OF_7_LOCAL',
                     EFFECTIVE_RS_AND_MUX='P0_LIVE_8_16_PEER16_EFFECTIVE8_LEGACY64; P1_P2_LIVE_32_32_PEER32_EFFECTIVE32_CREDIT128_BOTH_ENDS_Q0_Q1_SEPARATE',
                     P0_P1_P2_ANDROID_RESULTS='P0A_P1A_P2A_P2B_P1B_DELIVERED; P0B_SINGLE_AND_SMALL_COMPLETE_PARALLEL_INTERRUPTED_BY_RENEWAL', CUMULATIVE_GAIN_VS_P0='RAW_SINGLE_WINDOWS_GAIN_IN_BOTH_ORDERS; REVERSE_AGGREGATE_UNAVAILABLE; NO_CLEAN_ADMISSION',
                     Q1_CORRECTNESS_AND_COST='EARLY_LOCAL_ATTEMPTS_FIXED_LOCAL; OBSERVED_SINGLE_MINUS3_736_AND_MINUS5_974_PERCENT_AGGREGATE_PLUS0_068_AND_MINUS1_442_PERCENT; NO_ADDED_SPEED_GAIN_OR_CLEAN_ADMISSION; LIVE_RETRY_CLASSIFICATION_UNKNOWN',
                     LATENCY_FAILURES_RESOURCE_LIMITS='SEVEN_PHASES_RETAINED; TWO_PARTIAL_BODIES_AND_TUN_GUARD_FAILURE; P0B_CPU_ONLY_OLD_PID_UNTIL_STOP; ANDROID_POINT_ONLY; WHOLE_WIRE_UNKNOWN',
                     SIGNED_APK_PATH_AND_SHA256=signing['signed']['sha256'], CURRENT_OWNER_AND_GATEWAY_STATE='INSTALLED97; P0_CONFIRMED_BOTH_ENDS_AFTER_RENEWAL; ANDROID_CONNECTED_READY_ERRORS17; SAME_CANDIDATE_BINARY; NEW_CERT_CRL'),
        product_admission=False,
        pending_owner_actions=[],
        unresolved=['Mux protocol-error branches and post-delivery exhaustion causes not established; new P0 Android session17 errors retained',
                    'original/new P0 speed cause unresolved; protocol/closure exclusions prevent product admission',
                    'reverse aggregate unavailable after scheduled renewal interruption; no automatic retry',
                    'post-renewal active route/DNS/HTTPS checks, automatic network-loss recovery and overnight stability not run'],
    )
    target = ROOT / 'docs/releases/2026-10-21-android-speed-candidate.evidence.json'
    write(target, json.dumps(data, indent=2, sort_keys=True) + '\n')
    print(json.dumps(dict(evidence=str(target.relative_to(ROOT)), go_attempts=len(logs), build_logs=len(build_logs), live_bytes=actual_bytes)))


if __name__ == '__main__':
    main()
