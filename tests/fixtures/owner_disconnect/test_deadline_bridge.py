"""Actual Python bridge regression with the Java callback's fixed stop states."""
import base64
import importlib.util
import os
from pathlib import Path
import time
import types
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('bootstrap_bridge',ROOT/'tests/fixtures/mobile_bootstrap/test_transport_bridge.py')
bridge=importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)


class DeadlineBridgeTest(unittest.TestCase):
    def setUp(self):
        source=ROOT/'state-client-build'/os.environ.get('FC_DEADLINE_TEST_SOURCE','owner-deadline103-20261022')/'android-source'
        self.module=bridge.load(source,'deadline_bridge')
        self.channel=self.module.Channel.__new__(self.module.Channel)
        self.callbacks=types.SimpleNamespace(cancelled=lambda:True,stopReason=lambda:'TIMEOUT',bindSocket=lambda descriptor:False)
        self.channel.callbacks=self.callbacks

    def test_shared_deadline_is_typed_unavailability(self):
        with self.assertRaises(self.module.TransportUnavailable):
            self.channel._wait(lambda:False,time.monotonic()+20)

    def test_shared_deadline_request_never_sends_or_replays(self):
        calls=[]
        self.channel.link=types.SimpleNamespace(request=lambda *args,**kwargs:calls.append(args))
        self.assertEqual(['UNAVAILABLE',None],self.channel.readiness_request('/friends/restricted-readiness','e30='))
        self.assertEqual([],calls)

    def test_explicit_cancel_remains_non_availability(self):
        self.callbacks.stopReason=lambda:'CANCELLED'
        with self.assertRaises(OSError) as observed:self.channel._wait(lambda:False,-1)
        self.assertNotIsInstance(observed.exception,self.module.TransportUnavailable)

    def test_invalid_stop_reason_is_fail_closed(self):
        self.callbacks.stopReason=lambda:'UNKNOWN'
        with self.assertRaises(ValueError):self.channel._wait(lambda:True,time.monotonic()+20)

    def test_no_network_shared_deadline_releases_lock(self):
        public=base64.b64encode(bytes(64)).decode()
        with patch('socket.socket',return_value=types.SimpleNamespace(fileno=lambda:42,close=lambda:None)):
            self.assertEqual(['UNAVAILABLE',None],self.module.readiness_open('unused','127.0.0.1',1,public,self.callbacks))
        self.assertFalse(self.module._session_lock.locked())

    def test_non_transport_response_errors_stay_errors(self):
        for failure in [ValueError('invalid response'),OSError('Relay refused request'),RuntimeError('unknown')]:
            self.channel.request=lambda *args:(_ for _ in ()).throw(failure)
            with self.assertRaises(type(failure)):self.channel.readiness_request('/friends/restricted-readiness','e30=')


class InheritedBridgeTest(bridge.TransportBridgeTest):
    def setUp(self):
        super().setUp()
        source=ROOT/'state-client-build'/os.environ.get('FC_DEADLINE_TEST_SOURCE','owner-deadline103-20261022')/'android-source'
        self.current=bridge.load(source,'current_candidate')


if __name__=='__main__':unittest.main()
