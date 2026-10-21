import copy
import json
import unittest
from interaction_prepare import WORK
from interaction_proof import validate


class CompletionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (WORK/'A1/server-peer.jsonl').exists():
            raise unittest.SkipTest('private captured A1 evidence is not present')

    def setUp(self):
        self.rows=[[json.loads(line) for line in (WORK/'A1'/name).read_text().splitlines()] for name in ['peer.jsonl','server-peer.jsonl']]
        self.proofs=[next(row for row in rows if row.get('event')=='p_drained') for rows in self.rows]
        self.requests=[row for row in self.rows[0] if row.get('event')=='host_request']

    def test_known_delivered_body_and_ack_not_controller_acceptance(self):
        validate(self.proofs,self.requests,65536)

    def test_terminal_empty_depth_is_not_success(self):
        proofs=copy.deepcopy(self.proofs)
        proofs[1]['reliability']['Terminal']='recovery_exhausted'
        with self.assertRaises(AssertionError):validate(proofs,self.requests,65536)

    def test_missing_ack_or_body_hash_or_tail(self):
        for name in ['ack','hash','tail','credit']:
            proofs,requests=copy.deepcopy(self.proofs),copy.deepcopy(self.requests)
            if name=='ack':proofs[0]['reliability']['Performance']['ReleasedBlocks']-=1
            if name=='hash':requests[0]['sha256']='0'*64
            if name=='tail':proofs[1]['packing']['QueueBytes']=1
            if name=='credit':proofs[1]['mux']['Window']=131072
            with self.assertRaises(AssertionError):validate(proofs,requests,65536)


if __name__=='__main__':unittest.main()
