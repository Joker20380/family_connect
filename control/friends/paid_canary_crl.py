"""Unbound source-only CRL orchestration; trusted adapters/configuration are injected."""
import argparse
import base64
from contextlib import contextmanager
from dataclasses import dataclass
import fcntl
from functools import wraps
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import secrets
import stat

from cryptography import x509
from cryptography.x509.oid import NameOID

from . import paid_beta, restricted_admin
from .access import Rejected
from .paid_beta_canary import ALIAS, token_for
from .restricted import PROTOCOL, delegation, directory, utc

MAX_REQUEST = 20000
MAX_RESPONSE = 8192
STATES = frozenset(('PREPARED', 'DELIVERY_IN_PROGRESS', 'REMOTE_ACCEPTED', 'LOCAL_COMMIT_IN_PROGRESS',
                    'COMMITTED', 'TRANSPORT_NOT_SENT', 'DELIVERY_UNRESOLVED', 'REMOTE_REJECTED', 'LOCAL_COMMIT_FAILED'))
CODES = frozenset(('PASS', 'LOCK_BUSY', 'INVALID_PERMIT', 'PRECONDITION_FAILED', 'CRL_GENERATION_FAILED',
    'CRL_GENERATION_ALREADY_COMPLETED', 'CRL_EXPECTED_SET_MISMATCH', 'CRL_UNEXPECTED_REVOCATION',
    'TRANSPORT_NOT_SENT', 'TRANSPORT_FAILED', 'CRL_DELIVERY_UNRESOLVED', 'CRL_PAYLOAD_CONFLICT',
    'REMOTE_REJECTED', 'GATEWAY_VALIDATION_FAILED', 'DIRECTORY_VALIDATION_FAILED', 'LOCAL_PRECONDITION_CHANGED',
    'REMOTE_ACCEPTED_LOCAL_COMMIT_FAILED', 'LOCAL_COMMIT_FAILED', 'LOCAL_COMMIT_CONFLICT', 'READBACK_MISMATCH'))


class CRLError(ValueError):
    def __init__(self, code):
        super().__init__(code if code in CODES else 'PRECONDITION_FAILED')


def require(condition, code='PRECONDITION_FAILED'):
    if not condition:
        raise CRLError(code)


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def strict(raw, limit, code='PRECONDITION_FAILED'):
    require(type(raw) is bytes and 0 < len(raw) <= limit, code)
    def pairs(items):
        result = {}
        for name, value in items:
            require(name not in result, code)
            result[name] = value
        return result
    try:
        return json.loads(raw, object_pairs_hook=pairs, parse_constant=lambda _: require(False, code))
    except (ValueError, UnicodeError, RecursionError):
        raise CRLError(code) from None


def validate_permit(value):
    names = ('schema alias operation_id device_token safe_ref expected_subscription_version expected_event_count '
             'expected_effective_state expected_certificate_safe_token not_before not_after')
    require(type(value) is dict and set(value) == set(names.split()), 'INVALID_PERMIT')
    require(type(value['schema']) is int and value['schema'] == 1 and value['alias'] == ALIAS, 'INVALID_PERMIT')
    for name, pattern in (('operation_id', r'canary_crl_[0-9a-f]{32}'), ('device_token', r'[0-9a-f]{64}'),
                          ('expected_certificate_safe_token', r'[0-9a-f]{12}')):
        require(type(value[name]) is str and re.fullmatch(pattern, value[name]), 'INVALID_PERMIT')
    require(value['safe_ref'] == 'dev_' + value['device_token'][:12], 'INVALID_PERMIT')
    require(all(type(value[name]) is int and value[name] == 3 for name in
                ('expected_subscription_version', 'expected_event_count')), 'INVALID_PERMIT')
    require(value['expected_effective_state'] == 'expired', 'INVALID_PERMIT')
    require(all(type(value[name]) is int and 0 <= value[name] <= paid_beta.MAX_TIME for name in
                ('not_before', 'not_after')) and 0 < value['not_after'] - value['not_before'] <= 300, 'INVALID_PERMIT')


def serial_token(key, serial):
    return hmac.new(key, str(serial).encode(), hashlib.sha256).hexdigest()[:12]


def checked_path(path, *, folder=False, private=True):
    require(isinstance(path, Path) and path.is_absolute() and '..' not in path.parts)
    for parent in path.parents:
        info = parent.lstat()
        require(stat.S_ISDIR(info.st_mode) and not stat.S_ISLNK(info.st_mode))
        require(not info.st_mode & 0o022 or (info.st_uid == 0 and info.st_mode & stat.S_ISVTX))
    info = path.lstat()
    require(info.st_uid == os.geteuid() and not stat.S_ISLNK(info.st_mode))
    require(stat.S_ISDIR(info.st_mode) if folder else stat.S_ISREG(info.st_mode) and info.st_nlink == 1)
    require(stat.S_IMODE(info.st_mode) == (0o700 if folder else 0o600) if private else not info.st_mode & 0o022)
    return info


def read_file(path, limit):
    checked_path(path)
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(descriptor, 'rb') as stream:
        require(os.fstat(stream.fileno()).st_nlink == 1)
        raw = stream.read(limit + 1)
    require(len(raw) <= limit)
    return raw


def fsync_folder(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def write_file(path, raw, *, replace=False):
    checked_path(path.parent, folder=True)
    if replace and path.exists():
        checked_path(path)
    temporary = path.with_name('.pending-' + secrets.token_hex(16)) if replace else path
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        if replace:
            os.replace(temporary, path)
        fsync_folder(path.parent)
    finally:
        if replace and temporary.exists():
            temporary.unlink()


def stage_file(path, raw):
    checked_path(path)
    temporary = path.with_name('.commit-' + secrets.token_hex(16))
    write_file(temporary, raw)
    return temporary


def install_file(temporary, path):
    checked_path(temporary)
    checked_path(path)
    os.replace(temporary, path)
    fsync_folder(path.parent)


@dataclass(frozen=True, repr=False)
class Configuration:
    service: object
    operations: Path
    sync_lock: Path
    crl: Path
    directory: Path
    receipt_key: bytes


@dataclass(frozen=True, repr=False)
class TrustedReadback:
    crl_number: int
    payload_sha256: str
    minimum_crl: int
    directory_bytes: bytes


@dataclass(frozen=True, repr=False)
class TransportResult:
    outcome: str
    readback: TrustedReadback | None = None
    pre_send_proof: str | None = None
    rejection: str = 'REMOTE_REJECTED'


def bounded(method):
    @wraps(method)
    def run(self, *args, **kwargs):
        try:
            with self.locked():
                return method(self, *args, **kwargs)
        except CRLError:
            raise
        except Exception:
            raise CRLError('PRECONDITION_FAILED') from None
    return run


class Operation:
    def __init__(self, configuration, permit):
        validate_permit(permit)
        require(type(configuration) is Configuration)
        require(type(configuration.receipt_key) is bytes and len(configuration.receipt_key) == 32)
        self.config = configuration
        self.permit = strict(encode(permit), 4096, 'INVALID_PERMIT')
        self.path = configuration.operations / permit['operation_id']

    def now(self):
        return int(self.config.service.access.clock())

    @contextmanager
    def locked(self):
        checked_path(self.config.operations, folder=True)
        checked_path(self.config.sync_lock)
        descriptor = os.open(self.config.sync_lock, os.O_RDWR | os.O_NOFOLLOW)
        try:
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise CRLError('LOCK_BUSY') from None
            yield
        finally:
            os.close(descriptor)

    def sequence(self, database):
        row = database.execute('SELECT sequence FROM restricted_crl_sequence WHERE singleton=1').fetchone()
        require(row is not None and type(row[0]) is int and row[0] >= 0)
        return row[0]

    def preconditions(self, database, now):
        service = self.config.service
        trust, authority = delegation(service.manifest, service.anchor, now)
        matches = [row[0] for row in database.execute('SELECT device FROM devices')
                   if hmac.compare_digest(token_for(self.config.receipt_key, row[0]), self.permit['device_token'])]
        require(len(matches) == 1)
        device = matches[0]
        for table in ('paid_beta_subscriptions', 'paid_beta_events'):
            require(database.execute('SELECT 1 FROM ' + table + ' WHERE device!=? LIMIT 1', (device,)).fetchone() is None)
        subscription = database.execute('SELECT * FROM paid_beta_subscriptions WHERE device=?', (device,)).fetchone()
        events = database.execute('SELECT * FROM paid_beta_events WHERE device=? ORDER BY rowid', (device,)).fetchall()
        require(subscription is not None and subscription['version'] == 3 and subscription['state'] == 'expired'
                and subscription['revoked_at'] is None and len(events) == 3
                and [row['event_type'] for row in events] == ['payment', 'payment', 'expire']
                and subscription['last_event_id'] == events[-1]['event_id'])
        effective = paid_beta.effective_subscription_state(database, device, now)
        require(effective.state == 'expired' and effective.allowed is False)
        paid_beta.confirm_android106(database, device)
        grant = service._legacy_grant(database, device, now)
        require(grant['family'] == trust['family'] and grant['revision'] >= trust['minimum_revision'])
        try:
            service._grant(database, device, now)
        except Rejected:
            pass
        else:
            raise CRLError('PRECONDITION_FAILED')
        certificates = [row for row in database.execute('SELECT * FROM restricted_certificates WHERE device=?', (device,))
                        if serial_token(self.config.receipt_key, row['serial']) == self.permit['expected_certificate_safe_token']]
        require(len(certificates) == 1)
        row = certificates[0]
        certificate = x509.load_pem_x509_certificate(row['certificate'].encode())
        certificate.verify_directly_issued_by(authority)
        require(certificate.not_valid_before_utc <= utc(now) < certificate.not_valid_after_utc)
        require(row['expires'] == int(certificate.not_valid_after_utc.timestamp())
                and str(certificate.serial_number) == row['serial'] and row['revision'] == grant['revision'])
        require(certificate.public_key().public_bytes_raw() == base64.b64decode(grant['public'], validate=True)[32:])
        require([item.value for item in certificate.subject.get_attributes_for_oid(NameOID.SERIAL_NUMBER)] == [device])
        require({item.value for item in certificate.subject.get_attributes_for_oid(NameOID.ORGANIZATIONAL_UNIT_NAME)} ==
                {'protocol=' + PROTOCOL, 'family=' + trust['family'], 'role=device', 'revision=' + str(grant['revision'])})
        fingerprint = {}
        for table in ('devices', 'invites', 'device_support', 'restricted_grants', 'restricted_certificates',
                      'paid_beta_subscriptions', 'paid_beta_events'):
            fingerprint[table] = [dict(item) for item in database.execute('SELECT * FROM ' + table + ' WHERE device=? ORDER BY rowid', (device,))]
        fingerprint['authority'] = service.manifest
        fingerprint['anchor'] = service.anchor.hex()
        fingerprint['policy'] = [service.all_activated, sorted(service.eligible_devices) if service.eligible_devices is not None else None]
        return certificate.serial_number, hmac.new(self.config.receipt_key, encode(fingerprint), hashlib.sha256).hexdigest(), trust

    def save(self, journal):
        journal = dict(journal)
        journal.pop('mac', None)
        journal['mac'] = hmac.new(self.config.receipt_key, encode(journal), hashlib.sha256).hexdigest()
        write_file(self.path / 'journal.json', encode(journal), replace=True)

    def load(self):
        checked_path(self.path, folder=True)
        journal = strict(read_file(self.path / 'journal.json', 32768), 32768)
        mac = journal.pop('mac')
        require(hmac.compare_digest(mac, hmac.new(self.config.receipt_key, encode(journal), hashlib.sha256).hexdigest()))
        require(journal['permit_hash'] == digest(encode(self.permit)) and journal['generation_count'] == 1)
        require(journal['state'] in STATES and type(journal['delivery_attempts']) is int and 0 <= journal['delivery_attempts'] <= 2)
        payload = read_file(self.path / 'payload.pem', 16384)
        request = read_file(self.path / 'request.json', MAX_REQUEST)
        require(digest(payload) == journal['payload_sha256'] and digest(request) == journal['request_sha256'])
        value = strict(request, MAX_REQUEST)
        require(type(value) is dict and set(value) == {'revocations'} and value['revocations'].encode() == payload)
        require(encode(value) == request)
        if journal['state'] == 'DELIVERY_IN_PROGRESS':
            journal.update(state='DELIVERY_UNRESOLVED', result='CRL_DELIVERY_UNRESOLVED')
            self.save(journal)
        return journal, payload, request

    def receipt(self, journal):
        names = ('state previous_crl_number generated_crl_number payload_sha256 payload_size request_sha256 '
                 'generation_count delivery_attempts this_update next_update expected_revoked_count unrelated_revocation_count')
        result = {name: journal[name] for name in names.split()}
        result.update(schema=1, operation_safe_label=ALIAS, result=journal['result'], observed_at=self.now(),
                      gateway_minimum_crl=journal.get('gateway_minimum_crl'),
                      directory_validation='PASS' if journal.get('response_sha256') else 'NOT_RUN',
                      local_commit='PASS' if journal['state'] == 'COMMITTED' else 'NOT_COMMITTED')
        return result

    @bounded
    def status(self):
        journal, _, _ = self.load()
        return self.receipt(journal)

    @bounded
    def prepare(self):
        if self.path.exists() or self.path.is_symlink():
            raise CRLError('CRL_GENERATION_ALREADY_COMPLETED')
        now = self.now()
        require(self.permit['not_before'] <= now < self.permit['not_after'])
        checked_path(self.config.service.access.path, private=False)
        with paid_beta.connection(self.config.service.access.path) as database:
            expected, fingerprint, trust = self.preconditions(database, now)
            previous_raw = read_file(self.config.crl, 16384)
            previous = x509.load_pem_x509_crl(previous_raw)
            previous_set = {item.serial_number for item in previous}
            prior_directory = read_file(self.config.directory, MAX_RESPONSE)
            directory(prior_directory, trust['family'], trust['gateway'], now)
            sequence = self.sequence(database)
            self.path.mkdir(mode=0o700)
            fsync_folder(self.config.operations)
            try:
                payload, metadata = restricted_admin.build_crl_payload(self.config.service, database, previous_raw,
                    sequence, now, 900, receipt_key=self.config.receipt_key)
                _, authority = delegation(self.config.service.manifest, self.config.service.anchor, now)
                generated = x509.load_pem_x509_crl(payload)
                require(generated.is_signature_valid(authority.public_key()) and generated.issuer == authority.subject)
                require(generated.extensions.get_extension_for_class(x509.CRLNumber).value.crl_number ==
                        metadata['generated_number'] == max(metadata['previous_number'], sequence) + 1)
                require(generated.last_update_utc == utc(metadata['this_update']) and
                        generated.next_update_utc == utc(metadata['next_update']) and
                        previous.last_update_utc <= generated.last_update_utc <= utc(now) < generated.next_update_utc and
                        0 < metadata['next_update'] - metadata['this_update'] <= 900)
            except Exception:
                raise CRLError('CRL_GENERATION_FAILED') from None
            require(len(payload) <= 16384, 'CRL_GENERATION_FAILED')
            new_set = {item.serial_number for item in x509.load_pem_x509_crl(payload)}
            added = new_set - previous_set
            require(expected in added, 'CRL_EXPECTED_SET_MISMATCH')
            for serial in added - {expected}:
                row = database.execute('SELECT * FROM restricted_certificates WHERE serial=? AND expires>?', (str(serial), now)).fetchone()
                require(row is not None, 'CRL_UNEXPECTED_REVOCATION')
                try:
                    grant = self.config.service._grant(database, row['device'], now)
                    denied = grant['revision'] != row['revision'] or grant['family'] != trust['family'] or grant['revision'] < trust['minimum_revision']
                except Rejected:
                    denied = True
                require(denied, 'CRL_UNEXPECTED_REVOCATION')
            request = encode(dict(revocations=payload.decode('ascii')))
            require(len(request) <= MAX_REQUEST, 'CRL_GENERATION_FAILED')
            journal = dict(permit_hash=digest(encode(self.permit)), state='PREPARED', result='PASS', generation_count=1,
                delivery_attempts=0, previous_crl_number=metadata['previous_number'], generated_crl_number=metadata['generated_number'],
                this_update=metadata['this_update'], next_update=metadata['next_update'], generated_at=now,
                payload_sha256=digest(payload), payload_size=len(payload), request_sha256=digest(request),
                expected_revoked_count=len(new_set), unrelated_revocation_count=len(added - {expected}),
                expected_tokens=sorted(serial_token(self.config.receipt_key, serial) for serial in added),
                prior_crl_hash=digest(previous_raw), prior_directory_hash=digest(prior_directory),
                prior_sequence=sequence, fingerprint=fingerprint)
            write_file(self.path / 'payload.pem', payload)
            write_file(self.path / 'request.json', request)
            self.save(journal)
        return self.receipt(journal)

    def validate_readback(self, journal, readback, code='GATEWAY_VALIDATION_FAILED'):
        require(type(readback) is TrustedReadback, code)
        require(type(readback.crl_number) is int and type(readback.minimum_crl) is int
                and readback.crl_number == readback.minimum_crl == journal['generated_crl_number']
                and readback.payload_sha256 == journal['payload_sha256'], code)
        try:
            trust, _ = delegation(self.config.service.manifest, self.config.service.anchor, self.now())
            directory(readback.directory_bytes, trust['family'], trust['gateway'], self.now())
        except Exception:
            raise CRLError('DIRECTORY_VALIDATION_FAILED' if code != 'READBACK_MISMATCH' else code) from None
        require(self.now() < journal['next_update'], code)

    def accept(self, journal, readback):
        self.validate_readback(journal, readback)
        response = self.path / 'response.json'
        if response.exists():
            require(read_file(response, MAX_RESPONSE) == readback.directory_bytes, 'READBACK_MISMATCH')
        else:
            write_file(response, readback.directory_bytes)
        journal.update(state='REMOTE_ACCEPTED', result='PASS', response_sha256=digest(readback.directory_bytes),
                       gateway_minimum_crl=readback.minimum_crl)
        self.save(journal)

    @bounded
    def deliver(self, transport):
        journal, _, request = self.load()
        require(journal['state'] == 'PREPARED' or
                (journal['state'] == 'TRANSPORT_NOT_SENT' and journal['delivery_attempts'] == 1),
                'CRL_DELIVERY_UNRESOLVED' if journal['state'] == 'DELIVERY_UNRESOLVED' else 'TRANSPORT_FAILED')
        require(journal['delivery_attempts'] < 2, 'TRANSPORT_FAILED')
        require(self.now() < journal['next_update'], 'GATEWAY_VALIDATION_FAILED')
        journal.update(state='DELIVERY_IN_PROGRESS', delivery_attempts=journal['delivery_attempts'] + 1)
        self.save(journal)
        try:
            outcome = transport(request)
        except Exception:
            outcome = TransportResult('UNKNOWN')
        if type(outcome) is not TransportResult or outcome.outcome not in ('ACCEPTED', 'REJECTED', 'NOT_SENT', 'UNKNOWN'):
            outcome = TransportResult('UNKNOWN')
        if outcome.outcome == 'NOT_SENT' and outcome.pre_send_proof not in ('PROCESS_NOT_STARTED', 'REMOTE_NOT_STARTED'):
            outcome = TransportResult('UNKNOWN')
        if outcome.outcome == 'ACCEPTED':
            try:
                self.accept(journal, outcome.readback)
            except CRLError as error:
                journal.update(state='DELIVERY_UNRESOLVED', result=str(error))
                self.save(journal)
                raise
        else:
            state, result = {'NOT_SENT': ('TRANSPORT_NOT_SENT', 'TRANSPORT_NOT_SENT'),
                'UNKNOWN': ('DELIVERY_UNRESOLVED', 'CRL_DELIVERY_UNRESOLVED'),
                'REJECTED': ('REMOTE_REJECTED', 'REMOTE_REJECTED')}[outcome.outcome]
            if outcome.outcome == 'REJECTED' and outcome.rejection == 'CRL_PAYLOAD_CONFLICT':
                result = 'CRL_PAYLOAD_CONFLICT'
            if outcome.outcome == 'NOT_SENT' and journal['delivery_attempts'] == 2:
                result = 'TRANSPORT_FAILED'
            journal.update(state=state, result=result)
            self.save(journal)
        return self.receipt(journal)

    @bounded
    def reconcile(self, readback):
        journal, _, _ = self.load()
        require(journal['state'] == 'DELIVERY_UNRESOLVED', 'READBACK_MISMATCH')
        require(type(readback) is TrustedReadback, 'READBACK_MISMATCH')
        require(type(readback.crl_number) is int and type(readback.minimum_crl) is int, 'READBACK_MISMATCH')
        if (readback.crl_number == journal['previous_crl_number'] and readback.payload_sha256 == journal['prior_crl_hash']
                and readback.minimum_crl == readback.crl_number):
            try:
                trust, _ = delegation(self.config.service.manifest, self.config.service.anchor, self.now())
                directory(readback.directory_bytes, trust['family'], trust['gateway'], self.now())
            except Exception:
                raise CRLError('READBACK_MISMATCH') from None
            return self.receipt(journal)
        self.validate_readback(journal, readback, 'READBACK_MISMATCH')
        self.accept(journal, readback)
        return self.receipt(journal)

    @bounded
    def commit(self):
        journal, payload, _ = self.load()
        require(journal['state'] in ('REMOTE_ACCEPTED', 'LOCAL_COMMIT_IN_PROGRESS', 'LOCAL_COMMIT_FAILED', 'COMMITTED'),
                'LOCAL_COMMIT_FAILED')
        response = read_file(self.path / 'response.json', MAX_RESPONSE)
        require(digest(response) == journal['response_sha256'], 'LOCAL_COMMIT_CONFLICT')
        readback = TrustedReadback(journal['generated_crl_number'], journal['payload_sha256'], journal['gateway_minimum_crl'], response)
        self.validate_readback(journal, readback)
        temporary_crl = temporary_directory = None
        try:
            with paid_beta.connection(self.config.service.access.path, write=True) as database:
                sequence = self.sequence(database)
                crl_hash = digest(read_file(self.config.crl, 16384))
                directory_hash = digest(read_file(self.config.directory, MAX_RESPONSE))
                require(sequence in (journal['prior_sequence'], journal['generated_crl_number'])
                        and crl_hash in (journal['prior_crl_hash'], journal['payload_sha256'])
                        and directory_hash in (journal['prior_directory_hash'], journal['response_sha256']),
                        'LOCAL_PRECONDITION_CHANGED' if journal['state'] == 'REMOTE_ACCEPTED' else 'LOCAL_COMMIT_CONFLICT')
                if journal['state'] == 'COMMITTED':
                    require(sequence == journal['generated_crl_number'] and crl_hash == journal['payload_sha256']
                            and directory_hash == journal['response_sha256'], 'LOCAL_COMMIT_CONFLICT')
                    return self.receipt(journal)
                if (sequence == journal['generated_crl_number'] and crl_hash == journal['payload_sha256']
                        and directory_hash == journal['response_sha256'] and journal['state'] != 'REMOTE_ACCEPTED'):
                    journal.update(state='COMMITTED', result='PASS')
                    self.save(journal)
                    return self.receipt(journal)
                try:
                    _, fingerprint, _ = self.preconditions(database, self.now())
                    require(fingerprint == journal['fingerprint'])
                except Exception:
                    raise CRLError('LOCAL_PRECONDITION_CHANGED') from None
                if journal['state'] == 'REMOTE_ACCEPTED':
                    require(sequence == journal['prior_sequence'] and crl_hash == journal['prior_crl_hash']
                            and directory_hash == journal['prior_directory_hash'], 'LOCAL_PRECONDITION_CHANGED')
                temporary_crl = stage_file(self.config.crl, payload)
                temporary_directory = stage_file(self.config.directory, response)
                journal.update(state='LOCAL_COMMIT_IN_PROGRESS', result='PASS')
                self.save(journal)
                if sequence != journal['generated_crl_number']:
                    database.execute('UPDATE restricted_crl_sequence SET sequence=? WHERE singleton=1', (journal['generated_crl_number'],))
                install_file(temporary_crl, self.config.crl)
                install_file(temporary_directory, self.config.directory)
            with paid_beta.connection(self.config.service.access.path) as database:
                require(self.sequence(database) == journal['generated_crl_number'], 'LOCAL_COMMIT_CONFLICT')
            require(read_file(self.config.crl, 16384) == payload and read_file(self.config.directory, MAX_RESPONSE) == response,
                    'LOCAL_COMMIT_CONFLICT')
            journal.update(state='COMMITTED', result='PASS')
            self.save(journal)
        except CRLError as error:
            if str(error) in ('LOCAL_PRECONDITION_CHANGED', 'LOCAL_COMMIT_CONFLICT'):
                journal.update(state='LOCAL_COMMIT_FAILED', result=str(error))
                self.save(journal)
                raise
            journal.update(state='LOCAL_COMMIT_FAILED', result='REMOTE_ACCEPTED_LOCAL_COMMIT_FAILED')
            self.save(journal)
            raise CRLError('REMOTE_ACCEPTED_LOCAL_COMMIT_FAILED') from None
        except Exception:
            journal.update(state='LOCAL_COMMIT_FAILED', result='REMOTE_ACCEPTED_LOCAL_COMMIT_FAILED')
            self.save(journal)
            raise CRLError('REMOTE_ACCEPTED_LOCAL_COMMIT_FAILED') from None
        finally:
            for temporary in (temporary_crl, temporary_directory):
                if temporary is not None and temporary.exists():
                    temporary.unlink()
                    fsync_folder(temporary.parent)
        return self.receipt(journal)


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise CRLError('INVALID_PERMIT')


def main(argv=None):
    try:
        parser = Parser(description='Unbound CRL source capsule: help/manifest only; no operational configuration.')
        parser.add_argument('--manifest', action='store_true')
        args = parser.parse_args(argv)
        require(args.manifest, 'INVALID_PERMIT')
        print(encode(dict(schema=1, binding='unbound', operation_permit=None, production_configuration='absent')).decode())
        return 0
    except CRLError as error:
        print(encode(dict(schema=1, result=str(error))).decode())
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
