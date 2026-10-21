"""Sanitized results only; raw exports and deployment credentials stay local."""

import json
import subprocess

from prepare import ROOT, WORK, GATEWAY, APK, digest


def read(name):
    return json.loads((WORK/name).read_text())


def main():
    final=read('final-post-readback.json')
    assert final['gateway']['sha256']==GATEWAY and final['phone']['apk_sha256']==APK
    assert final['phone']['code']==90
    control=read('final-control/result.json')
    confirmed=read('final-control-confirmed/result.json')
    assert confirmed['control_pass'] and len(final['vpn'])==1
    phases={}
    baseline_bytes=candidate_bytes=0
    for name in ('baseline-raw','a-measure','a-measure-fixed','b-measure','b-ready','a-return','a-return-ready'):
        result=read(name+'/result.json')
        attempted=sum(row['intended_bytes'] for row in result['requests'])
        if name.startswith('b-'):candidate_bytes+=attempted
        else:baseline_bytes+=attempted
        analysis=read(name+'/analysis.json') if (WORK/name/'analysis.json').exists() else None
        phases[name]=dict(attempted_bytes=attempted,received_bytes=result['application_bytes'],
            failures=sum(not row['valid'] for row in result['requests']),gateway=result['gateway'],
            requests=[dict(name=row['name'],valid=row['valid'],bytes=int(row['metrics'].get('BODY_BYTES',0)),
                curl_exit=row['metrics'].get('CURL_EXIT'),full_seconds=row['metrics'].get('time_total'),ttfb_seconds=row['metrics'].get('time_starttransfer'),
                observed_body_sha256=row['metrics'].get('BODY_SHA256'),mbit_s=row.get('mbit_s')) for row in result['requests']],
            parallel=result['parallel'],topology_stable=result['topology_stable'],capture_exit=result['capture_exit'],
            analysis=analysis,result_sha256=digest(WORK/name/'result.json'))
    baseline_bytes+=8192
    assert baseline_bytes<=32*1024*1024 and candidate_bytes<=32*1024*1024 and baseline_bytes+candidate_bytes<=64*1024*1024
    tests={}
    for label in ('observation-suite-1','candidate-observed-suite','candidate-local-default','baseline-counted-queue','candidate-counted-queue','candidate-deadlines-queue'):
        path=WORK/'tests'/(label+'.jsonl')
        rows=[json.loads(line) for line in path.read_text().splitlines() if line.startswith('{')]
        assert not any(row['Action']=='fail' for row in rows)
        tests[label]=dict(sha256=digest(path),pass_cases=sum(row['Action']=='pass' and bool(row.get('Test')) for row in rows),skip_cases=sum(row['Action']=='skip' and bool(row.get('Test')) for row in rows))
    artifacts={}
    for label in ('observation-queue','candidate-observed','candidate'):
        build=read(label+'-build.json');assert digest(WORK/('gateway-'+label))==build['sha256']
        artifacts[label]={key:build[key] for key in ('sha256','inventory','bootstrap1011_preserved')}
    result=dict(schema='family_connect_queue_retry_v1',source_checkpoint=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        pushed=False,CURRENT_BASELINE=dict(apk_sha256=APK,gateway_sha256=GATEWAY,phone=final['phone'],gateway=final['gateway'],verified_at=final['utc'],vpn_count=len(final['vpn'])),
        QUEUE_RETRY_HYPOTHESIS=dict(local='CONFIRMED_9_PENDING_ATTEMPTS_BEFORE_FIRST_WRITE',physical='NOT_DEMONSTRATED_AS_CURRENT_DOMINANT_LIMIT',
            before_pending=9,after_pending=1,before_retries=8,after_retries=0,synthetic_rto_ms=30,synthetic_writer_hold_ms=340),
        TARGETED_CHANGE=dict(result='TESTED_NOT_ACCEPTED_FOR_SHIPMENT',wire_changed=False,server_only=True,normal_candidate_deployed=False),
        BEFORE_AFTER_GOODPUT_AND_FAILURES=phases,
        STABILITY_AND_IDENTITY_PRESERVED=dict(android_updated=False,identity_keys_support_id_mutated=False,admission_or_floors_rolled_back=False,
            bootstrap1011_preserved=True,extended_android_trace=False,temporary_server_performance_trace=False,overnight_acceptance=False,
            final_small_control=True,unexplained_intermediate_tun_absence=True,
            identity_basis='No client install/data writes; same installed APK/native, UID and PID; prior same-key receipt retained'),
        FINAL_CONTROL=dict(first_attempt=dict(utc=control['utc_start'],curl_exit=control['curl_exit'],body_bytes=control['body_bytes'],pass_result=control['control_pass']),
            first_retry='NOT_RUN_NO_TUN',passive_observations=[json.loads(line) for line in (WORK/'final-vpn-observation.jsonl').read_text().splitlines()],
            confirmed_after_tun_return=confirmed,needed_owner_action=None,
            original_empty_remote_ip_socket_count='INVALID_ATTRIBUTION_NOT_ACCEPTED; corrected guard for future controls'),
        tests=tests,artifacts=artifacts,source_pins_sha256=digest(ROOT/'tests/fixtures/queue_retry/source-pins.json'),
        requested_bytes=dict(baseline=baseline_bytes,candidate=candidate_bytes,total=baseline_bytes+candidate_bytes),
        remaining_evidence='Current slow physical intervals have prompt NL local writes but delayed head/ACK progress; receiver-side fate of the same natural retries is not captured on ordinary90.',
        FINAL_RESULT='NO_REPEATABLE_SPEED_ACCEPTANCE_CURRENT1011_RESTORED_FINAL_SMALL_CONTROL_PASS')
    with (ROOT/'docs/releases/2026-10-20-mesh-queue-retry.evidence.json').open('x') as output:json.dump(result,output,indent=2)
    print(json.dumps(dict(final=result['FINAL_RESULT'],requested_bytes=result['requested_bytes'],tests=tests)))


if __name__=='__main__':main()
