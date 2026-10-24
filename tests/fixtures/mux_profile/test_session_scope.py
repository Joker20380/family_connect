import unittest

from .session_scope import select_session


class SessionScopeTests(unittest.TestCase):
    def setUp(self):
        self.scope = dict(session_tag='a' * 64, profile='CREDIT128', window=131072)
        self.owner = dict(session_tag='a' * 64, observed_epoch=100,
                          performance=dict(Mux=dict(Profile='CREDIT128', Window=131072)))
        self.peer = dict(session_tag='b' * 64, observed_epoch=102,
                         performance=dict(Mux=dict(Profile='LEGACY64', Window=65536)))

    def test_other_peer_retained_but_not_attributed(self):
        records = [self.owner, self.peer]
        self.assertEqual(select_session(records, self.scope, 103), [self.owner])
        self.assertEqual(len(records), 2)

    def test_missing_owner_fails_closed(self):
        with self.assertRaisesRegex(AssertionError, 'MISSING'):
            select_session([self.peer], self.scope, 103)

    def test_other_peer_does_not_refresh_owner(self):
        with self.assertRaisesRegex(AssertionError, 'STALE'):
            select_session([self.owner, self.peer], self.scope, 109)

    def test_profile_and_window_must_match(self):
        for key, value in [('Profile', 'LEGACY64'), ('Window', 65536)]:
            with self.subTest(key=key):
                wrong = dict(self.owner, performance=dict(Mux=dict(self.owner['performance']['Mux'], **{key: value})))
                with self.assertRaisesRegex(AssertionError, 'PROFILE_CHANGED'):
                    select_session([wrong], self.scope, 103)

    def test_offline_analysis_uses_same_attribution(self):
        self.assertEqual(select_session([self.owner, self.peer], self.scope), [self.owner])


if __name__ == '__main__':
    unittest.main()
