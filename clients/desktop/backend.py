import ctypes
import hashlib
import json
import math
import urllib.request
import stat
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import uuid
import copy
import platform
from profile_config import validate, parse, parse_tcp, AWG_FIELDS, MAX_PROFILE


class NativeDiagnostics106:
    MAX_NUMBER = 9007199254740991
    TRACE_REASONS = 'NONE SIGNAL_WS_CLOSE ICE_DISCONNECTED ICE_FAILED PEER_CONNECTION_FAILED CARRIER_EOF CARRIER_ERROR FAMILY_TLS_EOF FAMILY_TLS_ERROR GATEWAY_CLOSE HEARTBEAT_TIMEOUT REMOTE_CLOSE RECOVERY_CLEANUP_FAILED RECOVERY_DESCRIPTOR_FAILED RECOVERY_JOIN_FAILED RECOVERY_CARRIER_FAILED RELIABLE_HANDSHAKE_TIMEOUT RELIABLE_FRAME_TIMEOUT RELIABLE_RETRY_EXHAUSTED UNKNOWN_INTERNAL'
    TRACE_STAGES = 'AUTHORIZED ROOM_CREATION DESCRIPTOR GATEWAY_JOIN SIGNALING WEBSOCKET ICE PEER_CONNECTION CARRIER CARRIER_ACTIVITY FAMILY_TLS GATEWAY_SESSION HEARTBEAT LIVENESS LOCAL_CLOSE REMOTE_CLOSE RECOVERY CLEANUP'
    TRACE_STATES = 'STARTED ESTABLISHED ISSUED TX RX FAILED CLOSED COMPLETED ATTEMPTED NOT_ATTEMPTED new checking connecting connected completed disconnected failed closed'
    BOUNDARY_STAGES = 'reliable_send carrier_queued carrier_written rtp_written rtp_received vp8_reassembled carrier_message_completed reliable_data_accepted ack_generated ack_sent ack_received'
    BOUNDARY_RESULTS = 'ok write_error no_rtp incomplete duplicate stale recent capacity conflict expired crc malformed protocol old_rtp window frame_discard'
    MUX_REASONS = 'none eof reset protocol cancelled deadline closed_pipe other'
    STARTUP_CAUSES = 'NONE CANCELLED DEADLINE IO_DEADLINE CLOSED_PIPE TIMEOUT_UNQUALIFIED CERTIFICATE_TIME_INVALID CERTIFICATE_INVALID CERTIFICATE_AUTHORITY CERTIFICATE_HOSTNAME PROVIDER_API CARRIER_CLOSED EOF PROTOCOL_REJECTED CREDENTIALS_REJECTED DESCRIPTOR_REJECTED DESCRIPTOR_EXPIRED EXCHANGE_CLOSED UNKNOWN'
    STARTUP_STOPS = 'NONE STARTUP_BUDGET CONNECT_CANCEL CLEANUP'

    def __init__(self):
        self.lost = 0

    def obj(self, value):
        if isinstance(value, dict) and len(value) <= 128:
            return value
        self.lost += 1
        return {}

    def number(self, value, maximum=None):
        return type(value) is int and 0 <= value <= (self.MAX_NUMBER if maximum is None else maximum)

    def tag(self, value):
        return isinstance(value, str) and re.fullmatch('[a-f0-9]{64}', value) is not None

    def pick(self, source, numbers='', flags='', choices=None, extra=()):
        source = self.obj(source)
        choices = choices or {}
        result = {}
        self.lost += len(set(source) - set(numbers.split()) - set(flags.split()) - set(choices) - set(extra))
        for name in numbers.split():
            if name in source:
                if self.number(source[name]):result[name] = source[name]
                else:self.lost += 1
        for name in flags.split():
            if name in source:
                if type(source[name]) is bool:result[name] = source[name]
                else:self.lost += 1
        for name, allowed in choices.items():
            if name in source:
                if isinstance(source[name], str) and source[name] in allowed.split('|'):result[name] = source[name]
                else:self.lost += 1
        return result

    def choices(self, **values):
        return {name: value.replace(' ', '|') for name, value in values.items()}

    def entries(self, value, maximum, *, first=False):
        if not isinstance(value, list):
            self.lost += value is not None
            return []
        self.lost += max(0, len(value)-maximum)
        return value[:maximum] if first else value[-maximum:]

    def object_entries(self, value, maximum, *, first=False):
        result = []
        for item in self.entries(value, maximum, first=first):
            if isinstance(item, dict):result.append(item)
            else:self.lost += 1
        return result

    def component(self, source, numbers, flags=''):
        selected = self.pick(source, numbers, flags)
        if set(selected) != set((numbers+' '+flags).split()):
            self.lost += 1
            return None
        return selected

    def delivery(self, value):
        source = self.obj(value)
        self.pick(source, extra=('flow', 'assembly', 'pending', 'queued', 'written', 'received'))
        result = {}
        if 'flow' in source:
            flow = self.component(source['flow'], 'send_base send_next receive_next receive_mask ack_base ack_mask pending buffered head_retries', 'ack_seen head_sacked')
            if flow and (0 <= flow['send_next']-flow['send_base'] <= 32 and flow['ack_base'] <= flow['send_next'] and
                    all(flow[name] <= 32 for name in ('pending', 'buffered', 'head_retries')) and
                    all(flow[name] <= 4294967295 for name in ('receive_mask', 'ack_mask'))):result['flow'] = flow
            else:self.lost += 1
        if 'assembly' in source:
            assembly = self.component(source['assembly'], 'fragments completed expired malformed duplicate conflict capacity crc_failed recent pending rtp rtp_gaps vp8_frames')
            if assembly and assembly['pending'] <= 16:result['assembly'] = assembly
            else:self.lost += 1
        for name in ('pending', 'queued', 'written', 'received'):
            if name not in source:continue
            point = self.component(source[name], 'sender message total mask data_sequence', 'data_known')
            if point and (point['sender'] <= 4294967295 and point['message'] <= 4294967295 and 1 <= point['total'] <= 8 and
                          point['mask'] < 1 << point['total'] and (point['data_known'] or point['data_sequence'] == 0)):
                result[name] = point
            else:self.lost += 1
        return result or None

    def boundaries(self, value):
        source = self.obj(value)
        result = self.pick(source, 'dropped', extra=('events', 'projection_dropped'))
        if 'dropped' not in result or not isinstance(source.get('events'), list):return None
        previous, rejected, events = 0, max(0, len(source['events'])-64), []
        numbers = 'index at_ms data_sequence attempt sender message fragment total timestamp media_track first_rtp last_rtp packets ack_base ack_mask'
        flags = 'data_known attempt_known message_known frame_known'
        for entry in self.entries(source['events'], 64):
            entry = self.obj(entry)
            point = self.pick(entry, numbers, flags, self.choices(stage=self.BOUNDARY_STAGES, result=self.BOUNDARY_RESULTS, direction='tx rx'))
            valid = all(name not in entry or name in point for name in (numbers+' '+flags).split())
            for names, maximum in (('attempt', 32), ('sender message timestamp media_track ack_mask packets', 4294967295), ('first_rtp last_rtp', 65535), ('fragment total', 8)):
                valid = valid and all(point.get(name, 0) <= maximum for name in names.split())
            if not valid or not {'index', 'at_ms', 'stage', 'result', 'direction'} <= point.keys() or point['index'] <= previous:
                rejected += 1;self.lost += 1;continue
            previous = point['index'];events.append(point)
        result.update(events=events, projection_dropped=rejected+self.count(source.get('projection_dropped', 0)))
        return result

    def count(self, value):
        if self.number(value):return value
        self.lost += 1
        return 0

    def trace_event(self, value, tag):
        source = self.obj(value)
        result = self.pick(source, 'sequence timestamp_ms tx rx reliable_age_ms reliable_retries reliable_pending reliable_sacked reliable_ack_age_ms reliable_progress_age_ms reliable_ack_received lease_deadline_ms lease_sequence close_code',
            choices=self.choices(stage=self.TRACE_STAGES, state=self.TRACE_STATES, reason=self.TRACE_REASONS,
                lease_action='offer request accepted applied confirmed', target='SUBSCRIBER PUBLISHER', heartbeat_kind='APPLICATION WEBSOCKET',
                close_reason='ping timeout duplicate expired inactivity shutdown restart invalid ack idle session READ_ERROR READ_TIMEOUT INVALID_MESSAGE WRITE_ERROR'),
            extra=('session_tag', 'close_source', 'delivery'))
        if source.get('session_tag') != tag or not {'stage', 'state', 'reason', 'sequence', 'timestamp_ms'} <= result.keys() or result['sequence'] == 0:
            self.lost += 1;return None
        result['session_tag'] = tag
        if source.get('close_source'):
            close = source['close_source']
            result['close_source'] = close if isinstance(close, str) and close in DesktopDiagnostics.CLOSE_SOURCES else 'UNKNOWN'
            self.lost += result['close_source'] == 'UNKNOWN' and close != 'UNKNOWN'
        if 'lease_action' not in result:result.pop('lease_sequence', None)
        if 'close_code' in result and not 1000 <= result['close_code'] <= 4999:result.pop('close_code');self.lost += 1
        if 'delivery' in source:
            delivery = self.delivery(source['delivery'])
            if delivery:result['delivery'] = delivery
        return result

    def trace(self, value, tag):
        source = self.obj(value)
        result = self.pick(source, 'trace_dropped export_dropped delivery_dropped archive_dropped',
            extra=('session_tag', 'correlation_status', 'boundaries', 'first_failure', 'first_close', 'trace', 'projection_dropped', 'delivery_projection_dropped'))
        if not self.tag(tag) or source.get('session_tag') != tag or source.get('correlation_status') != 'VALID':
            self.lost += bool(source);return None
        result.update(session_tag=tag, correlation_status='VALID')
        if 'boundaries' in source:
            boundaries = self.boundaries(source['boundaries'])
            if boundaries:result['boundaries'] = boundaries
        for name in ('first_failure', 'first_close'):
            if name not in source:continue
            event = self.trace_event(source[name], tag)
            if event and (event['reason'] != 'NONE' if name == 'first_failure' else 'close_source' in event):result[name] = event
        events, previous = [], 0
        raw = source.get('trace')
        rejected = max(0, len(raw)-192) if isinstance(raw, list) else 0
        for entry in self.entries(raw, 192):
            event = self.trace_event(entry, tag)
            if event and event['sequence'] > previous:previous = event['sequence'];events.append(event)
            else:rejected += 1;self.lost += bool(event)
        retained, removed = 0, 0
        for event in reversed(events):
            if 'delivery' in event:
                retained += 1
                if retained > 8:event.pop('delivery');removed += 1
        result.update(trace=events, projection_dropped=rejected+self.count(source.get('projection_dropped', 0)),
                      delivery_projection_dropped=removed+self.count(source.get('delivery_projection_dropped', 0)))
        self.lost += removed
        return result

    def mux_event(self, value):
        return self.pick(value, 'index at id kind', choices=self.choices(
            stage='create opened enqueue send_start send_done receive finish remove unknown failure close violation',
            reason='new peer lease socket control data batch local wire terminal missing caller '+self.MUX_REASONS))

    def mux_incident(self, value):
        source = self.obj(value)
        result = self.pick(source, 'failure_at bytes credit', 'known cancelled', self.choices(**{
            'class': 'expected violation unclassified',
            'detail': 'no_retained_history live_state after_session_failure malformed after_peer_terminal crossed_reset not_local_abort cancelled_open not_opened data_after_fin credit_overflow inflight_data_on_abort inflight_credit_on_abort duplicate_fin inflight_fin_on_abort close_before_fin crossed_close terminal_state'}), extra=('event', 'stream'))
        if isinstance(source.get('event'), dict):result['event'] = self.mux_event(source['event'])
        if isinstance(source.get('stream'), dict):
            stream = source['stream']
            times = ('enqueued', 'send_started', 'send_done', 'receive_at')
            selected = self.pick(stream, 'id created opened finished removed sent received used send_credit receive_credit',
                'local_fin remote_fin local_abort peer_terminal peer_close', self.choices(reason=self.MUX_REASONS+' '), extra=times)
            for name in times:
                if isinstance(stream.get(name), list):selected[name] = [self.count(value) for value in self.entries(stream[name], 9, first=True)]
            result['stream'] = selected
        return result

    def mux(self, value):
        source = self.obj(value)
        result = self.pick(source, 'dropped failure_at close_at incident_dropped expected_crossings actual_violations unclassified',
            'projection_overflow', self.choices(failure_reason=self.MUX_REASONS+' '), extra=('events', 'first_unknown', 'incidents'))
        result['events'] = [self.mux_event(item) for item in self.object_entries(source.get('events'), 32)]
        if isinstance(source.get('first_unknown'), dict):result['first_unknown'] = self.mux_incident(source['first_unknown'])
        result['incidents'] = [self.mux_incident(item) for item in self.object_entries(source.get('incidents'), 32, first=True)]
        if isinstance(source.get('incidents'), list) and len(source['incidents']) > 32:result['projection_overflow'] = True
        if len(json.dumps(result, separators=(',', ':'))) > 98304:
            self.lost += len(result['incidents']);result.pop('incidents');result['projection_overflow'] = True
        return result

    def session(self, value):
        source = self.obj(value)
        if not source:return {}
        result = self.pick(source, 'retry_bytes terminal_at_ms observed_at_ms retransmissions recovery_timeouts received_frames sent_frames protocol_errors dns_responses dns_errors tcp_open_ok tcp_open_errors tcp_admission_waits tcp_admission_rejected tcp_admission_timeouts tcp_admission_cancelled tcp_admission_waiting lease_admission_rejected sent_bytes received_bytes evidence_dropped terminal_observed_at_ms',
            'authorization_denied', self.choices(speed_profile='P0 P1 P2', terminal_reason='NONE CANCELLED DEADLINE EOF IO_CLOSED FAMILY_REJECTED MUX_PROTOCOL RELIABLE_PROTOCOL RELIABLE_EXHAUSTED REMOTE_RESET RELIABLE_CLOSED NETWORK_TIMEOUT NETWORK_ERROR UNKNOWN',
                reliable_terminal='closed recovery_exhausted protocol_violation remote_reset cancelled carrier_closed UNKNOWN ',
                signaling_failure='NONE UNKNOWN read_error read_timeout invalid_json '+' '.join('close_code_'+str(code) for code in (1000,1001,1002,1003,1006,1007,1008,1009,1010,1011,1012,1013,1015)),
                ice_failure='NONE UNKNOWN SUBSCRIBER_failed SUBSCRIBER_disconnected PUBLISHER_failed PUBLISHER_disconnected',
                subscriber_state='new connecting connected disconnected failed closed UNKNOWN', publisher_state='new connecting connected disconnected failed closed UNKNOWN'),
            extra=('session_tag', 'correlation_status', 'reliable_limits', 'mux_profile', 'mux_window', 'lifecycle', 'mux_lifecycle', 'protocol_error_reasons'))
        tag = source.get('session_tag')
        if self.tag(tag):result['session_tag'] = tag
        result['correlation_status'] = 'VALID' if self.tag(tag) else 'INVALID' if tag or source.get('correlation_status') == 'INVALID' else 'MISSING'
        for name in ('terminal_reason', 'reliable_terminal', 'signaling_failure', 'ice_failure', 'subscriber_state', 'publisher_state'):
            result.setdefault(name, 'UNKNOWN')
        if 'reliable_limits' in source:
            limits = self.component(source['reliable_limits'], 'local_send local_receive peer_receive effective_send', 'local_write_completion')
            if limits and (1 <= limits['local_send'] <= 32 and 1 <= limits['local_receive'] <= 32 and limits['peer_receive'] <= 32 and limits['effective_send'] == min(limits['local_send'], limits['peer_receive'])):
                result['reliable_limits'] = limits
            else:self.lost += 1
        if isinstance(source.get('mux_profile'), str) and type(source.get('mux_window')) is int and (source['mux_profile'], source['mux_window']) in (('LEGACY64', 65536), ('CREDIT128', 131072)):
            result.update(mux_profile=source['mux_profile'], mux_window=source['mux_window'])
        elif 'mux_profile' in source or 'mux_window' in source:self.lost += 1
        if 'lifecycle' in source:
            trace = self.trace(source['lifecycle'], tag)
            if trace:result['lifecycle'] = trace
        if isinstance(source.get('mux_lifecycle'), dict):result['mux_lifecycle'] = self.mux(source['mux_lifecycle'])
        if isinstance(source.get('protocol_error_reasons'), dict):
            result['protocol_error_reasons'] = self.pick(source['protocol_error_reasons'], 'open_replay unknown_stream open_state data_state credit_state fin_state close_state frame_kind dns_replay dns_role dns_unmatched')
        return result

    def startup(self, value):
        source = self.obj(value)
        result = self.pick(source, 'schema attempt started_unix_ms observed_ms completed_ms', 'complete', self.choices(
            status='RUNNING SUCCEEDED FAILED CANCELLED', stage='STARTUP OWNERSHIP_DRAIN PROFILE DIRECTORY SEED_CREATE SEED_CONNECT SEED_ADMISSION SEED_READ FAMILY_AUTH HELLO_RECEIVE REQUEST_SEND DESCRIPTOR_RECEIVE DESCRIPTOR_VALIDATE BYE_SEND BYE_RECEIVE DEDICATED_CREATE DEDICATED_CONNECT DEDICATED_AUTH DEDICATED_BIND DEDICATED_MUX CONTROL_REFRESH UNKNOWN', cause=self.STARTUP_CAUSES),
            extra=('directory_fingerprint', 'observation', 'local_stop', 'bootstrap_exchanges', 'bootstrap_exchanges_dropped'))
        if result.get('schema') != 1 or result.get('attempt', 0) < 1 or not {'started_unix_ms', 'complete', 'status'} <= result.keys():
            self.lost += bool(source);return {}
        result.setdefault('stage', 'UNKNOWN');result.setdefault('cause', 'UNKNOWN')
        if self.tag(source.get('directory_fingerprint')):result['directory_fingerprint'] = source['directory_fingerprint']
        for name in ('observation', 'local_stop'):
            if not isinstance(source.get(name), dict):continue
            choices = self.choices(point='FAMILY_RECEIVE STARTUP_CALLER', error_category=self.STARTUP_CAUSES, context_state='LIVE DEADLINE CANCELLED', stop_at_observation=self.STARTUP_STOPS) if name == 'observation' else self.choices(source=self.STARTUP_STOPS)
            facts = self.pick(source[name], 'elapsed_ms', choices=choices, extra=('bootstrap_exchange_tag',) if name == 'observation' else ())
            for key in choices:facts.setdefault(key, 'UNKNOWN')
            if name == 'observation' and self.tag(source[name].get('bootstrap_exchange_tag')):facts['bootstrap_exchange_tag'] = source[name]['bootstrap_exchange_tag']
            result[name] = facts
        if isinstance(source.get('bootstrap_exchanges'), list):
            exchanges = []
            for item in self.entries(source['bootstrap_exchanges'], 4, first=True):
                item = self.obj(item)
                selected = self.pick(item, flags='family_authenticated', extra=('bootstrap_exchange_tag',))
                if self.tag(item.get('bootstrap_exchange_tag')) and 'family_authenticated' in selected:
                    selected['bootstrap_exchange_tag'] = item['bootstrap_exchange_tag'];exchanges.append(selected)
                else:self.lost += 1
            result.update(bootstrap_exchanges=exchanges, bootstrap_exchanges_dropped=min(self.MAX_NUMBER, self.count(source.get('bootstrap_exchanges_dropped', 0))+len(source['bootstrap_exchanges'])-len(exchanges)))
        return result


class DesktopDiagnostics:
    RECORD_LIMIT = 256 * 1024
    EXPORT_LIMIT = 2 * RECORD_LIMIT + 1024
    STATES = frozenset('DISCONNECTED CONNECTING CONNECTED RESTORING STOPPING FAILED'.split())
    SUPPORT = re.compile(r'FC-[23456789ABCDEFGHJKMNPQRSTVWXYZ]{4}-[23456789ABCDEFGHJKMNPQRSTVWXYZ]{4}')
    NUMBERS = frozenset('''schema attempt started_unix_ms observed_ms completed_ms elapsed_ms sequence timestamp_ms
        tx rx reliable_age_ms reliable_retries reliable_pending reliable_sacked reliable_ack_age_ms
        reliable_progress_age_ms reliable_ack_received lease_deadline_ms lease_sequence close_code trace_dropped
        export_dropped delivery_dropped evidence_dropped terminal_at_ms observed_at_ms retry_bytes mux_window
        retransmissions recovery_timeouts received_frames sent_frames protocol_errors dns_responses dns_errors
        tcp_open_ok tcp_open_errors tcp_admission_waits tcp_admission_rejected tcp_admission_timeouts
        tcp_admission_cancelled tcp_admission_waiting lease_admission_rejected sent_bytes received_bytes
        local_send local_receive peer_receive effective_send open_replay unknown_stream open_state data_state
        credit_state fin_state close_state frame_kind dns_replay dns_role dns_unmatched bootstrap_exchanges_dropped
        dns tcp tcp_active tcp_peak limit_denied udp_denied ipv6_denied protect_ok protect_denied underlay_dns
        events_dropped dropped incident_dropped archive_dropped projection_dropped delivery_projection_dropped
        bytes packets queued pending total received sent written enqueued used created removed index stream
        send_credit receive_credit ack_base ack_mask data_sequence event at_ms timestamp duration_ms retry_count
        send_started send_done opened finished close_at receive_at failure_at first_rtp last_rtp id actual_violations
        expected_crossings unclassified observed_at failures consecutive_failures successes sample_age_ms
        probes progress_overrides last_elapsed_ms probe_duration_ms'''.split())
    BOOLEANS = frozenset('''complete family_authenticated known frame_known message_known data_known attempt_known
        local_fin remote_fin local_abort peer_close peer_terminal durable tun_ready cancelled relay_available
        probe_ok traffic_progress'''.split())
    STRUCTURES = frozenset('''reliable_limits lifecycle trace first_failure first_close delivery boundaries events
        mux_lifecycle incidents protocol_error_reasons observation local_stop bootstrap_exchanges flow sender
        assembly fragment message media_track fault first_unknown readiness receipt health'''.split())
    TEXT_FIELDS = frozenset('''state stage reason cause status point error_category context_state stop_at_observation
        source result phase code ack_state speed_profile mux_profile correlation_status terminal_reason
        reliable_terminal signaling_failure ice_failure subscriber_state publisher_state close_source target
        heartbeat_kind close_reason lease_action direction kind class detail broker_reason'''.split())
    CODES = frozenset('''UNKNOWN NONE CANCELLED DISCONNECTED CONNECTING CONNECTED RESTORING STOPPING FAILED
        STARTED ESTABLISHED ISSUED TX RX CLOSED COMPLETED ATTEMPTED NOT_ATTEMPTED READY NOT_READY MISSING
        NOT_STARTED PREPARING VERIFYING VERIFIED VALIDATING PERSISTING DURABLE PREPARED COMMITTED
        VALID INVALID SUCCESS ERROR PENDING COMPLETE IN_PROGRESS NOT_USABLE USABLE
        AUTHORIZED ROOM_CREATION DESCRIPTOR GATEWAY_JOIN SIGNALING WEBSOCKET ICE PEER_CONNECTION CARRIER
        CARRIER_ACTIVITY FAMILY_TLS GATEWAY_SESSION HEARTBEAT LIVENESS LOCAL_CLOSE REMOTE_CLOSE RECOVERY CLEANUP
        P0 P1 LEGACY64 CREDIT128 ACK_PENDING ACK_RECEIVED AUTH NETWORK CONFIGURATION TRANSPORT_UNAVAILABLE
        BOOTSTRAP_UNAVAILABLE INTERNAL AUTH_OR_STARTUP_FAILED AUTHORIZATION_REJECTED FAMILY_REJECTED
        DEADLINE NETWORK_TIMEOUT NETWORK_ERROR REMOTE_RESET RELIABLE_EXHAUSTED RELIABLE_CLOSED IO_CLOSED EOF
        MUX_PROTOCOL RELIABLE_PROTOCOL UNKNOWN_INTERNAL UNDERLAY_CHANGED UNDERLAY_UNAVAILABLE
        CLEANUP_FAILED CLEANUP_PENDING WORKER_PROTOCOL_REJECTED SERVICE_RESTARTED RECOVERY_CREDENTIAL_UNAVAILABLE
        FETCH_FAILED PERSISTENCE_FAILED STALE_STATE EXPIRED INVALID_CACHE INVALID_RECEIPT CACHE_REJECTED
        CACHE_READ CACHE_VALIDATE CACHE_VALIDATED CACHE_WRITE CACHE_PERSISTED REFRESH VALIDATE COMMIT
        RNS HTTPS STARTUP_FAILED STARTUP_REJECTED STARTUP_BUDGET FIRST SECOND FRESH CACHED
        UPPER_CLOSE PARENT_CANCELLED PARENT_DEADLINE RECEIVE_QUEUE_FULL SUBSCRIBER_DISCONNECTED
        PUBLISHER_DISCONNECTED SIGNAL_WRITE SIGNAL_READ CONFERENCE_ENDED SUBSCRIBER_NEGOTIATION
        SUBSCRIBER_ICE_CONFIG PUBLISHER_ICE_CONFIG PUBLISHER_ANSWER PUBLISHER_NEGOTIATION ICE_PENDING_LIMIT
        REMOTE_ICE QUEUED_ICE HEARTBEAT_WRITE DATA_CHANNEL_WRITE VP8_WRITE RELIABLE_EXHAUSTION
        BROKER_LIFETIME BROKER_UNUSED BROKER_AUTHORIZATION FAMILY_CONTRACT FAMILY_CONTEXT FAMILY_WRITE
        FAMILY_READ FAMILY_UPPER_CLOSE FAMILY_CREDENTIAL_EXPIRY SUBSCRIBER PUBLISHER APPLICATION WEBSOCKET
        new checking connecting connected completed disconnected failed closed recovery_exhausted
        protocol_violation remote_reset cancelled carrier_closed offer request accepted applied confirmed
        ping timeout duplicate expired inactivity shutdown restart invalid ack idle session
        READ_ERROR READ_TIMEOUT INVALID_MESSAGE WRITE_ERROR read_error read_timeout invalid_json
        SUBSCRIBER_failed SUBSCRIBER_disconnected PUBLISHER_failed PUBLISHER_disconnected
        STARTUP_CANCEL SERVICE_STOP USER_DISCONNECT INPUT OUTPUT IN OUT SEND RECEIVE OPEN DATA FIN CLOSE CREDIT
        READINESS BOOTSTRAP AUTHENTICATION ROOM JOIN TLS MUX ROUTE HEALTH WAIT STOP TCP DNS UDP IPv6
        CONTROL_UNAVAILABLE NATIVE_VALIDATION_FAILED BOOTSTRAP_VALIDATION_FAILED ATOMIC_IMPORT_FAILED
        EXPIRED_ON_IMPORT ORCHESTRATOR_NOT_USABLE INTERNAL_ERROR SIGNAL_WS_CLOSE ICE_DISCONNECTED ICE_FAILED
        PEER_CONNECTION_FAILED CARRIER_EOF CARRIER_ERROR FAMILY_TLS_EOF FAMILY_TLS_ERROR GATEWAY_CLOSE
        HEARTBEAT_TIMEOUT RECOVERY_CLEANUP_FAILED RECOVERY_DESCRIPTOR_FAILED RECOVERY_JOIN_FAILED
        RECOVERY_CARRIER_FAILED RELIABLE_HANDSHAKE_TIMEOUT RELIABLE_FRAME_TIMEOUT RELIABLE_RETRY_EXHAUSTED
        RUNNING SUCCEEDED STARTUP OWNERSHIP_DRAIN PROFILE DIRECTORY SEED_CREATE SEED_CONNECT SEED_ADMISSION
        SEED_READ FAMILY_AUTH HELLO_RECEIVE REQUEST_SEND DESCRIPTOR_RECEIVE DESCRIPTOR_VALIDATE BYE_SEND
        BYE_RECEIVE DEDICATED_CREATE DEDICATED_CONNECT DEDICATED_AUTH DEDICATED_BIND DEDICATED_MUX CONTROL_REFRESH
        IO_DEADLINE CLOSED_PIPE TIMEOUT_UNQUALIFIED CERTIFICATE_TIME_INVALID CERTIFICATE_INVALID
        CERTIFICATE_AUTHORITY CERTIFICATE_HOSTNAME PROVIDER_API CARRIER_CLOSED PROTOCOL_REJECTED
        CREDENTIALS_REJECTED DESCRIPTOR_REJECTED DESCRIPTOR_EXPIRED EXCHANGE_CLOSED CONNECT_CANCEL
        FAMILY_RECEIVE STARTUP_CALLER LIVE VERIFIED_READBACK cache refresh import resume HEALTHY UNHEALTHY ok unavailable
        SERVICE_UNAVAILABLE AUTHORIZATION_CANCELLED CHALLENGE_TEMPORARY_SERVER_FAILURE CHALLENGE_TIMEOUT
        CHALLENGE_UNAUTHORIZED CHALLENGE_UNAVAILABLE FETCH_NETWORK_FAILURE FETCH_TEMPORARY_SERVER_FAILURE
        HEALTH_UNAVAILABLE INVALID_MATERIALS_COMMAND MATERIALS_FAILED MATERIALS_PROTOCOL_REJECTED
        MATERIALS_WORKER_FAILED NETWORK_SETUP_FAILED PACKET_OR_IPC_FAILED READINESS_FAILED RNS_PROTOCOL_REJECTED
        RNS_UNAVAILABLE RNS_WORKER_UNAVAILABLE TLS_TRUST_REJECTED WORKER_EXITED VALIDATED_CACHE
        PRESENT_VALID RECEIPT_READY OK UNAVAILABLE PACKET_READY ROUTE_CONFIRMING TRANSPORT_READY'''.split())
    HASHES = frozenset(('session_tag', 'directory_fingerprint', 'bootstrap_exchange_tag'))
    NATIVE_EVENTS = frozenset(('bootstrap_cache_loaded', 'bootstrap_carrier_connected', 'bootstrap_family_auth',
        'family_auth', 'bootstrap_descriptor_received', 'bootstrap_closed_before_dedicated', 'dedicated_data_ready',
        'startup_credentials_rejected', 'startup_control_unavailable', 'startup_failed', 'bootstrap_exchange_failed'))
    CLOSE_SOURCES = frozenset('UNKNOWN UPPER_CLOSE PARENT_CANCELLED PARENT_DEADLINE RECEIVE_QUEUE_FULL SUBSCRIBER_DISCONNECTED PUBLISHER_DISCONNECTED SIGNAL_WRITE SIGNAL_READ CONFERENCE_ENDED SUBSCRIBER_NEGOTIATION SUBSCRIBER_ICE_CONFIG PUBLISHER_ICE_CONFIG PUBLISHER_ANSWER PUBLISHER_NEGOTIATION ICE_PENDING_LIMIT REMOTE_ICE QUEUED_ICE HEARTBEAT_WRITE DATA_CHANNEL_WRITE VP8_WRITE RELIABLE_EXHAUSTION BROKER_LIFETIME BROKER_UNUSED BROKER_AUTHORIZATION FAMILY_CONTRACT FAMILY_CONTEXT FAMILY_WRITE FAMILY_READ FAMILY_UPPER_CLOSE FAMILY_CREDENTIAL_EXPIRY'.split())

    def __init__(self, version, storage=None, clock=time.time):
        self.version, self.storage, self.clock = version, Path(storage) if storage else None, clock
        self.lock = threading.RLock()
        self.connection = str(uuid.uuid4())
        self.incident_id = str(uuid.uuid4())
        self.events, self.history, self.incident = [], [], None
        self.events_dropped = self.history_dropped = 0
        self.current = self._base()
        self.last_signature = None
        self.persistence_failed = False
        self._restore()

    def _storage_ready(self):
        self.storage.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        info = self.storage.parent.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700:
            raise ValueError('Unsafe diagnostic storage')

    def _restore(self):
        if self.storage is None:
            return
        try:
            self._storage_ready()
            descriptor = os.open(self.storage, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
            with os.fdopen(descriptor, 'rb') as source:
                info = os.fstat(source.fileno())
                if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_nlink != 1 or stat.S_IMODE(info.st_mode) != 0o600:
                    raise ValueError('Unsafe diagnostic record')
                raw = source.read(self.EXPORT_LIMIT + 1)
            if len(raw) > self.EXPORT_LIMIT:
                raise ValueError('Oversized diagnostic record')
            bundle = json.loads(raw)
            if not isinstance(bundle, dict) or set(bundle) - {'ring', 'incident'}:
                raise ValueError('Invalid diagnostic record')
            previous = bundle.get('ring', {})
            losses = previous.get('diagnostic_losses', {})
            self.events_dropped = self._count(losses.get('events_dropped'))
            self.history_dropped = self._count(losses.get('history_dropped'))
            previous_events = previous.get('events', [])
            for event in previous_events[-128:]:
                projected = self._stored_event(event)
                if projected is None:
                    self.events_dropped += 1
                else:
                    self.events.append(projected)
            self.events_dropped += max(0, len(previous_events) - 128)
            last, restored_rejected = self.native_projection(previous.get('restricted_session', {}), 'session', stored=True)
            history_limit = 3 if last.get('session_tag') else 4
            self.history = []
            for item in previous.get('restricted_history', [])[-history_limit:]:
                selected, removed = self.native_projection(item, 'session', stored=True)
                self.history.append(selected);restored_rejected += removed
            self.history_dropped += max(0, len(previous.get('restricted_history', [])) - history_limit)
            if last.get('session_tag'):
                self.history.append(last)
            if isinstance(bundle.get('incident'), dict):
                source = bundle['incident']
                self.incident = self._base()
                self.incident['state'] = 'FAILED'
                for key in ('connection_id', 'incident_id'):
                    if isinstance(source.get(key), str) and re.fullmatch('[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}', source[key]):
                        self.incident[key] = source[key]
                for key in ('restricted_session', 'restricted_startup', 'readiness_fetch', 'counters'):
                    if key in ('restricted_session', 'restricted_startup'):
                        self.incident[key], removed = self.native_projection(source.get(key, {}), key.removeprefix('restricted_'), stored=True)
                    else:self.incident[key], removed = self.project(source.get(key, {}))
                    self.incident['diagnostic_losses']['restored_projection_dropped'] = self.incident['diagnostic_losses'].get('restored_projection_dropped', 0) + removed
                reason = source.get('first_failure')
                self.incident['first_failure'] = reason if reason in self.CODES else 'UNKNOWN'
            self.current['events'], self.current['restricted_history'] = copy.deepcopy(self.events), copy.deepcopy(self.history)
            self.current['diagnostic_losses'] = dict(events_dropped=self.events_dropped, history_dropped=self.history_dropped,
                restored_projection_dropped=restored_rejected+self._count(losses.get('restored_projection_dropped')))
        except FileNotFoundError:
            pass
        except (OSError, ValueError, TypeError, AttributeError, RecursionError):
            self.persistence_failed = True

    def persist(self):
        if self.storage is None:
            return
        try:
            self._storage_ready()
            self.save_export(self.storage, self.export())
            self.persistence_failed = False
        except (OSError, ValueError, BackendError):
            self.persistence_failed = True

    def _base(self):
        return dict(schema=1, platform='linux', app_version=self.version, device_support_id=None,
                    connection_id=self.connection, incident_id=self.incident_id, state='DISCONNECTED',
                    network_class='UNKNOWN', vpn_capture_open=False, restricted_readiness='UNKNOWN',
                    bootstrap_directory='UNKNOWN', selected_transport='none', actual_transport='none',
                    selected_profile='UNKNOWN', first_failure='NONE', counters={}, restricted_session={},
                    restricted_startup={}, readiness_fetch={}, restricted_history=[], events=[],
                    transport_outcomes={}, diagnostic_losses={})

    @classmethod
    def native_projection(cls, source, kind, *, stored=False):
        projector = NativeDiagnostics106()
        source = projector.obj(source)
        annotations = ('device_support_id', 'connection_id', 'incident_id')
        raw = {name: value for name, value in source.items() if not stored or name not in annotations}
        selected = getattr(projector, kind)(raw)
        if stored and selected:
            for name in annotations:
                value = source.get(name)
                if isinstance(value, str) and (cls.SUPPORT.fullmatch(value) if name == 'device_support_id' else re.fullmatch('[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}', value)):
                    selected[name] = value
                elif name == 'device_support_id' and name in source and value is None:selected[name] = None
                elif value is not None:projector.lost += 1
        return selected, projector.lost

    @classmethod
    def project(cls, source):
        lost = [0]
        visited = [0]
        def visit(value, depth=0):
            visited[0] += 1
            if depth > 16 or visited[0] > 20000 or not isinstance(value, dict):
                lost[0] += 1
                return {}
            result = {}
            for name, child in value.items():
                if name in cls.NUMBERS and type(child) is int and 0 <= child <= 9007199254740991:
                    result[name] = child
                elif name in cls.BOOLEANS and type(child) is bool:
                    result[name] = child
                elif name in cls.HASHES and isinstance(child, str) and re.fullmatch('[0-9a-f]{64}', child):
                    result[name] = child
                elif name in cls.TEXT_FIELDS and isinstance(child, str):
                    valid = child in cls.CODES or (name == 'signaling_failure' and re.fullmatch('close_code_10[0-9]{2}', child))
                    result[name] = child if valid else 'UNKNOWN'
                    lost[0] += not valid
                elif name in cls.STRUCTURES and isinstance(child, dict):
                    result[name] = visit(child, depth + 1)
                elif name in cls.STRUCTURES and isinstance(child, list):
                    lost[0] += max(0, len(child) - 192)
                    result[name] = [visit(item, depth + 1) for item in child[-192:]]
                else:
                    lost[0] += 1
            return result
        return visit(source), lost[0]

    def sample(self, state, transport, profile='P0', service=None):
        with self.lock:
            state = state if state in self.STATES else 'FAILED'
            automatic = transport == 'auto'
            if automatic:
                service = service if isinstance(service, dict) else {}
                controller = service.get('controller') or {}
                policy = controller.get('policy') or {}
                transport = {'awg': 'awg', 'tcp': 'tcp', 'restricted': 'mesh'}.get(service.get('selected'), 'none')
                mesh = controller.get('mesh') or {}
                service = dict(mesh if transport == 'mesh' else {}, desired_connected=service.get('desired_connected'),
                    reason=policy.get('first_reason') or service.get('reason') or 'NONE',
                    attempt=(controller.get('platform') or {}).get('attempt', 0), events=policy.get('events') or [],
                    events_dropped=policy.get('events_dropped', 0))
            transport = {'mesh': 'restricted', 'awg': 'awg', 'tcp': 'tcp'}.get(transport, 'none')
            service = service if (automatic or transport == 'restricted') and isinstance(service, dict) else {}
            native = service.get('native', {})
            native = native if isinstance(native, dict) else {}
            session = native.get('native', {})
            session = session if isinstance(session, dict) else {}
            packet = session.get('packet', {})
            packet = packet if isinstance(packet, dict) else {}
            old = self.current
            if state in ('CONNECTING', 'RESTORING') and old['state'] in ('DISCONNECTED', 'FAILED'):
                self.connection, self.incident_id = str(uuid.uuid4()), str(uuid.uuid4())
            record = self._base()
            record.update(state=state, selected_transport='auto' if automatic else transport, selected_profile=profile if (automatic or transport == 'restricted') and profile in ('P0', 'P1') else 'UNKNOWN')
            record['device_support_id'] = old['device_support_id']
            record['vpn_capture_open'] = state == 'CONNECTED' and transport != 'none' and (transport != 'restricted' or session.get('tun_ready') is True)
            record['actual_transport'] = transport if record['vpn_capture_open'] else 'none'
            diagnostic, rejected = self.native_projection(packet.get('diagnostic', {}), 'session')
            startup, startup_rejected = self.native_projection(session.get('startup') or native.get('startup') or {}, 'startup')
            previous_session = old['restricted_session']
            previous_attempt = self._count((old.get('recovery') or {}).get('attempt'))
            current_attempt = self._count(service['attempt']) if 'attempt' in service else previous_attempt if transport == 'restricted' else 0
            same_attempt = previous_attempt == current_attempt
            if transport == 'restricted' and old['connection_id'] == self.connection:
                if not diagnostic and previous_session.get('session_tag'):
                    diagnostic = copy.deepcopy(previous_session)
                previous_startup = old['restricted_startup']
                if same_attempt and previous_startup and (not startup or startup['attempt'] < previous_startup['attempt'] or
                        startup['attempt'] == previous_startup['attempt'] and previous_startup.get('complete')):
                    startup = copy.deepcopy(previous_startup)
            if diagnostic.get('session_tag'):
                same = previous_session.get('session_tag') == diagnostic['session_tag']
                lifecycle = diagnostic.get('lifecycle')
                first = (previous_session.get('lifecycle') or {}).get('first_failure') if same else None
                if lifecycle is not None and first:lifecycle['first_failure'] = copy.deepcopy(first)
                if same and 'terminal_observed_at_ms' in previous_session:
                    diagnostic = copy.deepcopy(previous_session)
                    if lifecycle is not None:diagnostic['lifecycle'] = lifecycle
                else:
                    for name in ('device_support_id', 'connection_id', 'incident_id'):
                        diagnostic[name] = previous_session.get(name, record[name]) if same else record[name]
                    if diagnostic.get('terminal_reason') not in ('NONE', 'UNKNOWN'):
                        diagnostic['terminal_observed_at_ms'] = int(self.clock()*1000)
            if startup:
                startup.update(connection_id=self.connection, incident_id=self.incident_id)
            readiness, readiness_rejected = self.project(service.get('readiness', {}))
            reason = service.get('first_reason', service.get('reason', 'NONE'))
            record['first_failure'] = reason if reason in self.CODES else 'UNKNOWN'
            if old['connection_id'] == self.connection and old['first_failure'] not in ('NONE', 'CANCELLED', 'UNKNOWN'):
                record['first_failure'] = old['first_failure']
            record['restricted_session'], record['restricted_startup'], record['readiness_fetch'] = diagnostic, startup, readiness
            source_events = native.get('events', [])
            source_events = source_events if isinstance(source_events, list) else []
            record['native_events'] = [event for event in source_events[-32:] if isinstance(event, str) and event in self.NATIVE_EVENTS]
            record['restricted_readiness'] = readiness.get('code', 'UNKNOWN')
            record['bootstrap_directory'] = 'USABLE' if readiness.get('code') == 'READY' and readiness.get('durable') is True else 'UNKNOWN'
            record['counters'] = {name: value for name, value in {**packet, **session}.items()
                                  if name in ('dns', 'tcp', 'tcp_active', 'tcp_peak', 'limit_denied', 'udp_denied', 'ipv6_denied', 'protect_ok', 'protect_denied', 'underlay_dns')
                                  and type(value) is int and 0 <= value <= 9007199254740991}
            record['recovery'] = dict(desired_connected=service.get('desired_connected') is True,
                                      attempt=current_attempt)
            previous = old['restricted_session']
            if previous.get('session_tag') and previous.get('session_tag') != diagnostic.get('session_tag'):
                self.history.append(previous)
                if len(self.history) > 4:
                    self.history.pop(0)
                    self.history_dropped += 1
            signature = (state, transport, service.get('reason', 'NONE'), record['recovery']['attempt'])
            changed = signature != self.last_signature
            if changed:
                self.events.append(dict(timestamp=int(self.clock() * 1000), connection_id=self.connection,
                    incident_id=self.incident_id, component='ORCHESTRATOR', state_from=old['state'], state_to=state,
                    transport_class=transport, reason_code=signature[2] if signature[2] in self.CODES else 'UNKNOWN',
                    duration_ms=0, retry_count=max(0, record['recovery']['attempt']), app_version=self.version))
                if len(self.events) > 128:
                    del self.events[1]
                    self.events_dropped += 1
                self.last_signature = signature
            record['events'], record['restricted_history'] = copy.deepcopy(self.events), copy.deepcopy(self.history)
            record['service_lifecycle'], service_rejected = self.project({'events': service.get('events', [])})
            record['health'], health_rejected = self.project(native.get('health') or {})
            record['diagnostic_losses'] = dict(projection_dropped=rejected + startup_rejected + readiness_rejected + service_rejected,
                events_dropped=self.events_dropped, history_dropped=self.history_dropped,
                service_events_dropped=self._count(service.get('events_dropped')), native_events_dropped=self._count(native.get('events_dropped')))
            record['diagnostic_losses']['projection_dropped'] += health_rejected
            record['diagnostic_losses']['projection_dropped'] += len(source_events) - len(record['native_events'])
            if old['diagnostic_losses'].get('restored_projection_dropped'):
                record['diagnostic_losses']['restored_projection_dropped'] = old['diagnostic_losses']['restored_projection_dropped']
            if old['connection_id'] == self.connection:
                record['transport_outcomes'] = dict(old['transport_outcomes'])
            if state in ('CONNECTED', 'FAILED'):
                record['transport_outcomes'][transport] = 'SUCCESS' if state == 'CONNECTED' else record['first_failure']
            self.current = record
            if state == 'FAILED':
                self.incident = copy.deepcopy(record)
            return changed

    def _stored_event(self, value):
        if not isinstance(value, dict):
            return None
        result = dict(component='ORCHESTRATOR', app_version=self.version)
        for key in ('connection_id', 'incident_id'):
            candidate = value.get(key)
            if not isinstance(candidate, str) or not re.fullmatch('[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}', candidate):
                return None
            result[key] = candidate
        for key in ('state_from', 'state_to'):
            if value.get(key) not in self.STATES:
                return None
            result[key] = value[key]
        result['transport_class'] = value.get('transport_class') if value.get('transport_class') in ('awg', 'tcp', 'restricted', 'none') else 'none'
        result['reason_code'] = value.get('reason_code') if value.get('reason_code') in self.CODES else 'UNKNOWN'
        for key in ('timestamp', 'duration_ms', 'retry_count'):
            result[key] = self._count(value.get(key))
        return result

    @staticmethod
    def _count(value):
        return value if type(value) is int and 0 <= value <= 9007199254740991 else 0

    def support(self, value):
        with self.lock:
            self.current['device_support_id'] = value if isinstance(value, str) and self.SUPPORT.fullmatch(value) else None

    @staticmethod
    def _encode(value):
        return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode('utf-8')

    @classmethod
    def bounded(cls, source):
        record = copy.deepcopy(source)
        size = len(cls._encode(record))
        if size <= cls.RECORD_LIMIT:
            return record
        omitted = {}
        record['record_budget'] = dict(limit_bytes=cls.RECORD_LIMIT, untrimmed_bytes=size, omitted_detail_items=omitted)
        size = len(cls._encode(record))
        def trim(parent, name, path):
            nonlocal size
            values = parent.get(name) if isinstance(parent, dict) else None
            while isinstance(values, list) and len(values) > 2 and size > cls.RECORD_LIMIT:
                removed = len(cls._encode(values[1])) + 1
                before = len(cls._encode(omitted))
                del values[1]
                omitted[path] = omitted.get(path, 0) + 1
                size += len(cls._encode(omitted)) - before - removed
        def session(value, path):
            lifecycle = value.get('lifecycle', {})
            trim(lifecycle, 'trace', path + '.lifecycle.trace')
            trim(lifecycle.get('boundaries', {}), 'events', path + '.lifecycle.boundaries.events')
            for name in ('events', 'incidents'):
                trim(value.get('mux_lifecycle', {}), name, path + '.mux_lifecycle.' + name)
        for index, value in enumerate(record.get('restricted_history', [])):
            session(value, 'restricted_history[' + str(index) + ']')
        session(record.get('restricted_session', {}), 'restricted_session')
        trim(record, 'events', 'events')
        if len(cls._encode(record)) > cls.RECORD_LIMIT:
            raise BackendError('Diagnostic record exceeds the safe export limit')
        return record

    def export(self, environment=None):
        with self.lock:
            record = copy.deepcopy(self.current)
            record['os'] = dict(name='Linux', release=platform.release(), architecture=platform.machine())
            record['core_reference'] = 'android106-native105'
            record['sampled_at_ms'] = int(self.clock() * 1000)
            record['diagnostic_losses']['persistence_failed'] = self.persistence_failed
            record.update(environment or {})
            bundle = dict(ring=self.bounded(record))
            if self.incident is not None:
                incident = copy.deepcopy(self.incident)
                incident['device_support_id'] = record['device_support_id']
                bundle['incident'] = self.bounded(incident)
            encoded = self._encode(bundle)
            if len(encoded) > self.EXPORT_LIMIT:
                raise BackendError('Diagnostic export exceeds the safe export limit')
            return encoded

    @staticmethod
    def environment():
        network = 'NONE'
        try:
            for line in Path('/proc/net/route').read_text().splitlines()[1:]:
                columns = line.split()
                if len(columns) < 4 or columns[1] != '00000000' or not int(columns[3], 16) & 1:
                    continue
                name = columns[0]
                if not re.fullmatch('[A-Za-z0-9_.:-]{1,15}', name):
                    continue
                interface = Path('/sys/class/net') / name
                if name.startswith(('fc', 'tun', 'wg', 'tap')):
                    continue
                network = 'WIFI' if (interface / 'wireless').exists() else 'ETHERNET' if int((interface / 'type').read_text()) == 1 else 'UNKNOWN'
                break
        except (OSError, ValueError):
            network = 'UNKNOWN'
        versions = dict(available=False)
        if mesh_component_available():
            try:
                raw = (MESH_ROOT / 'capabilities.json').read_bytes()
                if len(raw) > 4096:
                    raise ValueError('Metadata bound')
                value = json.loads(raw)
                versions = {name: value[name] for name in ('bridge_protocol', 'materials_protocol', 'intent_protocol')
                            if type(value.get(name)) is int}
                versions['available'] = True
                for name in ('source_digest', 'native_sha256'):
                    if isinstance(value.get(name), str) and re.fullmatch('[0-9a-f]{64}', value[name]):
                        versions[name] = value[name]
            except (OSError, ValueError):
                versions = dict(available=False)
        return dict(network_class=network, native_version=versions)

    @classmethod
    def save_export(cls, destination, encoded):
        if not isinstance(encoded, bytes) or len(encoded) > cls.EXPORT_LIMIT or not isinstance(json.loads(encoded), dict):
            raise BackendError('Invalid diagnostic export')
        destination = Path(destination)
        if destination.is_symlink() or (destination.exists() and not destination.is_file()):
            raise BackendError('Choose a regular diagnostic file')
        descriptor, temporary = tempfile.mkstemp(prefix='.fc-diagnostics-', dir=destination.parent)
        try:
            with os.fdopen(descriptor, 'wb') as output:
                output.write(encoded)
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary, destination)
            directory = os.open(destination.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

def read_profile(path, *, allow_awg=False, allow_awg31=False):
    with Path(path).open("rb") as source:
        return validate(source.read(MAX_PROFILE+1).decode("utf-8-sig"),allow_awg=allow_awg,allow_awg31=allow_awg31)


def verified_server_load(payload,country,now):
    """Telemetry is informational; stale/unknown capacity is never zero load."""
    if country not in ('ru','nl') or len(payload)>8192:raise ValueError('Invalid load sample')
    value=json.loads(payload)
    if value.get('schema')!=1:raise ValueError('Invalid load schema')
    sample=value['gateways'][country]
    if sample['country']!=country:raise ValueError('Wrong gateway')
    def number(key,minimum=0,maximum=1e12):
        n=sample[key]
        if type(n) not in (int,float) or not math.isfinite(n) or not minimum<=n<=maximum:
            raise ValueError('Invalid load value')
        return n
    observed=number('observed_at')
    if not -15<=now-observed<=45:raise ValueError('Stale load sample')
    cpu=number('cpu_percent',0,100);rx=number('rx_mbps');tx=number('tx_mbps')
    capacity=sample.get('capacity_mbps')
    if capacity is not None:capacity=number('capacity_mbps',.001,1e9)
    direction=sample.get('capacity_direction','duplex')
    if direction not in ('duplex','egress'):raise ValueError('Invalid capacity direction')
    used=tx if direction=='egress' else max(rx,tx)
    percent=min(100,max(cpu,100*used/capacity)) if capacity else None
    return dict(country=country,observed_at=observed,cpu=cpu,rx=rx,tx=tx,percent=percent,estimated=sample.get('capacity_basis')=='provider-default-estimate',capacity=capacity,direction=direction)


def verified_server_loads(payload,now):
    """Parse both public gateways; a missing/stale gateway is omitted, never zero load."""
    if len(payload)>8192:raise ValueError('Invalid load sample')
    value=json.loads(payload)
    if value.get('schema')!=1:raise ValueError('Invalid load schema')
    result={}
    for country in ('ru','nl'):
        if country not in value.get('gateways',{}):continue
        try:result[country]=verified_server_load(payload,country,now)
        except (ValueError,KeyError):continue
    return result


PREFIX='fc-app-'
class BackendError(Exception): pass
class AuthorizationError(BackendError): pass


# Self-contained so the existing six-file desktop archive remains compatible.
import functools
import threading
from contextlib import contextmanager
from dataclasses import dataclass


class ConnectionBusy(BackendError):
    pass


class StaleConnection(BackendError):
    pass


_operation_mutex = threading.RLock()
_operation_local = threading.local()


def operation_directory():
    return Path.home()/'.local/state/family-connect-operations'


class OperationLease:
    def __init__(self, directory, owner, record):
        self.directory, self.owner, self.record = directory, owner, record

    def save(self):
        raw=json.dumps(self.record,separators=(',',':')).encode()
        temporary='.operation-'+uuid.uuid4().hex
        fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=self.directory)
        try:
            with os.fdopen(fd,'wb') as stream:
                stream.write(raw);stream.flush();os.fsync(stream.fileno())
            os.replace(temporary,'state.json',src_dir_fd=self.directory,dst_dir_fd=self.directory)
            os.fsync(self.directory)
        finally:
            try:os.unlink(temporary,dir_fd=self.directory)
            except FileNotFoundError:pass

    def reserve(self):
        if self.owner is None:raise BackendError('Control owner required')
        if self.record['pending'] is None:
            self.record['pending']=self.owner;self.record['generation']+=1;self.save()

    def finish(self):
        if self.record['pending'] is not None:
            if self.record['pending']!=self.owner:raise ConnectionBusy('Connection recovery is pending')
            self.record['pending']=None;self.record['generation']+=1;self.save()


@contextmanager
def connection_operation(*, owner=None, mutate=False, expected=None):
    """Nonblocking process/thread exclusion plus durable pending-control ownership.

    Normal operations never bypass an interrupted control transaction. Only the
    same local journal owner can finish recovery and clear its durable marker.
    """
    import fcntl
    if owner is not None and (type(owner) is not str or not re.fullmatch('[0-9a-f]{64}',owner)):
        raise BackendError('Invalid control owner')
    if not _operation_mutex.acquire(blocking=False):
        raise ConnectionBusy('Connection settings are being updated')
    directory=lock=None
    try:
        current=getattr(_operation_local,'lease',None)
        if current is not None:
            if owner is not None and owner!=current.owner:raise ConnectionBusy('Another control owner is active')
            yield current;return
        path=operation_directory()
        path.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
        fresh=False
        try:path.mkdir(mode=0o700);fresh=True
        except FileExistsError:pass
        directory=os.open(path,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
        info=os.fstat(directory)
        if info.st_uid!=os.getuid() or stat.S_IMODE(info.st_mode)!=0o700:
            raise BackendError('Unsafe connection coordination directory')
        def safe(fd):
            info=os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_uid!=os.getuid() or stat.S_IMODE(info.st_mode)!=0o600 or info.st_nlink!=1:
                raise BackendError('Unsafe connection coordination file')
        lock=os.open('.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW|os.O_NONBLOCK,0o600,dir_fd=directory)
        safe(lock)
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise ConnectionBusy('Connection settings are being updated') from None
        try:
            fd=os.open('state.json',os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=directory)
        except FileNotFoundError:
            if not fresh:raise BackendError('Missing connection coordination state') from None
            record=dict(generation=0,pending=None)
            OperationLease(directory,owner,record).save()
        else:
            try:
                safe(fd);raw=os.read(fd,1025)
                record=json.loads(raw)
                if (len(raw)>1024 or type(record) is not dict or set(record)!={'generation','pending'} or
                    type(record['generation']) is not int or not 0<=record['generation']<2**63 or
                    (record['pending'] is not None and (type(record['pending']) is not str or not re.fullmatch('[0-9a-f]{64}',record['pending'])))):
                    raise ValueError()
            except (ValueError,TypeError,UnicodeError,RecursionError):
                raise BackendError('Invalid connection coordination state') from None
            finally:os.close(fd)
        if record['pending'] is not None and record['pending']!=owner:
            raise ConnectionBusy('Connection recovery is pending; resume the control client')
        if expected is not None and expected!=record['generation']:
            raise StaleConnection('Connection settings changed; refresh the selection')
        lease=OperationLease(directory,owner,record)
        if mutate:
            lease.record['generation']+=1;lease.save()
        _operation_local.lease=lease
        try:yield lease
        finally:_operation_local.lease=None
    finally:
        if lock is not None:os.close(lock)
        if directory is not None:os.close(directory)
        _operation_mutex.release()


# A short-lived, pipe-only session; it accepts only existing VPN helper verbs.
# No socket, policy relaxation, caller-selected executable, or secret on argv.
_SESSION_HELPERS = {kind: '/usr/local/lib/family-connect-'+kind+'/helper'
                    for kind in ('awg', 'tcp', 'mesh')}
_SESSION_HELPERS['auto'] = _SESSION_HELPERS['mesh']
_SESSION_HELPERS['chat'] = _SESSION_HELPERS['mesh']


def _session_line(stream, deadline):
    import select
    result = bytearray()
    while len(result) <= MAX_PROFILE * 2 + 4096:
        remaining = deadline - time.monotonic()
        if remaining <= 0 or not select.select([stream], [], [], remaining)[0]:
            raise BackendError('VPN authorization session timed out')
        chunk = os.read(stream.fileno(), 1)
        if not chunk:
            raise EOFError('VPN authorization session closed')
        if chunk == b'\n':
            return json.loads(result)
        result.extend(chunk)
    raise BackendError('VPN authorization message too large')


def _session_request(request):
    if not isinstance(request, dict) or set(request) != {'kind', 'action', 'ident', 'data'}:
        raise ValueError('Invalid session request')
    kind, action, ident, data = (request[k] for k in ('kind', 'action', 'ident', 'data'))
    if kind not in _SESSION_HELPERS or action not in ('import', 'up', 'down'):
        raise ValueError('Invalid session operation')
    if kind == 'chat':
        if action != 'up' or ident != 'fcchat0' or data is not None:
            raise ValueError('Invalid chat setup operation')
        return [_SESSION_HELPERS[kind], 'chat-up', 'fcchat0'], None
    if kind == 'mesh':
        if action not in ('up', 'down') or ident != 'fcmesh0' or data is not None:
            raise ValueError('Invalid MESH session operation')
        return [_SESSION_HELPERS[kind], action, ident], None
    if kind == 'auto':
        if (action not in ('up', 'down') or data is not None or not isinstance(ident, str) or
                (ident != 'fcauto0' if action == 'up' else re.fullmatch('[a-f0-9]{32}', ident) is None)):
            raise ValueError('Invalid Auto session operation')
        return [_SESSION_HELPERS[kind], 'auto-'+action, ident], None
    if action == 'import':
        if ident is not None or not isinstance(data, str) or len(data.encode()) > MAX_PROFILE:
            raise ValueError('Invalid import')
    elif data is not None or not isinstance(ident, str) or not re.fullmatch('fc'+kind+r'[0-9a-f]{8}', ident):
        raise ValueError('Invalid profile identity')
    return [_SESSION_HELPERS[kind], action] + ([ident] if ident else []), data


def privileged_session():
    # Invoked only by the root-installed helper, after pkexec authentication.
    uid = os.environ.get('PKEXEC_UID', '')
    if os.geteuid() != 0 or not uid.isdecimal() or int(uid) == 0:
        raise ValueError('Authenticated desktop user required')
    deadline = time.monotonic() + 300
    env = {'PATH': '/usr/sbin:/usr/bin:/sbin:/bin', 'LANG': 'C',
           'HOME': '/root', 'PKEXEC_UID': uid}
    print('{"ready":1}', flush=True)
    for _ in range(32):
        try:
            request = _session_line(sys.stdin.buffer, deadline)
        except EOFError:
            return
        args, data = _session_request(request)
        try:
            result = subprocess.run(args, input=data, capture_output=True, text=True,
                                    env=env, timeout=min(120, max(.1, deadline-time.monotonic())))
            reply = {'ok': result.returncode == 0,
                     'value': result.stdout.strip() if result.returncode == 0 else ''}
        except subprocess.TimeoutExpired:
            reply = {'ok': False, 'value': ''}
        print(json.dumps(reply), flush=True)


def _authorization_available(helper):
    try:
        marker = Path(helper).with_name('authorization-session-v1')
        for parent in marker.parents:
            info = parent.lstat()
            if not stat.S_ISDIR(info.st_mode) or info.st_uid != 0 or info.st_mode & 0o022:
                return False
        info = marker.lstat()
        return stat.S_ISREG(info.st_mode) and info.st_uid == 0 and not info.st_mode & 0o022
    except OSError:
        return False


class _AuthorizationSession:
    def __init__(self):
        self.process = None
        self.failed = False

    def call(self, kind, action, ident, data):
        request = dict(kind=kind, action=action, ident=ident, data=data)
        _session_request(request)
        if CANDIDATE_GUARD is not None and action != 'down':
            state = system_component_status()
            if state != 'READY':
                raise BackendError('Matching internal candidate system required: ' + state)
        if self.failed:
            raise AuthorizationError('VPN authorization session unavailable; retry explicitly')
        if self.process is None:
            helper = _SESSION_HELPERS[kind]
            if not _authorization_available(helper):
                raise BackendError('Update the Linux VPN helper to support single authorization')
            self.failed = True  # Never re-prompt after denial or a broken pipe.
            self.process = subprocess.Popen(['pkexec', helper, 'session'], stdin=subprocess.PIPE,
                                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=0)
            try:
                if _session_line(self.process.stdout, time.monotonic()+120) != {'ready': 1}:
                    raise ValueError('Invalid authorization response')
            except (EOFError, ValueError, BackendError):
                raise AuthorizationError('VPN authorization cancelled or unavailable') from None
            self.failed = False
        try:
            payload = memoryview((json.dumps(request)+'\n').encode())
            while payload:
                count = self.process.stdin.write(payload)
                if not count:
                    raise OSError('Closed authorization pipe')
                payload = payload[count:]
            reply = _session_line(self.process.stdout, time.monotonic()+125)
            if not isinstance(reply, dict) or set(reply) != {'ok', 'value'}:
                raise ValueError('Invalid operation response')
        except (OSError, EOFError, ValueError, BackendError):
            self.failed = True
            raise BackendError('VPN authorization session interrupted; recovery required') from None
        if reply['ok'] is not True:
            raise BackendError('VPN operation failed')
        return reply['value']

    def close(self):
        if self.process is not None:
            self.process.stdin.close()  # EOF revokes the session, including on exceptions.
            self.process.stdout.close()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                # An in-flight helper owns cleanup; it is bounded by the server timeout.
                threading.Thread(target=self.process.wait, daemon=True).start()


@contextmanager
def authorization_operation():
    if getattr(_operation_local, 'authorization', None) is not None:
        yield
        return
    session = _AuthorizationSession()
    _operation_local.authorization = session
    try:
        yield
    finally:
        _operation_local.authorization = None
        session.close()


def serialized_connection(method):
    @functools.wraps(method)
    def call(*args,**kwargs):
        with connection_operation(mutate=True), authorization_operation():
            return method(*args,**kwargs)
    return call


@contextmanager
def privileged_transport_start(kind, *, auto_guard=None):
    import fcntl
    if os.geteuid() != 0 or kind not in ('awg', 'tcp', 'mesh'):
        raise ValueError('Privileged transport owner required')
    descriptor = os.open('/run/family-connect-transport.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or info.st_nlink != 1 or stat.S_IMODE(info.st_mode) != 0o600:
            raise ValueError('Unsafe transport lock')
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if any(os.path.lexists('/run/family-connect-auto/'+name) for name in ('guard.json', 'normal.json', 'mesh.json')):
            if auto_guard is None:
                raise BackendError('Disconnect Auto and finish its cleanup before switching transports')
            auto_guard._owned()
        elif auto_guard is not None:
            raise BackendError('Auto traffic guard is unavailable')
        if kind != 'mesh' and Path('/run/family-connect-mesh/active.json').exists():
            raise BackendError('Disconnect MESH and finish its cleanup before switching transports')
        if kind != 'awg' and os.path.lexists('/run/family-connect-awg/active.json'):
            raise BackendError('Disconnect AWG and finish its cleanup before switching transports')
        yield
    finally:
        os.close(descriptor)


@dataclass(frozen=True)
class ConnectionSnapshot:
    generation: int
    items: list
    active_ids: list
    active: bool
    healthy: bool | None


def run(*args,timeout=30):
    result=subprocess.run(args,capture_output=True,text=True,timeout=timeout,
        creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0) if sys.platform=='win32' else 0)
    if result.returncode:
        raise BackendError('System VPN operation failed: '+Path(args[0]).name+'; exit='+str(result.returncode))
    return result.stdout.strip()


HEALTH_TARGETS=(('https://1.1.1.1/cdn-cgi/trace','trace'),('https://api.ipify.org','plain'))


def probe_interface(interface, expected):
    import ipaddress
    if not re.fullmatch(r'[a-zA-Z0-9_.-]{1,15}',interface):raise BackendError('Invalid VPN interface')
    expected=str(ipaddress.ip_address(expected))
    deadline=time.monotonic()+8
    for url,kind in HEALTH_TARGETS:
        remaining=deadline-time.monotonic()
        if remaining<=0:break
        try:
            # Reserve part of the shared budget for the independent second service.
            attempt=min(5,remaining)
            raw=run('/usr/bin/curl','--disable','--noproxy','*','--interface','if!'+interface,'--fail','--silent',
                '--connect-timeout',str(min(3,attempt)),'--max-time',str(attempt),
                '--max-filesize','4096',url,timeout=min(attempt+1,remaining))
            actual=dict(line.split('=',1) for line in raw.splitlines() if '=' in line).get('ip') if kind=='trace' else raw.strip()
            if actual==expected and time.monotonic()<deadline:return
        except (BackendError,subprocess.TimeoutExpired):pass
    raise BackendError('VPN internet checks failed')


class RecoveryPolicy:
    """UI-thread policy; health workers never change connection intent or routing."""
    interval=15
    max_attempts=3
    def __init__(self,clock=time.monotonic):
        self.clock=clock;self.stop()
    def stop(self):
        self.identity=None;self.failures=0;self.attempts=0;self.next_check=0
        self.good_since=None;self.exhausted=False
    def arm(self,identity):
        self.stop();self.identity=identity;self.next_check=self.clock()+self.interval
    def due(self,identity):
        return self.identity is not None and self.identity==identity and not self.exhausted and self.clock()>=self.next_check
    def observe(self,healthy,*,allow_recovery=True):
        if self.identity is None or self.exhausted:return False
        now=self.clock();self.next_check=now+self.interval
        if healthy:
            self.failures=0
            if self.good_since is None:self.good_since=now
            if now-self.good_since>=60:self.attempts=0
            return False
        self.good_since=None;self.failures+=1
        if self.failures<2 or not allow_recovery:return False
        if self.attempts>=self.max_attempts:self.exhausted=True;return False
        self.attempts+=1;return True
    def recovered(self,success):
        self.good_since=None
        if success:self.failures=0
        else:self.failures=2
        self.exhausted=not success and self.attempts>=self.max_attempts
        self.next_check=self.clock()+min(60,15*2**max(0,self.attempts-1))


class Linux:
    def server_load(self,ident):
        if ident in ('country:ru','country:nl'):country=ident.split(':')[1]
        else:
            records=self._awg_records()
            if hasattr(self,'_tcp_records'):records.update(self._tcp_records())
            endpoint=records.get(ident,{}).get('endpoint')
            country={'185.251.89.19':'ru','186.246.45.246':'nl'}.get(endpoint)
        if country is None:return None
        request=urllib.request.Request('https://185.251.89.19:8443/status/server-load.json',
            headers={'Accept':'application/json','Cache-Control':'no-cache'})
        with urllib.request.urlopen(request,timeout=5) as response:payload=response.read(8193)
        return verified_server_load(payload,country,time.time())
    def server_loads(self):
        request=urllib.request.Request('https://185.251.89.19:8443/status/server-load.json',
            headers={'Accept':'application/json','Cache-Control':'no-cache'})
        with urllib.request.urlopen(request,timeout=5) as response:payload=response.read(8193)
        return verified_server_loads(payload,time.time())
    @contextmanager
    def control_transaction(self, owner):
        # GUI status polling briefly owns the same lock. Wait only on entry;
        # never replay an application mutation, bypass pending ownership, or
        # make GUI operations block behind control. The bound also covers an
        # unrelated pending owner, which still fails closed after five seconds.
        from contextlib import ExitStack
        deadline = time.monotonic() + 5
        with ExitStack() as stack:
            while True:
                try:
                    lease = stack.enter_context(connection_operation(owner=owner))
                    break
                except ConnectionBusy:
                    if time.monotonic() >= deadline:
                        raise
                    time.sleep(.05)
            with authorization_operation():
                yield lease

    def poll_state(self, ident, health=False):
        with connection_operation() as lease:
            generation=lease.record['generation']
        try:
            items=self.profiles()
            active_ids=[key for key,_ in items if self.active(key)]
            healthy=self.healthy(ident) if health else None
        finally:
            with connection_operation(expected=generation):pass
        return ConnectionSnapshot(generation,items,active_ids,ident in active_ids,healthy)

    def recover_if_current(self, ident, generation):
        # Recovery preserves connection intent and its finite retry budget.
        # Nested driver mutations are already covered by this exclusive lease.
        with connection_operation(expected=generation):
            self.recover(ident)
            return self.active(ident)

    awg_root=Path('/etc/family-connect/awg')
    awg_helper='/usr/local/lib/family-connect-awg/helper'
    def _awg_records(self):
        return self._records(self.awg_root,'fcawg')
    def _records(self,root,prefix):
        if not root.exists(): return {}
        info=root.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid!=0 or info.st_mode&0o022:
            raise BackendError('Unsafe AWG installation')
        records={}
        for path in root.glob(prefix+'*.json'):
            fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
            try:
                info=os.fstat(fd)
                if not stat.S_ISREG(info.st_mode) or info.st_uid!=0 or info.st_mode&0o022 or info.st_nlink!=1:
                    raise BackendError('Unsafe AWG metadata')
                record=json.loads(os.read(fd,4097))
            finally:os.close(fd)
            if record['owner']!=os.getuid():continue
            if not re.fullmatch(prefix+r'[0-9a-f]{8}',record['id']) or path.stem!=record['id']:
                raise BackendError('Invalid AWG metadata')
            records[record['id']]=record
        return records
    def _awg(self,action,ident=None,data=None):
        session = getattr(_operation_local, 'authorization', None)
        if session is not None:
            return session.call('awg', action, ident, data)
        args=['pkexec',self.awg_helper,action]+([ident] if ident else [])
        try:
            p=subprocess.run(args,input=data,capture_output=True,text=True,timeout=120)
        except subprocess.TimeoutExpired:
            raise BackendError('AWG authorization or operation timed out') from None
        if p.returncode in (126,127):raise AuthorizationError('AmneziaWG authorization cancelled or unavailable')
        if p.returncode:raise BackendError('AmneziaWG operation failed')
        return p.stdout.strip()
    def _fallback(self,ident):
        matches=[key for key,value in self._awg_records().items() if value.get('primary')==ident]
        if len(matches)>1:raise BackendError('Ambiguous fallback configuration')
        return matches[0] if matches else None
    def _nm_active(self,ident):
        return ident in run('nmcli','-t','-f','UUID','connection','show','--active',timeout=3).splitlines()
    def _probe(self,ident,expected):
        interface=run('nmcli','-g','GENERAL.DEVICES','connection','show',ident,timeout=3)
        if not re.fullmatch(r'[a-zA-Z0-9_.-]{1,15}',interface): raise BackendError('Missing VPN interface')
        probe_interface(interface,expected)
    def supports_recovery(self,ident):
        return ident in self._awg_records() or self._fallback(ident) is not None
    def control_healthy(self,ident,expected):
        """A control commit requires traffic health even for standalone NM WG.

        The expected gateway comes from the verified configuration. Existing
        AWG/TCP health stays in its transport implementation; NM WG additionally
        proves interface-bound HTTPS egress instead of only reporting active.
        """
        if not self.healthy(ident):return False
        if self._nm_active(ident):
            try:self._probe(ident,expected)
            except (BackendError,subprocess.TimeoutExpired):return False
        return True

    def healthy(self,ident):
        records=self._awg_records();fallback=self._fallback(ident)
        awg=ident if ident in records else fallback
        if not awg:return self.active(ident)
        primary=records.get(ident,{}).get('primary') or ident
        try:
            if Path('/sys/class/net',awg).exists():probe_interface(awg,records[awg]['endpoint'])
            elif self._nm_active(primary):self._probe(primary,records[awg]['endpoint'])
            else:return False
            return True
        except (BackendError,subprocess.TimeoutExpired):return False
    @serialized_connection
    def recover(self,ident):
        # Called only after UI intent/revision checks; serialized with user operations.
        # A failed AWG may reconnect to a working original WG, then fall back again.
        records=self._awg_records()
        primary=records.get(ident,{}).get('primary') or ident
        fallback=self._fallback(primary)
        failed_wg=bool(fallback and not Path('/sys/class/net',fallback).exists() and self._nm_active(primary))
        self.disconnect(primary)
        if failed_wg:self._awg('up',fallback)
        else:self.connect(primary)
        if not self.healthy(primary):raise BackendError('Connection recovery failed')
    def profiles(self):
        result=[]
        for line in run('nmcli','-t','--escape','no','-f','UUID,NAME,TYPE','connection','show').splitlines():
            parts=line.split(':')
            if len(parts)==3 and parts[2]=='wireguard' and (parts[1].startswith(PREFIX) or parts[1]=='fc-ru-linux'):
                result.append((parts[0],parts[1]))
        result.extend((ident,'AmneziaWG · '+ident) for ident in self._awg_records())
        return result
    def active(self,ident):
        records=self._awg_records()
        if ident in records:
            primary=records[ident].get('primary')
            return Path('/sys/class/net',ident).exists() or bool(primary and self._nm_active(primary))
        fallback=self._fallback(ident)
        if fallback and Path('/sys/class/net',fallback).exists():return True
        return ident in run('nmcli','-t','-f','UUID','connection','show','--active',timeout=3).splitlines()
    @serialized_connection
    def connect(self,ident):
        records=self._awg_records()
        if ident in records:
            primary=records[ident].get('primary')
            was_active=bool(primary and self._nm_active(primary))
            if was_active:run('nmcli','connection','down','uuid',primary)
            try:self._awg('up',ident)
            except Exception:
                if was_active:run('nmcli','connection','up','uuid',primary)
                raise
            return
        fallback=self._fallback(ident)
        if fallback and Path('/sys/class/net',fallback).exists():
            self._awg('up',fallback);return
        if not fallback:
            run('nmcli','connection','up','uuid',ident);return
        # Bounded connection-time failover. No routing changes during status polling.
        try:
            run('nmcli','connection','up','uuid',ident)
            for attempt in range(2):
                try:self._probe(ident,records[fallback]['endpoint']);return
                except BackendError:
                    if attempt:raise
                    time.sleep(1)
        except (BackendError,subprocess.TimeoutExpired):
            if self._nm_active(ident):run('nmcli','connection','down','uuid',ident)
            self._awg('up',fallback)
    @serialized_connection
    def disconnect(self,ident):
        records=self._awg_records()
        if ident in records:
            self._awg('down',ident)
            primary=records[ident].get('primary')
            if primary and self._nm_active(primary):run('nmcli','connection','down','uuid',primary)
            return
        fallback=self._fallback(ident)
        if fallback:self._awg('down',fallback)
        if self._nm_active(ident):run('nmcli','connection','down','uuid',ident)
    @serialized_connection
    def import_profile(self,path):
        data=read_profile(path,allow_awg=True,allow_awg31=True)
        if set(parse(data,allow_awg=True,allow_awg31=True)['Interface'])&AWG_FIELDS:
            return self._awg('import',data=data)
        name=PREFIX+uuid.uuid4().hex[:8]
        with tempfile.TemporaryDirectory(prefix='family-connect-') as folder:
            file=Path(folder)/(name+'.conf')
            fd=os.open(file,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
            with os.fdopen(fd,'w') as out: out.write(data)
            answer=run('nmcli','connection','import','type','wireguard','file',str(file))
            match=re.search(r'\b[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\b',answer,re.I)
            if not match: raise BackendError('Unable to identify imported connection')
            ident=match.group()
            try:
                run('nmcli','connection','modify',ident,'connection.autoconnect','no',
                    'ipv4.dns-priority','-50','ipv6.dns-priority','-50','ipv4.dns-search','~.')
            except Exception:
                run('nmcli','connection','delete','uuid',ident)
                raise
        return ident


class LinuxTCP(Linux):
    tcp_root=Path('/etc/family-connect/tcp')
    tcp_helper='/usr/local/lib/family-connect-tcp/helper'
    def _tcp_records(self):return self._records(self.tcp_root,'fctcp')
    def _tcp(self,action,ident=None,data=None):
        session = getattr(_operation_local, 'authorization', None)
        if session is not None:
            return session.call('tcp', action, ident, data)
        try:
            p=subprocess.run(['pkexec',self.tcp_helper,action]+([ident] if ident else []),
                input=data,capture_output=True,text=True,timeout=120)
        except subprocess.TimeoutExpired:raise BackendError('TCP operation timed out') from None
        if p.returncode in (126,127):raise AuthorizationError('TCP authorization cancelled or unavailable')
        if p.returncode:raise BackendError('TCP operation failed')
        return p.stdout.strip()
    def _chain(self,ident):
        awg=self._awg_records();tcp=self._tcp_records()
        primary={**awg,**tcp}.get(ident,{}).get('primary') or ident
        matches=[key for key,value in tcp.items() if key==primary or value.get('primary')==primary]
        if len(matches)>1:raise BackendError('Ambiguous TCP fallback')
        if not matches:return None
        end=matches[0]
        fallback=self._fallback(primary)
        expected=awg[fallback]['endpoint'] if fallback else tcp[end]['endpoint']
        chain=[] if primary==end else [('wg',primary,expected)]
        if fallback:chain.append(('awg',fallback,awg[fallback]['endpoint']))
        chain.append(('tcp',end,tcp[end]['endpoint']))
        return chain
    def _live(self,item):
        kind,ident,_=item
        return self._nm_active(ident) if kind=='wg' else Path('/sys/class/net',ident).exists()
    def _stop(self,item):
        kind,ident,_=item
        if kind=='wg':
            if self._nm_active(ident):run('nmcli','connection','down','uuid',ident)
        elif kind=='awg':self._awg('down',ident)
        else:self._tcp('down',ident)
    def _check(self,item):
        kind,ident,expected=item
        if kind=='wg':self._probe(ident,expected)
        else:probe_interface(ident,expected)
    def _attempt(self,chain):
        for index,item in enumerate(chain):
            kind,ident,_=item
            try:
                if kind=='wg':run('nmcli','connection','up','uuid',ident)
                elif kind=='awg':self._awg('up',ident)
                else:self._tcp('up',ident)
                self._check(item);return
            except AuthorizationError:raise
            except (BackendError,subprocess.TimeoutExpired):
                # A cleanup failure stops the chain; never stack conflicting routes.
                # No later transport will start: an inactive final TCP needs no
                # second authorization. Any residual root state remains guarded
                # by the helper on the next explicit start.
                if not (kind=='tcp' and index==len(chain)-1 and not self._live(item)):
                    self._stop(item)
                if index==len(chain)-1:raise BackendError('All VPN transports failed') from None
    def profiles(self):
        return super().profiles()+[(ident,'VLESS + REALITY · '+ident) for ident in self._tcp_records()]
    def supports_recovery(self,ident):return bool(self._chain(ident)) or super().supports_recovery(ident)
    def allows_automatic_recovery(self,ident):
        chain=self._chain(ident)
        return not (chain and len(chain)==1 and chain[0][0]=='tcp')
    def active(self,ident):
        chain=self._chain(ident)
        return any(self._live(item) for item in chain) if chain else super().active(ident)
    def healthy(self,ident):
        chain=self._chain(ident)
        if not chain:return super().healthy(ident)
        live=[item for item in chain if self._live(item)]
        if len(live)!=1:return False
        try:self._check(live[0]);return True
        except (BackendError,subprocess.TimeoutExpired):return False
    @serialized_connection
    def disconnect(self,ident):
        chain=self._chain(ident)
        if not chain:return super().disconnect(ident)
        for item in reversed(chain):
            if item[0]=='awg' or self._live(item):self._stop(item)
    @serialized_connection
    def connect(self,ident):
        chain=self._chain(ident)
        if not chain:return super().connect(ident)
        selected=next((item for item in chain if item[1]==ident),chain[0])
        if self.healthy(ident) and (selected==chain[0] or self._live(selected)):return
        self.disconnect(ident)
        start=next((i for i,item in enumerate(chain) if item[1]==ident),0)
        self._attempt(chain[start:])
    @serialized_connection
    def recover(self,ident):
        chain=self._chain(ident)
        if not chain:return super().recover(ident)
        live=[i for i,item in enumerate(chain) if self._live(item)]
        start=(live[0]+1)%len(chain) if len(live)==1 else 0
        self.disconnect(ident)
        self._attempt(chain[start:]+chain[:start])
    @serialized_connection
    def import_profile(self,path):
        with Path(path).open('rb') as source:raw=source.read(MAX_PROFILE+1).decode('utf-8-sig')
        if raw.lstrip().startswith('{'):
            return self._tcp('import',data=json.dumps(parse_tcp(raw)))
        return super().import_profile(path)


MESH_ROOT = Path('/usr/local/lib/family-connect-mesh')
CANDIDATE_GUARD = None
CANDIDATE_SETUP = None
CANDIDATE_VERSION = None
MESH_RUN = Path('/run/family-connect-mesh')
MESH_FILES = ('helper', 'fc-mesh', 'mesh_ipc.py', 'mesh_chat.py', 'mesh_chat_host.py', 'provisioning/chat_bridge_protocol.py', 'mesh_materials.py', 'mesh_network.py', 'mesh_intent.py',
              'mesh_service.py', 'mesh_system.py', 'backend.py', 'profile_config.py',
              'authorization-session-v1', 'capabilities.json', 'rns/fc-rns.pyz', 'rns/build.json',
              'installed.json', 'python-runtime.json', 'system_runtime.py', 'chat_direct_host.py',
              'mesh_chat_service.py', 'mesh_ownership.py', 'update.pub', 'provisioning/chat_direct.py',
              'provisioning/chat_bridge.py', 'provisioning/friends.py', 'device_identity/device.py', 'messenger/codec.py')


def mesh_presentation(status):
    state = status.get('state', 'FAILED')
    if state not in ('DISCONNECTED', 'CONNECTING', 'CONNECTED', 'RESTORING', 'STOPPING', 'FAILED'):
        state = 'FAILED'
    desired = status.get('desired_connected') is True
    result = dict(state=state, desired=desired, owned=desired or state != 'DISCONNECTED',
                  connected=state == 'CONNECTED', pending=state in ('CONNECTING', 'RESTORING', 'STOPPING'),
                  selected_profile=None, effective=None)
    worker = status.get('native')
    native = worker.get('native') if isinstance(worker, dict) else None
    if not isinstance(native, dict):
        return result
    selected = native.get('selected_profile')
    if selected in ('P0', 'P1'):
        result['selected_profile'] = selected
    if not result['connected'] or native.get('tun_ready') is not True:
        return result
    packet = native.get('packet')
    diagnostic = packet.get('diagnostic') if isinstance(packet, dict) else None
    if not isinstance(diagnostic, dict):
        return result
    limits = diagnostic.get('reliable_limits')
    if not isinstance(limits, dict):
        return result
    send, receive = limits.get('effective_send'), limits.get('local_receive')
    mux, window = diagnostic.get('mux_profile'), diagnostic.get('mux_window')
    if (type(send) is int and 1 <= send <= 32 and type(receive) is int and 1 <= receive <= 32 and
            ((mux == 'CREDIT128' and window == 131072) or (mux == 'LEGACY64' and window == 65536))):
        result['effective'] = f'RS{send}/{receive} · {mux}'
    return result


def auto_presentation(status):
    state = 'STOPPING' if status.get('state') == 'DISCONNECTING' else status.get('state', 'FAILED')
    controller = status.get('controller')
    controller = controller if isinstance(controller, dict) else {}
    selected = status.get('selected', '')
    mesh = controller.get('mesh') or {}
    view = mesh_presentation(dict(state=state, desired_connected=status.get('desired_connected'),
        native=mesh.get('native') if selected == 'restricted' else None))
    view['selected_profile'] = status.get('requested_profile') if selected == 'restricted' and status.get('requested_profile') in ('P0', 'P1') else None
    view['transport'] = {'awg': 'AWG 3.1', 'tcp': 'TCP REALITY', 'restricted': 'MESH'}.get(selected) if view['connected'] else None
    return view


def _mesh_trusted(path, directory=False):
    info = path.lstat()
    if (info.st_uid != 0 or info.st_mode & 0o022 or
            not (stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode)) or
            (not directory and info.st_nlink != 1)):
        raise BackendError('Unsafe MESH system component')
    return info


def system_component_status():
    try:
        for kind in ('awg', 'tcp'):
            config = Path('/etc/family-connect') / kind
            for directory in (config, *config.parents):
                _mesh_trusted(directory, directory=True)
            if stat.S_IMODE(config.lstat().st_mode) != 0o755:
                return 'NORMAL_CONFIGURATION_UNAVAILABLE'
        for parent in (MESH_ROOT, *MESH_ROOT.parents):
            _mesh_trusted(parent, directory=True)
        for name in MESH_FILES:
            if '/' in name:
                _mesh_trusted((MESH_ROOT / name).parent, directory=True)
            _mesh_trusted(MESH_ROOT / name)
        if not all(os.access(MESH_ROOT / name, os.X_OK) for name in ('helper', 'fc-mesh')):
            return 'EXECUTABLE_UNAVAILABLE'
        with (MESH_ROOT / 'capabilities.json').open('rb') as source:
            raw = source.read(2049)
        if len(raw) > 2048:
            return 'CAPABILITY_OVERSIZED'
        value = json.loads(raw)
        compatible = (type(value) is dict and value.get('schema') == 2 and value.get('runtime_contract') == 2 and value.get('chat_setup_protocol') == 1 and
                all(type(value.get(key)) is int and value[key] == 1 for key in ('bridge_protocol', 'materials_protocol', 'intent_protocol')) and
                value['core_reference'] == 'android106-native105' and value['profiles'] == ['P0', 'P1'] and
                isinstance(value['source_digest'], str) and re.fullmatch('[a-f0-9]{64}', value['source_digest']) is not None)
        if not compatible:
            return 'RUNTIME_CONTRACT_MISMATCH'
        with (MESH_ROOT / 'installed.json').open('rb') as source:
            inventory_raw = source.read(1048577)
        if len(inventory_raw) > 1048576 or hashlib.sha256(inventory_raw).hexdigest() != value['installed_sha256']:
            return 'INSTALLED_MANIFEST_MISMATCH'
        inventory = json.loads(inventory_raw)
        if inventory['schema'] != 2 or inventory['build_id'] != value['build_id'] or inventory['source_digest'] != value['source_digest']:
            return 'BUILD_ID_MISMATCH'
        files = inventory['files']
        required = {str(MESH_ROOT / name) for name in MESH_FILES if name not in ('installed.json', 'capabilities.json', 'authorization-session-v1')}
        required.update('/etc/systemd/system/family-connect-' + name + '@.service' for name in ('mesh', 'auto', 'chat-direct', 'chat-mesh'))
        required.add('/etc/systemd/system/family-connect-tcp@.service')
        for kind, names in {'awg': ('awg', 'amneziawg-go', 'awg-quick', 'awg31.json', 'LICENSE-go', 'LICENSE-tools', 'awg_lifecycle.py'),
                            'tcp': ('xray', 'LICENSE')}.items():
            required.update('/usr/local/lib/family-connect-' + kind + '/' + name
                            for name in (*names, 'helper', 'backend.py', 'profile_config.py', 'authorization-session-v1'))
        if not required <= set(files) or not any(str(MESH_ROOT / 'vendor') + '/' in name for name in files):
            return 'RUNTIME_INCOMPLETE'
        for name, expected in files.items():
            path = Path(name)
            allowed = path.is_relative_to(MESH_ROOT) or (path.parent == Path('/etc/systemd/system') and name in required)
            allowed = allowed or name in required
            if not allowed or '..' in path.parts:
                return 'INSTALLED_PATH_INVALID'
            for parent in path.parents:
                _mesh_trusted(parent, directory=True)
            info = _mesh_trusted(path)
            if info.st_size != expected['size'] or stat.S_IMODE(info.st_mode) != expected['mode']:
                return 'INSTALLED_FILE_METADATA_MISMATCH'
            if hashlib.sha256(path.read_bytes()).hexdigest() != expected['sha256']:
                return 'INSTALLED_FILE_HASH_MISMATCH'
        vendor = {str(path) for path in (MESH_ROOT / 'vendor').rglob('*') if path.is_symlink() or not path.is_dir()}
        if vendor != {name for name in files if name.startswith(str(MESH_ROOT / 'vendor') + '/')}:
            return 'PYTHON_RUNTIME_MEMBERS_MISMATCH'
        return CANDIDATE_GUARD(value) if CANDIDATE_GUARD is not None else 'READY'
    except FileNotFoundError:
        return 'RUNTIME_INCOMPLETE'
    except (OSError, ValueError, TypeError, KeyError, BackendError):
        return 'UNSAFE_RUNTIME'


def mesh_component_available():
    return system_component_status() == 'READY'


def prepare_chat_services():
    state = system_component_status()
    if state != 'READY':
        raise BackendError('Verified chat system component required: ' + state)
    with authorization_operation():
        return _operation_local.authorization.call('chat', 'up', 'fcchat0', None)


def setup_candidate_system():
    if CANDIDATE_SETUP is None:
        raise BackendError('Install the complete internal candidate first')
    return CANDIDATE_SETUP()


def _mesh_protocol():
    import importlib.util
    if not mesh_component_available():
        raise BackendError('Install the verified MESH system component first')
    spec = importlib.util.spec_from_file_location('family_connect_private_mesh_ipc', MESH_ROOT / 'mesh_ipc.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MeshServiceClient:
    def __init__(self):
        self.protocol = _mesh_protocol()

    def call(self, action, material=None):
        import socket
        import struct
        protocol = self.protocol
        request = dict(schema=1, id=1, action=action)
        if material is not None:
            request['materials'] = material
        protocol.validate_request(request)
        connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            info = _mesh_trusted(MESH_RUN, directory=True)
            if stat.S_IMODE(info.st_mode) != 0o711:
                raise BackendError('Unsafe MESH service endpoint')
            endpoint = MESH_RUN / (str(os.getuid()) + '.sock')
            info = endpoint.lstat()
            if not stat.S_ISSOCK(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o600:
                raise BackendError('Unsafe MESH service endpoint')
            connection.settimeout(4)
            connection.connect(str(endpoint))
            credentials = connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12)
            if struct.unpack('3i', credentials)[1] != 0:
                raise BackendError('MESH service is not privileged')
            deadline = time.monotonic() + (24 if action == 'stop' else 4)
            protocol.send(connection.fileno(), request, protocol.MAX_REQUEST, deadline)
            reply = protocol.receive(connection.fileno(), protocol.MAX_REPLY, deadline)
            fields = {'schema', 'id', 'ok', 'state', 'reason', 'first_reason', 'desired_connected', 'attempt',
                      'events', 'events_dropped', 'native', 'readiness'}
            if (set(reply) != fields or type(reply['schema']) is not int or reply['schema'] != 1 or
                    type(reply['id']) is not int or reply['id'] != 1 or type(reply['ok']) is not bool or
                    type(reply['desired_connected']) is not bool or reply['state'] not in
                    ('DISCONNECTED', 'CONNECTING', 'CONNECTED', 'RESTORING', 'STOPPING', 'FAILED')):
                raise BackendError('Invalid MESH service response')
            if not reply['ok']:
                raise BackendError('MESH service rejected the operation')
            for field in ('reason', 'first_reason'):
                if not isinstance(reply[field], str) or not re.fullmatch('[A-Z][A-Z0-9_]{0,63}', reply[field]):
                    raise BackendError('Invalid MESH diagnostic code')
            for field in ('attempt', 'events_dropped'):
                if type(reply[field]) is not int or not 0 <= reply[field] < 2**63:
                    raise BackendError('Invalid MESH service counter')
            if (not isinstance(reply['events'], list) or len(reply['events']) > 32 or
                    not isinstance(reply['native'], dict) or not isinstance(reply['readiness'], dict)):
                raise BackendError('Invalid MESH service state')
            return reply
        except (OSError, ValueError, EOFError, TimeoutError):
            raise BackendError('MESH service communication failed') from None
        finally:
            request.clear()
            connection.close()


class LinuxMesh(LinuxTCP):
    def mesh_available(self):
        return mesh_component_available()

    def _mesh_setup(self, action):
        session = getattr(_operation_local, 'authorization', None)
        if session is None:
            raise BackendError('MESH setup requires the existing authorization owner')
        return session.call('mesh', action, 'fcmesh0', None)

    def mesh_status(self):
        endpoint = MESH_RUN / (str(os.getuid()) + '.sock')
        if not endpoint.exists():
            if (MESH_RUN / 'active.json').exists():
                return dict(state='FAILED', desired_connected=True, reason='SERVICE_UNAVAILABLE')
            return dict(state='DISCONNECTED', desired_connected=False, reason='NONE')
        return MeshServiceClient().call('status')

    def profiles(self):
        result = super().profiles()
        if self.mesh_available():
            result.append(('fcmesh0', 'Family Connect · MESH'))
        return result

    def active(self, ident):
        return self.mesh_status()['state'] == 'CONNECTED' if ident == 'fcmesh0' else super().active(ident)

    def allows_automatic_recovery(self, ident):
        return False if ident == 'fcmesh0' else super().allows_automatic_recovery(ident)

    def check_mesh_ip(self):
        import ipaddress
        before = self.mesh_status()
        if before['state'] != 'CONNECTED':
            raise BackendError('MESH is not connected')
        raw = run('/usr/bin/curl', '--disable', '--noproxy', '*', '--interface', 'if!fcmesh0',
                  '--fail', '--silent', '--connect-timeout', '3', '--max-time', '8',
                  '--max-filesize', '4096', 'https://1.1.1.1/cdn-cgi/trace', timeout=9)
        after = self.mesh_status()
        if after['state'] != 'CONNECTED' or before.get('attempt') != after.get('attempt'):
            raise BackendError('MESH session changed')
        values = dict(line.split('=', 1) for line in raw.splitlines() if '=' in line)
        try:
            address = str(ipaddress.IPv4Address(values.get('ip', '')))
        except ValueError:
            raise BackendError('Invalid MESH IP check response') from None
        country = values.get('loc', '')
        if not re.fullmatch('[A-Z]{2}', country):
            raise BackendError('Invalid MESH location response')
        return 'IP: ' + address + ' · ' + country

    @serialized_connection
    def start_mesh(self, material):
        try:
            client = MeshServiceClient()
            client.protocol.validate_request(dict(schema=1, id=1, action='start', materials=material))
            if any(super(LinuxMesh, self).active(ident) for ident, _ in super().profiles()):
                raise BackendError('Disconnect the existing VPN before starting MESH')
            self._mesh_setup('up')
            deadline = time.monotonic() + 5
            endpoint = MESH_RUN / (str(os.getuid()) + '.sock')
            while not endpoint.exists() and time.monotonic() < deadline:
                time.sleep(.05)
            return client.call('start', material)
        finally:
            material.clear()

    @serialized_connection
    def connect(self, ident):
        if ident == 'fcmesh0':
            raise BackendError('Connect MESH through this computer\'s activated account')
        if self.mesh_status().get('desired_connected'):
            raise BackendError('Disconnect MESH before switching transport')
        return super().connect(ident)

    @serialized_connection
    def disconnect(self, ident):
        if ident != 'fcmesh0':
            return super().disconnect(ident)
        try:
            if self.mesh_status()['state'] != 'DISCONNECTED':
                MeshServiceClient().call('stop')
        except BackendError:
            pass
        self._mesh_setup('down')
        if (MESH_RUN / 'active.json').exists():
            raise BackendError('MESH cleanup has not completed')

    def recover(self, ident):
        if ident == 'fcmesh0':
            raise BackendError('MESH recovery belongs to its existing system service')
        return super().recover(ident)

    def healthy(self, ident):
        if ident == 'fcmesh0':
            state = self.mesh_status()
            return state['state'] == 'CONNECTED' and state.get('native', {}).get('health', {}).get('state') == 'ok'
        return super().healthy(ident)


AUTO_RUN = Path('/run/family-connect-auto-ipc')
AUTO_UNIT = Path('/etc/systemd/system/family-connect-auto@.service')
AUTO_FILES = ('auto_ipc.py', 'auto_intent.py', 'auto_service.py', 'auto_runtime.py', 'auto_platform.py',
              'auto_policy.py', 'auto_guard.py', 'auto_configuration.py', 'auto_mesh.py', 'auto_normal.py',
              'auto_normal_worker.py', 'auto-capabilities.json')


def auto_component_present():
    return any(os.path.lexists(path) for path in (MESH_ROOT/'auto_service.py', MESH_ROOT/'auto-capabilities.json', AUTO_UNIT))


def auto_component_available():
    try:
        if not mesh_component_available():
            return False
        for name in AUTO_FILES:
            _mesh_trusted(MESH_ROOT/name)
        for parent in AUTO_UNIT.parents:
            _mesh_trusted(parent, directory=True)
        _mesh_trusted(AUTO_UNIT)
        with (MESH_ROOT/'auto-capabilities.json').open('rb') as source:
            raw = source.read(2049)
        if len(raw) > 2048:
            return False
        value = json.loads(raw)
        base = json.loads((MESH_ROOT/'capabilities.json').read_bytes())
        return (type(value) is dict and set(value) == {'schema', 'service_protocol', 'catalog_protocol', 'source_digest', 'build_id'} and
                value['schema'] == 2 and all(type(value[key]) is int and value[key] == 1 for key in ('service_protocol', 'catalog_protocol')) and
                value['source_digest'] == base['source_digest'] and value['build_id'] == base['build_id'])
    except (OSError, ValueError, BackendError):
        return False


def _auto_protocol():
    import importlib.util
    if not auto_component_available():
        raise BackendError('Update the verified Auto system component first')
    name = 'family_connect_auto_protocol_'+uuid.uuid4().hex
    spec = importlib.util.spec_from_file_location(name, MESH_ROOT/'auto_ipc.py', submodule_search_locations=[str(MESH_ROOT)])
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
        return module
    finally:
        sys.modules.pop(name+'.mesh_ipc', None)
        sys.modules.pop(name, None)


class AutoServiceClient:
    def __init__(self):
        self.protocol = _auto_protocol()

    def call(self, action, *, selection=None, generation=None):
        import socket
        protocol = self.protocol
        request = dict(schema=1, id=1, action=action)
        if selection is not None:
            request['selection'] = selection
        if generation is not None:
            request['generation'] = generation
        protocol.validate_request(request)
        connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            info = _mesh_trusted(AUTO_RUN, directory=True)
            if stat.S_IMODE(info.st_mode) != 0o711:
                raise BackendError('Unsafe Auto service endpoint')
            endpoint = AUTO_RUN/(str(os.getuid())+'.sock')
            info = endpoint.lstat()
            if not stat.S_ISSOCK(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o600:
                raise BackendError('Unsafe Auto service socket')
            connection.settimeout(4)
            connection.connect(str(endpoint))
            if protocol.ipc.peer_uid(connection) != 0:
                raise BackendError('Auto service is not privileged')
            deadline = time.monotonic()+6
            protocol.ipc.send(connection.fileno(), request, protocol.MAX_REQUEST, deadline)
            reply = protocol.ipc.receive(connection.fileno(), protocol.MAX_REPLY, deadline)
            common = {'schema', 'id', 'ok'}
            expected = common | ({'catalog'} if action == 'catalog' else
                {'state', 'reason', 'generation', 'desired_connected', 'requested_profile', 'controller'})
            if (set(reply) != expected or type(reply['schema']) is not int or reply['schema'] != 1 or
                    type(reply['id']) is not int or reply['id'] != 1 or type(reply['ok']) is not bool):
                raise BackendError('Invalid Auto service response')
            if not reply['ok']:
                raise BackendError('Auto service rejected the operation; inspect current status before retrying')
            if action == 'catalog':
                if reply['catalog'] is not None:
                    protocol.catalog(reply['catalog'])
                return reply['catalog']
            if (reply['state'] not in ('DISCONNECTED', 'CONNECTING', 'CONNECTED', 'RESTORING', 'FAILED', 'DISCONNECTING') or
                    type(reply['desired_connected']) is not bool or not isinstance(reply['generation'], str) or
                    (reply['generation'] != '' and re.fullmatch('[a-f0-9]{32}', reply['generation']) is None) or
                    not isinstance(reply['reason'], str) or re.fullmatch('[A-Z_]{0,64}', reply['reason']) is None or
                    reply['requested_profile'] not in ('', 'P0', 'P1') or
                    (reply['state'] != 'DISCONNECTED' and not reply['generation'])):
                raise BackendError('Invalid Auto service state')
            controller = reply['controller']
            if controller is not None:
                if (not isinstance(controller, dict) or set(controller) != {'policy', 'platform', 'mesh'} or
                        not all(isinstance(controller[key], dict) for key in controller) or
                        controller['policy'].get('selected', '') not in ('', 'wg', 'awg', 'tcp', 'restricted')):
                    raise BackendError('Invalid Auto controller snapshot')
            reply['selected'] = controller['policy'].get('selected', '') if controller else ''
            return reply
        except (OSError, EOFError, ValueError, TimeoutError):
            raise BackendError('Auto service unavailable or protocol rejected; do not replay a start') from None
        finally:
            request.clear()
            connection.close()


def _auto_receipt(value=None):
    with connection_operation() as lease:
        def validate(record):
            if (not isinstance(record, dict) or set(record) != {'schema', 'generation', 'desired'} or
                    type(record['schema']) is not int or record['schema'] != 1 or type(record['desired']) is not bool or
                    not isinstance(record['generation'], str) or
                    (record['generation'] != '' and re.fullmatch('[a-f0-9]{32}', record['generation']) is None)):
                raise BackendError('Invalid Auto session receipt')
        if value is not None:
            validate(value)
            temporary = '.auto-session-'+uuid.uuid4().hex
            descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=lease.directory)
            try:
                with os.fdopen(descriptor, 'wb') as output:
                    output.write(json.dumps(value, separators=(',', ':')).encode())
                    output.flush()
                    os.fsync(output.fileno())
                os.replace(temporary, 'auto-session.json', src_dir_fd=lease.directory, dst_dir_fd=lease.directory)
                os.fsync(lease.directory)
            finally:
                try:os.unlink(temporary, dir_fd=lease.directory)
                except FileNotFoundError:pass
        try:
            descriptor = os.open('auto-session.json', os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=lease.directory)
        except FileNotFoundError:
            return None
        with os.fdopen(descriptor, 'rb') as source:
            info = os.fstat(source.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_nlink != 1 or stat.S_IMODE(info.st_mode) != 0o600:
                raise BackendError('Unsafe Auto session receipt')
            raw = source.read(1025)
        if len(raw) > 1024:
            raise BackendError('Oversized Auto session receipt')
        record = json.loads(raw)
        validate(record)
        if value is not None and record != value:
            raise BackendError('Auto session receipt readback failed')
        return record


class LinuxAuto(LinuxMesh):
    def support_normal_state(self):
        with connection_operation():
            records = dict(self._awg_records(), **self._tcp_records())
            if len(records) > 64:
                raise BackendError('Support observation limit')
            for ident in records:
                if Path('/sys/class/net', ident).exists():
                    return 'CONNECTED', 'tcp' if ident.startswith('fctcp') else 'awg'
            lines = run('nmcli', '-t', '--escape', 'no', '-f', 'UUID,TYPE,NAME', 'connection', 'show', '--active', timeout=3).splitlines()
            if len(lines) > 256:
                raise BackendError('Support observation limit')
            for line in lines:
                fields = line.split(':', 2)
                if len(fields) == 3 and fields[1] == 'wireguard' and (fields[2].startswith(PREFIX) or fields[2] == 'fc-ru-linux'):
                    return 'CONNECTED', 'awg'
            return 'DISCONNECTED', 'none'

    @serialized_connection
    def resolve_auto_status(self):
        self._auto_setup('up')
        return self.auto_status()

    def check_auto_ip(self):
        import ipaddress
        before = self.auto_status()
        controller = before.get('controller') or {}
        platform = controller.get('platform') or {}
        interface = platform.get('interface', '')
        attempt = platform.get('attempt')
        if (before['state'] != 'CONNECTED' or not re.fullmatch(r'fc(?:mesh0|(?:awg|tcp)[a-f0-9]{8})', interface) or
                type(attempt) is not int or attempt < 1):
            raise BackendError('Auto has no ready system tunnel')
        raw = run('/usr/bin/curl', '--disable', '--noproxy', '*', '--interface', 'if!'+interface,
                  '--fail', '--silent', '--connect-timeout', '3', '--max-time', '8', '--max-filesize', '4096',
                  'https://1.1.1.1/cdn-cgi/trace', timeout=9)
        after = self.auto_status()
        current = (after.get('controller') or {}).get('platform') or {}
        if (after['state'] != 'CONNECTED' or after.get('generation') != before.get('generation') or
                current.get('interface') != interface or current.get('attempt') != attempt):
            raise BackendError('Auto session changed during IP check')
        values = dict(line.split('=', 1) for line in raw.splitlines() if '=' in line)
        try:
            address = str(ipaddress.IPv4Address(values.get('ip', '')))
        except ValueError:
            raise BackendError('Invalid Auto IP check response') from None
        country = values.get('loc', '')
        if not re.fullmatch('[A-Z]{2}', country):
            raise BackendError('Invalid Auto location response')
        return 'IP: '+address+' · '+country

    def auto_available(self):
        return auto_component_available()

    def _auto_setup(self, action, generation=None):
        session = getattr(_operation_local, 'authorization', None)
        if session is None:
            raise BackendError('Auto setup requires the existing authorization owner')
        return session.call('auto', action, 'fcauto0' if action == 'up' else generation, None)

    def auto_status(self):
        with connection_operation():
            endpoint = AUTO_RUN/(str(os.getuid())+'.sock')
            if not endpoint.exists():
                receipt = _auto_receipt()
                return dict(state='FAILED' if receipt and receipt['desired'] else 'DISCONNECTED',
                            desired_connected=bool(receipt and receipt['desired']), generation=receipt['generation'] if receipt else '',
                            reason='SERVICE_UNAVAILABLE' if receipt and receipt['desired'] else '', selected='', requested_profile='', controller=None)
            reply = AutoServiceClient().call('status')
            _auto_receipt(dict(schema=1, generation=reply['generation'], desired=reply['desired_connected']))
            return reply

    @serialized_connection
    def normal_catalog(self):
        if not auto_component_present():
            receipt = _auto_receipt()
            if receipt and receipt['desired']:
                raise BackendError('Restore the Auto component before refreshing normal configuration')
            return None
        client = AutoServiceClient()
        self._auto_setup('up')
        state = client.call('status')
        if state['desired_connected'] or state['state'] != 'DISCONNECTED':
            raise BackendError('Disconnect Auto before refreshing normal configuration')
        return client.call('catalog')

    @serialized_connection
    def start_auto(self, material):
        try:
            client = AutoServiceClient()
            selection = dict(materials=material, preferred='')
            client.protocol.validate_request(dict(schema=1, id=1, action='start', selection=selection))
            if self.mesh_status().get('desired_connected') or any(super(LinuxMesh, self).active(ident) for ident, _ in super(LinuxMesh, self).profiles()):
                raise BackendError('Disconnect the existing VPN before starting Auto')
            self._auto_setup('up')
            previous = client.call('status')
            if previous['state'] != 'DISCONNECTED' or previous['desired_connected']:
                raise BackendError('Auto already owns a connection; inspect its status')
            _auto_receipt(dict(schema=1, generation='', desired=True))
            result = client.call('start', selection=selection)
            _auto_receipt(dict(schema=1, generation=result['generation'], desired=result['desired_connected']))
            return result
        finally:
            material.clear()

    @serialized_connection
    def stop_auto(self, generation):
        if not isinstance(generation, str) or re.fullmatch('[a-f0-9]{32}', generation) is None:
            raise BackendError('Inspect Auto status before stopping an unknown generation')
        try:
            client = AutoServiceClient()
            current = client.call('status')
            if current['generation'] != generation:
                raise StaleConnection('Auto session changed; stale stop rejected')
            client.call('stop', generation=generation)
            deadline = time.monotonic()+40
            while time.monotonic() < deadline:
                state = client.call('status')
                if state['generation'] != generation:
                    raise StaleConnection('Auto session changed during cleanup')
                if state['state'] == 'DISCONNECTED' and not state['desired_connected']:
                    _auto_receipt(dict(schema=1, generation=generation, desired=False))
                    return state
                if state['state'] == 'FAILED':
                    break
                time.sleep(.1)
        except StaleConnection:
            raise
        except BackendError:
            pass
        self._auto_setup('down', generation)
        _auto_receipt(dict(schema=1, generation=generation, desired=False))
        return self.auto_status()

    @serialized_connection
    def connect(self, ident):
        if ident == 'fcauto0':
            raise BackendError('Connect Auto through this computer\'s activated account')
        if auto_component_present() and self.auto_status().get('desired_connected'):
            raise BackendError('Disconnect Auto before switching transport')
        return super().connect(ident)

    @serialized_connection
    def start_mesh(self, material):
        if auto_component_present() and self.auto_status().get('desired_connected'):
            material.clear()
            raise BackendError('Disconnect Auto before switching transport')
        return super().start_mesh(material)


class Windows:
    def __init__(self):
        if not ctypes.windll.shell32.IsUserAnAdmin(): raise BackendError('Administrator rights required')
        script=Path(getattr(sys,'_MEIPASS',Path(__file__).parent))/'verify-wireguard.ps1'
        try:
            answer=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',script.read_text(encoding='utf-8')],capture_output=True,text=True,timeout=30,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        except FileNotFoundError:
            raise BackendError('PowerShell unavailable') from None
        errors={20:'WireGuard not installed',21:'WireGuard signature verification failed'}
        if answer.returncode:
            raise BackendError(errors.get(answer.returncode,'WireGuard verification failed; exit='+str(answer.returncode)))
        self.exe=Path(answer.stdout.strip())
        if not self.exe.is_file(): raise BackendError('WireGuard not installed')
        self.directory=self.exe.parent/'Data'/'Configurations'
    def _state(self,name):
        from ctypes import wintypes as w
        class STATUS(ctypes.Structure):
            _fields_=[(n,w.DWORD) for n in ['type','state','controls','win32','specific','checkpoint','hint']]
        api=ctypes.WinDLL('advapi32',use_last_error=True)
        api.OpenSCManagerW.argtypes=[w.LPCWSTR,w.LPCWSTR,w.DWORD];api.OpenSCManagerW.restype=w.HANDLE
        api.OpenServiceW.argtypes=[w.HANDLE,w.LPCWSTR,w.DWORD];api.OpenServiceW.restype=w.HANDLE
        api.CloseServiceHandle.argtypes=[w.HANDLE]
        api.QueryServiceStatus.argtypes=[w.HANDLE,ctypes.POINTER(STATUS)]
        manager=api.OpenSCManagerW(None,None,1)
        if not manager: raise BackendError('Cannot access Windows services')
        try:
            service=api.OpenServiceW(manager,name,4)
            if not service:
                if ctypes.get_last_error()==1060:return 0
                raise BackendError('Cannot query VPN service')
            try:
                status=STATUS()
                if not api.QueryServiceStatus(service,ctypes.byref(status)): raise BackendError('Cannot query VPN service')
                return status.state
            finally:api.CloseServiceHandle(service)
        finally:api.CloseServiceHandle(manager)
    def profiles(self):
        return [(p.name.removesuffix('.conf.dpapi'),p.name.removesuffix('.conf.dpapi'))
                for p in self.directory.glob(PREFIX+'*.conf.dpapi')]
    def active(self,ident): return self._state('WireGuardTunnel$'+ident)==4
    def connect(self,ident):
        if not re.fullmatch(r'fc-app-[0-9a-f]{8}',ident): raise BackendError('Invalid profile identifier')
        service='WireGuardTunnel$'+ident
        if self._state(service): run('sc.exe','start',service)
        else: run(str(self.exe),'/installtunnelservice',str(self.directory/(ident+'.conf.dpapi')))
        run('sc.exe','config',service,'start=','demand')
    def disconnect(self,ident):run(str(self.exe),'/uninstalltunnelservice',ident)
    def import_profile(self,path):
        data=read_profile(path)
        if not self._state('WireGuardManager'): run(str(self.exe),'/installmanagerservice')
        elif self._state('WireGuardManager')!=4: run('sc.exe','start','WireGuardManager')
        for _ in range(30):
            if self.directory.is_dir(): break
            time.sleep(0.1)
        else: raise BackendError('WireGuard secure store unavailable')
        name=PREFIX+uuid.uuid4().hex[:8]
        plain=self.directory/(name+'.conf')
        # Official manager owns ACL and DPAPI conversion. No app-managed plaintext store.
        try:
            with plain.open('x',encoding='utf-8') as out:out.write(data)
            for _ in range(100):
                if not plain.exists() and (self.directory/(name+'.conf.dpapi')).exists():return name
                time.sleep(0.1)
            raise BackendError('WireGuard secure import timed out')
        finally:plain.unlink(missing_ok=True)


def backend():
    if sys.platform=='win32':return Windows()
    if sys.platform.startswith('linux'):return LinuxAuto()
    raise BackendError('Unsupported operating system')


TCP_UPDATER=Path('/usr/local/lib/family-connect-tcp-updater/broker')

def tcp_updater_available():
    try:
        for p in (TCP_UPDATER.parent,*TCP_UPDATER.parent.parents):
            info=p.lstat()
            if not stat.S_ISDIR(info.st_mode) or info.st_uid!=0 or info.st_mode&0o022:return False
        info=TCP_UPDATER.lstat()
        return stat.S_ISREG(info.st_mode) and info.st_uid==0 and info.st_nlink==1 and not info.st_mode&0o022 and os.access(TCP_UPDATER,os.X_OK)
    except OSError:return False

@serialized_connection
def install_tcp_component():
    if not tcp_updater_available():raise BackendError('TCP system updater is not installed')
    try:
        result=subprocess.run(['pkexec',str(TCP_UPDATER),'install'],stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=900)
    except subprocess.TimeoutExpired as error:raise BackendError('TCP installation timed out; check system state before retrying') from error
    if result.returncode in (126,127):raise AuthorizationError('TCP installation authorization cancelled or unavailable')
    if result.returncode:raise BackendError('TCP installation failed')
    return True
