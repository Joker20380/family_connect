import base64
from contextlib import contextmanager
import hmac
import os
from pathlib import Path
import stat
import time

from cryptography import x509
from cryptography.hazmat.primitives.serialization import Encoding, load_pem_private_key

from credential_renewal import (DAY, MAX_BYTES, THRESHOLD, VALIDITY, Rejected, Validator, atomic, canonical, digest, parse,
                               private_directory, read_private, require, spki, utc)
from grant_cutover import GrantDatabase, prepare_crl, validate_grant_plan
from production_transport import DurableOperation, SystemdBarrier
from offline_handoff import verify as verify_handoff


def pinned(path, allowed_owners):
    for parent in path.parents:
        require(stat.S_ISDIR(parent.lstat().st_mode), 'INPUT_PARENT_SYMLINK')
    descriptor = os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(descriptor,'rb') as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_uid in allowed_owners
                and before.st_mode & 0o777 == 0o600, 'INPUT_PERMISSIONS')
        raw = stream.read(MAX_BYTES+1)
        after = os.fstat(stream.fileno())
        require(len(raw) <= MAX_BYTES and (before.st_size,before.st_mtime_ns,before.st_ctime_ns)
                == (after.st_size,after.st_mtime_ns,after.st_ctime_ns), 'INPUT_CHANGED_DURING_READ')
        return raw,dict(uid=before.st_uid,gid=before.st_gid,mode=0o600)


class ProductionNode:
    def __init__(self, role, live, state, validator, *, database=None, barrier=None, clock=time.time, fault=lambda stage:None,
                 profile_uid=None, policy_paths=None, profile_store=None, service_units=None):
        require(role in ('RU','NL'), 'NODE_ROLE')
        self.role,self.live,self.state,self.validator = role,Path(live),Path(state),validator
        self.database,self.clock,self.fault,self.profile_uid = database,clock,fault,profile_uid
        self.operation = DurableOperation(self.state)
        self.profile_store = profile_store
        require(profile_store is None or role == 'NL', 'PROFILE_STORE_ROLE')
        self.policy_paths = policy_paths or {}
        self.barrier = barrier or SystemdBarrier(role,self.state,units=service_units,clock=clock)
        private_directory(self.state)
        require(self.live.stat().st_dev == self.state.stat().st_dev, 'STAGING_FILESYSTEM_MISMATCH')
        require(not self.live.is_symlink() and self.live.is_dir(), 'LIVE_DIRECTORY_INVALID')

    def names(self):
        return ('issuer.json','revocations.pem') if self.role == 'RU' else ('gateway.json',)

    def read(self, name):
        require(name in (*self.names(),'issuer.key'), 'PATH_NOT_ALLOWLISTED')
        if name == 'gateway.json' and self.profile_store is not None:
            return self.profile_store.read(), self.profile_store.locator.profile_metadata
        return pinned(self.live/name,{os.geteuid(),self.profile_uid})

    @contextmanager
    def profile_lock(self):
        if self.profile_store is None:
            yield
            return
        from control.friends.profile_store import ProfileError
        try:
            with self.profile_store.lock():
                yield
        except ProfileError as error:
            raise Rejected(error.code) from None

    def directory_path(self):
        return self.profile_store.locator.directory_port.path if self.profile_store is not None else self.live/'directory.json'

    def read_directory(self):
        if self.profile_store is not None:
            from control.friends.profile_store import read_regular
            port = self.profile_store.locator.directory_port
            return read_regular(port.path, port.expected, 8192, publisher_parent=port.publisher_parent), port.expected
        return pinned(self.directory_path(), {os.geteuid(), self.profile_uid})

    def inspect(self):
        files = {name:digest(self.read(name)[0]) for name in self.names()}
        value = dict(files=files,role=self.role,session_inventory='UNKNOWN')
        if self.validator.all_activated:
            value['admission_mode'] = 'all_activated'
        if self.policy_paths:
            value['policy'] = {name:digest(pinned(path,{os.geteuid()})[0]) for name,path in self.policy_paths.items()}
        if self.role == 'RU':
            value['database_sha256'] = digest(canonical(self.database.snapshot()))
        return value

    def public_gateway(self):
        require(self.role == 'NL', 'NODE_ROLE')
        raw,_ = self.read('gateway.json')
        import json
        profile = json.loads(raw)
        leaf = x509.load_pem_x509_certificate(profile['certificate'].encode())
        key = load_pem_private_key(profile['private_key'].encode(),None)
        require(hmac.compare_digest(spki(key.public_key()),spki(leaf.public_key())), 'GATEWAY_KEY_MISMATCH')
        return dict(profile_sha256=digest(raw),**{name:profile[name] for name in
            ('authority','certificate','revocations','family','gateway','minimum_revision','minimum_crl')})

    def public_authority(self):
        require(self.role == 'RU', 'NODE_ROLE')
        import json
        raw = self.read('revocations.pem')[0]
        crl = x509.load_pem_x509_crl(raw)
        return dict(authority=json.loads(self.read('issuer.json')[0]),crl=raw.decode(),
                    grants=self.database.snapshot()['restricted_grants'],
                    pending_revocations=self.database.pending_revocations(crl,int(self.clock())))

    def authority_request(self, operation_id):
        require(self.role == 'RU', 'NODE_ROLE')
        with self.operation.lock():
            path = self.state/'authority-request.json'
            if path.exists():
                request = parse(read_private(path))
                require(request['operation_id'] == operation_id, 'OFFLINE_HANDOFF_ALREADY_PENDING')
                return request
            require(not (self.state/'owner.json').exists(), 'OPERATION_BUSY')
            import json
            envelope = json.loads(self.read('issuer.json')[0])
            now = int(self.clock())
            trust,issuer = self.validator.delegation_parser(envelope,self.validator.anchor,now)
            signer = load_pem_private_key(self.read('issuer.key')[0],None)
            require(hmac.compare_digest(spki(signer.public_key()),spki(issuer.public_key())), 'ISSUER_SIGNING_KEY_MISMATCH')
            start = now-5
            builder = (x509.CertificateBuilder().subject_name(issuer.subject).issuer_name(issuer.issuer)
                .public_key(issuer.public_key()).serial_number(x509.random_serial_number())
                .not_valid_before(utc(start)).not_valid_after(utc(start+self.validator.authority_validity)))
            for extension in issuer.extensions:
                builder = builder.add_extension(extension.value,extension.critical)
            certificate = builder.sign(signer,None)
            certificate.verify_directly_issued_by(certificate)
            successor = dict(trust,sequence=trust['sequence']+1,issued_at=start,expires_at=start+self.validator.authority_validity,
                             authority=certificate.public_bytes(Encoding.PEM).decode())
            request = dict(schema=1,operation_id=operation_id,previous_authority=envelope,successor_payload=successor,
                           request_expires_at=now+86400)
            atomic(path,canonical(request))
            return request

    def recovery_evidence(self, checkpoint):
        try:
            return self._recovery_evidence(checkpoint)
        except Rejected:
            raise
        except Exception:
            raise Rejected('RECOVERY_CHECKPOINT_UNCONFIRMED') from None

    def _recovery_evidence(self, checkpoint, owned_operation=None):
        from expired_recovery import fields
        fields(checkpoint, 'operation_id plan_sha256 snapshot_sha256')
        import re
        require(re.fullmatch('[a-z0-9-]{16,96}', checkpoint['operation_id']) is not None, 'OPERATION_ID')
        if (self.state/'owner.json').exists():
            require(owned_operation is not None and self.owner(owned_operation)['state'] == 'QUIESCED',
                    'OTHER_OPERATION_RECOVERY_REQUIRED')
        ledger = parse(read_private(self.state/'completed.json'))
        require(checkpoint['operation_id'] in ledger, 'RECOVERY_CHECKPOINT_UNCONFIRMED')
        location = self.state/'archive'/checkpoint['operation_id']
        manifest = parse(read_private(location/'archive-manifest.json'))
        require(digest(canonical(manifest)) == ledger[checkpoint['operation_id']]['manifest_sha256'],
                'RECOVERY_CHECKPOINT_UNCONFIRMED')
        saved = {}
        for name in ('plan.json', 'files.json', 'reconciliation.json'):
            raw = read_private(location/name)
            require(digest(raw) == manifest.get(name), 'RECOVERY_CHECKPOINT_UNCONFIRMED')
            saved[name] = parse(raw)
        plan = saved['plan.json']
        require(digest(canonical(plan)) == checkpoint['plan_sha256']
                and digest(canonical(plan['candidate'])) == checkpoint['snapshot_sha256']
                and all(item['plan_sha256'] == checkpoint['plan_sha256']
                        for item in saved['reconciliation.json'].values()), 'RECOVERY_CHECKPOINT_UNCONFIRMED')
        for name in self.names():
            expected = saved['files.json'].get(name, {}).get('after',
                plan['ru_expected']['files'].get(name) if self.role == 'RU' else plan['nl_profile_sha256'])
            require(expected is not None and digest(self.read(name)[0]) == expected,
                    'RECOVERY_CHECKPOINT_UNCONFIRMED')
        if self.role == 'RU':
            current = self.database.snapshot()
            old = {row['device']: row for row in plan['candidate']['grants']}
            devices = {row['device']: row for row in plan['grant_plan']['before']['devices']}
            present = {row['device']: row for row in current['devices']}
            for row in current['restricted_grants']:
                previous = old.get(row['device'])
                require(previous is not None and row['family'] == previous['family']
                        and row['revision'] >= previous['revision'] and row['revoked'] >= previous['revoked'],
                        'RECOVERY_FLOOR')
                require(row['device'] in devices and row['device'] in present
                        and present[row['device']]['public'] == devices[row['device']]['public'], 'RECOVERY_DEVICE_BINDING')
            crl = x509.load_pem_x509_crl(self.read('revocations.pem')[0])
            require(current['restricted_crl_sequence'][0]['sequence']
                    == crl.extensions.get_extension_for_class(x509.CRLNumber).value.crl_number, 'RECOVERY_FLOOR')
        return dict(checkpoint=checkpoint, current=self.inspect())

    def recovery_authority_request(self, operation_id, request):
        from expired_recovery import historical, request_check
        require(self.role == 'RU', 'NODE_ROLE')
        with self.operation.lock():
            require(operation_id == request['operation_id'], 'RECOVERY_OPERATION_MISMATCH')
            evidence = self.recovery_evidence(request['checkpoint'])
            require(evidence['current'] == request['expected']['RU'], 'RECOVERY_STALE_APPROVAL')
            old = historical(canonical(request['predecessor']), self.validator.anchor, all_activated=self.validator.all_activated)
            import json
            require(old.snapshot['authority'] == json.loads(self.read('issuer.json')[0])
                    and old.snapshot['crl'].encode() == self.read('revocations.pem')[0]
                    and old.snapshot['grants'] == self.database.snapshot()['restricted_grants'], 'RECOVERY_STALE_APPROVAL')
            signer = load_pem_private_key(self.read('issuer.key')[0], None)
            require(spki(signer.public_key()) == spki(old.issuer.public_key()), 'ISSUER_SIGNING_KEY_MISMATCH')
            now = int(self.clock())
            start = now - 5
            builder = (x509.CertificateBuilder().subject_name(old.issuer.subject).issuer_name(old.issuer.issuer)
                .public_key(old.issuer.public_key()).serial_number(x509.random_serial_number())
                .not_valid_before(utc(start)).not_valid_after(utc(start + self.validator.authority_validity)))
            for extension in old.issuer.extensions:
                builder = builder.add_extension(extension.value, extension.critical)
            issuer = builder.sign(signer, None)
            request = dict(request, successor_payload=dict(old.trust, sequence=old.trust['sequence'] + 1,
                issued_at=start, expires_at=start + self.validator.authority_validity, authority=issuer.public_bytes(Encoding.PEM).decode()))
            request_check(request, self.validator, now)
            from expired_recovery import RecoveryAuthorization
            authorization = RecoveryAuthorization(request, {}, old)
            self.database.recovery_plan(issuer, now, authorization)
            return request

    def acquire(self, operation_id, expected):
        with self.operation.lock():
            if (self.state/'completed.json').exists():
                require(operation_id not in parse(read_private(self.state/'completed.json')), 'OPERATION_REPLAY')
            if (self.state/'owner.json').exists():
                return self.operation.acquire(operation_id,expected)
            require(self.inspect() == expected, 'STALE_NODE_STATE')
            return self.operation.acquire(operation_id,expected)

    def owner(self, operation_id):
        owner = parse(read_private(self.state/'owner.json'))
        require(owner['operation_id'] == operation_id, 'OTHER_OPERATION_RECOVERY_REQUIRED')
        return owner

    def resume_authorized(self, owner):
        path = self.state/'start-intent-0.json'
        if owner['state'] not in ('COMMIT_DECIDED','RESUMED','ROLLED_BACK','ABORTED') or not path.exists():
            return False
        intent = parse(read_private(path))
        require(set(intent) == {'schema','unit','timestamp'} and intent['schema'] == 1
                and intent['unit'] == self.barrier.units[0], 'RESUME_INTENT_INVALID')
        return True

    def previous_readback(self, operation_id):
        owner = self.owner(operation_id)
        require(owner['state'] in ('ROLLED_BACK','ABORTED'), 'TRANSACTION_STATE')
        actual,expected = self.inspect(),dict(owner['expected_state'])
        if self.role == 'RU' and self.resume_authorized(owner):
            actual.pop('database_sha256')
            expected.pop('database_sha256')
        require(actual == expected, 'ROLLBACK_READBACK_MISMATCH')
        return dict(result='PREVIOUS_SNAPSHOT_RESTORED')

    def quiesce(self, operation_id):
        with self.operation.lock():
            owner = self.owner(operation_id)
            require(owner['state'] in ('ACQUIRED','QUIESCED'), 'TRANSACTION_STATE')
            if self.role == 'NL' and not (self.state/'directory-before.json').exists():
                raw,_ = self.read_directory()
                atomic(self.state/'directory-before.json',canonical(dict(sha256=digest(raw))))
            self.barrier.quiesce()
            require(self.inspect() == owner['expected_state'], 'STALE_NODE_STATE')
            return self.operation.advance(owner,'QUIESCED')

    def fence(self, operation_id):
        with self.operation.lock():
            self.owner(operation_id)
            if self.role == 'NL' and not (self.state/'directory-before.json').exists():
                raw,_ = self.read_directory()
                atomic(self.state/'directory-before.json',canonical(dict(sha256=digest(raw))))
            self.barrier.quiesce()
            require(self.barrier.stopped(), 'READERS_NOT_QUIESCED')
            return dict(stopped=True)

    def prepare(self, operation_id, gateway, *, authority_handoff=None, expired_handoff=None):
        require(self.role == 'RU', 'NODE_ROLE')
        with self.operation.lock():
            owner = self.owner(operation_id)
            require(owner['state'] == 'QUIESCED' and self.barrier.stopped(), 'READERS_NOT_QUIESCED')
            require(self.inspect() == owner['expected_state'], 'STALE_NODE_STATE')
            saved = self.state/'prepared-plan.json'
            if saved.exists():
                plan = parse(read_private(saved))
                require(plan['operation_id'] == operation_id and plan['nl_profile_sha256'] == gateway['profile_sha256'],
                        'PREPARE_ALREADY_EXISTS')
                self.validate(plan,recovery=True)
                return plan
            import json
            envelope = json.loads(self.read('issuer.json')[0])
            previous_crl = self.read('revocations.pem')[0]
            now = int(self.clock())
            database = self.database.snapshot()
            previous = canonical(dict(schema=1,authority=envelope,crl=previous_crl.decode(),
                certificate=gateway['certificate'],grants=database['restricted_grants']))
            authorization = None
            if expired_handoff is None:
                _,trust,issuer,_,leaf = self.validator.validate(previous,now,expired_leaf_predecessor=True)
            else:
                from expired_recovery import verify
                require(authority_handoff is None, 'RECOVERY_PURPOSE')
                authorization = verify(expired_handoff, self.validator, operation_id, now)
                require(authorization.predecessor.encoded == previous
                        and authorization.request['expected']['RU'] == owner['expected_state'], 'RECOVERY_STALE_APPROVAL')
                trust,issuer,leaf = (authorization.predecessor.trust, authorization.predecessor.issuer,
                                     authorization.predecessor.leaf)
            require(gateway['authority'] == trust['authority'] and gateway['revocations'] == previous_crl.decode(), 'RU_NL_MISMATCH')
            require(all(gateway[name] == trust[name] for name in ('family','gateway','minimum_revision')), 'GATEWAY_BINDING')
            signer = load_pem_private_key(self.read('issuer.key')[0],None)
            require(hmac.compare_digest(spki(signer.public_key()),spki(issuer.public_key())), 'ISSUER_SIGNING_KEY_MISMATCH')
            if authority_handoff is not None:
                envelope = verify_handoff(authority_handoff,self.validator,envelope,operation_id,now)
                trust,issuer = self.validator.delegation_parser(envelope,self.validator.anchor,now)
            if authorization is not None:
                self._recovery_evidence(authorization.request['checkpoint'], operation_id)
                envelope = authorization.authority
                trust,issuer = self.validator.delegation_parser(envelope,self.validator.anchor,now)
            require(trust['expires_at'] >= now + VALIDITY['leaf'], 'OFFLINE_AUTHORITY_RENEWAL_REQUIRED')
            grant_plan = (self.database.plan(issuer,now,readers_quiesced=self.barrier.stopped)
                if authorization is None else self.database.recovery_plan(issuer, now, authorization))
            old_crl = x509.load_pem_x509_crl(previous_crl)
            crl_due = int(old_crl.next_update_utc.timestamp()) - now <= THRESHOLD['crl']
            missing_revocations = any(old_crl.get_revoked_certificate_by_serial_number(serial) is None
                                      for serial in grant_plan['predecessors'])
            crl = prepare_crl(previous_crl,issuer,signer,grant_plan,now) if crl_due or missing_revocations else previous_crl
            successor = gateway['certificate']
            if int(leaf.not_valid_after_utc.timestamp()) - now <= THRESHOLD['leaf']:
                issued = max(now-5,int(issuer.not_valid_before_utc.timestamp()))
                builder = (x509.CertificateBuilder().subject_name(leaf.subject).issuer_name(issuer.subject)
                    .public_key(leaf.public_key()).serial_number(x509.random_serial_number())
                    .not_valid_before(utc(issued)).not_valid_after(utc(issued+VALIDITY['leaf'])))
                for extension in leaf.extensions:
                    builder = builder.add_extension(extension.value,extension.critical)
                successor = builder.sign(signer,None).public_bytes(Encoding.PEM).decode()
            candidate = canonical(dict(schema=1,authority=envelope,crl=crl.decode(),certificate=successor,
                                       grants=grant_plan['after_grants']))
            plan = dict(schema=1,operation_id=operation_id,previous=parse(previous),candidate=parse(candidate),
                grant_plan=grant_plan,ru_expected=owner['expected_state'],nl_profile_sha256=gateway['profile_sha256'])
            if authorization is not None:
                plan['expired_recovery'] = dict(bundle=base64.b64encode(expired_handoff).decode(), accepted_at=now)
            self.validate(plan)
            path = self.state/'prepared-plan.json'
            if path.exists():
                require(read_private(path) == canonical(plan), 'PREPARE_ALREADY_EXISTS')
            else:
                atomic(path,canonical(plan))
            return plan

    def validate(self, plan, *, recovery=False):
        extra = {'expired_recovery'} if 'expired_recovery' in plan else set()
        require(set(plan) == {'schema','operation_id','previous','candidate','grant_plan','ru_expected','nl_profile_sha256'} | extra
                and plan['schema'] == 1, 'PLAN_SCHEMA')
        now = int(self.clock())
        previous,candidate = canonical(plan['previous']),canonical(plan['candidate'])
        validation_time = plan['grant_plan']['issued_at'] if recovery else now
        if extra:
            from expired_recovery import transition
            authorization = self.recovery_authorization(plan, durable=recovery)
            require(previous == authorization.predecessor.encoded, 'RECOVERY_PREDECESSOR_DIGEST')
            transition(self.validator, authorization, plan['candidate'], now)
        else:
            self.validator.transition(previous,candidate,validation_time,revoke=True,expired_leaf_predecessor=True)
        validate_grant_plan(plan['grant_plan'],plan['grant_plan']['issued_at'] if recovery else now)
        require(plan['candidate']['grants'] == plan['grant_plan']['after_grants']
                and plan['previous']['grants'] == plan['grant_plan']['before']['restricted_grants'], 'GRANT_PLAN_MISMATCH')
        old = x509.load_pem_x509_crl(plan['previous']['crl'].encode())
        new = x509.load_pem_x509_crl(plan['candidate']['crl'].encode())
        require({entry.serial_number for entry in new}
                == {entry.serial_number for entry in old} | set(plan['grant_plan']['predecessors']), 'UNEXPECTED_REVOCATION_CHANGE')
        return self.validator.validate(candidate,now)

    def recovery_authorization(self, plan, *, durable):
        from expired_recovery import fields, verify
        evidence = plan['expired_recovery']
        fields(evidence, 'bundle accepted_at')
        return verify(base64.b64decode(evidence['bundle'], validate=True), self.validator, plan['operation_id'],
                      int(self.clock()), accepted_at=evidence['accepted_at'] if durable else None)

    def stage(self, operation_id, plan):
        with self.operation.lock():
            owner = self.owner(operation_id)
            require(owner['state'] in ('QUIESCED','STAGED') and self.barrier.stopped(), 'READERS_NOT_QUIESCED')
            require(plan['operation_id'] == operation_id, 'PLAN_BINDING')
            self.validate(plan)
            if 'expired_recovery' in plan:
                authorization = self.recovery_authorization(plan, durable=False)
                require(owner['expected_state'] == authorization.request['expected'][self.role], 'RECOVERY_STALE_APPROVAL')
            require(self.inspect() == owner['expected_state'], 'STALE_NODE_STATE')
            if self.role == 'RU':
                require(owner['expected_state'] == plan['ru_expected'], 'PLAN_BINDING')
                require(read_private(self.state/'prepared-plan.json') == canonical(plan), 'PREPARED_PLAN_MISMATCH')
                files = {'issuer.json':self.read('issuer.json')[0] if plan['candidate']['authority'] == plan['previous']['authority']
                         else canonical(plan['candidate']['authority']),
                         'revocations.pem':plan['candidate']['crl'].encode()}
            else:
                gateway = self.public_gateway()
                require(gateway['profile_sha256'] == plan['nl_profile_sha256']
                        and gateway['certificate'] == plan['previous']['certificate']
                        and gateway['revocations'] == plan['previous']['crl'], 'STALE_NODE_STATE')
                import json
                profile = json.loads(self.read('gateway.json')[0])
                profile.update(authority=self.validator.validate(canonical(plan['candidate']),int(self.clock()))[1]['authority'],
                               certificate=plan['candidate']['certificate'],revocations=plan['candidate']['crl'])
                from control.friends.profile_store import ProfileError, renewal_target
                try:
                    target = renewal_target(self.read('gateway.json')[0], canonical(profile), self.clock(),
                                            expired_predecessor=True)
                except ProfileError as error:
                    raise Rejected(error.code) from None
                files = {'gateway.json':target}
            metadata = {}
            for name,raw in files.items():
                before,info = self.read(name)
                if raw == before:
                    continue
                metadata[name] = dict(info,before=digest(before),after=digest(raw))
                if (self.state/(name+'.before')).exists():
                    require(read_private(self.state/(name+'.before')) == before, 'STAGE_REPLAY_MISMATCH')
                else:
                    atomic(self.state/(name+'.before'),before)
                atomic(self.state/(name+'.staged'),raw)
                self.fault('stage-'+name)
            atomic(self.state/'files.json',canonical(metadata))
            atomic(self.state/'plan.json',canonical(plan))
            self.operation.advance(owner,'STAGED')
            return dict(plan_sha256=digest(canonical(plan)),crl_sha256=digest(plan['candidate']['crl'].encode()),
                        files={name:item['after'] for name,item in metadata.items()})

    def replace(self, name, raw, metadata, *, rollback=False):
        require(self.barrier.stopped(), 'READERS_NOT_QUIESCED')
        current,info = self.read(name)
        require(info == {key:metadata[key] for key in ('uid','gid','mode')}, 'ACTIVE_FILE_METADATA_CHANGED')
        require(digest(current) in (metadata['before'],metadata['after']), 'ACTIVE_FILE_UNEXPECTED')
        if name == 'gateway.json' and self.profile_store is not None:
            self.replace_profile(raw, current, metadata, rollback=rollback)
            return
        temporary = self.state/(name+'.promoting')
        if temporary.exists() or temporary.is_symlink():
            pending,info = pinned(temporary,{os.geteuid(),metadata['uid']})
            require(digest(pending) in (metadata['before'],metadata['after']), 'ORPHAN_STAGING_UNEXPECTED')
            temporary.unlink()
        atomic(temporary,raw)
        descriptor = os.open(temporary,os.O_RDONLY|os.O_NOFOLLOW)
        try:
            os.fchown(descriptor,metadata['uid'],metadata['gid'])
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        self.fault('before-rename-'+name)
        os.replace(temporary,self.live/name)
        for directory in (self.live,self.state):
            descriptor = os.open(directory,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
        self.fault('after-rename-'+name)
        require(self.read(name)[0] == raw, 'PROMOTE_READBACK_MISMATCH')

    def replace_profile(self, raw, current, metadata, *, rollback):
        from control.friends.profile_store import ProfileError, profile_material, renewal_target
        store = self.profile_store
        require(store is not None, 'CANONICAL_PROFILE_REQUIRED')
        try:
            if rollback:
                require(digest(raw) == metadata['before'], 'ROLLBACK_PROFILE_MISMATCH')
                profile_material(raw, self.clock(), expired_predecessor=True)
                store.replace(raw, expected=current, permit=lambda: require(self.barrier.stopped(), 'READERS_NOT_QUIESCED'))
                return
            require(digest(raw) == metadata['after'], 'STAGED_FILE_CHANGED')
            require(renewal_target(current, raw, self.clock(), expired_predecessor=True) == raw, 'STAGED_FILE_CHANGED')
            profile = profile_material(raw, self.clock())[0]
            before_directory = store.locator.directory_port.read(profile, self.clock())
            def ready():
                require(self.barrier.stopped(), 'READERS_NOT_QUIESCED')
                require(renewal_target(current, raw, self.clock(), expired_predecessor=True) == raw, 'STAGED_FILE_CHANGED')
                store.locator.directory_port.after(before_directory, profile, self.clock())
            self.fault('before-rename-gateway.json')
            store.replace(raw, expected=current, permit=ready)
            try:
                self.fault('after-rename-gateway.json')
                store.locator.directory_port.after(before_directory, profile, self.clock())
                require(store.read() == raw, 'PROMOTE_READBACK_MISMATCH')
            except Exception:
                store.replace(current, expected=raw, permit=lambda: require(self.barrier.stopped(), 'READERS_NOT_QUIESCED'))
                raise
        except ProfileError as error:
            raise Rejected(error.code) from None

    def promote(self, operation_id):
        with self.operation.lock(), self.profile_lock():
            owner = self.owner(operation_id)
            require(owner['state'] in ('STAGED','PROMOTING','PROMOTED') and self.barrier.stopped(), 'READERS_NOT_QUIESCED')
            plan = parse(read_private(self.state/'plan.json'))
            _,_,issuer,_,_ = self.validate(plan,recovery=True)
            metadata = parse(read_private(self.state/'files.json'))
            if 'expired_recovery' in plan:
                current = self.inspect()
                require(current.get('policy') == owner['expected_state'].get('policy'), 'RECOVERY_STALE_APPROVAL')
                require(all(current['files'][name] in (item['before'], item['after']) for name,item in metadata.items()),
                        'RECOVERY_STALE_APPROVAL')
                if self.role == 'RU':
                    expected = dict(plan['grant_plan']['before'], restricted_grants=plan['grant_plan']['after_grants'])
                    crl = x509.load_pem_x509_crl(plan['candidate']['crl'].encode())
                    expected['restricted_crl_sequence'] = [dict(singleton=1, sequence=crl.extensions.get_extension_for_class(x509.CRLNumber).value.crl_number)]
                    require(current['database_sha256'] in (plan['grant_plan']['before_sha256'], digest(canonical(expected))),
                            'RECOVERY_STALE_APPROVAL')
            for name in self.names():
                if name not in metadata:
                    require(digest(self.read(name)[0]) == owner['expected_state']['files'][name], 'UNSTAGED_FILE_CHANGED')
            owner = self.operation.advance(owner,'PROMOTING')
            for name,item in metadata.items():
                raw = read_private(self.state/(name+'.staged'))
                require(digest(raw) == item['after'], 'STAGED_FILE_CHANGED')
                self.replace(name,raw,item)
            if self.role == 'RU':
                self.database.apply(plan['grant_plan'],plan['candidate']['crl'].encode(),issuer,int(self.clock()),
                                    readers_quiesced=self.barrier.stopped,
                                    recovery_authorization=self.recovery_authorization(plan, durable=True)
                                    if 'expired_recovery' in plan else None)
                self.fault('after-sqlite-commit')
            self.operation.advance(owner,'PROMOTED')
            return self.readback(operation_id)

    def readback(self, operation_id):
        owner = self.owner(operation_id)
        metadata = parse(read_private(self.state/'files.json'))
        plan = parse(read_private(self.state/'plan.json'))
        self.validate(plan,recovery=True)
        require(all(digest(self.read(name)[0]) == item['after'] for name,item in metadata.items()), 'READBACK_MISMATCH')
        require(all(digest(self.read(name)[0]) == metadata.get(name,{}).get('after',owner['expected_state']['files'][name])
                    for name in self.names()), 'READBACK_MISMATCH')
        if self.policy_paths:
            require(self.inspect()['policy'] == owner['expected_state']['policy'], 'POLICY_CHANGED')
        if self.role == 'RU' and not self.resume_authorized(owner):
            expected = dict(plan['grant_plan']['before'],restricted_grants=plan['grant_plan']['after_grants'])
            crl = x509.load_pem_x509_crl(plan['candidate']['crl'].encode())
            expected['restricted_crl_sequence'] = [dict(singleton=1,sequence=crl.extensions.get_extension_for_class(x509.CRLNumber).value.crl_number)]
            require(self.database.snapshot() == expected, 'DATABASE_READBACK_MISMATCH')
        return dict(plan_sha256=digest(canonical(plan)),crl_sha256=digest(plan['candidate']['crl'].encode()),state='PROMOTED')

    def rollback(self, operation_id):
        with self.operation.lock(), self.profile_lock():
            owner = self.owner(operation_id)
            require(owner['state'] not in ('COMMIT_DECIDED','RESUMED'), 'ROLLBACK_AFTER_COMMIT_FORBIDDEN')
            require(self.barrier.stopped(), 'READERS_NOT_QUIESCED')
            prepared = self.state/'prepared-plan.json'
            staged = self.state/'plan.json'
            require(not any(path.exists() and 'expired_recovery' in parse(read_private(path))
                            for path in (prepared, staged)), 'RECOVERY_ROLLFORWARD_ONLY')
            if not (self.state/'files.json').exists() or not (self.state/'plan.json').exists():
                require(self.inspect() == owner['expected_state'], 'ROLLBACK_READBACK_MISMATCH')
                return self.operation.advance(owner,'ROLLED_BACK')
            plan = parse(read_private(self.state/'plan.json'))
            self.validator.validate(canonical(plan['previous']),int(self.clock()),expired_leaf_predecessor=True)
            metadata = parse(read_private(self.state/'files.json'))
            for name,item in metadata.items():
                raw = read_private(self.state/(name+'.before'))
                require(digest(raw) == item['before'], 'BACKUP_CHANGED')
                self.replace(name,raw,item,rollback=True)
            if self.role == 'RU':
                with self.database.connect(write=True) as database:
                    actual = self.database.snapshot(database)
                    before = plan['grant_plan']['before']
                    candidate_crl = x509.load_pem_x509_crl(plan['candidate']['crl'].encode())
                    candidate_sequence = candidate_crl.extensions.get_extension_for_class(x509.CRLNumber).value.crl_number
                    after = dict(before,restricted_grants=plan['grant_plan']['after_grants'],
                        restricted_crl_sequence=[dict(singleton=1,sequence=candidate_sequence)])
                    require(actual in (before,after), 'ROLLBACK_DATABASE_UNEXPECTED')
                    if actual != before:
                        for row in before['restricted_grants']:
                            database.execute('UPDATE restricted_grants SET revision=?,expires=? WHERE device=?',
                                             (row['revision'],row['expires'],row['device']))
                        database.execute('UPDATE restricted_crl_sequence SET sequence=? WHERE singleton=1',
                                         (before['restricted_crl_sequence'][0]['sequence'],))
                    require(self.database.snapshot(database) == before, 'ROLLBACK_DATABASE_MISMATCH')
            require(self.inspect() == owner['expected_state'], 'ROLLBACK_READBACK_MISMATCH')
            return self.operation.advance(owner,'ROLLED_BACK')

    def commit_decision(self, operation_id, reconciliation):
        with self.operation.lock():
            owner = self.owner(operation_id)
            require(owner['state'] in ('PROMOTED','COMMIT_DECIDED','RESUMED'), 'TRANSACTION_STATE')
            local = self.readback(operation_id)
            require(set(reconciliation) == {'RU','NL'} and all(value == local for value in reconciliation.values()),
                    'RU_NL_RECONCILIATION_FAILED')
            if owner['state'] == 'RESUMED':
                require(parse(read_private(self.state/'reconciliation.json')) == reconciliation, 'RECONCILIATION_CHANGED')
                return owner
            atomic(self.state/'reconciliation.json',canonical(reconciliation))
            return self.operation.advance(owner,'COMMIT_DECIDED')

    def resume(self, operation_id):
        with self.operation.lock():
            owner = self.owner(operation_id)
            require(owner['state'] in ('COMMIT_DECIDED','RESUMED'), 'TRANSACTION_STATE')
            local = self.readback(operation_id)
            require(all(value == local for value in parse(read_private(self.state/'reconciliation.json')).values()),
                    'RU_NL_RECONCILIATION_FAILED')
            if self.role == 'RU':
                accepted = parse(read_private(self.state/'directory-accepted.json'))
                require(digest(pinned(self.live/'directory.json',{os.geteuid()})[0]) == accepted['sha256'], 'DIRECTORY_READBACK_MISMATCH')
            self.barrier.resume(commit_decided=True,equality_verified=True)
            return self.operation.advance(owner,'RESUMED')

    def public_directory(self, operation_id):
        require(self.role == 'NL', 'NODE_ROLE')
        owner = self.owner(operation_id)
        require(owner['state'] in ('RESUMED','ABORTED'), 'TRANSACTION_STATE')
        from control.friends.restricted import directory, clock_nanoseconds, DirectoryValidationError
        previous = parse(read_private(self.state/'directory-before.json'))['sha256']
        stop_at = time.monotonic()+90
        while True:
            raw,_ = self.read_directory()
            profile = self.public_gateway()
            if digest(raw) != previous:
                try:
                    directory(raw,profile['family'],profile['gateway'],now_ns=clock_nanoseconds(self.clock))
                except DirectoryValidationError as error:
                    raise Rejected('DIRECTORY_'+error.predicate.upper()) from None
                return dict(directory=base64.b64encode(raw).decode(),sha256=digest(raw))
            require(time.monotonic() < stop_at, 'NEW_DIRECTORY_NOT_READY')
            time.sleep(.25)

    def publish_directory(self, operation_id, payload):
        require(self.role == 'RU', 'NODE_ROLE')
        with self.operation.lock():
            owner = self.owner(operation_id)
            require(owner['state'] in ('COMMIT_DECIDED','RESUMED','ROLLED_BACK','ABORTED'), 'TRANSACTION_STATE')
            require(set(payload) == {'directory','sha256'}, 'DIRECTORY_RESPONSE_SCHEMA')
            raw = base64.b64decode(payload['directory'],validate=True)
            require(digest(raw) == payload['sha256'], 'DIRECTORY_HASH_MISMATCH')
            from control.friends.restricted import directory, clock_nanoseconds, DirectoryValidationError
            trust,_ = self.validator.delegation_parser(self.public_authority()['authority'],self.validator.anchor,int(self.clock()))
            try:
                directory(raw,trust['family'],trust['gateway'],now_ns=clock_nanoseconds(self.clock))
            except DirectoryValidationError as error:
                raise Rejected('DIRECTORY_'+error.predicate.upper()) from None
            if owner['state'] in ('RESUMED','ABORTED'):
                require(pinned(self.live/'directory.json',{os.geteuid()})[0] == raw, 'DIRECTORY_CHANGED_AFTER_RESUME')
                return dict(result='UNCHANGED',sha256=digest(raw))
            require(self.barrier.stopped(), 'READERS_NOT_QUIESCED')
            path = self.state/'directory.pending'
            atomic(path,raw)
            os.replace(path,self.live/'directory.json')
            descriptor = os.open(self.live,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
            atomic(self.state/'directory-accepted.json',canonical(dict(sha256=digest(raw),operation_id=operation_id)))
            return dict(result='PUBLISHED',sha256=digest(raw))

    def restore(self, operation_id, previous):
        with self.operation.lock():
            owner = self.owner(operation_id)
            self.previous_readback(operation_id)
            _,trust,_,_,_ = self.validator.validate(canonical(previous),int(self.clock()))
            if self.role == 'RU':
                actual = self.public_authority()
                fields = ('authority','crl') if self.resume_authorized(owner) else ('authority','crl','grants')
                require(all(actual[name] == previous[name] for name in fields), 'ROLLBACK_READBACK_MISMATCH')
            else:
                actual = self.public_gateway()
                require(actual['certificate'] == previous['certificate'] and actual['revocations'] == previous['crl']
                        and actual['authority'] == trust['authority'], 'ROLLBACK_READBACK_MISMATCH')
            if self.role == 'RU':
                accepted = parse(read_private(self.state/'directory-accepted.json'))
                require(digest(pinned(self.live/'directory.json',{os.geteuid()})[0]) == accepted['sha256'], 'DIRECTORY_READBACK_MISMATCH')
            self.barrier.resume(commit_decided=True,equality_verified=True)
            return self.operation.advance(owner,'ABORTED')

    def cleanup(self, operation_id):
        with self.operation.lock():
            ledger_path = self.state/'completed.json'
            ledger = parse(read_private(ledger_path)) if ledger_path.exists() else {}
            if not (self.state/'owner.json').exists():
                require(operation_id in ledger, 'TRANSACTION_STATE')
                return dict(result='CLEANED',operation_id=operation_id)
            owner = self.owner(operation_id)
            require(owner['state'] in ('RESUMED','ABORTED','CLEANING'), 'TRANSACTION_STATE')
            archive = self.state/'archive'
            if not archive.exists():
                archive.mkdir(mode=0o700)
            private_directory(archive)
            destination = archive/operation_id
            if not destination.exists():
                destination.mkdir(mode=0o700)
            private_directory(destination)
            if owner['state'] != 'CLEANING':
                if owner['state'] == 'RESUMED':
                    self.readback(operation_id)
                else:
                    self.previous_readback(operation_id)
                names = [path.name for path in self.state.iterdir()
                         if path.name not in ('operation.lock','owner.json','completed.json','archive')]
                metadata = {name:digest(read_private(self.state/name)) for name in names}
                atomic(destination/'archive-manifest.json',canonical(metadata))
                owner = self.operation.advance(owner,'CLEANING')
            metadata = parse(read_private(destination/'archive-manifest.json'))
            for name,expected in metadata.items():
                require('/' not in name and name not in ('.','..'), 'ARCHIVE_PATH')
                source,target = self.state/name,destination/name
                if source.exists():
                    require(digest(read_private(source)) == expected, 'ARCHIVE_SOURCE_CHANGED')
                    require(not target.exists(), 'ARCHIVE_COLLISION')
                    os.replace(source,target)
                require(digest(read_private(target)) == expected, 'ARCHIVE_HASH_MISMATCH')
                self.fault('archive-'+name)
            for directory in (destination,archive,self.state):
                descriptor = os.open(directory,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
                try:
                    os.fsync(descriptor)
                finally:
                    os.close(descriptor)
            limit = 4096 if self.validator.all_activated else 256
            require(len(ledger) < limit or operation_id in ledger, 'OPERATION_HISTORY_CAPACITY')
            ledger[operation_id] = dict(result='CLEANED',manifest_sha256=digest(canonical(metadata)),timestamp=int(self.clock()))
            atomic(ledger_path,canonical(ledger))
            (self.state/'owner.json').unlink()
            descriptor = os.open(self.state,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
            return dict(result='CLEANED',operation_id=operation_id,retention='BOUNDED_256_OPERATIONS_OPERATOR_ARCHIVE_REQUIRED')
