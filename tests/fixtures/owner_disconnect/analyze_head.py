"""Join retained head85 by sender/message, never by subtracting endpoint clocks."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
WORK=ROOT/'state-client-build/owner-disconnections-20261022'


def main():
    remote_path=WORK/'accept-initial-recovery/gateway-analysis.json'
    remote=json.loads(remote_path.read_text())
    terminal=next(row['diagnostic'] for row in remote['records'] if row.get('event')=='session_terminal'
        and row.get('diagnostic',{}).get('session_tag','').startswith('2aca1f37'))
    tag=terminal['session_tag']
    received={}
    sources={str(remote_path.relative_to(WORK)):hashlib.sha256(remote_path.read_bytes()).hexdigest()}
    for path in sorted((WORK/'post102-connect').glob('*.json')):
        current=json.loads(path.read_text())['snapshot'].get('restricted_session',{})
        if current.get('session_tag')!=tag:continue
        sources[str(path.relative_to(WORK))]=hashlib.sha256(path.read_bytes()).hexdigest()
        for event in current.get('lifecycle',{}).get('boundaries',{}).get('events',[]):
            if event['direction']=='rx':received[event['index']]=event
    sent=[event for event in terminal['lifecycle']['boundaries']['events'] if event.get('data_known')
        and event.get('data_sequence')==85 and event['stage']=='rtp_written' and event['result']=='ok']
    pairs=[]
    for event in sent:
        matching=[value for value in received.values() if value.get('message_known') and value.get('sender')==event['sender']
            and value.get('message')==event['message']]
        pairs.append(dict(sender=event,receiver=matching,complete_vp8_observed=any(value['stage']=='vp8_reassembled' and value['result']=='ok' for value in matching)))
    result=dict(session_tag=tag,sources=sources,pairs=pairs,receiver_old_rtp=[event for event in received.values() if event['result']=='old_rtp'],
        conclusion='Actual sender RTP writes for retained attempts; matched receiver frames incomplete where present. Missing samples are not absent packets. No proof of timer-before-write or exact physical loss location.',
        constraints=['SFU RTP identifiers differ across legs','Ring gaps and dropped counts retained','No payload or packet logger','No cross-clock latency subtraction'])
    destination=WORK/'head85-analysis.json'
    with destination.open('x') as output:json.dump(result,output,indent=2);output.write('\n')
    print('HEAD85_PAIRS',[(pair['sender']['attempt'],pair['sender']['packets'],[(event['stage'],event['result'],event.get('packets')) for event in pair['receiver']]) for pair in pairs])


if __name__=='__main__':main()
