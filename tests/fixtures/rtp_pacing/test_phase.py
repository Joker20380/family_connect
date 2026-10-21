"""Offline guards for mode/window/session attribution; no ADB or SSH."""

import ast
import copy
import types
import unittest
from pathlib import Path


class PhaseGateTests(unittest.TestCase):
    def setUp(self):
        path = Path(__file__).with_name('measure.py')
        tree = ast.parse(path.read_text())
        function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'select_records')
        namespace = dict(rate=0, time=types.SimpleNamespace(time=lambda:100.0))
        exec(compile(ast.Module(body=[function], type_ignores=[]), str(path), 'exec'), namespace)
        self.select = namespace['select_records']
        self.row = dict(session_tag='owner', observed_epoch=99.0,
                        performance=dict(PacketPacing=dict(RateBytesPerSecond=0), Mux=dict(Profile='LEGACY64', Window=65536)))

    def test_owner_mode_and_window(self):
        self.assertEqual(self.select([self.row]), [self.row])

    def test_other_peer_not_attributed(self):
        other = dict(session_tag='other', performance=dict(Mux=dict(Profile='LEGACY64', Window=65536)))
        self.assertEqual(self.select([other]), [])
        self.assertEqual(self.select([other, self.row]), [self.row])

    def test_wrong_mode_rejected(self):
        self.row['performance']['PacketPacing']['RateBytesPerSecond'] = 500000
        with self.assertRaises(AssertionError):
            self.select([self.row])

    def test_wrong_window_rejected(self):
        self.row['performance']['Mux']['Window'] = 131072
        with self.assertRaises(AssertionError):
            self.select([self.row])

    def test_second_session_rejected(self):
        other = copy.deepcopy(self.row)
        other['session_tag'] = 'new-owner-session'
        with self.assertRaises(AssertionError):
            self.select([self.row, other])

    def test_stale_or_future_snapshot_rejected(self):
        for observed in (90.0, 103.0):
            self.row['observed_epoch'] = observed
            with self.assertRaises(AssertionError):
                self.select([self.row])


if __name__ == '__main__':
    unittest.main()
