import time


class PreparationAborted(Exception):
    pass


def candidate(status, session, export_failure):
    sample = dict(utc_ms=int(time.time() * 1000), session=session,
                  direction='client_to_gateway', reason='endpoint_unavailable')
    try:
        current = status({'operation': 'status'})
        sample['reason'] = 'invalid_status'
        diagnostic = current['stats']['packet']['diagnostic']
        if diagnostic['session_tag'] != session or current['healthy'] is not True or diagnostic['reliable_terminal'] is not False:
            raise PreparationAborted('SESSION_UNHEALTHY_OR_CHANGED')
        events = [event for event in diagnostic['lifecycle']['trace']
                  if event.get('delivery', {}).get('flow')]
        if not events:
            raise PreparationAborted('NO_FLOW_SAMPLE')
        event = events[-1]
        if event['session_tag'] != session:
            raise PreparationAborted('WRONG_FLOW_SESSION')
        flow = event['delivery']['flow']
        fields = {name: flow[name] for name in ('pending', 'send_base', 'send_next')}
        fields.update(sequence=event['sequence'], timestamp_ms=event['timestamp_ms'],
                      observed_at_ms=diagnostic['observed_at_ms'])
        if any(type(value) is not int or value < 0 for value in fields.values()):
            raise PreparationAborted('INVALID_FLOW_SAMPLE')
        sample.update(fields)
        if any(previous['sequence'] >= event['sequence'] or previous['timestamp_ms'] > event['timestamp_ms']
               for previous in events[:-1]):
            raise PreparationAborted('REGRESSING_FLOW_SAMPLE')
        return current, flow
    except Exception as primary:
        try:
            export_failure(dict(error_type=type(primary).__name__, samples=[sample]))
        except Exception:
            pass
        raise
