import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[3]
ARCHIVE = ROOT / 'state-client-build/mesh-perf-3b/successor04b/friends-http-successor.pyz'
EXPECTED = 'f935b8830efdd05e9b6994f945acb6d68a9b0ba19906e31f0f1e7c5cf63a653e'
if hashlib.sha256(ARCHIVE.read_bytes()).hexdigest() != EXPECTED:
    raise RuntimeError('exact operation03 API archive required')
sys.path.insert(0, str(ARCHIVE))

import friends_http
from control.friends import owner_handoff, restricted

for module in (friends_http, owner_handoff, restricted):
    if not module.__file__.startswith(str(ARCHIVE) + '/'):
        raise RuntimeError('module did not load from pinned archive')

spec = importlib.util.spec_from_file_location('failed_connect_fixtures', ROOT / 'tests/test_friends_restricted.py')
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)


class PreparedRotationReproducer(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.service, self.owner, self.now = fixtures.configured(Path(self.directory.name), 1800000000)
        with self.service.access.db() as database:
            owner_handoff.migrate(database)
            self.operation = owner_handoff.prepare(database, 'synthetic-gap', self.owner.reference,
                                                  'a' * 32, 'b' * 32, self.now + 2400, self.now)
        self.first = self.service.fetch(fixtures.proof(self.service, self.owner))
        self.canary = copy.deepcopy(self.first['directory'])
        self.canary['issued_at'] = fixtures.iso(self.now)
        self.canary['seeds'][0]['join_url'] = 'https://telemost.yandex.ru/j/synthetic-canary'
        self.returning = copy.deepcopy(self.first['directory'])
        self.returning['issued_at'] = fixtures.iso(self.now + 10)
        self.returning['seeds'][0]['join_url'] = 'https://telemost.yandex.ru/j/synthetic-return'
        self.service.access.clock = lambda: self.now + 10
        self.service.seed_source = lambda: json.dumps(self.returning).encode()

    def row(self):
        with self.service.access.db() as database:
            return dict(owner_handoff.current(database))

    def fetch_http(self):
        proof = fixtures.proof(self.service, self.owner)
        payload = json.dumps(proof).encode()
        handler = object.__new__(friends_http.Handler)
        handler.connection = Mock()
        handler.path = '/friends/restricted-readiness'
        handler.headers = {'Content-Length': str(len(payload)), 'Content-Type': 'application/json'}
        handler.rfile = io.BytesIO(payload)
        replies = []
        handler.reply = lambda status, value: replies.append((status, value))
        with patch.object(friends_http, 'access', self.service.access), patch.object(restricted, 'from_env', return_value=self.service):
            handler.do_POST()
        self.assertEqual(len(replies), 1)
        return replies[0]

    def test_prepared_rotation_returns_503_without_advancing_floor_then_arm_allows_canary(self):
        before = self.row()
        self.assertEqual(self.fetch_http(), (503, {'error': 'unavailable'}))
        self.assertEqual(self.row(), before)
        with self.service.access.db() as database:
            owner_handoff.arm(database, self.owner.reference, self.operation['operation'],
                              self.canary, self.returning, 'c' * 32, self.now + 10,
                              generation=self.operation['generation'])
        with patch.dict('os.environ', {'INVOCATION_ID': 'c' * 32}):
            status, result = self.fetch_http()
        self.assertEqual(status, 200)
        self.assertEqual(result['directory'], self.canary)
        self.assertTrue(owner_handoff.preserves(owner_handoff.floor(result), owner_handoff.floor(self.first)))

    def test_existing_forward_return_closes_gap_without_canary_or_floor_rollback(self):
        self.assertEqual(self.fetch_http()[0], 503)
        with self.service.access.db() as database:
            owner_handoff.return_only(database, self.owner.reference, self.operation['operation'],
                                      generation=self.operation['generation'])
        status, result = self.fetch_http()
        self.assertEqual(status, 200)
        self.assertEqual(result['directory'], self.returning)
        self.assertTrue(owner_handoff.preserves(owner_handoff.floor(result), owner_handoff.floor(self.first)))
        with self.assertRaises(ValueError):
            with self.service.access.db() as database:
                owner_handoff.arm(database, self.owner.reference, self.operation['operation'],
                                  self.canary, self.returning, 'c' * 32, self.now + 10,
                                  generation=self.operation['generation'])
        self.assertEqual(self.row()['phase'], 'RETURN')


if __name__ == '__main__':
    unittest.main(verbosity=2)
