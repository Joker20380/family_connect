"""Publish only sanitized summaries/hashes after verified trace-off return."""

import json
import subprocess

from preserve import ROOT, WORK, digest
from normal import NORMAL


def read(path):
    return json.loads(path.read_text())


def tests(path):
    records=[json.loads(line) for line in path.read_text().splitlines() if line.startswith('{')]
    assert not any(record['Action']=='fail' for record in records)
    return dict(sha256=digest(path),passed=sum(record['Action']=='pass' and bool(record.get('Test')) for record in records),
                skipped=sum(record['Action']=='skip' and bool(record.get('Test')) for record in records))


def main():
    fixture=ROOT/'tests/fixtures/mesh_receive_path'
    pins=read(fixture/'source-pins.json')
    summary=read(WORK/'physical-receiver-summary.json')
    signing=read(NORMAL/'delivery/signing-receipt.json')
    upgrade=read(NORMAL/'upgrade-receipt.json')
    device=read(NORMAL/'final-device.json')
    identity=read(NORMAL/'identity-after.json')
    identity_before=read(NORMAL/'identity-before.json')
    for field in ('identity_bindings_sha256','support_id_sha256','owner_record_count'):
        assert identity[field]==identity_before[field]
    assert identity['beta92_readiness']['result']=='READY' and not identity['owner_revoked']
    assert device['code']==92 and device['native_sha256']==pins['normal92']['native_sha256']
    assert device['apk_sha256']==signing['signed']['sha256']==pins['normal92']['apk_sha256']
    assert upgrade['exit']==0 and not upgrade['uninstall'] and not upgrade['data_cleared']
    runtime=read(WORK/'transitions/a/receipts/accepted-return-readiness.json')
    assert runtime['loaded_sha256']==pins['baseline_gateway']
    control=read(NORMAL/'physical-control/result.json')
    assert control['control_pass'] and control['body_bytes']<=4096
    assert control['matching_production_pid_socket_samples']>0
    build=read(NORMAL/'android-build/receipt.json')
    apk=NORMAL/'delivery/FamilyConnect-0.1.18-beta92-stability.apk'
    assert digest(apk)==signing['signed']['sha256']
    modes={name:read(WORK/name/'result.json') for name in ('small','small-return','baseline')}
    assert modes['small-return']['small_gate_pass'] and modes['baseline']['topology_stable']
    attempted=sum(json.loads(line)['intended_bytes'] for name in modes
                  for line in (WORK/name/'requests.jsonl').read_text().splitlines())+4096
    assert attempted<=32*1024*1024
    failures=[dict(path=str(path.relative_to(WORK)),sha256=digest(path)) for path in
              (NORMAL/'android-build').glob('gradle-*.log') if 'BUILD FAILED' in path.read_text()]
    result=dict(schema='family_connect_mesh_receive_path_v1',
        source_checkpoint=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        source_state='LOCAL_EXACT_BASE_OVERLAYS_NOT_MAIN_RUNTIME',pushed=False,public_release=False,
        SOURCE_AND_RUNTIME_BASELINE=dict(initial_apk_sha256='68cbcccfb5adf8656e8203436126330e780de099670ee2031d71019baadc3e9a',
            initial_native_sha256=pins['normal92']['native_sha256'],gateway_sha256=pins['baseline_gateway'],
            gateway_inventory='4722b7353ba93209657f66b45c47874915362f1fbe732845ec61745abdb673e6'),
        DATA_HEAD=dict(saved_session='2219e060af8bc8a0532e29b7e55e5e2bda5eb68f592264d98400d174de714b5c',sequence=597,
            attempt=2,sender=752154365,message=4260144682,nl_local_fragments_written=3,
            android='fragments0/2 assembled; fragment1 gap-discard; late5981 old_rtp',
            covering_ack_received=False,last_ack=dict(base=597,mask=220),
            terminal_suffix='FINAL_SIX_SECONDS_AND_LATER_ANDROID_ATTEMPTS_NOT_CAPTURED'),
        CLASSIFICATION=dict(current=summary['classification'],session=summary['session'],
            damaged_data=[614,1127,1294],prompt_consume_ack_controls=[649,741],
            current_capacity_events=0,local_deadline_overshoot_ms=68.25,
            overshoot_scope='buffered unidentified/control frames near614; not a complete available head614',
            average_throughput_cause='NOT_UNIQUELY_ESTABLISHED',specific_network_actor='NOT_ATTRIBUTED'),
        CORRELATION_COMPLETENESS=dict(small_gate_logical_data=57,bulk_logical_data=260,
            snapshot_counts=modes['baseline']['snapshot_counts'],parser_errors=modes['baseline']['parser_error_counts'],
            android_receive_coverage=summary['android_coverage'],absence_is_not_loss=True,
            ack_token_is_shared=False,cross_node_latency_computed=False),
        TARGETED_CHANGE=dict(observation='VERIFIED_NATIVE_JNI_EXPORT_CAPTURE_CORRELATION_THEN_REMOVED',
            discarded_frame_cleanup='LOCAL_CORRECTNESS_VALIDATED_NOT_BUILT_OR_DEPLOYED',
            gap_timer='UNCHANGED_NOT_SHIPPED_AS_SPEED_FIX',functional_candidate_live=False,
            accepted_speed_fix=False,rejected_previous=['read-alignment','SACK-hole','queue-retry']),
        THROUGHPUT_BEFORE_AFTER=dict(baseline=summary['requests'],parallel=modes['baseline']['parallel'],
            successes=3,attempts=3,after='NOT_RUN_NO_JUSTIFIED_FUNCTIONAL_CANDIDATE',
            mode='HTTP1.1_FRESH_IDENTITY_PHONE_BODY_READ',mux_streams=summary['bulk_mux_streams'],
            network='CELLULAR_UNDERLAY_321',new_actual_bytes=sum(row['application_bytes'] for row in modes.values())+control['body_bytes'],
            new_requested_bound_bytes=attempted,observed_hash_is_origin_digest=False),
        TUN_CHANGE=dict(first_small_gate=modes['small']['small_gate_pass'],
            classification=read(WORK/'small/startup-classification.json')['classification'],
            first_gate_preserved=True,older_unexplained_tun_gap='RETAINED_SEPARATELY'),
        RECOVERY_PRESERVED=dict(source='EXACT_ACCEPTED90_NATIVE_AND_JAVA',normal_jvm_tests=build['tests'],
            new_production_faults=False,natural_session_close_in_bulk=False,overnight_acceptance=False,
            bootstrap1011_preserved=True),
        IDENTITY_PRESERVED=dict(id_key_bindings_and_support_id=True,uid=device['uid'],ready='READY',
            uninstall=False,data_clear=False,reenrollment=False),
        APK_OR_SERVER_ARTIFACT=dict(final_apk=signing['signed'],path=str(apk.relative_to(ROOT)),
            native_sha256=device['native_sha256'],source_inventory=build['source_inventory'],
            installed_utc=upgrade['after']['utc'],final_gateway_sha256=runtime['loaded_sha256'],
            gateway_pid=runtime['state']['MainPID'],gateway_invocation=runtime['state']['InvocationID'],
            gateway_readiness_utc=runtime['utc'],extended_performance_trace=False,
            observation_apk=pins['observation_apk'],observation_gateway_sha256=pins['observation_gateway_sha256']),
        VALIDATION=dict(default=tests(WORK/'validation/results/default.jsonl'),
            observation=tests(WORK/'validation/results/observation.jsonl'),
            candidate_local=tests(WORK/'candidate-regression.jsonl'),normal_build_failure_preserved=failures,
            final_control=control),
        SPB_IPV6_SEPARATE_STATUS='NOT_RUN',AMSTERDAM_IPV6='DEFERRED_BY_OWNER',
        NEXT_HOST_COMPARISON_INPUTS=dict(apk_sha256=device['apk_sha256'],native_sha256=device['native_sha256'],
            gateway_sha256=runtime['loaded_sha256'],endpoint='https://speed.cloudflare.com/__down?bytes=2097152',
            method='bounded same-code IPv4 A/B/A, single2MiB then parallel2x2MiB, all failures retained',
            placement='NOT_SELECTED_NO_PURCHASE_OR_PRODUCTION_MIGRATION'),
        FINAL_RESULT='RECEIVER_BOUNDARIES_LOCALIZED_NO_ACCEPTED_SPEED_FIX_STABLE92_B9_RESTORED',
        local_evidence_sha256={name:digest(WORK/name) for name in
            ('owner-beta90-export.json','owner-beta91-export.json','saved-head597.json','physical-receiver-summary.json')})
    target='docs/releases/2026-10-20-mesh-receive-path.evidence.json'
    assert not (ROOT/target).exists()
    text=json.dumps(result,indent=2,ensure_ascii=False)+'\n'
    subprocess.run(['apply_patch','*** Begin Patch\n*** Add File: '+target+'\n'+''.join('+'+line+'\n' for line in text.splitlines())+'*** End Patch\n'],cwd=ROOT,check=True)
    print(result['FINAL_RESULT'])


if __name__=='__main__':main()
