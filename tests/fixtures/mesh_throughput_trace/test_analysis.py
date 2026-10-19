import json
from pathlib import Path
import unittest

from analyze import summarize
from correlate import correlate


class AnalysisTest(unittest.TestCase):
    def test_terminal_null_streams_and_local_ack_boundary(self):
        diagnostic = json.loads(Path(__file__).with_name('synthetic-native-snapshot.json').read_text())['packet']['diagnostic']
        performance = diagnostic['restricted_performance_v1']
        performance['Mux'] = dict(Streams=None, Retired=None)
        record = dict(session_tag=diagnostic['session_tag'], performance=performance)
        result = summarize(correlate({'Android': [record]}))
        intervals = result['nodes']['Android']['intervals']
        self.assertGreaterEqual(intervals['ack_created_to_local_write_ns']['max_ms'], 6)
        self.assertEqual(result['nodes']['Android']['sample_interval_seconds'], 0)
        self.assertIsNone(result['nodes']['Android']['delta']['ReceiveReadyWaitNS'])
        self.assertFalse(result['errors'])


if __name__ == '__main__':
    unittest.main()
