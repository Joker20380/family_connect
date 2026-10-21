"""Reconcile an exact phase with a later owner export, retaining late errors."""

import json
from pathlib import Path
import re
import sys
from prepare import WORK, digest


def main():
    phase, source_file, label = sys.argv[1:]
    assert phase in ('P0a','P1a','P2a','P2b','P1b','P0b') and re.fullmatch('[a-z0-9-]+',label)
    source = Path(source_file)
    assert source.stat().st_size <= 525312
    ring = json.loads(source.read_text())['ring']
    assert ring['version_code'] == 97
    scope = json.loads((WORK/('scope-'+phase+'.json')).read_text())
    before = scope['android_diagnostic']
    candidates = [('current',ring.get('restricted_session',{}))] + [('history',row) for row in ring.get('restricted_history',[])]
    matching = [(location,row) for location,row in candidates if row.get('session_tag') == before['session_tag']]
    assert len(matching) == 1, 'Missing or ambiguous phase tag; do not substitute another session'
    location, after = matching[0]
    for key in ('speed_profile','reliable_limits','mux_profile','mux_window'):
        assert after[key] == before[key]
    keys = ('protocol_errors','retry_bytes','retransmissions','recovery_timeouts','sent_bytes','received_bytes','dns_errors','tcp_open_errors')
    deltas = {key:after[key]-before[key] if key in after and key in before and after[key] >= before[key] else None for key in keys}
    counters = {key:after.get(key) for key in keys}
    observation_path = WORK/('observation-'+label+'.json')
    server = []
    if observation_path.exists():
        observation = json.loads(observation_path.read_text())
        for row in observation['gateway']['records']:
            diagnostic = row.get('diagnostic',{})
            if row['event'] == 'session_terminal' and diagnostic.get('session_tag') == before['session_tag']:
                lifecycle = diagnostic.get('lifecycle',{})
                server.append(dict(utc=row.get('utc'),**{key:diagnostic.get(key) for key in ('speed_profile','protocol_errors','reliable_terminal','retry_bytes','retransmissions','terminal_reason')},
                                   first_failure=lifecycle.get('first_failure'),first_close=lifecycle.get('first_close')))
    exclusions = []
    if before.get('protocol_errors',0):
        exclusions.append('Android protocol errors already nonzero before measured load; not new request failures')
    if after.get('protocol_errors',0):
        exclusions.append('Android session has protocol errors; exact first time requires separate observations')
    if any(row.get('protocol_errors',0) for row in server):
        exclusions.append('Gateway whole-session terminal protocol counter nonzero; first error time unknown')
    if any(row.get('reliable_terminal') not in (None,'','closed','cancelled') for row in server):
        exclusions.append('Gateway terminal failure retained; does not negate completed body delivery')
    result = dict(phase=phase,session_tag=before['session_tag'],location=location,source_sha256=digest(source),
                  counter_scope='same-session Android preflight export to later current/history snapshot; includes time/background outside bulk',
                  observed_interval_ms=[before['observed_at_ms'],after.get('observed_at_ms')],after=counters,delta=deltas,
                  android_terminal={key:after.get(key) for key in ('terminal_reason','reliable_terminal','terminal_at_ms','terminal_observed_at_ms')},
                  gateway_terminal=server,gateway_counter_scope='whole session startup to terminal; first error time unknown unless trace proves it',
                  clean_acceptance=False,clean_exclusion_reasons=exclusions,needs_review=bool(deltas['protocol_errors']) or bool(server),
                  caveats=['archive presence is not a terminal-completion receipt','late errors do not negate already received HTTP bodies',
                           'RS retry count is not packet-loss count; no early/local/network classification from totals alone'])
    destination = WORK/('post-'+phase+'-'+label+'.json')
    assert not destination.exists()
    destination.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(phase=phase,location=location,android_counter_delta=deltas,gateway_terminal=server,clean_acceptance=False)))


if __name__ == '__main__':main()
