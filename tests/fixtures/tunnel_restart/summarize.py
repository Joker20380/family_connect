"""Create a sanitized, bounded first-cause summary from the preserved evidence."""

from collections import Counter
import datetime
import json

from preserve import WORK, digest


def utc(milliseconds):
    return datetime.datetime.fromtimestamp(milliseconds / 1000, datetime.timezone.utc).isoformat()


def main():
    export = json.loads((WORK / 'owner-export.json').read_text())
    ring = export['ring']
    events = ring['events']
    sessions = []
    for session in ring['restricted_history']:
        lifecycle = session.get('lifecycle', {})
        first = lifecycle.get('first_failure', {})
        accepted = ('stage', 'state', 'reason', 'close_source', 'close_reason', 'timestamp_ms',
                    'reliable_age_ms', 'reliable_retries', 'reliable_pending', 'reliable_ack_age_ms',
                    'reliable_progress_age_ms', 'reliable_ack_received')
        sessions.append(dict(tag=session['session_tag'], terminal_utc=utc(session['terminal_at_ms']),
            first={key: first[key] for key in accepted if key in first},
            flow=first.get('delivery', {}).get('flow', {}),
            drops={key: value for key, value in lifecycle.items() if key.endswith('_dropped')}))
    rows = []
    initial = (WORK / 'NL-episodes.jsonl').read_text().splitlines()
    runtime = json.loads(initial[0])
    rows.extend(json.loads(line) for line in initial[1:])
    management = (WORK / 'NL-management.jsonl').read_text().splitlines()
    fatal = json.loads(management[0])
    for line in management[1:]: rows.extend(json.loads(line)['rows'])
    causal, malformed = [], []
    for record in rows:
        message = record.get('MESSAGE', '')
        try: value = json.loads(message)
        except (TypeError, ValueError):
            if isinstance(message, str) and message.startswith('{'):
                malformed.append(dict(bytes=len(message.encode()), invocation=record.get('_SYSTEMD_INVOCATION_ID')))
            continue
        trace = value.get('trace', {})
        if trace.get('reason') not in (None, '', 'NONE'):
            causal.append({key: trace[key] for key in ('session_tag', 'timestamp_ms', 'stage', 'state', 'reason', 'close_source',
                'reliable_age_ms', 'reliable_retries', 'reliable_pending', 'reliable_ack_age_ms', 'reliable_progress_age_ms') if key in trace})
    tests = {}
    for name in ('gateway-race.jsonl', 'gateway-race-rerun.jsonl', 'reliable-race.jsonl'):
        for line in (WORK / 'tests' / name).read_text().splitlines():
            try: item = json.loads(line)
            except ValueError: continue
            if item.get('Test') and item['Action'] in ('pass', 'fail', 'skip'):
                tests[(item['Package'], item['Test'])] = item['Action']
    result = dict(source_checkpoint='dddc3347db5b02896c123488f2e5e0292ff2b7a7',
        export_sha256=digest(WORK / 'owner-export.json'), export_bytes=(WORK / 'owner-export.json').stat().st_size,
        ring_version=ring['version_code'], stale_incident_version=export['incident']['version_code'],
        android_sessions=sessions, android_events=[dict(utc=utc(event['timestamp']), **{key: event[key] for key in
            ('event','reason_code','component','state_from','state_to','retry_count') if key in event})
            for event in events if event.get('event') or event.get('reason_code') == 'NETWORK'],
        dns_reasons=dict(Counter(event.get('reason_code') for event in events if event.get('component') == 'DNS')),
        gateway_runtime=runtime, gateway_causal_events=causal,
        seed_fatals=[{key: record[key] for key in ('timestamp_utc','invocation_id','pid','binary_sha256','first_stage',
            'first_cause','seed_close_source','signaling_read','fatal','signal','credential_headroom_seconds') if key in record}
            for record in fatal.values() if record],
        legacy_json_errors=malformed, gateway_journal_row_cap=600,
        tests=dict(go_cases_including_subtests=dict(Counter(tests.values())),
                   android_jvm=json.loads((WORK / 'android-build/receipt.json').read_text())['tests']))
    (WORK / 'summary.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(dict(dns=result['dns_reasons'],tests=result['tests'],legacy_json_errors=len(malformed))))


if __name__ == '__main__':
    main()
