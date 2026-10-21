"""Record the integration review after original/new P0 exceeded the frozen gate."""

import json
from prepare import ROOT, WORK, ANDROID, GATEWAY, digest


def main():
    comparisons = []
    for side, original, candidate in (
        ('android',ANDROID/'android-source/carrier',WORK/'android-source/carrier'),
        ('gateway',GATEWAY/'candidate',WORK/'gateway-source'),
    ):
        names = ['go.mod','go.sum','reliablestream/protocol.go','telemost/msg.go','telemost/vp8.go','telemost/rtp.go',
                 'reliablestream/receive_default.go','reliablestream/target_default.go']
        names += [str(path.relative_to(original)) for path in (original/'tcpforward').glob('*.go') if not path.name.endswith('_test.go')]
        for name in names:
            before, after = digest(original/name), digest(candidate/name)
            assert before == after, (side,name)
            comparisons.append(dict(side=side,path=name,sha256=after,equal=True))
        before = (original/'reliablestream/engine.go').read_text()
        after = (candidate/'reliablestream/engine.go').read_text()
        assert before[before.index('func newEngine('):] == after[after.index('func newEngine('):]
        comparisons.append(dict(side=side,path='reliablestream/engine.go',comparison='all engine functions after newEngine identical; Stats.Limits only',equal=True))
        profile = (candidate/'sessionprofile/profile.go').read_text()
        assert 'config := reliablestream.DefaultConfig()' in profile
        assert 'if profile == P1 || profile == P2 {' in profile
        assert 'if profile == P2 {\n\t\treturn localwrite.WithCompletion(ctx)' in profile
    scope = json.loads((WORK/'scope-P0a.json').read_text())
    after = json.loads((WORK/'android-p0a-post.json').read_text())['ring']['restricted_session']
    before = scope['android_diagnostic']
    assert after['session_tag'] == before['session_tag']
    keys = ('protocol_errors','retry_bytes','retransmissions','recovery_timeouts','sent_bytes','received_bytes')
    assert all(after[key] >= before[key] for key in keys)
    assert after['terminal_reason'] == 'NONE' and not after['reliable_terminal']
    result = dict(status='INTEGRATION_REVIEW_DONE_ORIGINAL_NEW_SPEED_COMPARABILITY_NOT_ESTABLISHED',
        frozen_consistency_gate='TRIGGERED_15_PERCENT; not waived or retuned',
        equal_files_and_functions=comparisons,
        q0_review=['Android Q1 completion map/observe/wait/obsolete updates gated off in P0',
                   'nil localwrite Register/Begin/Complete preserve the ordinary carrier send path',
                   'unconditional queued timestamp and larger queued-frame struct remain a small integration cost, not benchmark-proven free',
                   'gateway old734 already has Q1 code; P0 profile returns unchanged context/default config',
                   'same 2ms/frame,33ms timebase,wire,Mux implementation,RTO/retries and dependencies',
                   'new bounded applied-limits projection and one gateway startup receipt are diagnostic deltas'],
        existing_local_cross_process='old-old, new-P0 and return-P0 exact body/EOF/empty terminal pass; not a controlled throughput benchmark',
        live=dict(same_underlay=True,different_sessions=True,different_gateway_invocations=True,
                  original_owner_tag_unproven=True, original_whole_session_errors_not_attributable_to_phase=True,
                  android_post_profile=after['speed_profile'],android_protocol_errors_before=before['protocol_errors'],
                  android_protocol_errors_after=after['protocol_errors'],
                  android_delta={key:after[key]-before[key] for key in keys},
                  android_counter_interval_ms=[before['observed_at_ms'],after['observed_at_ms']],
                  delta_scope='same Android session; pre/post interval includes non-bulk time/background, not per-request or whole-wire overhead',
                  gateway_head_retry_samples=dict(original_active_unattributed=dict(nonzero=2,total=40),new_owner=dict(nonzero=29,total=49)),
                  sample_scope='2s observations, not exact stall durations, independent loss rate, or exclusive cause',
                  cause='UNRESOLVED; no altered P0 window/cadence/recovery policy found; observed recovery/path difference cannot be assigned solely to binary'),
        continuation='bounded new-pair P0/P1/P2 reverse contrasts may be measured; no clean original-to-new equivalence or product admission claimed',
        hashes={name:digest(WORK/name) for name in ('scope-P0a.json','android-p0a-post.json','p0-consistency.json')})
    (WORK/'p0-integration-audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],equal_file_checks=len(comparisons),protocol_error_delta=after['protocol_errors']-before['protocol_errors'],speed_cause='UNRESOLVED')))


if __name__ == '__main__':main()
