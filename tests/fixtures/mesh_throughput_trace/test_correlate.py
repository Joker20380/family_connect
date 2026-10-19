import base64
import hashlib
import json
from pathlib import Path
import unittest

from correlate import android_export, correlate, reconstruct


def chunks(record, capture=1, stream='one'):
    raw = json.dumps(record).encode()
    parts = [raw[index:index + 1800] for index in range(0, len(raw), 1800)]
    return [json.dumps(dict(_STREAM_ID=stream, MESSAGE=json.dumps(dict(
        event='restricted_performance_chunk_v1', origin=record['performance']['Trace']['origin'],
        session_tag=record['session_tag'], capture=capture, parts=len(parts), part=index,
        bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(), data=base64.b64encode(part).decode()))))
        for index, part in enumerate(parts)]


class CorrelationTest(unittest.TestCase):
    def setUp(self):
        native = json.loads(Path(__file__).with_name('synthetic-native-snapshot.json').read_text())
        diagnostic = native['packet']['diagnostic']
        self.record = dict(event='restricted_performance_v1', session_tag=diagnostic['session_tag'],
                           performance=diagnostic['restricted_performance_v1'])

    def test_split_and_stream_binding(self):
        first, second = chunks(self.record), chunks(self.record, stream='other')
        records, errors = reconstruct([part for pair in zip(first, second) for part in pair])
        self.assertEqual(errors, [])
        self.assertEqual(records, [self.record, self.record])

    def test_incomplete_is_not_loss(self):
        records, errors = reconstruct(chunks(self.record)[:-1])
        self.assertEqual(records, [])
        self.assertEqual(errors[0]['error'], 'incomplete')

    def test_invalid_json_kept(self):
        records, errors = reconstruct(['broken', *chunks(self.record)])
        self.assertEqual(len(errors), 1)
        self.assertEqual(records, [self.record])

    def test_conflicting_chunk_kept(self):
        lines = chunks(self.record)
        conflict = json.loads(lines[0])
        inner = json.loads(conflict['MESSAGE'])
        inner['data'] = base64.b64encode(b'bad').decode()
        conflict['MESSAGE'] = json.dumps(inner)
        records, errors = reconstruct([lines[0], json.dumps(conflict), *lines[1:]])
        self.assertEqual(errors[0]['error'], 'chunk content conflict')
        self.assertEqual(len(records), 1)

    def test_checksum_kept(self):
        lines = chunks(self.record)
        modified = []
        for line in lines:
            outer = json.loads(line)
            inner = json.loads(outer['MESSAGE'])
            inner['sha256'] = '0' * 64
            outer['MESSAGE'] = json.dumps(inner)
            modified.append(json.dumps(outer))
        records, errors = reconstruct(modified)
        self.assertEqual(records, [])
        self.assertEqual(errors[0]['error'], 'chunk checksum mismatch')

    def test_duplicate_snapshots_not_duplicate_consume(self):
        result = correlate({'Android': [self.record, self.record]})
        self.assertFalse(result['errors'])
        logical = [value for value in result['logical_data'] if value['sequence'] == 2]
        self.assertEqual(len(logical), 1)
        self.assertEqual(logical[0]['consumes'], 1)
        self.assertEqual(logical[0]['receive_results'], ['new', 'duplicate'])
        self.assertFalse(logical[0]['first_submission_observed'])

    def test_android_export_keeps_perf(self):
        session = dict(session_tag=self.record['session_tag'], restricted_performance_v1=self.record['performance'])
        records = android_export(dict(ring=dict(restricted_session=session)))
        self.assertEqual(records, [self.record])

    def test_ack_matches_are_not_unique_tokens(self):
        remote = json.loads(json.dumps(self.record))
        points = remote['performance']['Trace']['points']
        generated = next(point for point in points if point['kind'] == 'ack_created' and point.get('base') == 3)
        points[:] = [dict(i=1, ns=1, seq=0, kind='ack_input', wire=generated['wire'], base=3, result='accepted')]
        remote['performance']['Trace'].update(count=1, overwritten=0)
        result = correlate({'NL': [remote], 'Android': [self.record]})
        match = next(value for value in result['ack_correspondence'] if value['base'] == 3)
        self.assertFalse(match['unique_wire_identifier'])
        self.assertGreaterEqual(len(match['possible_local_generations']), 2)

    def test_ring_gap_is_explicit(self):
        trace = self.record['performance']['Trace']
        trace['points'] = trace['points'][-3:]
        trace['overwritten'] = trace['count'] - 3
        result = correlate({'Android': [self.record]})
        self.assertGreater(result['completeness'][0]['prefix_unobserved'], 0)
        self.assertEqual(result['completeness'][0]['interior_missing'], 0)

    def test_ack_local_write_survives_saved_correlation(self):
        result = correlate({'Android': [self.record]})
        events = [value['point'] for value in result['ack_events']]
        written = next(point for point in events if point['kind'] == 'ack_carrier_written' and point['reason'] == 'duplicate')
        created = next(point for point in events if point['kind'] == 'ack_created' and point.get('token') == written['token'])
        self.assertGreaterEqual(written['ns'] - created['ns'], 6_000_000)


if __name__ == '__main__':
    unittest.main()
