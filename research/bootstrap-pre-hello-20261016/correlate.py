import argparse
import json
from pathlib import Path
import re


def correlate(startup, records):
    header = records[0] if records else {}
    footer = records[-1] if len(records) > 1 else {}
    events = [entry for entry in records if 'sequence' in entry]
    status = 'COMPLETE_WINDOW'
    if header.get('enabled') is not True:
        status = 'DISABLED_OR_UNAVAILABLE'
    elif footer.get('stopped') is not True or footer.get('written') != len(events) or [entry['sequence'] for entry in events] != list(range(1, len(events)+1)):
        status = 'INCOMPLETE_OUTPUT'
    elif footer.get('limited') is not False:
        status = 'LIMITED_OR_UNKNOWN'
    elif not header.get('until_ms', 0)-900000 <= startup.get('started_unix_ms', 0) < header.get('until_ms', 0):
        status = 'EXPIRED_OR_OUTSIDE_WINDOW'
    tags = {entry.get('bootstrap_exchange_tag') for entry in startup.get('bootstrap_exchanges', [])
            if re.fullmatch('[0-9a-f]{64}', entry.get('bootstrap_exchange_tag', ''))}
    matches = []
    for event in events:
        if event.get('exchange') in tags and event.get('action') in ('authenticated', 'busy', 'wait', 'wait_end', 'grant', 'hello_sent', 'exchange_end'):
            safe = {key: event[key] for key in ('sequence', 'exchange', 'action', 'holder_exchange', 'generation', 'holder_state', 'same_identity', 'reason') if key in event}
            safe['holder_role'] = 'UNKNOWN'
            matches.append(safe)
    return dict(capture_status=status, requester_evidence='OBSERVED' if matches else 'NOT_OBSERVED',
                holder_absence='NOT_PROVEN', matches=matches)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Offline bounded correlation; never contacts a gateway')
    parser.add_argument('startup', type=Path)
    parser.add_argument('capture', type=Path)
    args = parser.parse_args()
    if args.startup.stat().st_size > 1048576 or args.capture.stat().st_size > 1048576:
        raise SystemExit('Input bound exceeded')
    startup = json.loads(args.startup.read_text())
    records = []
    for line in args.capture.read_text().splitlines()[:514]:
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            break
    print(json.dumps(correlate(startup, records), indent=2))
