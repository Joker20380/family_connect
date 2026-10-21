import json
import unittest

from journal import reassemble, performance_lines


class JournalTest(unittest.TestCase):
    def test_interleaved_streams(self):
        def row(stream,text,partial=False):
            return json.dumps(dict(_STREAM_ID=stream,_PID='7',_SYSTEMD_INVOCATION_ID='a',MESSAGE=text,**({'_LINE_BREAK':'line-max'} if partial else {})))
        rows,errors=reassemble([row('a','{"event":"restricted_',True),row('b','other'),row('a','performance_v1"}')])
        self.assertEqual(errors,[])
        self.assertEqual(len(list(performance_lines(rows))),1)
        self.assertEqual(json.loads(rows[-1]['MESSAGE'])['event'],'restricted_performance_v1')

    def test_incomplete_and_oversized(self):
        rows,errors=reassemble([json.dumps(dict(_STREAM_ID='a',_PID='7',_SYSTEMD_INVOCATION_ID='a',MESSAGE='{',_LINE_BREAK='line-max'))])
        self.assertEqual(rows,[])
        self.assertEqual(errors[0]['error'],'incomplete_journal_continuation')
        rows,errors=reassemble([json.dumps(dict(MESSAGE='x'*(1024*1024+1)))])
        self.assertEqual(rows,[])
        self.assertTrue(errors)


if __name__=='__main__':unittest.main()
