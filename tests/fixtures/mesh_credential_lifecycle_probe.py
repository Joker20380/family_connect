"""Offline decision-path reproduction against hash-pinned, read-only source copies.

No credentials, nodes, systemd services, or network connections are used. Validated
metadata is stubbed; these tests do not attest cryptographic or recovery acceptance.
Run directly with --source-dir pointing to the audited deployed renewal modules.
"""

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


PINS = {
    'credential_renewal': 'fb83d851b4ac88b7ad90b97c59f516ee327bc7bbb92a642a031da08bbc50d25c',
    'production_controller': 'b9af8199e137e861f9e68db9e5fc1d601e6fcaa3877994bf9f83366e68d9f0b5',
    'production_transport': 'c3a9775da86e32a4feec6a294578a07a7bc53046f461bb8aee355719dacf45bf',
    'maintenance_policy': '4944dcc16769ccbd8bb46a926c088055743db264036dc704da42a6c75a537070',
    'offline_handoff': '2ff54b0d35b4b8108c5aec944194e93c80f87e53a24e8719cf3109a111e3ffdf',
}
OPERATION = 'offline-lifecycle-probe-20261018'


def epoch(clock):
    return int(datetime.fromisoformat('2026-10-18T' + clock + '+00:00').timestamp())


def metadata(parent='08:57:40'):
    expiry = epoch(parent)
    child = datetime.fromtimestamp(epoch('06:41:35'), timezone.utc)
    return (
        {'grants': [{'expires': expiry, 'revoked': False}]},
        {'expires_at': expiry},
        None,
        SimpleNamespace(next_update_utc=child),
        SimpleNamespace(not_valid_after_utc=child),
    )


class MutationBoundary(Exception):
    pass


class ForbiddenNode:
    def call(self, *args, **kwargs):
        raise AssertionError('Node access forbidden in offline probe')


class Boundary:
    @contextmanager
    def lock(self):
        raise MutationBoundary('Decision reached transaction boundary; no mutation performed')
        yield


class LifecycleProbe(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.now = epoch('03:11:35')
        self.validated = metadata()
        self.validator = SimpleNamespace(validate=lambda *args, **kwargs: self.validated)
        self.controller = ProductionController(
            self.folder.name, {'RU': ForbiddenNode(), 'NL': ForbiddenNode()},
            self.validator, clock=lambda: self.now,
        )
        self.current = {'RU': {'fixture': True}, 'NL': {'fixture': True}}
        self.changed = False
        self.controller.read = lambda operation: ({}, {}, self.current, self.changed)
        self.controller.operation = Boundary()
        network = patch('subprocess.run', side_effect=AssertionError('Process launch forbidden'))
        network.start()
        self.addCleanup(network.stop)

    def scheduled(self, approved=True):
        return self.controller.run(OPERATION, scheduled=True, approved_leaf_crl_schedule=approved)

    def approval(self, state=None):
        return MaintenanceAuthorization(
            OPERATION, renewal.digest(renewal.canonical(self.current if state is None else state)),
            self.now, self.now + 900,
        )

    def assert_blocked(self, result):
        self.assertEqual(result['result'], 'MAINTENANCE_REQUIRED')
        self.assertEqual(result['mutations'], 0)
        self.assertIn('MAINTENANCE_BLOCKED_BY_SESSION_UNCERTAINTY', result['alerts'])
        self.assertEqual(list(Path(self.folder.name).iterdir()), [])

    def test_025634_no_renewal_due(self):
        self.now = epoch('02:56:34')
        result = self.scheduled()
        self.assertEqual(result['result'], 'NOOP')
        self.assertEqual(result['due'], [])
        self.assertEqual(result['headroom']['authority'], 21666)
        self.assertEqual(result['headroom']['leaf'], 13501)

    def test_025740_parent_threshold_exact(self):
        before = renewal.evaluate(self.validated, epoch('02:57:39'))
        after = renewal.evaluate(self.validated, epoch('02:57:40'))
        self.assertEqual(before['due'], [])
        self.assertEqual(after['due'], ['authority', 'grant'])

    def test_031135_parent_renewal_not_authorized_by_leaf_schedule(self):
        self.assert_blocked(self.scheduled())

    def test_051135_children_due_but_parent_gate_still_blocks(self):
        self.now = epoch('05:11:35')
        self.assertEqual(renewal.evaluate(self.validated, self.now)['due'],
                         ['authority', 'crl', 'grant', 'leaf'])
        self.assert_blocked(self.scheduled())

    def test_fresh_parent_allows_approved_leaf_crl_to_transaction_boundary(self):
        self.now = epoch('05:11:35')
        self.validated = metadata(parent='20:57:40')
        with self.assertRaises(MutationBoundary):
            self.scheduled()

    def test_leaf_schedule_requires_existing_approval(self):
        self.now = epoch('05:11:35')
        self.validated = metadata(parent='20:57:40')
        self.assert_blocked(self.scheduled(approved=False))

    def test_pending_revocations_cannot_use_leaf_only_schedule(self):
        self.now = epoch('05:11:35')
        self.validated = metadata(parent='20:57:40')
        self.changed = True
        self.assert_blocked(self.scheduled())

    def test_operator_approval_alone_cannot_replace_offline_root_bundle(self):
        result = self.controller.run(OPERATION, approval=self.approval())
        self.assertEqual(result, {'result': 'OFFLINE_AUTHORITY_RENEWAL_REQUIRED', 'mutations': 0})

    def test_scheduled_operator_outage_forbidden(self):
        with self.assertRaisesRegex(renewal.Rejected, 'SCHEDULED_OUTAGE_FORBIDDEN'):
            self.controller.run(OPERATION, scheduled=True, approval=self.approval())

    def test_stale_operator_approval_rejected(self):
        with self.assertRaisesRegex(renewal.Rejected, 'MAINTENANCE_APPROVAL_BINDING'):
            self.controller.run(OPERATION, approval=self.approval({'different': True}))

    def test_expired_leaf_predecessor_flag_does_not_allow_expired_crl(self):
        start = renewal.utc(epoch('02:41:35'))
        end = renewal.utc(epoch('06:41:35'))
        issuer = SimpleNamespace(subject='fixture', public_key=lambda: None,
                                 not_valid_before_utc=start, not_valid_after_utc=end)
        leaf = SimpleNamespace(not_valid_before_utc=start, not_valid_after_utc=end,
                               verify_directly_issued_by=lambda authority: None)
        crl = SimpleNamespace(issuer='fixture', is_signature_valid=lambda key: True,
                              public_bytes=lambda encoding: b'fixture',
                              last_update_utc=start, next_update_utc=end)
        trust = {'issued_at': epoch('02:41:35'), 'expires_at': epoch('08:57:40')}
        validator = renewal.Validator(b'fixture', lambda *args: (trust, issuer))
        raw = renewal.canonical(dict(schema=1, authority={}, certificate='fixture', crl='fixture', grants=[]))
        with patch.object(renewal.x509, 'load_pem_x509_certificate', return_value=leaf), \
                patch.object(renewal.x509, 'load_pem_x509_crl', return_value=crl):
            for expired_leaf in (False, True):
                expected = 'CRL_EXPIRED_OR_FUTURE' if expired_leaf else 'LEAF_EXPIRED_OR_FUTURE'
                with self.subTest(expired_leaf=expired_leaf), self.assertRaisesRegex(renewal.Rejected, expected):
                    validator.validate(raw, epoch('06:42:05'), expired_leaf_predecessor=expired_leaf)

    def test_recovery_requires_committed_checkpoint(self):
        with self.assertRaisesRegex(renewal.Rejected, 'RECOVERY_CHECKPOINT_UNCONFIRMED'):
            self.controller.recovery_checkpoint()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir', type=Path, required=True)
    args, remaining = parser.parse_known_args()
    source = args.source_dir.resolve()
    for name, expected in PINS.items():
        if hashlib.sha256((source / (name + '.py')).read_bytes()).hexdigest() != expected:
            parser.error('Audited source hash mismatch: ' + name)
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(source))
    import credential_renewal as renewal
    from maintenance_policy import MaintenanceAuthorization
    from production_controller import ProductionController
    unittest.main(argv=[sys.argv[0], *remaining])
