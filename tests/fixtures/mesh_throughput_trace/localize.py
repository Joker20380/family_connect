"""Conservative sender-local SACK evidence; missing trace is not packet loss."""

import hashlib
import json
from pathlib import Path
import sys


def localize(result):
    wires = {block['wire'] for block in result['logical_data'] if any(
        event['node'] == 'NL' and event['point']['kind'] == 'submission' for event in block['events'])}
    assert len(wires) == 1
    wire = wires.pop()
    acks = sorted((event for event in result['ack_events'] if event['node'] == 'NL'
        and event['point']['kind'] == 'ack_input' and event['point']['wire'] == wire
        and event['point']['result'] == 'accepted'), key=lambda event: event['point']['ns'])
    opportunities, controls = [], []
    for block in result['logical_data']:
        if block['wire'] != wire:
            continue
        points = sorted((event['point'] for event in block['events'] if event['node'] == 'NL'), key=lambda point: point['ns'])
        submitted = next((point for point in points if point['kind'] == 'submission'), None)
        retry = next((point for point in points if point['kind'] == 'retry_timeout'), None)
        if not submitted:
            continue
        if not block['retries'] and submitted['bytes'] == 16384 and block['consumes'] == 1 and len(controls) < 3:
            controls.append(block)
        if not retry:
            continue
        sequence = block['sequence']
        for event in acks:
            ack = event['point']
            if ack['ns'] >= retry['ns']:
                break
            if ack['ns'] < submitted['ns'] + 250_000_000:
                continue
            base, mask = ack.get('base', 0), ack.get('mask', 0)
            if not base < sequence < base + 32 or mask & (1 << (sequence - base)):
                continue
            later = sum(bool(mask & (1 << bit)) for bit in range(sequence-base+1, 32))
            if later < 3:
                continue
            opportunities.append(dict(sequence=sequence, wire=wire, later_sacked=later,
                sender_eligible_to_timeout_ns=retry['ns']-ack['ns'], timeout_age_ns=retry['ns']-submitted['ns'],
                two_sided=block['consumes'] == 1 and 'new' in block['receive_results'],
                evidence_ack=event, events=block['events'], intervals=block['local_intervals']))
            break
    examples = [value for value in opportunities if value['two_sided'] and value['sender_eligible_to_timeout_ns'] > 300_000_000][:6]
    return dict(nonhead_timeout_opportunities=len(opportunities),
        two_sided_opportunities=sum(value['two_sided'] for value in opportunities),
        over_300ms=sum(value['sender_eligible_to_timeout_ns'] > 300_000_000 for value in opportunities),
        examples=examples, controls=controls,
        interpretation='Existing >=3 later-SACK and RTO/4 guards already met; head-only condition delays other holes. Tick scheduling still applies.',
        limitations=['No inferred one-way latency', 'No unique retry-to-arrival attribution',
            'No identification of a specific SFU/network loss point', 'Ring gaps remain explicit; zero absence is not asserted'])


if __name__ == '__main__':
    path = Path(sys.argv[1])
    result = localize(json.loads(path.read_text()))
    result['input_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    with path.with_name('localization.json').open('x') as handle:
        json.dump(result, handle, indent=2)
    print(json.dumps({key: result[key] for key in ('nonhead_timeout_opportunities', 'two_sided_opportunities', 'over_300ms')}))
