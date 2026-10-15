import base64
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
                 profile_uid=979, policy_paths=None):
        require(role in ('RU','NL'), 'NODE_ROLE')
        self.role,self.live,self.state,self.validator = role,Path(live),Path(state),validator
        self.database,self.clock,self.fault,self.profile_uid = database,clock,fault,profile_uid
        self.operation = DurableOperation(self.state)
        self.policy_paths = policy_paths or {}
        self.barrier = barrier or SystemdBarrier(role,self.state,clock=clock)
        private_directory(self.state)
        require(self.live.stat().st_dev == self.state.stat().st_dev, 'STAGING_FILESYSTEM_MISMATCH')
        require(not self.live.is_symlink() and self.live.is_dir(), 'LIVE_DIRECTORY_INVALID')

    def names(self):
        return ('issuer.json','revocations.pem') if self.role == 'RU' else ('gateway.json',)

    def read(self, name):
        require(name in (*self.names(),'issuer.key'), 'PATH_NOT_ALLOWLISTED')
        return pinned(self.live/name,{os.geteuid(),self.profile_uid})

    def inspect(self):
        files = {name:digest(self.read(name)[0]) for name in self.names()}
        value = dict(files=files,role=self.role,session_inventory='UNKNOWN')
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
                .not_valid_before(utc(start)).not_valid_after(utc(start+VALIDITY['authority'])))
            for extension in issuer.extensions:
                builder = builder.add_extension(extension.value,extension.critical)
            certificate = builder.sign(signer,None)
            certificate.verify_directly_issued_by(certificate)
            successor = dict(trust,sequence=trust['sequence']+1,issued_at=start,expires_at=start+VALIDITY['authority'],
                             authority=certificate.public_bytes(Encoding.PEM).decode())
            request = dict(schema=1,operation_id=operation_id,previous_authority=envelope,successor_payload=successor,
                           request_expires_at=now+86400)
            atomic(path,canonical(request))
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
        from production_transport import UNITS
        intent = parse(read_private(path))
        require(set(intent) == {'schema','unit','timestamp'} and intent['schema'] == 1
                and intent['unit'] == UNITS[self.role][0], 'RESUME_INTENT_INVALID')
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
                raw,_ = pinned(self.live/'directory.json',{os.geteuid(),self.profile_uid})
                atomic(self.state/'directory-before.json',canonical(dict(sha256=digest(raw))))
            self.barrier.quiesce()
            require(self.inspect() == owner['expected_state'], 'STALE_NODE_STATE')
            return self.operation.advance(owner,'QUIESCED')

    def fence(self, operation_id):
        with self.operation.lock():
            self.owner(operation_id)
            if self.role == 'NL' and not (self.state/'directory-before.json').exists():
                raw,_ = pinned(self.live/'directory.json',{os.geteuid(),self.profile_uid})
                atomic(self.state/'directory-before.json',canonical(dict(sha256=digest(raw))))
            self.barrier.quiesce()
            require(self.barrier.stopped(), 'READERS_NOT_QUIESCED')
            return dict(stopped=True)

    def prepare(self, operation_id, gateway, *, authority_handoff=None):
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
            _,trust,issuer,_,leaf = self.validator.validate(previous,now,expired_leaf_predecessor=True)
            require(gateway['authority'] == trust['authority'] and gateway['revocations'] == previous_crl.decode(), 'RU_NL_MISMATCH')
            require(all(gateway[name] == trust[name] for name in ('family','gateway','minimum_revision')), 'GATEWAY_BINDING')
            signer = load_pem_private_key(self.read('issuer.key')[0],None)
            require(hmac.compare_digest(spki(signer.public_key()),spki(issuer.public_key())), 'ISSUER_SIGNING_KEY_MISMATCH')
            if authority_handoff is not None:
                envelope = verify_handoff(authority_handoff,self.validator,envelope,operation_id,now)
                trust,issuer = self.validator.delegation_parser(envelope,self.validator.anchor,now)
            require(trust['expires_at'] >= now + VALIDITY['leaf'], 'OFFLINE_AUTHORITY_RENEWAL_REQUIRED')
            grant_plan = self.database.plan(issuer,now,readers_quiesced=self.barrier.stopped)
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
            self.validate(plan)
            path = self.state/'prepared-plan.json'
            if path.exists():
                require(read_private(path) == canonical(plan), 'PREPARE_ALREADY_EXISTS')
            else:
                atomic(path,canonical(plan))
            return plan

    def validate(self, plan, *, recovery=False):
        require(set(plan) == {'schema','operation_id','previous','candidate','grant_plan','ru_expected','nl_profile_sha256'}
                and plan['schema'] == 1, 'PLAN_SCHEMA')
        now = int(self.clock())
        previous,candidate = canonical(plan['previous']),canonical(plan['candidate'])
        validation_time = plan['grant_plan']['issued_at'] if recovery else now
        self.validator.transition(previous,candidate,validation_time,revoke=True,expired_leaf_predecessor=True)
        validate_grant_plan(plan['grant_plan'],plan['grant_plan']['issued_at'] if recovery else now)
        require(plan['candidate']['grants'] == plan['grant_plan']['after_grants']
                and plan['previous']['grants'] == plan['grant_plan']['before']['restricted_grants'], 'GRANT_PLAN_MISMATCH')
        old = x509.load_pem_x509_crl(plan['previous']['crl'].encode())
        new = x509.load_pem_x509_crl(plan['candidate']['crl'].encode())
        require({entry.serial_number for entry in new}
                == {entry.serial_number for entry in old} | set(plan['grant_plan']['predecessors']), 'UNEXPECTED_REVOCATION_CHANGE')
        return self.validator.validate(candidate,now)

    def stage(self, operation_id, plan):
        with self.operation.lock():
            owner = self.owner(operation_id)
            require(owner['state'] in ('QUIESCED','STAGED') and self.barrier.stopped(), 'READERS_NOT_QUIESCED')
            require(plan['operation_id'] == operation_id, 'PLAN_BINDING')
            self.validate(plan)
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
                files = {'gateway.json':canonical(profile)}
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

    def replace(self, name, raw, metadata):
        require(self.barrier.stopped(), 'READERS_NOT_QUIESCED')
        current,info = self.read(name)
        require(info == {key:metadata[key] for key in ('uid','gid','mode')}, 'ACTIVE_FILE_METADATA_CHANGED')
        require(digest(current) in (metadata['before'],metadata['after']), 'ACTIVE_FILE_UNEXPECTED')
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

    def promote(self, operation_id):
        with self.operation.lock():
            owner = self.owner(operation_id)
            require(owner['state'] in ('STAGED','PROMOTING','PROMOTED') and self.barrier.stopped(), 'READERS_NOT_QUIESCED')
            plan = parse(read_private(self.state/'plan.json'))
            _,_,issuer,_,_ = self.validate(plan,recovery=True)
            metadata = parse(read_private(self.state/'files.json'))
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
                                    readers_quiesced=self.barrier.stopped)
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
        with self.operation.lock():
            owner = self.owner(operation_id)
            require(owner['state'] not in ('COMMIT_DECIDED','RESUMED'), 'ROLLBACK_AFTER_COMMIT_FORBIDDEN')
            require(self.barrier.stopped(), 'READERS_NOT_QUIESCED')
            if not (self.state/'files.json').exists() or not (self.state/'plan.json').exists():
                require(self.inspect() == owner['expected_state'], 'ROLLBACK_READBACK_MISMATCH')
                return self.operation.advance(owner,'ROLLED_BACK')
            plan = parse(read_private(self.state/'plan.json'))
            self.validator.validate(canonical(plan['previous']),int(self.clock()),expired_leaf_predecessor=True)
            metadata = parse(read_private(self.state/'files.json'))
            for name,item in metadata.items():
                raw = read_private(self.state/(name+'.before'))
                require(digest(raw) == item['before'], 'BACKUP_CHANGED')
                self.replace(name,raw,item)
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
            raw,_ = pinned(self.live/'directory.json',{os.geteuid(),self.profile_uid})
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
            require(len(ledger) < 256 or operation_id in ledger, 'OPERATION_HISTORY_CAPACITY')
            ledger[operation_id] = dict(result='CLEANED',manifest_sha256=digest(canonical(metadata)),timestamp=int(self.clock()))
            atomic(ledger_path,canonical(ledger))
            (self.state/'owner.json').unlink()
            descriptor = os.open(self.state,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
            return dict(result='CLEANED',operation_id=operation_id,retention='BOUNDED_256_OPERATIONS_OPERATOR_ARCHIVE_REQUIRED')
