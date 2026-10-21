"""Reconcile the first small gate's TUN change with the saved ordinary export."""

import datetime
import json

from preserve import WORK, digest


def main():
    export=WORK/'owner-beta91-export.json'
    ring=json.loads(export.read_text())['ring']
    assert ring['version_code']==91 and ring['state']=='CONNECTED'
    events=ring['events']
    connections={event['connection_id'] for event in events if event['state_to']!='DISCONNECTED'}
    assert len(connections)==1
    assert not any(event['state_to'] in ('RESTORING','FAILED') or event['retry_count'] for event in events)
    captures=[event for event in events if event['reason_code']=='VPN_CAPTURE_READY']
    assert len(captures)==2 and all(event['state_to']=='CONNECTING' for event in captures)
    preflight=json.loads((WORK/'small/preflight.json').read_text())
    preflight_ms=datetime.datetime.fromisoformat(preflight['utc']).timestamp()*1000
    assert captures[0]['timestamp']<preflight_ms<captures[1]['timestamp']
    rows=[dict(utc=datetime.datetime.fromtimestamp(event['timestamp']/1000,datetime.timezone.utc).isoformat(),
               component=event['component'],reason=event['reason_code'],
               before=event['state_from'],after=event['state_to'],retry=event['retry_count'])
          for event in events]
    result=dict(export_sha256=digest(export),classification='INITIAL_BLOCKING_TO_WORKING_TUN',
                evidence=rows,preflight=preflight['utc'],first_small_gate_pass=False,
                explanation='The failed topology gate remains failed; both VPN captures precede CONNECTED, '
                            'with one connection, no restoration or failed health series. Exact AutomaticVpnOwner '
                            'and RestrictedTunnelEngine sources establish the blocking and working TUN separately.',
                limitation='Export does not carry interface names. Interface mapping is inferred from the '
                           'two captures and preflight/postflight, not a direct kernel transition trace.')
    with (WORK/'small/startup-classification.json').open('x') as output:json.dump(result,output,indent=2)
    print(json.dumps(dict(classification=result['classification'],events=len(rows),sha256=result['export_sha256'])))


if __name__=='__main__':main()
