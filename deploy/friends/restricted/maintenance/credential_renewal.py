"""Coordinated credential renewal; LocalNode is a fixture adapter."""

import base64
import contextlib
import datetime
import fcntl
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import secrets
import stat
import time

from cryptography import x509
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

DAY = 86400
HOUR = 3600
MAX_BYTES = 1048576
HANDOFF_DOMAIN = b'family-connect-renewal-offline-handoff-v1\0'
VALIDITY = {'authority': DAY, 'leaf': 4 * HOUR, 'grant': DAY, 'crl': 4 * HOUR}
THRESHOLD = {'authority': 6 * HOUR, 'leaf': 90 * 60, 'grant': 6 * HOUR, 'crl': 90 * 60}
ALERTS = {kind: (120 * 60, 90 * 60, 60 * 60, 30 * 60) for kind in VALIDITY}
AUTHORITY_MAINTENANCE_LEAD = 14 * DAY
TERMINAL = frozenset(('COMMITTED', 'ROLLED_BACK', 'ABORTED'))


class Rejected(Exception):
    def __init__(self, cause):
        super().__init__(cause if type(cause) is str and re.fullmatch('[A-Z][A-Z0-9_]{0,63}', cause) else 'UNKNOWN')


def require(condition, cause):
    if not condition:
        raise Rejected(cause)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def parse(raw):
    require(len(raw) <= MAX_BYTES, 'INPUT_TOO_LARGE')
    def pairs(items):
        result = {}
        for name, value in items:
            require(name not in result, 'DUPLICATE_FIELD')
            result[name] = value
        return result
    try:
        value = json.loads(raw, object_pairs_hook=pairs)
        require(canonical(value) == raw, 'NON_CANONICAL_INPUT')
        return value
    except (ValueError, TypeError):
        raise Rejected('MALFORMED_INPUT') from None


def utc(epoch):
    return datetime.datetime.fromtimestamp(epoch, datetime.timezone.utc)


def spki(key):
    return key.public_bytes(Encoding.DER, PublicFormat.SubjectPublicKeyInfo)


def private_directory(path):
    info = path.lstat()
    require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.geteuid()
            and stat.S_IMODE(info.st_mode) == 0o700, 'DIRECTORY_PERMISSIONS')


def read_private(path):
    private_directory(path.parent)
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as stream:
        info = os.fstat(stream.fileno())
        require(stat.S_ISREG(info.st_mode) and info.st_uid == os.geteuid()
                and stat.S_IMODE(info.st_mode) == 0o600 and info.st_nlink == 1, 'FILE_PERMISSIONS')
        raw = stream.read(MAX_BYTES + 1)
        require(len(raw) <= MAX_BYTES, 'INPUT_TOO_LARGE')
        return raw


def atomic(path, raw):
    private_directory(path.parent)
    require(len(raw) <= MAX_BYTES, 'INPUT_TOO_LARGE')
    if path.exists() or path.is_symlink():
        read_private(path)
    temporary = path.parent / ('.pending-' + secrets.token_hex(16))
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        with os.fdopen(descriptor, 'wb') as output:
            output.write(raw)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        temporary.unlink(missing_ok=True)


class Validator:
    def __init__(self, anchor, delegation_parser, *, all_activated=False):
        self.anchor = anchor
        self.delegation_parser = delegation_parser
        self.all_activated = all_activated
        self.authority_validity = 90 * DAY if all_activated else VALIDITY['authority']

    def validate(self, raw, now, *, expired_leaf_predecessor=False):
        try:
            value = parse(raw)
            require(set(value) == {'schema', 'authority', 'crl', 'certificate', 'grants'}, 'SNAPSHOT_SCHEMA')
            require(value['schema'] == 1, 'SNAPSHOT_SCHEMA')
            trust, issuer = self.delegation_parser(value['authority'], self.anchor, now)
            require(0 < trust['expires_at'] - trust['issued_at'] <= self.authority_validity + 5, 'AUTHORITY_VALIDITY')
            require(0 < (issuer.not_valid_after_utc - issuer.not_valid_before_utc).total_seconds()
                    <= self.authority_validity + 5, 'AUTHORITY_VALIDITY')
            crl = x509.load_pem_x509_crl(value['crl'].encode())
            leaf = x509.load_pem_x509_certificate(value['certificate'].encode())
            require(crl.public_bytes(Encoding.PEM).decode() == value['crl'], 'CRL_ENCODING')
            require(crl.is_signature_valid(issuer.public_key()) and crl.issuer == issuer.subject, 'CRL_SIGNATURE')
            leaf.verify_directly_issued_by(issuer)
            require(leaf.not_valid_before_utc <= utc(now)
                    and (utc(now) < leaf.not_valid_after_utc or expired_leaf_predecessor), 'LEAF_EXPIRED_OR_FUTURE')
            require(0 < (leaf.not_valid_after_utc - leaf.not_valid_before_utc).total_seconds() <= VALIDITY['leaf'] + 5, 'LEAF_VALIDITY')
            require(crl.last_update_utc <= utc(now)
                    and (utc(now) < crl.next_update_utc or (self.all_activated and expired_leaf_predecessor)),
                    'CRL_EXPIRED_OR_FUTURE')
            require(0 < (crl.next_update_utc - crl.last_update_utc).total_seconds() <= VALIDITY['crl'], 'CRL_VALIDITY')
            require(max(leaf.not_valid_after_utc, crl.next_update_utc) <= issuer.not_valid_after_utc, 'AUTHORITY_HEADROOM_INSUFFICIENT')
            require(leaf.not_valid_after_utc.timestamp() <= trust['expires_at'], 'AUTHORITY_HEADROOM_INSUFFICIENT')
            require(leaf.extensions.get_extension_for_class(x509.AuthorityKeyIdentifier).value.key_identifier
                    == issuer.extensions.get_extension_for_class(x509.SubjectKeyIdentifier).value.digest, 'AKI_MISMATCH')
            sequence = crl.extensions.get_extension_for_class(x509.CRLNumber).value.crl_number
            require(type(sequence) is int and 0 < sequence < 2**53, 'CRL_SEQUENCE')
            grants = value['grants']
            require(type(grants) is list and (self.all_activated or bool(grants)) and len(grants) <= 256, 'GRANT_SCHEMA')
            require(len({row['device'] for row in grants}) == len(grants), 'DUPLICATE_GRANT')
            for row in grants:
                require(type(row['expires']) is int and type(row['revision']) is int
                        and row['revision'] >= trust['minimum_revision'] and row['family'] == trust['family'], 'GRANT_BINDING')
                if not row['revoked'] and not self.all_activated:
                    require(now < row['expires'] <= min(now + VALIDITY['grant'], trust['expires_at']), 'GRANT_VALIDITY')
            return value, trust, issuer, crl, leaf
        except Rejected:
            raise
        except Exception:
            raise Rejected('SNAPSHOT_VALIDATION_FAILED') from None

    def transition(self, previous, candidate, now, revoke=False, *, expired_leaf_predecessor=False):
        old, old_trust, old_issuer, old_crl, old_leaf = self.validate(previous, now,
            expired_leaf_predecessor=expired_leaf_predecessor)
        new, new_trust, new_issuer, new_crl, new_leaf = self.validate(candidate, now)
        require(hmac.compare_digest(spki(old_issuer.public_key()), spki(new_issuer.public_key())), 'ISSUER_KEY_MISMATCH')
        require(old_issuer.subject == new_issuer.subject, 'ISSUER_BINDING')
        require(hmac.compare_digest(spki(old_leaf.public_key()), spki(new_leaf.public_key())), 'GATEWAY_KEY_MISMATCH')
        require(old_leaf.subject == new_leaf.subject and tuple(old_leaf.extensions) == tuple(new_leaf.extensions), 'GATEWAY_BINDING')
        for name in ['family', 'gateway', 'minimum_revision']:
            require(new_trust[name] == old_trust[name], 'POLICY_CHANGED')
        require(new_trust['sequence'] >= old_trust['sequence'], 'AUTHORITY_ROLLBACK')
        require(new_trust['expires_at'] >= old_trust['expires_at'], 'AUTHORITY_EXPIRY_ROLLBACK')
        require(new_leaf.not_valid_after_utc >= old_leaf.not_valid_after_utc, 'LEAF_EXPIRY_ROLLBACK')
        require(new_crl.next_update_utc >= old_crl.next_update_utc, 'CRL_EXPIRY_ROLLBACK')
        old_number = old_crl.extensions.get_extension_for_class(x509.CRLNumber).value.crl_number
        new_number = new_crl.extensions.get_extension_for_class(x509.CRLNumber).value.crl_number
        crl_changed = old['crl'] != new['crl']
        require(new_number == old_number + int(crl_changed), 'CRL_SEQUENCE')
        def revoked_entries(crl):
            return {entry.serial_number: (entry.revocation_date_utc, tuple(entry.extensions)) for entry in crl}
        old_revocations, new_revocations = revoked_entries(old_crl), revoked_entries(new_crl)
        require(all(new_revocations.get(serial) == value for serial, value in old_revocations.items()), 'REVOCATION_SET_LOSS')
        require(revoke or old_revocations == new_revocations, 'REVOCATION_SET_CHANGED')
        require({row['device'] for row in old['grants']} == {row['device'] for row in new['grants']}, 'GRANT_IDENTITY_CHANGED')
        new_grants = {row['device']: row for row in new['grants']}
        for row in old['grants']:
            successor = new_grants[row['device']]
            require({name: value for name, value in row.items() if name not in ('revision', 'expires')}
                    == {name: value for name, value in successor.items() if name not in ('revision', 'expires')}, 'GRANT_SCOPE_CHANGED')
            changed = row['expires'] != successor['expires']
            require(successor['revision'] == row['revision'] + int(changed), 'GRANT_REVISION')
            require(successor['expires'] >= row['expires'], 'GRANT_EXPIRY_ROLLBACK')
        return new

    def handoff(self, raw, previous, operation_id, now):
        try:
            bundle = parse(raw)
            require(set(bundle) == {'payload', 'signature'}, 'HANDOFF_SCHEMA')
            payload = base64.b64decode(bundle['payload'], validate=True)
            signature = base64.b64decode(bundle['signature'], validate=True)
            Ed25519PublicKey.from_public_bytes(self.anchor).verify(signature, HANDOFF_DOMAIN + payload)
            request = parse(payload)
            require(set(request) == {'schema', 'operation_id', 'previous_sha256', 'authority', 'expires_at'}, 'HANDOFF_SCHEMA')
            require(request['schema'] == 1 and request['operation_id'] == operation_id
                    and request['previous_sha256'] == digest(previous) and now < request['expires_at'] <= now + DAY, 'HANDOFF_BINDING_OR_EXPIRY')
            old = self.validate(previous, now)
            trust, issuer = self.delegation_parser(request['authority'], self.anchor, now)
            require(trust['sequence'] == old[1]['sequence'] + 1, 'HANDOFF_REPLAY')
            require(spki(issuer.public_key()) == spki(old[2].public_key()), 'ISSUER_KEY_MISMATCH')
            require(all(trust[name] == old[1][name] for name in ('family', 'gateway', 'minimum_revision')), 'HANDOFF_BINDING')
            require(0 < trust['expires_at'] - trust['issued_at'] <= self.authority_validity, 'AUTHORITY_VALIDITY')
            return request['authority']
        except Rejected:
            raise
        except Exception:
            raise Rejected('HANDOFF_SIGNATURE_OR_SCHEMA') from None


def evaluate(validated, now, revocations_changed=False, *, all_activated=False):
    value, trust, issuer, crl, leaf = validated
    expiries = {'authority': trust['expires_at'], 'crl': int(crl.next_update_utc.timestamp()),
                'leaf': int(leaf.not_valid_after_utc.timestamp())}
    if not all_activated:
        expiries['grant'] = min(row['expires'] for row in value['grants'] if not row['revoked'])
    alerts = []
    due = []
    for kind, expiry in expiries.items():
        remaining = expiry - now
        alerts.extend(kind.upper() + '_T_MINUS_' + str(threshold // 60) + 'M'
                      for threshold in ALERTS[kind] if remaining <= threshold)
        if remaining <= THRESHOLD[kind]:
            due.append(kind)
    if revocations_changed and 'crl' not in due:
        due.append('crl')
    if 'authority' in due:
        alerts.append('OFFLINE_AUTHORITY_RENEWAL_REQUIRED')
    if all_activated and expiries['authority'] - now <= AUTHORITY_MAINTENANCE_LEAD:
        alerts.append('OFFLINE_AUTHORITY_MAINTENANCE_DUE')
    return {'result': 'RENEWAL_REQUIRED' if due else 'NOOP', 'due': sorted(due), 'alerts': alerts,
            'headroom': {kind: expiry - now for kind, expiry in expiries.items()}}


class LocalNode:
    def __init__(self, root, validator, clock, fault=lambda stage: None):
        self.root, self.validator, self.clock, self.fault = Path(root), validator, clock, fault
        private_directory(self.root)

    def current(self):
        return read_private(self.root / 'current.json')

    def quiesce(self):
        with self.decision_lock(exclusive=True):
            atomic(self.root / 'reader.json', canonical({'active': False}))
        self.fault('quiesce')

    @contextlib.contextmanager
    def decision_lock(self, exclusive=False):
        descriptor = os.open(self.root / 'decision.lock', os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        try:
            info = os.fstat(descriptor)
            require(stat.S_ISREG(info.st_mode) and stat.S_IMODE(info.st_mode) == 0o600
                    and info.st_uid == os.geteuid() and info.st_nlink == 1, 'LOCK_PERMISSIONS')
            deadline = time.monotonic() + 1
            while True:
                try:
                    fcntl.flock(descriptor, (fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH) | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    require(time.monotonic() < deadline, 'READER_QUIESCE_TIMEOUT')
                    time.sleep(0.01)
            yield
        finally:
            os.close(descriptor)

    def security_read(self):
        with self.decision_lock():
            require(not self.stopped(), 'MAINTENANCE_FAIL_CLOSED')
            return self.validator.validate(self.current(), self.clock())

    def stopped(self):
        return parse(read_private(self.root / 'reader.json')) == {'active': False}

    def resume(self):
        self.validator.validate(self.current(), self.clock())
        self.fault('resume')
        atomic(self.root / 'reader.json', canonical({'active': True}))

    def stage(self, raw):
        require(self.stopped(), 'READER_NOT_QUIESCED')
        self.validator.validate(raw, self.clock())
        self.fault('stage')
        atomic(self.root / 'staged.json', raw)
        require(read_private(self.root / 'staged.json') == raw, 'STAGE_READBACK')

    def promote(self, raw):
        require(self.stopped(), 'READER_NOT_QUIESCED')
        require(read_private(self.root / 'staged.json') == raw, 'STAGE_HASH_MISMATCH')
        self.validator.validate(raw, self.clock())
        self.fault('promote')
        atomic(self.root / 'current.json', raw)

    def rollback(self, previous):
        require(self.stopped(), 'READER_NOT_QUIESCED')
        self.validator.validate(previous, self.clock())
        self.fault('rollback')
        atomic(self.root / 'current.json', previous)

    def cleanup(self):
        self.fault('cleanup')
        (self.root / 'staged.json').unlink(missing_ok=True)


class Controller:
    def __init__(self, root, nodes, validator, clock, fault=lambda stage: None):
        self.root, self.nodes, self.validator, self.clock, self.fault = Path(root), nodes, validator, clock, fault
        private_directory(self.root)
        require(set(nodes) == {'RU', 'NL'}, 'NODE_SET')

    @contextlib.contextmanager
    def lock(self):
        descriptor = os.open(self.root / 'lock', os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        try:
            info = os.fstat(descriptor)
            require(stat.S_ISREG(info.st_mode) and stat.S_IMODE(info.st_mode) == 0o600
                    and info.st_uid == os.geteuid() and info.st_nlink == 1, 'LOCK_PERMISSIONS')
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise Rejected('OPERATION_BUSY') from None
            yield
        finally:
            os.close(descriptor)

    def marker(self, record, state):
        record['state'] = state
        atomic(self.root / 'transaction.json', canonical(record))
        self.fault(state)

    def receipt(self, record):
        safe = {name: record[name] for name in ['operation_id', 'state', 'first_cause', 'previous_sha256', 'candidate_sha256']}
        safe.update(schema=1, timestamp=self.clock(), remote_alert_delivery='UNAVAILABLE')
        try:
            self.fault('receipt')
            atomic(self.root / 'health.json', canonical(safe))
        except OSError:
            return False
        return True

    def reconcile_failure(self, record):
        for node in self.nodes.values():
            node.quiesce()
        require(all(node.stopped() for node in self.nodes.values()), 'MAINTENANCE_UNCERTAIN')
        previous = read_private(self.root / 'previous.json')
        require(digest(previous) == record['previous_sha256'], 'BACKUP_HASH_MISMATCH')
        for node in self.nodes.values():
            node.rollback(previous)
        require(all(node.current() == previous for node in self.nodes.values()), 'ROLLBACK_READBACK')
        self.marker(record, 'ROLLED_BACK')
        for node in self.nodes.values():
            node.resume()
            node.cleanup()

    def recover(self, record):
        require(record['state'] not in TERMINAL, 'RECOVERY_STATE')
        record['first_cause'] = record['first_cause'] or 'CONTROLLER_INTERRUPTED'
        self.marker(record, 'RECOVERY_REQUIRED')
        try:
            if record.get('commit_decided'):
                candidate = read_private(self.root / 'candidate.json')
                require(digest(candidate) == record['candidate_sha256'], 'CANDIDATE_HASH_MISMATCH')
                self.validator.validate(candidate, self.clock())
                for node in self.nodes.values():
                    node.quiesce()
                for node in self.nodes.values():
                    node.stage(candidate)
                    node.promote(candidate)
                require(all(node.current() == candidate for node in self.nodes.values()), 'READBACK_MISMATCH')
                for node in self.nodes.values():
                    node.resume()
                    node.cleanup()
                self.marker(record, 'COMMITTED')
            else:
                self.reconcile_failure(record)
        except Exception:
            for node in self.nodes.values():
                node.quiesce()
            self.marker(record, 'RECOVERY_REQUIRED')
            self.receipt(record)
            raise Rejected('RECOVERY_REQUIRED') from None
        self.receipt(record)
        return {'result': record['state'], 'operation_id': record['operation_id']}

    def run(self, operation_id, prepare, revocations_changed=False):
        require(type(operation_id) is str and re.fullmatch('[a-z0-9-]{16,96}', operation_id), 'OPERATION_ID')
        with self.lock():
            marker_path = self.root / 'transaction.json'
            if marker_path.exists():
                record = parse(read_private(marker_path))
                if record['state'] not in TERMINAL:
                    return self.recover(record)
                if record['operation_id'] == operation_id:
                    expected = record['candidate_sha256'] if record['state'] == 'COMMITTED' else record['previous_sha256']
                    require(all(digest(node.current()) == expected for node in self.nodes.values()), 'IDEMPOTENT_READBACK_MISMATCH')
                    for node in self.nodes.values():
                        self.validator.validate(node.current(), self.clock())
                    return {'result': record['state'], 'idempotent': True}
            previous = self.nodes['RU'].current()
            require(self.nodes['NL'].current() == previous, 'RU_NL_MISMATCH')
            decision = evaluate(self.validator.validate(previous, self.clock()), self.clock(), revocations_changed)
            if decision['result'] == 'NOOP':
                return decision
            candidate = prepare(previous, decision)
            self.validator.transition(previous, candidate, self.clock(), revocations_changed)
            record = dict(operation_id=operation_id, state='PREPARED', first_cause=None,
                          previous_sha256=digest(previous), candidate_sha256=digest(candidate))
            atomic(self.root / 'previous.json', previous)
            atomic(self.root / 'candidate.json', candidate)
            self.marker(record, 'PREPARED')
            try:
                for node in self.nodes.values():
                    node.quiesce()
                require(all(node.stopped() for node in self.nodes.values()), 'MAINTENANCE_UNCERTAIN')
                require(all(node.current() == previous for node in self.nodes.values()), 'STALE_BASE')
                self.marker(record, 'QUIESCED')
                for role, node in self.nodes.items():
                    node.stage(candidate)
                    self.marker(record, role + '_STAGED')
                self.marker(record, 'BOTH_VALIDATED')
                for role, node in self.nodes.items():
                    node.promote(candidate)
                    self.marker(record, role + '_PROMOTED')
                require(all(node.current() == candidate for node in self.nodes.values()), 'READBACK_MISMATCH')
                self.marker(record, 'READBACK_VERIFIED')
                record['commit_decided'] = True
                self.marker(record, 'COMMIT_DECIDED')
                for node in self.nodes.values():
                    node.resume()
                self.marker(record, 'READERS_RESUMED')
                for node in self.nodes.values():
                    node.cleanup()
                self.marker(record, 'COMMITTED')
                receipt_ok = self.receipt(record)
                return {'result': 'COMMITTED', 'receipt_written': receipt_ok}
            except Exception as error:
                record['first_cause'] = record['first_cause'] or (str(error) if isinstance(error, Rejected) else 'IO_OR_ACTIVATION_FAILED')
                self.marker(record, 'RECOVERY_REQUIRED')
                return self.recover(record)
