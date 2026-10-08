import ast
from pathlib import Path
import unittest

from preparation import candidate, PreparationAborted


class PreparationTests(unittest.TestCase):
    def value(self):
        return dict(healthy=True, stats=dict(packet=dict(diagnostic=dict(
            session_tag='scope', reliable_terminal=False, observed_at_ms=3,
            lifecycle=dict(trace=[dict(session_tag='scope', sequence=1, timestamp_ms=2,
                                      delivery=dict(flow=dict(send_next=19, send_base=18, pending=1)))])))))

    def test_candidate_not_quiescence_claim(self):
        value = self.value()
        _, flow = candidate(lambda _:value, 'scope', lambda _:self.fail('unexpected export'))
        self.assertEqual(flow['send_next'],19)
        self.assertEqual(flow['pending'],1)

    def test_wrong_session_and_missing_field(self):
        exports=[]
        with self.assertRaises(PreparationAborted):candidate(lambda _:self.value(), 'other', exports.append)
        value=self.value();del value['stats']['packet']['diagnostic']['lifecycle']['trace'][0]['delivery']['flow']['pending']
        with self.assertRaises(KeyError):candidate(lambda _:value, 'scope', exports.append)
        self.assertEqual(len(exports),2)

    def test_primary_preserved(self):
        primary=ConnectionError('fixture')
        def lost(_):raise primary
        def failed_export(_):raise OSError('fixture')
        with self.assertRaises(ConnectionError) as caught:candidate(lost,'scope',failed_export)
        self.assertIs(caught.exception,primary)

    def test_no_generic_fallback_or_selection_loop(self):
        root=Path(__file__).parent
        source=(root/'controller.py').read_text()
        ast.parse(source)
        self.assertNotIn("{'operation':'arm'}",source)
        self.assertNotIn('stable quiescent',source)
        self.assertEqual(source.count("operation='targeted_arm'"),1)
        self.assertLess(source.index("operation='prearm',key=key"),source.index("operation='targeted_arm'"))
        helper=(root/'OwnerSelectedRetryTest.java').read_text()
        self.assertNotIn('fault("arm")',helper)
        self.assertNotIn('operation.equals("arm")',helper)

    def test_actual_controller_prepare_block_success_and_rejection(self):
        tree=ast.parse((Path(__file__).parent/'controller.py').read_text())
        body=next(node for node in tree.body if isinstance(node,ast.Try)).body
        start=next(index for index,node in enumerate(body) if isinstance(node,ast.Assign) and any(isinstance(target,ast.Name) and target.id=='key' for target in node.targets))
        end=next(index for index,node in enumerate(body[start:],start) if isinstance(node,ast.Assert) and "'traffic'" in ast.unparse(node))
        code=compile(ast.Module(body=body[start:end+1],type_ignores=[]),'<controller preparation>','exec')
        for accepted in (True,False):
            calls=[]
            receipts={}
            def remote(request):
                calls.append(('receiver',request['operation']))
                key=dict(request['key'],generation='b'*32)
                return dict(state='ARMED',key=key)
            def phone(request):
                if request['operation']=='traffic':
                    calls.append(('sender','traffic'))
                    return dict(started=True)
                operation=request['request']['operation']
                calls.append(('sender',operation))
                key=request['request']['key']
                if operation=='prearm':return dict(state='ARMED',key=key)
                if not accepted:return dict(result='PREPARATION_ABORTED',reason='HEAD_NOT_FREE')
                return dict(result='ARMED',key=key,fault=dict(target='logical_data_attempt0',sequence=19,generation='c'*32,armed=True,consumed=False,count=0))
            namespace=dict(session='a'*64,flow=dict(send_next=19),remote_call=remote,phone_call=phone,save=lambda name,value:receipts.update({name:value}),PreparationAborted=PreparationAborted)
            if accepted:exec(code,namespace)
            else:
                with self.assertRaisesRegex(PreparationAborted,'HEAD_NOT_FREE'):exec(code,namespace)
            self.assertEqual(calls[:3],[('receiver','prearm'),('sender','prearm'),('sender','targeted_arm')])
            self.assertEqual(len(calls),4 if accepted else 3)
            self.assertIn('sender-targeted-arm.json',receipts)


if __name__=='__main__':unittest.main()
