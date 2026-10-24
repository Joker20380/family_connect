"""Public synthetic inputs for the accepted106 diagnostic projection contract."""
import copy


def support_cases():
    result = {name: dict(state='RESTORING', network_class='WIFI', restricted_readiness='READY',
                         vpn_capture_open=False, restricted_session=value['session']) for name, value in cases().items()}
    result['empty'] = {}
    for name in ('state', 'network_class', 'restricted_readiness', 'vpn_capture_open'):
        result['invalid-'+name] = dict(result['complete'], **{name: 'PRIVATE'})
    for index, value in enumerate((True, -1, 2**53, 1.5, 'PRIVATE', None, [], {})):
        source = copy.deepcopy(result['complete'])
        source['restricted_session']['protocol_errors'] = value
        result['invalid-counter-'+str(index)] = source
    source = copy.deepcopy(result['complete'])
    source.update(token='PRIVATE', room_url='https://private.invalid/', messages=['PRIVATE'])
    source['restricted_session']['private_key'] = 'PRIVATE'
    result['private-fields'] = source
    return result


def baseline():
    tag = 'a'*64
    flow = dict(send_base=1, send_next=3, receive_next=2, receive_mask=1, ack_base=1, ack_mask=0,
                pending=2, buffered=1, head_retries=2, ack_seen=True, head_sacked=False)
    assembly = dict.fromkeys('fragments completed expired malformed duplicate conflict capacity crc_failed recent pending rtp rtp_gaps vp8_frames'.split(), 0)
    point = dict(sender=1, message=2, total=2, mask=1, data_sequence=3, data_known=True)
    delivery = dict(flow=flow, assembly=assembly, **{name: dict(point) for name in ('pending', 'queued', 'written', 'received')})
    event = dict(session_tag=tag, sequence=2, timestamp_ms=1010, stage='CARRIER_ACTIVITY', state='TX', reason='NONE',
                 tx=100, rx=50, reliable_pending=2, reliable_retries=1, delivery=delivery)
    failure = dict(event, sequence=1, state='FAILED', stage='ICE', reason='ICE_FAILED')
    close = dict(event, sequence=3, stage='LOCAL_CLOSE', state='CLOSED', close_source='PARENT_CANCELLED',
                 close_code=1000, heartbeat_kind='WEBSOCKET', target='SUBSCRIBER', close_reason='shutdown')
    boundary = dict(index=1, at_ms=1001, data_sequence=3, data_known=True, attempt=1, attempt_known=True,
        sender=1, message=2, total=2, fragment=0, message_known=True, timestamp=4, media_track=5,
        first_rtp=100, last_rtp=101, packets=2, frame_known=True, ack_base=1, ack_mask=0,
        stage='reliable_send', result='ok', direction='tx')
    mux_event = dict(index=1, at=1100, id=7, kind=3, stage='receive', reason='wire')
    stream = dict(id=7, created=1000, opened=1010, finished=1030, removed=1040, sent=128, received=256,
        used=0, send_credit=131072, receive_credit=131072, local_fin=True, remote_fin=False,
        local_abort=False, peer_terminal=False, peer_close=False, reason='none',
        **{name: list(range(1000, 1009)) for name in ('enqueued', 'send_started', 'send_done', 'receive_at')})
    incident = dict(failure_at=1110, bytes=32, credit=64, known=True, cancelled=False, event=mux_event,
                    stream=stream, **{'class': 'expected', 'detail': 'inflight_data_on_abort'})
    session = dict(session_tag=tag, correlation_status='VALID', terminal_reason='NONE', reliable_terminal='',
        signaling_failure='NONE', ice_failure='NONE', subscriber_state='connected', publisher_state='connected',
        speed_profile='P1', reliable_limits=dict(local_send=32, local_receive=32, peer_receive=32, effective_send=32, local_write_completion=True),
        mux_profile='CREDIT128', mux_window=131072, retry_bytes=12,
        lifecycle=dict(session_tag=tag, correlation_status='VALID', trace_dropped=0, export_dropped=0, delivery_dropped=0,
                       first_failure=failure, first_close=close, trace=[event, close], boundaries=dict(dropped=1, events=[boundary])),
        mux_lifecycle=dict(dropped=0, failure_at=1110, close_at=1120, incident_dropped=0, expected_crossings=1,
                           actual_violations=0, unclassified=0, failure_reason='none', events=[mux_event], first_unknown=incident, incidents=[incident]))
    startup = dict(schema=1, attempt=2, started_unix_ms=1000, observed_ms=1050, completed_ms=0, complete=False,
        status='RUNNING', stage='SEED_READ', cause='IO_DEADLINE', directory_fingerprint='b'*64,
        observation=dict(bootstrap_exchange_tag='c'*64, point='FAMILY_RECEIVE', error_category='IO_DEADLINE', context_state='LIVE', stop_at_observation='NONE', elapsed_ms=50),
        local_stop=dict(source='NONE', elapsed_ms=0), bootstrap_exchanges_dropped=0,
        bootstrap_exchanges=[dict(bootstrap_exchange_tag='c'*64, family_authenticated=True)])
    return copy.deepcopy(dict(session=session, startup=startup))


def cases():
    result = {'complete': baseline()}
    def altered(name, path, value):
        selected = baseline()
        parent = selected
        for part in path[:-1]:parent = parent[part]
        parent[path[-1]] = value
        result[name] = selected
    for name, value in (('peer-zero', 0), ('peer-sixteen', 16)):
        altered(name, ('session', 'reliable_limits'), dict(local_send=32, local_receive=32, peer_receive=value, effective_send=value, local_write_completion=True))
    altered('p0', ('session', 'speed_profile'), 'P0')
    altered('legacy64', ('session', 'mux_profile'), 'LEGACY64')
    result['legacy64']['session']['mux_window'] = 65536
    altered('bad-credit-receipt', ('session', 'mux_window'), 65536)
    altered('bad-effective-window', ('session', 'reliable_limits', 'effective_send'), 16)
    altered('missing-write-completion', ('session', 'reliable_limits'), dict(local_send=32, local_receive=32, peer_receive=32, effective_send=32))
    altered('mismatched-lifecycle-tag', ('session', 'lifecycle', 'session_tag'), 'd'*64)
    altered('invalid-correlation', ('session', 'lifecycle', 'correlation_status'), 'INVALID')
    altered('bad-first-event-tag', ('session', 'lifecycle', 'first_failure', 'session_tag'), 'd'*64)
    altered('bad-first-event-sequence', ('session', 'lifecycle', 'first_failure', 'sequence'), 0)
    altered('close-code-outside-range', ('session', 'lifecycle', 'first_close', 'close_code'), 999)
    altered('unknown-close-source', ('session', 'lifecycle', 'first_close', 'close_source'), 'PRIVATE-DO-NOT-EXPORT')
    for name, path, value in (
        ('flow-window', ('flow', 'send_next'), 34), ('flow-mask', ('flow', 'ack_mask'), 4294967296),
        ('flow-flag', ('flow', 'ack_seen'), 1), ('flow-ack-base', ('flow', 'ack_base'), 4),
        ('assembly-pending', ('assembly', 'pending'), 17), ('fragment-mask', ('pending', 'mask'), 4),
        ('unknown-data-sequence', ('pending', 'data_known'), False)):
        altered(name, ('session', 'lifecycle', 'trace', 0, 'delivery', *path), value)
    original = baseline()['session']['lifecycle']['trace'][0]
    altered('trace-capacity', ('session', 'lifecycle', 'trace'), [dict(original, sequence=index+1) for index in range(200)])
    altered('trace-order', ('session', 'lifecycle', 'trace'), [dict(original, sequence=index) for index in (2, 2, 1, 3)])
    altered('trace-invalid-enum', ('session', 'lifecycle', 'trace', 0, 'reason'), 'private-proof')
    boundary = baseline()['session']['lifecycle']['boundaries']['events'][0]
    altered('boundary-capacity', ('session', 'lifecycle', 'boundaries', 'events'), [dict(boundary, index=index+1) for index in range(70)])
    altered('boundary-order', ('session', 'lifecycle', 'boundaries', 'events'), [dict(boundary, index=index) for index in (1, 1, 2)])
    altered('boundary-attempt', ('session', 'lifecycle', 'boundaries', 'events', 0, 'attempt'), 33)
    altered('boundary-rtp', ('session', 'lifecycle', 'boundaries', 'events', 0, 'last_rtp'), 65536)
    altered('boundary-flag', ('session', 'lifecycle', 'boundaries', 'events', 0, 'frame_known'), 'true')
    altered('boundary-direction', ('session', 'lifecycle', 'boundaries', 'events', 0, 'direction'), 'secret')
    mux = baseline()['session']['mux_lifecycle']
    altered('mux-event-capacity', ('session', 'mux_lifecycle', 'events'), [dict(mux['events'][0], index=index) for index in range(40)])
    altered('mux-incident-capacity', ('session', 'mux_lifecycle', 'incidents'), [copy.deepcopy(mux['incidents'][0]) for _ in range(40)])
    altered('mux-array-bound', ('session', 'mux_lifecycle', 'first_unknown', 'stream', 'send_done'), list(range(15)))
    altered('mux-unknown-enum', ('session', 'mux_lifecycle', 'first_unknown', 'detail'), 'private-proof')
    altered('startup-unknown-cause', ('startup', 'cause'), 'private-proof')
    altered('startup-cancel-after-io-deadline', ('startup', 'local_stop'), dict(source='CONNECT_CANCEL', elapsed_ms=51))
    altered('startup-wrong-schema', ('startup', 'schema'), 2)
    altered('startup-missing-complete', ('startup', 'complete'), None)
    altered('startup-exchanges-capacity', ('startup', 'bootstrap_exchanges'), [dict(bootstrap_exchange_tag=format(index, '064x'), family_authenticated=True) for index in range(6)])
    altered('startup-invalid-tag', ('startup', 'bootstrap_exchanges', 0, 'bootstrap_exchange_tag'), 'private-room-url')
    result['private-fields'] = baseline()
    for value in (result['private-fields']['session'], result['private-fields']['startup'],
                  result['private-fields']['session']['lifecycle']['trace'][0]['delivery']['flow'],
                  result['private-fields']['session']['mux_lifecycle']['first_unknown']['stream']):
        value.update(private_key='PRIVATE-DO-NOT-EXPORT', room_url='PRIVATE-DO-NOT-EXPORT', proof='PRIVATE-DO-NOT-EXPORT', message_text='PRIVATE-DO-NOT-EXPORT')
    return result


def projected(implementation, value):
    projector = implementation()
    session = projector.session(value['session'])
    fields = ('speed_profile', 'reliable_limits', 'retry_bytes', 'mux_profile', 'mux_window', 'lifecycle', 'mux_lifecycle')
    return dict(session={name: session[name] for name in fields if name in session}, startup=projector.startup(value['startup']))
