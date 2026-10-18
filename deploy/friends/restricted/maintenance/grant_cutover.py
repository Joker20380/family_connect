import contextlib
import hmac
import os
from pathlib import Path
import sqlite3
import stat

from cryptography import x509
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.x509.oid import NameOID

from credential_renewal import DAY, THRESHOLD, VALIDITY, canonical, digest, require, spki, utc


GRANT_FIELDS = ('device', 'family', 'revision', 'expires', 'revoked')
TABLES = ('devices', 'invites', 'restricted_grants', 'restricted_certificates', 'restricted_crl_sequence')


class GrantDatabase:
    def __init__(self, path, grant_validator, *, all_activated=False, family=None, minimum_revision=None):
        self.path = Path(path)
        self.grant_validator = grant_validator
        self.all_activated = all_activated
        self.family = family
        self.minimum_revision = minimum_revision
        require(not all_activated or (type(family) is str and type(minimum_revision) is int
                                     and minimum_revision > 0), 'ADMISSION_BINDING')

    @contextlib.contextmanager
    def connect(self, write=False):
        descriptor = os.open(self.path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        try:
            info = os.fstat(descriptor)
            require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1
                    and info.st_uid == os.geteuid() and not stat.S_IMODE(info.st_mode) & 0o077,
                    'DATABASE_PERMISSIONS')
            for parent in self.path.parents:
                parent_info = parent.lstat()
                require(stat.S_ISDIR(parent_info.st_mode), 'DATABASE_PARENT_SYMLINK')
                require(not parent_info.st_mode & 0o002 or bool(parent_info.st_mode & stat.S_ISVTX),
                        'DATABASE_PARENT_PERMISSIONS')
            mode = 'rw' if write else 'ro'
            database = sqlite3.connect(self.path.as_uri() + '?mode=' + mode, uri=True, timeout=2)
            try:
                current = self.path.lstat()
                require((current.st_dev,current.st_ino) == (info.st_dev,info.st_ino), 'DATABASE_PATH_CHANGED')
                database.row_factory = sqlite3.Row
                database.execute('PRAGMA foreign_keys=ON')
                database.execute('PRAGMA synchronous=FULL')
                database.execute('BEGIN IMMEDIATE' if write else 'BEGIN')
                require(database.execute('PRAGMA quick_check').fetchone()[0] == 'ok', 'DATABASE_INVALID')
                yield database
                if write:
                    database.commit()
                else:
                    database.rollback()
            except BaseException:
                database.rollback()
                raise
            finally:
                database.close()
        finally:
            os.close(descriptor)

    def snapshot(self, database=None):
        if database is None:
            with self.connect() as connection:
                return self.snapshot(connection)
        value = {}
        for table in TABLES:
            columns = [row['name'] for row in database.execute('PRAGMA table_info(' + table + ')')]
            require(columns, 'DATABASE_SCHEMA')
            if table == 'restricted_grants':
                require(tuple(columns) == GRANT_FIELDS, 'DATABASE_SCHEMA')
            rows = [dict(row) for row in database.execute('SELECT * FROM ' + table)]
            rows.sort(key=canonical)
            require(len(canonical(rows)) <= 512 * 1024, 'DATABASE_INPUT_BOUND')
            value[table] = rows
        require(len(value['restricted_grants']) <= 256, 'GRANT_COUNT_BOUND')
        require(len(value['restricted_crl_sequence']) == 1
                and value['restricted_crl_sequence'][0]['singleton'] == 1, 'CRL_SEQUENCE_STATE')
        return value

    def pending_revocations(self, crl, now):
        pending = []
        with self.connect() as database:
            for row in database.execute('SELECT device,revision,serial,expires FROM restricted_certificates WHERE expires>?',(now,)):
                if crl.get_revoked_certificate_by_serial_number(int(row['serial'])) is not None:
                    continue
                try:
                    grant = self.grant_validator(database,row['device'],now)
                    valid = grant['revision'] == row['revision']
                except ValueError:
                    valid = False
                if not valid:
                    pending.append(int(row['serial']))
        return len(set(pending))

    def plan(self, issuer, now, *, readers_quiesced):
        require(readers_quiesced(), 'READERS_NOT_QUIESCED')
        with self.connect() as database:
            before = self.snapshot(database)
            after = [dict(row) for row in before['restricted_grants']]
            changed = set()
            for row in after:
                if row['revoked'] or self.all_activated:
                    continue
                self.grant_validator(database, row['device'], now)
                require(type(row['expires']) is int, 'GRANT_EXPIRY_CONTRACT_REQUIRED')
                if row['expires'] - now > THRESHOLD['grant']:
                    continue
                successor_expiry = min(now + VALIDITY['grant'], int(issuer.not_valid_after_utc.timestamp()))
                require(successor_expiry - now > THRESHOLD['grant'], 'AUTHORITY_HEADROOM_INSUFFICIENT')
                row['expires'] = successor_expiry
                row['revision'] += 1
                changed.add(row['device'])
            predecessors = []
            grants = {row['device']: row for row in before['restricted_grants']}
            successors = {row['device']: row for row in after}
            devices = {row['device']: row for row in before['devices']}
            for row in before['restricted_certificates']:
                if row['expires'] <= now:
                    continue
                try:
                    effective = self.grant_validator(database,row['device'],now)
                    eligible = True
                except ValueError:
                    eligible = False
                require(self.all_activated or row['device'] in successors, 'CERTIFICATE_GRANT_MISSING')
                revision = effective['revision'] if self.all_activated and eligible else successors.get(row['device'], {}).get('revision')
                if eligible and row['revision'] == revision:
                    continue
                certificate = x509.load_pem_x509_certificate(row['certificate'].encode())
                certificate.verify_directly_issued_by(issuer)
                require(str(certificate.serial_number) == row['serial']
                        and int(certificate.not_valid_after_utc.timestamp()) == row['expires'],
                        'CERTIFICATE_RECORD_MISMATCH')
                grant = grants.get(row['device'])
                require(type(row['revision']) is int and row['revision'] > 0, 'CERTIFICATE_REVISION')
                if grant is not None:
                    require(row['revision'] <= grant['revision'], 'CERTIFICATE_REVISION_AHEAD')
                require(certificate.subject.get_attributes_for_oid(NameOID.SERIAL_NUMBER)[0].value == row['device'],
                        'CERTIFICATE_DEVICE_BINDING')
                claims = {attribute.value for attribute in certificate.subject.get_attributes_for_oid(NameOID.ORGANIZATIONAL_UNIT_NAME)}
                family = self.family if self.all_activated else grant['family']
                require({'role=device','family=' + family,'revision=' + str(row['revision'])} <= claims,
                        'CERTIFICATE_CLAIMS')
                import base64
                public = base64.b64decode(devices[row['device']]['public'], validate=True)
                from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
                require(len(public) == 64 and hmac.compare_digest(spki(certificate.public_key()),
                        spki(Ed25519PublicKey.from_public_bytes(public[32:]))), 'CERTIFICATE_KEY_BINDING')
                predecessors.append(int(row['serial']))
            require(readers_quiesced(), 'READERS_NOT_QUIESCED')
            return dict(schema=1,model='MAINTENANCE_CUTOVER_NO_OVERLAP',
                        before=before,after_grants=after,predecessors=sorted(set(predecessors)),
                        before_sha256=digest(canonical(before)),issued_at=now)

    def recovery_plan(self, issuer, now, authorization, *, issued_at=None):
        from expired_recovery import RecoveryAuthorization
        require(type(authorization) is RecoveryAuthorization, 'RECOVERY_TYPE')
        issued = now if issued_at is None else issued_at
        require(type(issued) is int and issued <= now, 'RECOVERY_PLAN_TIME')
        with self.connect() as database:
            before = self.snapshot(database)
            require(digest(canonical(before)) == authorization.request['expected']['RU']['database_sha256'],
                    'RECOVERY_STALE_APPROVAL')
            require(before['restricted_grants'] == authorization.predecessor.snapshot['grants'], 'RECOVERY_GRANT_SCOPE')
            after = [dict(row) for row in before['restricted_grants']]
            approved = authorization.request['grant_scope']
            require(sorted(row['device'] for row in after if not row['revoked']) == approved, 'RECOVERY_GRANT_SCOPE')
            require(all(row['expires'] <= now for row in before['restricted_certificates']),
                    'RECOVERY_UNEXPIRED_CERTIFICATE')
            with sqlite3.connect(':memory:') as proposal:
                database.backup(proposal)
                proposal.row_factory = sqlite3.Row
                for row in after:
                    if row['device'] not in approved or self.all_activated:
                        continue
                    row['expires'] = min(issued + VALIDITY['grant'], int(issuer.not_valid_after_utc.timestamp()))
                    row['revision'] += 1
                    require(row['expires'] > now, 'RECOVERY_STRICT_SUCCESSOR_INVALID')
                    proposal.execute('UPDATE restricted_grants SET revision=?,expires=? WHERE device=?',
                                     (row['revision'], row['expires'], row['device']))
                    try:
                        self.grant_validator(proposal, row['device'], now)
                    except ValueError:
                        require(False, 'RECOVERY_ENTITLEMENT_REJECTED')
            return dict(schema=1, model='MAINTENANCE_CUTOVER_NO_OVERLAP', before=before,
                        after_grants=after, predecessors=[], before_sha256=digest(canonical(before)), issued_at=issued)

    def apply(self, plan, candidate_crl, issuer, now, *, readers_quiesced, recovery_authorization=None):
        require(readers_quiesced(), 'READERS_NOT_QUIESCED')
        validate_grant_plan(plan, now if recovery_authorization is None else plan['issued_at'])
        if digest(canonical(self.snapshot())) == plan['before_sha256']:
            independently_planned = (self.plan(issuer, plan['issued_at'], readers_quiesced=readers_quiesced)
                if recovery_authorization is None else self.recovery_plan(issuer, now, recovery_authorization,
                    issued_at=plan['issued_at']))
            require(canonical(independently_planned) == canonical(plan), 'GRANT_PLAN_MISMATCH')
        crl = x509.load_pem_x509_crl(candidate_crl)
        require(crl.issuer == issuer.subject and crl.is_signature_valid(issuer.public_key()), 'CRL_SIGNATURE')
        require(crl.last_update_utc <= utc(now) < crl.next_update_utc, 'CRL_EXPIRED_OR_FUTURE')
        require(all(crl.get_revoked_certificate_by_serial_number(serial) is not None
                    for serial in plan['predecessors']), 'PREDECESSOR_REVOCATION_MISSING')
        number = crl.extensions.get_extension_for_class(x509.CRLNumber).value.crl_number
        with self.connect(write=True) as database:
            actual = self.snapshot(database)
            expected = dict(plan['before'], restricted_grants=plan['after_grants'],
                            restricted_crl_sequence=[dict(singleton=1,sequence=number)])
            if canonical(actual) == canonical(expected):
                return 'ALREADY_APPLIED'
            require(digest(canonical(actual)) == plan['before_sha256'], 'STALE_DATABASE')
            previous_number = actual['restricted_crl_sequence'][0]['sequence']
            require(number in (previous_number,previous_number+1), 'CRL_SEQUENCE')
            for old, new in zip(actual['restricted_grants'], plan['after_grants']):
                if old == new:
                    continue
                cursor = database.execute('UPDATE restricted_grants SET revision=?, expires=? '
                    'WHERE device=? AND revision=? AND expires=? AND revoked=?',
                    (new['revision'],new['expires'],old['device'],old['revision'],old['expires'],old['revoked']))
                require(cursor.rowcount == 1, 'STALE_DATABASE')
            database.execute('UPDATE restricted_crl_sequence SET sequence=? WHERE singleton=1', (number,))
            require(canonical(self.snapshot(database)) == canonical(expected), 'DATABASE_SCOPE_CHANGED')
            require(readers_quiesced(), 'READERS_NOT_QUIESCED')
        return 'APPLIED'


def validate_grant_plan(plan, now):
    require(plan['schema'] == 1 and plan['model'] == 'MAINTENANCE_CUTOVER_NO_OVERLAP', 'GRANT_PLAN_SCHEMA')
    require(digest(canonical(plan['before'])) == plan['before_sha256'], 'GRANT_PLAN_HASH')
    require(0 <= now - plan['issued_at'] <= 900, 'STALE_GRANT_PLAN')
    old = plan['before']['restricted_grants']
    new = plan['after_grants']
    require(len(old) == len(new), 'GRANT_COUNT_CHANGED')
    for predecessor, successor in zip(old, new):
        require(set(successor) == set(GRANT_FIELDS), 'GRANT_PLAN_SCHEMA')
        require({key:value for key,value in predecessor.items() if key not in ('revision','expires')}
                == {key:value for key,value in successor.items() if key not in ('revision','expires')},
                'GRANT_SCOPE_CHANGED')
        if predecessor == successor:
            continue
        require(predecessor['revoked'] == 0 and successor['revision'] == predecessor['revision'] + 1
                and plan['issued_at'] + THRESHOLD['grant'] < successor['expires'] <= plan['issued_at'] + VALIDITY['grant']
                and successor['expires'] > predecessor['expires'], 'GRANT_REVISION_OR_VALIDITY')


def prepare_crl(previous_pem, issuer, signing_key, plan, now):
    validate_grant_plan(plan, now)
    require(hmac.compare_digest(spki(issuer.public_key()),spki(signing_key.public_key())),
            'ISSUER_SIGNING_KEY_MISMATCH')
    previous = x509.load_pem_x509_crl(previous_pem)
    require(previous.issuer == issuer.subject and previous.is_signature_valid(issuer.public_key()), 'CURRENT_CRL_INVALID')
    previous_number = previous.extensions.get_extension_for_class(x509.CRLNumber).value.crl_number
    require(plan['before']['restricted_crl_sequence'][0]['sequence'] == previous_number, 'CURRENT_SEQUENCE_INVALID')
    issued = max(now - 5, int(issuer.not_valid_before_utc.timestamp()), int(previous.last_update_utc.timestamp()))
    require(issued <= now and utc(issued + VALIDITY['crl']) <= issuer.not_valid_after_utc, 'AUTHORITY_HEADROOM_INSUFFICIENT')
    builder = x509.CertificateRevocationListBuilder().issuer_name(issuer.subject).last_update(utc(issued)).next_update(utc(issued + VALIDITY['crl']))
    for extension in previous.extensions:
        builder = builder.add_extension(x509.CRLNumber(previous_number + 1) if isinstance(extension.value,x509.CRLNumber)
                                        else extension.value, extension.critical)
    existing = {entry.serial_number:entry for entry in previous}
    for serial in plan['predecessors']:
        if serial not in existing:
            existing[serial] = x509.RevokedCertificateBuilder().serial_number(serial).revocation_date(utc(now)).build()
    for serial in sorted(existing):
        builder = builder.add_revoked_certificate(existing[serial])
    raw = builder.sign(signing_key,None).public_bytes(Encoding.PEM)
    verified = x509.load_pem_x509_crl(raw)
    require(verified.is_signature_valid(issuer.public_key()) and verified.issuer == issuer.subject, 'CANDIDATE_SIGNATURE_INVALID')
    require({entry.serial_number for entry in verified} == set(existing), 'REVOCATION_SET_CHANGED')
    require(all(verified.get_revoked_certificate_by_serial_number(entry.serial_number).revocation_date_utc == entry.revocation_date_utc
                and tuple(verified.get_revoked_certificate_by_serial_number(entry.serial_number).extensions) == tuple(entry.extensions)
                for entry in previous), 'REVOCATION_SET_LOSS')
    return raw
