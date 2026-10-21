"""Join the preserved beta90 head with NL evidence, without inventing coverage."""

import collections
import json
import os
import sys

from preserve import ROOT, WORK, digest

sys.path.insert(0, str(ROOT / 'tests/fixtures/queue_retry'))
from journal import reassemble, performance_lines
sys.path.insert(0, str(ROOT / 'tests/fixtures/mesh_throughput_trace'))
from correlate import reconstruct

TAG = '2219e060af8bc8a0532e29b7e55e5e2bda5eb68f592264d98400d174de714b5c'


def objects(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from objects(child)


def main():
    os.umask(0o077)
    path = WORK / 'owner-beta90-export.json'
    export = json.loads(path.read_text())
    assert export['ring']['version_code'] == export['incident']['version_code'] == 90
    android = next(item for item in export['incident']['restricted_history'] if item.get('session_tag') == TAG)
    lifecycle = android['lifecycle']
    boundaries = lifecycle['boundaries']['events']
    journal_lines = []
    for line in (WORK / 'previous-evidence/a-measure-fixed/capture-private.jsonl').read_text().splitlines():
        row = json.loads(line)
        if row['kind'] == 'journal':
            journal_lines.append(row['raw'])
    journal, join_errors = reassemble(journal_lines)
    records, parser_errors = reconstruct(performance_lines(journal))
    points = {}
    for record in records:
        if record.get('session_tag') != TAG:
            continue
        for point in record['performance']['Trace']['points']:
            points[point['i']] = point
    logical = [item for item in points.values() if item.get('seq') == 597 or item.get('base') == 597]
    matches = []
    legacy_errors = []
    for row in journal:
        message = row['MESSAGE']
        if TAG not in message or 'restricted_performance_' in message[:100]:
            continue
        try:
            value = json.loads(message)
        except ValueError:
            legacy_errors.append(dict(timestamp=row.get('__REALTIME_TIMESTAMP'), error='invalid_legacy_json'))
            continue
        for item in objects(value):
            if item.get('stage') and (item.get('data_sequence') == 597 or item.get('message') == 4260144682):
                matches.append(item)
    unique = {json.dumps(item, sort_keys=True): item for item in matches}
    result = dict(session=TAG, android_export_sha256=digest(path), android_version=90,
                  android_observed_at_ms=android['observed_at_ms'], android_summary={key: android[key] for key in
                    ('native_state', 'terminal_reason', 'subscriber_state', 'publisher_state', 'retransmissions',
                     'received_frames', 'sent_frames', 'protocol_errors', 'sent_bytes', 'received_bytes')},
                  android_coverage={key: value for key, value in lifecycle.items() if key.endswith('dropped')},
                  android_boundaries_dropped=lifecycle['boundaries']['dropped'],
                  android_boundaries=boundaries, nl_transport=sorted(logical, key=lambda item: item['i']),
                  nl_legacy_matches=list(unique.values()),
                  errors=dict(journal=join_errors, performance=parser_errors, legacy=legacy_errors),
                  same_clock_intervals_only=True)
    (WORK / 'saved-head597.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(dict(android_boundaries=len(boundaries), android_boundaries_dropped=result['android_boundaries_dropped'],
                          android_head_events=[item for item in boundaries if item.get('data_sequence') == 597],
                          nl_logical_events=len(logical), nl_legacy_matches=len(unique),
                          errors={key:len(value) for key,value in result['errors'].items()})))


if __name__ == '__main__':
    main()
