"""Evidence-only labels; never changes runtime or historical protocol counters."""


def classify(records):
    tags={record['session_tag'] for record in records}
    if len(tags)!=1:raise ValueError('One endpoint/session generation required')
    events={};incidents={};failures=[]
    for record in records:
        life=record.get('mux_lifecycle') or {}
        if life.get('failure_at'):failures.append(life['failure_at'])
        for event in life.get('events',[]):events[event['index']]=event
        first=life.get('first_unknown')
        if first:
            incidents[first['event']['index']]=first
            events[first['event']['index']]=first['event']
    labels=[]
    for index,event in sorted(events.items()):
        if event['stage']!='unknown':continue
        first=incidents.get(index,{})
        before=[value for number,value in sorted(events.items()) if number<index and value['id']==event['id']]
        finished=[value for value in before if value['stage']=='finish']
        removed=[value for value in before if value['stage']=='remove']
        created=any(value['stage']=='create' for value in before)
        retired=first.get('stream',{})
        known=(first.get('known') and retired.get('id')==event['id'] and retired.get('reason')=='reset'
               and 0<retired.get('created',0)<=retired.get('finished',0)<=retired.get('removed',0)<=event['at'])
        known=known or (created and finished and removed and finished[-1]['reason']=='reset'
                        and finished[-1]['index']<removed[-1]['index'])
        prior_failure=first.get('failure_at',0) or (min(failures) if failures and min(failures)<=event['at'] else 0)
        if prior_failure or first.get('cancelled'):
            label='AFTER_PRIMARY_FAILURE_OR_CANCELLATION'
        elif event['kind']==6 and known:
            label='PROVEN_LATE_RESET_OF_RETIRED_RESET_STREAM'
        elif event['kind'] in (7,8) and known:
            label='PROVEN_LATE_CONTROL_OF_RETIRED_RESET_STREAM'
        else:label='UNCLASSIFIED_PROTOCOL_EVENT'
        labels.append(dict(index=index,id=event['id'],kind=event['kind'],at=event['at'],classification=label))
    raw=max(record.get('protocol_errors',0) for record in records)
    proven=sum(value['classification']=='PROVEN_LATE_RESET_OF_RETIRED_RESET_STREAM' for value in labels)
    controls=sum(value['classification']=='PROVEN_LATE_CONTROL_OF_RETIRED_RESET_STREAM' for value in labels)
    return dict(session_tag=next(iter(tags)),raw_protocol_errors=raw,proven_late_resets=proven,
                proven_late_controls=controls,remaining_unexplained=max(0,raw-proven-controls),events=labels,
                counter_unchanged=True,request_outcome_not_inferred=True)
