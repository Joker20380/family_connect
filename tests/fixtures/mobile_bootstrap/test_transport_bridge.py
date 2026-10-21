"""Exercise exact old/new Python boundary with synthetic failures, no production sockets."""
import base64
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
RELATIVE = 'clients/android/app/src/main/python/fc_rns_transport.py'


def load(source, name):
    rns = types.ModuleType('RNS')
    rns.Identity = lambda **options: types.SimpleNamespace(load_public_key=lambda public: None)
    interface = types.ModuleType('RNS.Interfaces.TCPInterface')
    interface.TCPClientInterface = object
    with patch.dict(sys.modules, {'RNS':rns, 'RNS.Interfaces':types.ModuleType('RNS.Interfaces'), 'RNS.Interfaces.TCPInterface':interface}):
        spec = importlib.util.spec_from_file_location(name, source / RELATIVE)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    module.initialize = lambda directory: None
    return module


class TransportBridgeTest(unittest.TestCase):
    def setUp(self):
        self.current = load(ROOT/'state-client-build/mobile-bootstrap-20261020/android-source','candidate')
        self.baseline = load(ROOT/'state-client-build/mux-profile-20261020/android-source','baseline')
        self.callbacks = types.SimpleNamespace(bindSocket=lambda descriptor:True,cancelled=lambda:False)
        self.args = ('unused','127.0.0.1',1,base64.b64encode(bytes(64)).decode(),self.callbacks)

    def refused(self):
        class Socket:
            def fileno(self):return 42
            def settimeout(self, timeout):pass
            def connect(self, target):raise ConnectionRefusedError('synthetic local refusal')
            def close(self):pass
        return Socket()

    def test_actual_old_boundary_raises_and_new_boundary_returns_typed_unavailability(self):
        with patch('socket.socket',side_effect=lambda *args:self.refused()):
            with self.assertRaises(ConnectionRefusedError):self.baseline.Channel(*self.args)
            self.assertEqual(['UNAVAILABLE',None],self.current.readiness_open(*self.args))
        self.assertFalse(self.current._session_lock.locked())
        self.assertFalse(self.baseline._session_lock.locked())

    def test_no_underlay_is_availability_but_cancel_is_not(self):
        self.callbacks.bindSocket=lambda descriptor:False
        with patch('socket.socket',side_effect=lambda *args:self.refused()):
            self.assertEqual(['UNAVAILABLE',None],self.current.readiness_open(*self.args))
            self.callbacks.cancelled=lambda:True
            with self.assertRaisesRegex(OSError,'cancelled'):self.current.readiness_open(*self.args)
        self.assertFalse(self.current._session_lock.locked())

    def test_invalid_bootstrap_busy_and_unknown_failure_do_not_become_availability(self):
        with self.assertRaises(ValueError):self.current.readiness_open('unused','127.0.0.1',1,'invalid',self.callbacks)
        self.current._session_lock.acquire()
        try:
            with self.assertRaises(OSError):self.current.readiness_open(*self.args)
        finally:self.current._session_lock.release()
        for failure in (ValueError('binding'),OSError('Relay refused request'),RuntimeError('unknown')):
            with patch.object(self.current,'Channel',side_effect=failure):
                with self.assertRaises(type(failure)):self.current.readiness_open(*self.args)

    def test_request_timeout_is_typed_and_proof_is_not_replayed(self):
        channel=self.current.Channel.__new__(self.current.Channel)
        calls=[]
        def request(path, body):
            calls.append(path)
            raise self.current.TransportUnavailable('timeout')
        channel.request=request
        self.assertEqual(['UNAVAILABLE',None],channel.readiness_request('/friends/restricted-readiness','fixture'))
        self.assertEqual(['/friends/restricted-readiness'],calls)
        with self.assertRaises(ValueError):channel.readiness_request('/friends/activate','fixture')

    def test_rejected_or_malformed_response_cannot_use_cached_authority(self):
        channel=self.current.Channel.__new__(self.current.Channel)
        for failure in (OSError('Relay refused request'),OSError('Invalid RNS response'),ValueError('signature')):
            channel.request=lambda *args:(_ for _ in ()).throw(failure)
            with self.assertRaises(type(failure)):channel.readiness_request('/friends/restricted-readiness','fixture')

    def test_wait_deadline_and_cancellation_are_distinct(self):
        channel=self.current.Channel.__new__(self.current.Channel)
        channel.callbacks=self.callbacks
        with self.assertRaises(self.current.TransportUnavailable):channel._wait(lambda:False,-1)
        self.callbacks.cancelled=lambda:True
        with self.assertRaisesRegex(OSError,'cancelled'):channel._wait(lambda:False,-1)


if __name__=='__main__':unittest.main()
