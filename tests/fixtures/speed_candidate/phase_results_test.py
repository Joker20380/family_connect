import json
import unittest

from phase_results import body_accounting, capture_messages


class BodyAccountingTest(unittest.TestCase):
    def test_partial_parallel_never_becomes_complete_goodput(self):
        requests = [dict(name='bulk-2-'+str(index),valid=False,intended_bytes=2097152,
                        metrics=dict(BODY_BYTES=str(size),CURL_EXIT='18'))
                    for index,size in enumerate((855726,790208))]
        result = body_accounting(requests,[dict(flows=2,completed=0,mbit_s=.578)])
        self.assertEqual(result['received_body_bytes'],1645934)
        self.assertEqual(result['complete_response_bytes'],0)
        self.assertEqual(result['partial_response_bytes'],1645934)
        self.assertIsNone(result['cells'][0]['completed_goodput_mbit_s'])
        self.assertEqual(result['cells'][0]['mbit_s'],.578)
        self.assertEqual(len(result['incomplete_responses']),2)

    def test_complete_single_keeps_observation_but_not_clean_acceptance(self):
        requests = [dict(name='bulk-1-0',valid=True,intended_bytes=4194304,
                         metrics=dict(BODY_BYTES='4194304',CURL_EXIT='0'))]
        result = body_accounting(requests,[dict(flows=1,completed=1,mbit_s=.654)])
        self.assertEqual(result['complete_response_bytes'],4194304)
        self.assertEqual(result['partial_response_bytes'],0)
        self.assertEqual(result['cells'][0]['completed_goodput_mbit_s'],.654)
        self.assertNotIn('clean_acceptance',result)

    def test_bound_journal_continuation_restores_terminal_not_success(self):
        first = dict(_SYSTEMD_INVOCATION_ID='epoch',_STREAM_ID='stream',_PID='7',
                     MESSAGE='{"event":"session_',_LINE_BREAK='line-max')
        second = dict(_SYSTEMD_INVOCATION_ID='epoch',_STREAM_ID='stream',_PID='7',
                      MESSAGE='terminal","diagnostic":{"protocol_errors":3}}')
        messages,errors = capture_messages([dict(kind='journal',raw=json.dumps(row)) for row in (first,second)])
        self.assertEqual(errors,[])
        self.assertEqual(messages[0]['diagnostic']['protocol_errors'],3)
        messages,errors = capture_messages([dict(kind='journal',raw=json.dumps(first))])
        self.assertEqual(messages,[])
        self.assertEqual(errors[0]['error'],'incomplete_journal_continuation')


if __name__ == '__main__':
    unittest.main()
