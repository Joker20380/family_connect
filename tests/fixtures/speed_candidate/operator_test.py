"""Compile the exact embedded operator script and test its bounded file writer."""

import ast
import os
from pathlib import Path
import tempfile
import time
import unittest


class OperatorTest(unittest.TestCase):
    def setUp(self):
        path=Path(__file__).with_name('policy.py')
        function=next(node for node in ast.parse(path.read_text()).body if isinstance(node,ast.FunctionDef) and node.name=='main')
        expression=next(node.value for node in function.body if isinstance(node,ast.Assign) and any(isinstance(target,ast.Name) and target.id=='remote' for target in node.targets))
        self.source=eval(compile(ast.Expression(expression),str(path),'eval'),{'config':dict(profile='P0',target='a'*32,binary='b'*64)})

    def test_embedded_script_compiles(self):
        compile(self.source,'<operator-template>','exec')

    def test_terminal_reader_retains_journal_selector(self):
        path=Path(__file__).with_name('after_original.py')
        function=next(node for node in ast.parse(path.read_text()).body if isinstance(node,ast.FunctionDef) and node.name=='main')
        expression=next(node.value for node in function.body if isinstance(node,ast.Assign) and any(isinstance(target,ast.Name) and target.id=='remote' for target in node.targets))
        source=eval(compile(ast.Expression(expression),str(path),'eval'),dict(scope={'gateway_invocation':'a'*32},tags=['b'*64],parser_source=''))
        compile(source,'<terminal-reader>','exec')
        self.assertIn("'_SYSTEMD_INVOCATION_ID='+invocation",source)

    def test_target_fits_existing_32_byte_reader(self):
        function=next(node for node in ast.parse(self.source).body if isinstance(node,ast.FunctionDef) and node.name=='put')
        with tempfile.TemporaryDirectory() as temporary:
            directory=Path(temporary)
            namespace=dict(directory=directory,os=os,time=time,info=directory.stat())
            exec(compile(ast.Module(body=[function],type_ignores=[]),'<bounded-writer>','exec'),namespace)
            namespace['put']('speed-target','a'*32)
            self.assertEqual((directory/'speed-target').read_bytes(),b'a'*32)
            self.assertEqual((directory/'speed-target').stat().st_mode&0o777,0o600)
            namespace['put']('speed-profile','P2')
            self.assertEqual((directory/'speed-profile').read_bytes(),b'P2')
            with self.assertRaises(AssertionError):namespace['put']('oversized','a'*33)
            self.assertFalse((directory/'oversized').exists())

    def test_observer_time_filter_retains_bounds_and_epoch(self):
        path=Path(__file__).with_name('observe.py')
        function=next(node for node in ast.parse(path.read_text()).body if isinstance(node,ast.FunctionDef) and node.name=='main')
        expression=[node.value for node in function.body if isinstance(node,ast.Assign) and any(isinstance(target,ast.Name) and target.id=='remote' for target in node.targets)][-1]
        parser_text=(path.parents[1]/'queue_retry/journal.py').read_text()
        parser_node=next(node for node in ast.parse(parser_text).body if isinstance(node,ast.FunctionDef) and node.name=='reassemble')
        for since in (None,'2026-10-21T13:45:00Z'):
            with self.subTest(since=since):
                namespace=dict(ast=ast,parser_text=parser_text,parser_node=parser_node,readback={'gateway':{'state':{'InvocationID':'a'*32}}},since=since)
                source=eval(compile(ast.Expression(expression),str(path),'eval'),namespace)
                compile(source,'<observer-template>','exec')
                self.assertIn('since='+repr(since),source)
                self.assertIn("state['InvocationID']==invocation",source)
                self.assertIn("'-n','4000'",source)
                self.assertIn('assert len(raw)<32*1024*1024',source)
                self.assertIn('timeout=20',source)
                self.assertIn("command.extend(['--since',since])",source)


if __name__=='__main__':unittest.main()
