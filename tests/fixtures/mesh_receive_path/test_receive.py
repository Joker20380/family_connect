import copy
import unittest

from correlate_receive import receive_evidence


class ReceiveCorrelationTest(unittest.TestCase):
    def record(self,origin='a',session='session',index=4):
        point=dict(i=index,ns=10,stage='fragment_stored',direction='rx',sender=1,message=2,
                   total=3,fragment=0,known=True,seq=597,mask=1)
        return dict(session_tag=session,performance=dict(Trace=dict(origin=origin,receive=dict(
            count=index,overwritten=index-1,points=[point],incident=[copy.deepcopy(point)]))))

    def test_pinned_duplicate_and_overwrite(self):
        record=self.record()
        result=receive_evidence(dict(Android=[record,copy.deepcopy(record)]))
        self.assertEqual(result['coverage'][0]['observed'],1)
        self.assertEqual(result['coverage'][0]['missing'],3)
        self.assertEqual(result['coverage'][0]['prefix_unobserved'],3)
        self.assertEqual(result['coverage'][0]['interior_missing'],0)
        self.assertEqual(len(result['carrier_lifecycles'][0]['events']),1)

    def test_session_and_origin_not_collapsed(self):
        result=receive_evidence(dict(Android=[self.record(),self.record(origin='b'),self.record(session='new')]))
        self.assertEqual(len(result['coverage']),3)
        self.assertEqual(len(result['carrier_lifecycles']),2)

    def test_missing_trace_not_zero(self):
        record=self.record()
        del record['performance']['Trace']['receive']
        result=receive_evidence(dict(Android=[record]))
        self.assertEqual(result['errors'][0]['error'],'missing_receive_trace')
        self.assertEqual(result['coverage'],[])

    def test_known_omitted_sequence_is_go_zero(self):
        record=self.record()
        receive=record['performance']['Trace']['receive']
        for point in receive['points']+receive['incident']:del point['seq']
        result=receive_evidence(dict(Android=[record]))
        self.assertEqual(result['carrier_lifecycles'][0]['sequences'],[0])

    def test_conflicting_point_is_error(self):
        first=self.record();second=copy.deepcopy(first)
        second['performance']['Trace']['receive']['points'][0]['mask']=3
        result=receive_evidence(dict(Android=[first,second]))
        self.assertTrue(result['errors'])


if __name__=='__main__':
    unittest.main()
