"""Complete hop-local late-frame evidence; no cross-machine time subtraction."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
WORK=ROOT/'state-client-build/owner-disconnections-20261022'


def main():
    head=json.loads((WORK/'head85-analysis.json').read_text())
    events={}
    sources={}
    for path in sorted((WORK/'post102-connect').glob('*.json')):
        current=json.loads(path.read_text()).get('snapshot',{}).get('restricted_session',{})
        if current.get('session_tag')!=head['session_tag']:continue
        sources[str(path.relative_to(WORK))]=hashlib.sha256(path.read_bytes()).hexdigest()
        for event in current.get('lifecycle',{}).get('boundaries',{}).get('events',[]):
            if event.get('direction')=='rx':events[event['index']]=event
    matches=[]
    for pair in head['pairs']:
        for prefix in pair['receiver']:
            tails=[event for event in events.values() if event['index']<prefix['index']
                and event.get('timestamp')==prefix.get('timestamp') and event.get('media_track')==prefix.get('media_track')
                and event.get('stage')=='rtp_received' and event.get('result')=='ok'
                and event.get('first_rtp')==event.get('last_rtp')==(prefix['last_rtp']+1)%65536]
            drops=[event for event in events.values() if event['index']<prefix['index']
                and event.get('timestamp')==prefix.get('timestamp') and event.get('media_track')==prefix.get('media_track')
                and event.get('result')=='old_rtp' and prefix['first_rtp']<=event.get('first_rtp',-1)<=prefix['last_rtp']]
            assert len(tails)==1 and len(drops)==2 and pair['sender']['packets']==3
            assert not any(event.get('stage')=='vp8_reassembled' and event.get('timestamp')==prefix['timestamp'] for event in events.values())
            matches.append(dict(attempt=pair['sender']['attempt'],sender=pair['sender'],tail=tails[0],prefix=prefix,drops=drops,
                same_receiver_delay_ms=drops[0]['at_ms']-tails[0]['at_ms'],received_packets=3))
    all_late=[]
    for event in events.values():
        if event.get('result')!='old_rtp':continue
        tails=[other for other in events.values() if other['index']<event['index'] and other.get('timestamp')==event.get('timestamp')
            and other.get('stage')=='rtp_received' and other.get('result')=='ok']
        if tails:all_late.append(event['at_ms']-min(other['at_ms'] for other in tails))
    result=dict(session_tag=head['session_tag'],sources=sources,matches=matches,receiver_late_delays_ms=sorted(set(all_late)),
        conclusion='All three hop-local RTP packet numbers are observed for attempts6/7. Prefix packets are explicitly discarded as old_rtp after the100ms reorder budget; complete RS DATA85 never reaches VP8 assembly in retained evidence.',
        unknown=['Why the prefix is delayed before track.Read','Other unretained attempts and other sessions','Live effect of750ms candidate'],
        candidate=dict(reorder_ms=750,observed_max_ms=max(all_late),margin_ms=750-max(all_late),rs_rto_ms=1000,
            retries_unchanged=True,memory_window_unchanged=256,expiry='On next packet, not a new wall-clock timer'))
    with (WORK/'reorder-complete-frame-analysis.json').open('x') as output:json.dump(result,output,indent=2);output.write('\n')
    print('COMPLETE_LATE_FRAMES',len(matches),'DELAYS_MS',result['receiver_late_delays_ms'])


if __name__=='__main__':main()
