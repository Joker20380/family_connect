"""No counter rewriting: fresh complete lifecycle evidence gates owner acceptance."""
import argparse
import json
from prepare import WORK


def classify(diagnostic):
    life=diagnostic.get('mux_lifecycle') or {}
    incidents=life.get('incidents') or []
    raw=diagnostic.get('protocol_errors')
    expected_raw=sum(row.get('class')=='expected' and row.get('stream',{}).get('removed',0)>0 for row in incidents)
    complete=not life.get('incident_dropped') and not life.get('projection_overflow')
    complete=complete and len(incidents)==sum(life.get(key,-1000000) for key in ('expected_crossings','actual_violations','unclassified'))
    clean=complete and life.get('actual_violations')==0 and life.get('unclassified')==0 and raw==expected_raw
    return dict(raw_protocol_errors=raw,expected_crossings=life.get('expected_crossings'),expected_raw=expected_raw,
                actual_violations=life.get('actual_violations'),unclassified=life.get('unclassified'),
                incident_dropped=life.get('incident_dropped'),complete=complete,clean=clean,incidents=incidents,
                raw_counter_not_rewritten=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('label');args=parser.parse_args()
    close=json.loads((WORK/(args.label+'-close-control-receipt.json')).read_text())
    before=json.loads((WORK/(args.label+'-close-control-before.json')).read_text())
    gateway=close['gateway_terminal']['diagnostic']
    result=dict(android=classify(before['restricted_session']),gateway=classify(gateway),
                android_cleanup=close.get('android_cleanup'),gateway_terminal_before_disconnect=close['gateway_terminal_before_disconnect'],
                gateway_terminal=gateway.get('terminal_reason'),reliable_terminal=gateway.get('reliable_terminal'),
                close_seconds=close['seconds'],session_tag=close['session_tag'])
    with (WORK/(args.label+'-audit.json')).open('x') as output:json.dump(result,output,indent=2)
    print(json.dumps({endpoint:{key:value for key,value in result[endpoint].items() if key!='incidents'} for endpoint in ('android','gateway')}))


if __name__=='__main__':main()
