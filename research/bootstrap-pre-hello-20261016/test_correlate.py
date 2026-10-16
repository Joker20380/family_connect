import unittest
from correlate import correlate


class CompletenessTest(unittest.TestCase):
    def test_capture_completeness_never_proves_no_holder(self):
        startup = {'started_unix_ms': 10000}
        header = {'enabled': True, 'until_ms': 910000}
        footer = {'stopped': True, 'limited': False, 'written': 0}
        for records, expected in [([], 'DISABLED_OR_UNAVAILABLE'),
                                  ([header], 'INCOMPLETE_OUTPUT'),
                                  ([header, dict(footer, written=1)], 'INCOMPLETE_OUTPUT'),
                                  ([header, dict(footer, limited=True)], 'LIMITED_OR_UNKNOWN'),
                                  ([dict(header, until_ms=9999), footer], 'EXPIRED_OR_OUTSIDE_WINDOW'),
                                  ([header, footer], 'COMPLETE_WINDOW')]:
            with self.subTest(expected=expected):
                result = correlate(startup, records)
                self.assertEqual(expected, result['capture_status'])
                self.assertEqual('NOT_PROVEN', result['holder_absence'])
                self.assertEqual('NOT_OBSERVED', result['requester_evidence'])


if __name__ == '__main__':
    unittest.main()
