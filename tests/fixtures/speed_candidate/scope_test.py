import copy
import unittest
from scope import validate_export


class ScopeTest(unittest.TestCase):
    def setUp(self):
        self.document = dict(ring=dict(version_code=97,app_version='0.1.18-beta97-speed',state='CONNECTED',
            vpn_capture_open=True,restricted_readiness='READY',restricted_session=dict(session_tag='a'*64,
            speed_profile='P0',terminal_reason='NONE',reliable_limits=dict(local_send=8,local_receive=16,
            peer_receive=16,effective_send=8,local_write_completion=False),mux_profile='LEGACY64',mux_window=65536)),
            incident=dict(version_code=96,state='FAILED'))

    def test_historical_incident_is_not_current(self):
        self.assertEqual(validate_export(self.document,'P0')['reliable_limits']['effective_send'],8)

    def test_terminal_and_mixed_window_are_rejected(self):
        for change in ('terminal','window','profile'):
            with self.subTest(change=change):
                document=copy.deepcopy(self.document)
                diagnostic=document['ring']['restricted_session']
                if change=='terminal':diagnostic['terminal_observed_at_ms']=1
                if change=='window':diagnostic['reliable_limits']['peer_receive']=32
                if change=='profile':diagnostic['speed_profile']='P2'
                with self.assertRaises(AssertionError):validate_export(document,'P0')


if __name__=='__main__':unittest.main()
