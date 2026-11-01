"""Verified disposable gateway installer, local health, rollback and owned cleanup."""

import os
import base64
import fcntl
from pathlib import Path
import pwd
import re
import shutil
import stat
import subprocess
import tempfile
import time

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey

from .bundle import safe_path
from .contracts import canonical, digest, exact, fail, load
from .enrollment import generate_node_key, proof_payload, verify_receipt
from .installer import fsync_directory
from .materials import generate_key, public_hex
from .private_files import checked, read_private, remove_private, write_private
from .rehearsal_materials import MaterialStore, possession_payload, verify_enrollment
from .rehearsal_templates import CURRENT, SYSCTL, TABLE, UNIT_NAMES, nftables, units
from .role_config import ADDRESS, MTU, PORTS, awg_config, mesh_config, publisher_config, ready_check, tcp_config


class Executor:
    def run(self, argv, *, input=None, check=True):
        try:
            result = subprocess.run(argv, input=input, capture_output=True, timeout=90)
        except (OSError, subprocess.TimeoutExpired):
            fail('role_command_unavailable')
        if check and result.returncode:
            fail('role_command_failed')
        return result


class Runtime:
    def __init__(self, *, manifest, contents, authorization, authority, directory,
                 root=Path('/'), executor=None, clock=time.time):
        self.manifest, self.contents = manifest, contents
        self.permit, self.authority = authorization['body'], authority
        self.root = Path(root).absolute()
        self.directory = Path(directory)
        self.clock = clock
        self.executor = executor or Executor()
        if self.root == Path('/') and os.geteuid() != 0:
            fail('root_operation_boundary')
        if self.root != Path('/') and executor is None:
            fail('isolated_executor_required')
        self.releases = self.path('/opt/family-connect/releases')
        self.current = self.path(CURRENT)
        self.configuration = self.path('/etc/family-connect/rehearsal')
        self.run_directory = self.path('/run/family-connect-rehearsal')/self.permit['instance_id']
        self.sysctl = self.path('/etc/sysctl.d/90-family-connect-rehearsal.conf')
        self.uid = 0 if self.root == Path('/') else os.getuid()
        self.root_gid = 0 if self.root == Path('/') else os.getgid()

    def path(self, absolute):
        return self.root/absolute.lstrip('/')

    def mkdir(self, path, mode=0o700, gid=None):
        if path.exists() or path.is_symlink():
            checked(path, directory=True, owner=self.uid)
            if stat.S_IMODE(path.stat().st_mode) != mode:
                fail('owned_directory_mode')
            return
        checked(path.parent, directory=True)
        path.mkdir(mode=mode)
        os.chown(path, self.uid, self.root_gid if gid is None else gid)
        path.chmod(mode)
        fsync_directory(path.parent)

    def write(self, path, content, mode=0o600, gid=None, replace=False):
        write_private(path, content, mode=mode, uid=self.uid,
                      gid=self.root_gid if gid is None else gid, replace=replace)

    def command(self, *argv, input=None, check=True):
        return self.executor.run(list(argv), input=input, check=check)

    def service_account(self):
        if self.root != Path('/'):
            return os.getuid(), os.getgid()
        try:
            account = pwd.getpwnam('fc-rehearsal')
        except KeyError:
            self.command('useradd','--system','--user-group','--home-dir','/nonexistent',
                         '--shell','/usr/sbin/nologin','fc-rehearsal')
            account = pwd.getpwnam('fc-rehearsal')
        if account.pw_uid == 0 or account.pw_gid == 0 or account.pw_shell != '/usr/sbin/nologin':
            fail('rehearsal_account_conflict')
        return account.pw_uid, account.pw_gid

    def enrolled_identity(self):
        receipt = load(read_private(self.directory/'enrollment.json', owner=self.uid))
        binding = receipt['body']['binding']
        if (any(binding[name] != self.permit[name] for name in ('instance_id','logical_gateway','ipv4','provider','region'))
                or binding['bundle_id'] not in (self.permit['bundle_a'], self.permit['bundle_b'])):
            fail('runtime_enrollment_binding')
        return verify_receipt(receipt, self.authority, binding, scope='rehearsal')

    def material_store(self):
        self.enrolled_identity()
        receipt = load(read_private(self.directory/'enrollment.json', owner=self.uid))
        key = X25519PrivateKey.from_private_bytes(read_private(self.directory/'material.key', owner=self.uid))
        binding = {name:self.permit[name] for name in ('instance_id','logical_gateway','ipv4','bundle_a','bundle_b')}
        binding.update(enrollment_public_key=receipt['body']['public_key'], material_public_key=public_hex(key.public_key()))
        enrollment = load(read_private(self.directory/'material-enrollment.json', owner=self.uid))
        service_uid, service_gid = self.service_account()
        return MaterialStore(self.directory, binding, self.authority, key, enrollment,
                             service_gid=service_gid, uid=self.uid, custody_gid=self.root_gid)

    def enroll(self, parameters):
        if parameters.get('phase')=='prove':
            exact(parameters,('phase','challenge','expires_at'))
            if type(parameters['expires_at']) is not int or not self.clock()<parameters['expires_at']<=self.clock()+600:
                fail('enrollment_challenge_expired')
            if (self.directory/'enrollment.json').exists():
                fail('already_enrolled')
            if not (self.directory/'identity.key').exists():
                generate_node_key(self.directory/'identity.key')
            if not (self.directory/'material.key').exists():
                generate_key(self.directory/'material.key')
            identity=Ed25519PrivateKey.from_private_bytes(read_private(self.directory/'identity.key',owner=self.uid))
            material=X25519PrivateKey.from_private_bytes(read_private(self.directory/'material.key',owner=self.uid))
            public=public_hex(identity.public_key())
            binding={name:self.permit[name] for name in ('instance_id','logical_gateway','ipv4','provider','region')}
            binding.update(bundle_id=self.manifest['bundle_id'],roles=self.manifest['roles'])
            material_binding={name:self.permit[name] for name in ('instance_id','logical_gateway','ipv4','bundle_a','bundle_b')}
            material_binding.update(enrollment_public_key=public,material_public_key=public_hex(material.public_key()))
            if not (self.directory/'boot-before').exists():
                self.write(self.directory/'boot-before',self.path('/proc/sys/kernel/random/boot_id').read_bytes())
            return dict(binding=binding,public_key=public,material_binding=material_binding,
                identity_proof=base64.b64encode(identity.sign(proof_payload(binding,parameters['challenge'],public,'rehearsal'))).decode(),
                material_proof=base64.b64encode(identity.sign(possession_payload(material_binding,parameters['challenge']))).decode())
        exact(parameters,('phase','enrollment','material_enrollment'))
        if parameters['phase']!='commit':
            fail('enrollment_phase')
        receipt=parameters['enrollment']
        verify_receipt(receipt,self.authority,receipt['body']['binding'],scope='rehearsal')
        identity=Ed25519PrivateKey.from_private_bytes(read_private(self.directory/'identity.key',owner=self.uid))
        material=X25519PrivateKey.from_private_bytes(read_private(self.directory/'material.key',owner=self.uid))
        binding={name:self.permit[name] for name in ('instance_id','logical_gateway','ipv4','bundle_a','bundle_b')}
        binding.update(enrollment_public_key=public_hex(identity.public_key()),material_public_key=public_hex(material.public_key()))
        if receipt['body']['public_key']!=binding['enrollment_public_key']:
            fail('enrollment_node_key_binding')
        verify_enrollment(parameters['material_enrollment'],binding,self.authority)
        for name,value in (('enrollment.json',receipt),('material-enrollment.json',parameters['material_enrollment'])):
            path=self.directory/name
            if path.exists():
                if read_private(path,owner=self.uid)!=canonical(value):
                    fail('enrollment_existing_conflict')
            else:
                self.write(path,canonical(value))
        self.enrolled_identity()
        return dict(instance_id=self.permit['instance_id'],public_key=binding['enrollment_public_key'],
                    material_public_key=binding['material_public_key'],enrollment_sha256=digest(canonical(receipt)))

    def verify_release(self, bundle_id):
        release = checked(self.releases/bundle_id, directory=True, owner=self.uid)
        if stat.S_IMODE(release.stat().st_mode)!=0o555:
            fail('release_directory_mode')
        manifest = load(read_private(release/'release.json', modes=(0o444,), owner=self.uid))
        if manifest['bundle_id'] != bundle_id:
            fail('release_binding')
        expected = {'release.json'} | {entry['path'] for entry in manifest['members']}
        actual = set()
        for path in release.rglob('*'):
            checked(path, directory=path.is_dir(), owner=self.uid)
            if path.is_dir() and stat.S_IMODE(path.stat().st_mode)!=0o555:
                fail('release_directory_mode')
            if path.is_file():
                actual.add(str(path.relative_to(release)))
        if actual != expected:
            fail('release_member_inventory')
        for entry in manifest['members']:
            raw = read_private(release/entry['path'], modes=(entry['mode'],), owner=self.uid, limit=64*1024*1024)
            if len(raw) != entry['size'] or digest(raw) != entry['sha256']:
                fail('release_member_hash')
        return manifest

    def stage(self, bundle_id):
        if bundle_id != self.manifest['bundle_id'] or bundle_id not in (self.permit['bundle_a'],self.permit['bundle_b']):
            fail('stage_bundle_binding')
        for absolute in ('/opt/family-connect','/opt/family-connect/releases','/etc/family-connect',
                         '/etc/family-connect/rehearsal','/run/family-connect-rehearsal'):
            path = self.path(absolute)
            self.mkdir(path, mode=0o755)
        lock = self.configuration/'owner.lock'
        if not lock.exists():
            try:
                self.write(lock,b'')
            except FileExistsError:
                pass
        read_private(lock,owner=self.uid,limit=0)
        descriptor=os.open(lock,os.O_RDONLY|os.O_NOFOLLOW)
        try:
            fcntl.flock(descriptor,fcntl.LOCK_EX)
            self.stage_owned(bundle_id)
        finally:
            os.close(descriptor)

    def retired_predecessor(self, previous):
        exact(previous,('instance_id','identity'))
        if (not re.fullmatch(r'fleet-rehearsal-[a-z0-9-]+',str(previous['instance_id']))
                or previous['instance_id']==self.permit['instance_id']):
            fail('rehearsal_install_owner_conflict')
        directory=checked(self.directory.parent/previous['instance_id'],directory=True,owner=self.uid)
        enrollment=load(read_private(directory/'enrollment.json',owner=self.uid))
        binding=enrollment['body']['binding']
        identity=verify_receipt(enrollment,self.authority,binding,scope='rehearsal')
        if (identity!=previous['identity'] or binding['instance_id']!=previous['instance_id']
                or any(binding[name]!=self.permit[name] for name in ('ipv4','logical_gateway','provider','region'))):
            fail('retired_predecessor_binding')
        state=load(read_private(directory/'operations/state.json',owner=self.uid))
        if (state.get('state')!='RETIRED' or state.get('fenced') is not False
                or state.get('instance_id')!=previous['instance_id'] or state.get('identity')!=identity):
            fail('retired_predecessor_state')
        journals=[load(read_private(path,owner=self.uid)) for path in (directory/'operations').glob('*.json') if path.name!='state.json']
        if not any(record.get('action')=='retire' and record.get('result')=='PASS'
                   and record.get('state_after')=='RETIRED' and record.get('instance_id')==previous['instance_id'] for record in journals):
            fail('retired_predecessor_receipt')
        custody=load(read_private(directory/'final-custody.json',owner=self.uid))
        if (custody['body'].get('scope')!='DISPOSABLE_FLEET_REHEARSAL_FINAL_CUSTODY'
                or custody['body'].get('instance_id')!=previous['instance_id']):
            fail('retired_predecessor_custody')
        try:
            Ed25519PublicKey.from_public_bytes(bytes.fromhex(enrollment['body']['public_key'])).verify(
                base64.b64decode(custody['signature'],validate=True),canonical(custody['body']))
        except (ValueError,InvalidSignature):
            fail('retired_predecessor_signature')
        resources=[directory/name for name in ('identity.key','material.key','slots','slots.pending')]
        resources += [self.current,self.sysctl,self.path('/run/family-connect-rehearsal')/previous['instance_id']]
        resources += [self.path('/etc/systemd/system')/name for name in
                      (*['fc-rehearsal-'+role+'.service' for role in UNIT_NAMES],'fc-rehearsal-expiry.timer','fc-rehearsal-expiry.service')]
        if (any(path.exists() or path.is_symlink() for path in resources)
                or set(path.name for path in self.configuration.iterdir())-{'owner.json','owner.lock'}
                or self.command('nft','-s','list','table','inet',TABLE,check=False).returncode==0
                or self.command('ip','link','show','dev','fcrh0',check=False).returncode==0):
            fail('retired_predecessor_resources')
        evidence=canonical(dict(previous=previous,enrollment_sha256=digest(canonical(enrollment)),
                                state_sha256=digest(canonical(state)),custody_sha256=digest(canonical(custody))))
        receipt=self.directory/'predecessor.json'
        if receipt.exists():
            if read_private(receipt,owner=self.uid)!=evidence:
                fail('retired_predecessor_changed')
        else:
            self.write(receipt,evidence)

    def stage_owned(self, bundle_id):
        owner=self.configuration/'owner.json'
        owner_binding=canonical(dict(instance_id=self.permit['instance_id'],identity=self.enrolled_identity()))
        if owner.exists():
            if read_private(owner,owner=self.uid)!=owner_binding:
                self.retired_predecessor(load(read_private(owner,owner=self.uid)))
                self.write(owner,owner_binding,replace=True)
        elif any(self.releases.iterdir()):
            fail('rehearsal_unowned_releases')
        else:
            self.write(owner,owner_binding)
        release = self.releases/bundle_id
        if release.exists():
            if self.verify_release(bundle_id) != self.manifest:
                fail('stage_existing_conflict')
            return
        pending = self.releases/(bundle_id+'.pending')
        if pending.exists():
            fail('interrupted_stage_requires_reconciliation')
        self.mkdir(pending)
        for member in self.manifest['members']:
            relative = safe_path(member['path'])
            content = self.contents[relative]
            if len(content) != member['size'] or digest(content) != member['sha256']:
                fail('stage_member_hash')
            target = pending/relative
            for parent in reversed(target.parent.relative_to(pending).parents):
                if str(parent) != '.':
                    self.mkdir(pending/parent, 0o755)
            if target.parent != pending:
                self.mkdir(target.parent, 0o755)
            self.write(target, content, member['mode'])
        self.write(pending/'release.json', canonical(self.manifest), 0o444)
        for path in sorted(pending.rglob('*'), key=lambda value:len(value.parts), reverse=True):
            if path.is_dir():
                path.chmod(0o555)
                fsync_directory(path)
        pending.chmod(0o555)
        fsync_directory(pending)
        os.rename(pending, release)
        fsync_directory(self.releases)
        self.verify_release(bundle_id)

    def configure(self, bundle_id):
        self.verify_release(bundle_id)
        self.material_store()
        service_uid, service_gid = self.service_account()
        slots = self.directory/'slots'
        receipt = load(read_private(slots/'receipt.json', owner=self.uid))
        if not self.clock() < receipt['expires_at'] <= self.permit['expires_at']:
            fail('configuration_material_expired')
        raw = {}
        for name, expected in receipt['slots'].items():
            raw[name] = read_private(slots/name, modes=(0o600,0o640), owner=self.uid)
            if digest(raw[name]) != expected:
                fail('configuration_material_hash')
        awg, awg_binding = awg_config(raw['awg-material'])
        tcp = tcp_config(raw['tcp-material'])
        mesh, mesh_binding = mesh_config(raw['mesh-material'], instance_id=self.permit['instance_id'],
                                         now=self.clock(), permit_expires_at=self.permit['expires_at'])
        publisher = publisher_config(raw['publisher-material'])
        config = self.configuration/bundle_id
        if config.exists():
            self.verify_configuration(bundle_id)
            return
        route = load(self.command('ip','-j','route','show','default').stdout)
        if len(route) != 1:
            fail('rehearsal_default_route')
        firewall = nftables(route[0]['dev'])
        lifetime = min(900,int(min(receipt['expires_at'],mesh_binding['expires_at'])-self.clock())-240)
        if lifetime<300:
            fail('configuration_start_window')
        templates = units(bundle_id, self.permit['instance_id'], lifetime, self.permit['expires_at'])
        self.mkdir(config, 0o750, service_gid)
        self.mkdir(config/'profile', 0o750, service_gid)
        self.mkdir(config/'units', 0o755)
        files = {'awg.conf':(awg,0o600), 'tcp.json':(tcp,0o640), 'profile/gateway.json':(mesh,0o640),
                 'publisher.env':(publisher,0o600), 'firewall.nft':(firewall,0o600)}
        for name, content in templates.items():
            files['units/'+name] = (content,0o444)
        metadata = dict(schema=1, instance_id=self.permit['instance_id'], bundle_id=bundle_id,
            runtime_lifetime_seconds=lifetime,
            material_expires_at=min(receipt['expires_at'],mesh_binding['expires_at']), revision=load(self.contents['metadata/revision.json'])['revision'],
            awg=awg_binding, mesh=mesh_binding, files={name:digest(content) for name,(content,mode) in files.items()},
            modes={name:mode for name,(content,mode) in files.items()}, service_gid=service_gid)
        for name, (content, mode) in files.items():
            self.write(config/name,content,mode,service_gid if mode==0o640 else None)
        self.write(config/'metadata.json',canonical(metadata),0o644)
        self.command(str(self.releases/bundle_id/'bin/xray'),'run','-test','-config',str(config/'tcp.json'))
        self.command('nft','-c','-f',str(config/'firewall.nft'))
        self.verify_units(bundle_id, templates)
        self.write(config/'validated.json',canonical(dict(bundle_id=bundle_id,metadata_sha256=digest(canonical(metadata)))))
        if not self.run_directory.exists():
            self.mkdir(self.run_directory,0o700)
            os.chown(self.run_directory,service_uid,service_gid)
        fsync_directory(config)

    def verify_units(self, bundle_id, templates):
        with tempfile.TemporaryDirectory(prefix='unit-check-',dir=self.directory) as temporary:
            preview=Path(temporary)
            for name,content in templates.items():
                self.write(preview/name,content.replace(CURRENT.encode(),str(self.releases/bundle_id).encode()),0o444)
            self.command('systemd-analyze','verify',*[str(preview/name) for name in templates])

    def verify_configuration(self, bundle_id):
        config = self.configuration/bundle_id
        validated = load(read_private(config/'validated.json',owner=self.uid))
        raw = read_private(config/'metadata.json',modes=(0o644,),owner=self.uid)
        metadata = load(raw)
        if validated != dict(bundle_id=bundle_id, metadata_sha256=digest(raw)) or metadata['instance_id'] != self.permit['instance_id']:
            fail('configuration_binding')
        if not self.clock() < metadata['material_expires_at']:
            fail('configuration_expired')
        for name, expected in metadata['files'].items():
            safe_path(name)
            mode=metadata['modes'][name]
            content = read_private(config/name,modes=(mode,),owner=self.uid)
            group=metadata['service_gid'] if mode==0o640 else self.root_gid
            if digest(content) != expected or (config/name).stat().st_gid!=group:
                fail('configuration_drift')
        profile=load(read_private(config/'profile/gateway.json',modes=(0o640,),owner=self.uid))
        unused,binding=mesh_config(canonical(dict(scope='DISPOSABLE_FLEET_REHEARSAL',instance_id=self.permit['instance_id'],credentials=profile)),
                                  instance_id=self.permit['instance_id'],now=self.clock(),permit_expires_at=self.permit['expires_at'])
        if binding!=metadata['mesh']:
            fail('configuration_mesh_binding')
        return metadata

    def pointer(self):
        if not self.current.is_symlink():
            if self.current.exists():
                fail('activation_pointer_conflict')
            return None
        target = os.readlink(self.current)
        if not re.fullmatch(r'releases/gw-[0-9a-f]{32}',target):
            fail('activation_pointer_path')
        return target.split('/')[-1]

    def firewall(self, content):
        existing = self.command('nft','-s','list','table','inet',TABLE,check=False)
        transaction = (b'delete table inet family_connect_rehearsal\n' if existing.returncode==0 else b'') + content
        self.command('nft','-c','-f','-',input=transaction)
        self.command('nft','-f','-',input=transaction)

    def switch(self, bundle_id):
        previous = self.pointer()
        if bundle_id is None:
            owned=self.owned_units()
            if owned:
                self.command('systemctl','disable','--now',*owned,check=False)
            if self.current.is_symlink():
                self.current.unlink()
                fsync_directory(self.current.parent)
            if (self.directory/'network-before.json').exists():
                self.firewall(b'')
            self.restore_sysctl()
            return
        self.verify_release(bundle_id)
        self.verify_configuration(bundle_id)
        baseline = self.directory/'network-before.json'
        if not baseline.exists():
            if self.sysctl.exists() or self.sysctl.is_symlink():
                fail('sysctl_preexisting_conflict')
            existing = self.command('nft','-s','list','table','inet',TABLE,check=False)
            if existing.returncode == 0:
                fail('firewall_preexisting_conflict')
            forwarding=self.command('sysctl','-n','net.ipv4.ip_forward').stdout.decode().strip()
            if forwarding not in ('0','1'):
                fail('sysctl_baseline')
            self.write(baseline,canonical(dict(ip_forward=forwarding)))
        config = self.configuration/bundle_id
        for source in sorted((config/'units').iterdir()):
            target=self.path('/etc/systemd/system')/source.name
            if (target.exists() or target.is_symlink()) and previous is None:
                fail('unit_preexisting_conflict')
        if previous:
            self.owned_units()
        predecessor=self.directory/'network-predecessor.json'
        saved=load(read_private(predecessor,owner=self.uid)) if predecessor.exists() else None
        prior_table=self.command('nft','-s','list','table','inet',TABLE,check=False)
        desired=(config/'firewall.nft').read_bytes()
        if saved and saved['bundle_id']==bundle_id:
            desired=saved['table'].encode()
        self.write(predecessor,canonical(dict(bundle_id=previous,table=prior_table.stdout.decode() if prior_table.returncode==0 else '')),
                   replace=predecessor.exists())
        for source in sorted((config/'units').iterdir()):
            unit = source.name
            target = self.path('/etc/systemd/system')/unit
            self.write(target,(config/'units'/unit).read_bytes(),0o644,replace=target.exists())
        if not self.sysctl.exists():
            self.write(self.sysctl,SYSCTL,0o644)
        elif read_private(self.sysctl,modes=(0o644,),owner=self.uid) != SYSCTL:
            fail('sysctl_drift')
        self.command('sysctl','-p',str(self.sysctl))
        self.firewall(desired)
        applied=self.directory/('network-'+bundle_id+'.json')
        self.write(applied,canonical(dict(sha256=digest(self.command('nft','-s','list','table','inet',TABLE).stdout))),replace=applied.exists())
        pending = self.current.with_name('current.pending')
        if pending.exists() or pending.is_symlink():
            fail('activation_interrupted')
        os.symlink('releases/'+bundle_id,pending)
        os.replace(pending,self.current)
        fsync_directory(self.current.parent)
        self.command('systemctl','daemon-reload')

    def start(self, bundle_id):
        if self.pointer() != bundle_id:
            fail('start_pointer_binding')
        self.verify_configuration(bundle_id)
        if self.command('ip','link','show','dev','fcrh0',check=False).returncode==0:
            fail('awg_interface_preexisting')
        for name in ('ready.json','ready.json.lock'):
            path=self.run_directory/name
            if path.exists() or path.is_symlink():
                remove_private(path,owner=self.service_account()[0])
        self.command('systemctl','enable',*['fc-rehearsal-'+name+'.service' for name in UNIT_NAMES],'fc-rehearsal-expiry.timer')
        self.command('systemctl','start','fc-rehearsal-expiry.timer')
        self.command('systemctl','start',*['fc-rehearsal-'+name+'.service' for name in UNIT_NAMES])

    def owned_units(self):
        owned=[]
        names=[*['fc-rehearsal-'+name+'.service' for name in reversed(UNIT_NAMES)],
               'fc-rehearsal-expiry.timer','fc-rehearsal-expiry.service']
        for unit in names:
            installed=self.path('/etc/systemd/system')/unit
            if not installed.exists() and not installed.is_symlink():
                continue
            observed=read_private(installed,modes=(0o644,),owner=self.uid)
            candidates=[self.configuration/bundle/'units'/unit for bundle in (self.permit['bundle_a'],self.permit['bundle_b'])]
            if not any(path.exists() and read_private(path,modes=(0o444,),owner=self.uid)==observed for path in candidates):
                fail('stop_unowned_unit')
            owned.append(unit)
        return owned

    def stop(self):
        self.cancel_reboot()
        owned=[name for name in self.owned_units() if name!='fc-rehearsal-expiry.service']
        if owned:
            result=self.command('systemctl','stop',*owned,check=False)
            if result.returncode and self.command('systemctl','is-active','--quiet',*owned,check=False).returncode==0:
                fail('role_stop_failed')

    def accept(self, bundle_id, fresh=True):
        if self.pointer() != bundle_id or fresh is not True:
            fail('health_current_binding')
        manifest = self.verify_release(bundle_id)
        config = self.verify_configuration(bundle_id)
        states = {}
        listeners = self.command('ss','-H','-lntup').stdout.decode()
        for name in UNIT_NAMES:
            result = self.command('systemctl','show','fc-rehearsal-'+name+'.service',
                                  '--property=ActiveState,SubState,NRestarts,MainPID').stdout.decode()
            values = dict(line.split('=',1) for line in result.splitlines() if '=' in line)
            if values.get('ActiveState') != 'active' or int(values.get('NRestarts','99')) > 2:
                fail('role_service_unhealthy')
            if name in PORTS:
                process = int(values.get('MainPID','0'))
                if process < 1 or not any(':'+str(PORTS[name])+' ' in line and 'pid='+str(process)+',' in line for line in listeners.splitlines()):
                    fail('role_listener_owner')
                if name in ('awg','tcp','mesh'):
                    binary = {'awg':'amneziawg-go','tcp':'xray','mesh':'gateway'}[name]
                    expected = next(member['sha256'] for member in manifest['members'] if member['path']=='bin/'+binary)
                    if digest(self.path('/proc/'+str(process)+'/exe').read_bytes()) != expected:
                        fail('role_process_hash')
                    unit=(self.configuration/bundle_id/'units'/('fc-rehearsal-'+name+'.service')).read_text()
                    expected_argv=next(line.removeprefix('ExecStart=').split() for line in unit.splitlines() if line.startswith('ExecStart='))
                    actual_argv=self.path('/proc/'+str(process)+'/cmdline').read_bytes().rstrip(b'\x00').decode().split('\x00')
                    if actual_argv!=expected_argv:
                        fail('role_process_argv')
            states[name] = dict(state='active',restarts=int(values['NRestarts']))
        address = load(self.command('ip','-j','address','show','dev','fcrh0').stdout)
        if (len(address) != 1 or address[0]['mtu'] != MTU
                or not any(item.get('local')=='10.203.217.1' and item.get('prefixlen')==30 for item in address[0]['addr_info'])):
            fail('awg_interface_health')
        peers = self.command(str(self.current/'bin/awg'),'show','fcrh0','peers').stdout.decode().split()
        import base64
        if len(peers)!=1 or digest(base64.b64decode(peers[0],validate=True)) != config['awg']['peer_sha256']:
            fail('awg_peer_inventory')
        public=self.command(str(self.current/'bin/awg'),'show','fcrh0','public-key').stdout.strip()
        if digest(base64.b64decode(public,validate=True))!=config['awg']['server_sha256']:
            fail('awg_server_identity')
        if self.command(str(self.current/'bin/awg'),'show','fcrh0','listen-port').stdout.strip()!=b'51827':
            fail('awg_listen_port')
        allowed=self.command(str(self.current/'bin/awg'),'show','fcrh0','allowed-ips').stdout.decode().split()
        if allowed!=[peers[0],'10.203.217.2/32']:
            fail('awg_allowed_peer_inventory')
        if self.command('sysctl','-n','net.ipv4.ip_forward').stdout.strip()!=b'1':
            fail('forwarding_health')
        table = self.command('nft','-s','list','table','inet',TABLE).stdout
        applied=load(read_private(self.directory/('network-'+bundle_id+'.json'),owner=self.uid))
        if digest(table)!=applied['sha256'] or read_private(self.sysctl,modes=(0o644,),owner=self.uid)!=SYSCTL:
            fail('firewall_health')
        ready = ready_check(read_private(self.run_directory/'ready.json',owner=self.service_account()[0]),
                            config['mesh'],now=self.clock(),permit_expires_at=self.permit['expires_at'])
        import urllib.request
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open('http://127.0.0.1:19727/status',timeout=5) as response:
            observations=load(response.read(65537))
        if (observations.get('instance_id')!=self.permit['instance_id'] or observations.get('bundle_id')!=bundle_id
                or observations.get('material_expires_at')!=config['material_expires_at']
                or not 0<=self.clock()-observations.get('observed_at',0)<=15):
            fail('monitoring_health')
        return dict(scope='LOCAL_NODE_HEALTH_ONLY',instance_id=self.permit['instance_id'],bundle_id=bundle_id,
                    configuration_sha256=digest(canonical(config)),services=states,ready=ready,
                    observations=observations,firewall_sha256=applied['sha256'],external_acceptance='NOT_ASSERTED_BY_NODE')

    def reboot_check(self, bundle_id, identity):
        if self.enrolled_identity()!=identity or self.pointer()!=bundle_id:
            fail('reboot_identity_or_bundle')
        previous = read_private(self.directory/'boot-before',owner=self.uid)
        if previous == self.path('/proc/sys/kernel/random/boot_id').read_bytes():
            fail('reboot_not_observed')
        request=self.directory/'reboot-request.json'
        if request.exists() or request.is_symlink():
            value=load(read_private(request,owner=self.uid))
            current=self.path('/proc/sys/kernel/random/boot_id').read_bytes()
            if (value['bundle_id']!=bundle_id or value['identity']!=identity or value['status'] not in ('PENDING','COMPLETED')
                    or value['boot_sha256']==digest(current)):
                fail('reboot_request_binding')
            value.update(status='COMPLETED',observed_boot_sha256=digest(current))
            self.write(request,canonical(value),replace=True)

    def request_reboot(self, bundle_id, identity):
        if self.enrolled_identity()!=identity or self.pointer()!=bundle_id:
            fail('reboot_identity_or_bundle')
        metadata=self.verify_configuration(bundle_id)
        if self.clock()+1200>=metadata['material_expires_at']:
            fail('reboot_material_window')
        request=self.directory/'reboot-request.json'
        if request.exists() or request.is_symlink():
            fail('reboot_already_requested')
        unit='fc-rehearsal-reboot-'+self.permit['instance_id']
        for suffix in ('.timer','.service'):
            state=self.command('systemctl','show',unit+suffix,'--property=LoadState','--value',check=False)
            if state.stdout.strip()!=b'not-found':
                fail('reboot_unit_conflict')
        self.command('/usr/sbin/sshd','-t')
        boot=self.path('/proc/sys/kernel/random/boot_id').read_bytes()
        self.write(request,canonical(dict(bundle_id=bundle_id,identity=identity,boot_sha256=digest(boot),status='PENDING')))
        self.command('systemd-run','--unit='+unit,'--on-active=10s','--timer-property=AccuracySec=1s',
                     '--property=Type=oneshot','/usr/bin/systemctl','reboot')
        return dict(reboot='SCHEDULED',bundle_id=bundle_id,boot_sha256=digest(boot))

    def cancel_reboot(self):
        request=self.directory/'reboot-request.json'
        if not request.exists() and not request.is_symlink():
            return
        value=load(read_private(request,owner=self.uid))
        if value['status']!='PENDING' or value['boot_sha256']!=digest(self.path('/proc/sys/kernel/random/boot_id').read_bytes()):
            return
        unit='fc-rehearsal-reboot-'+self.permit['instance_id']
        self.command('systemctl','stop',unit+'.timer',unit+'.service',check=False)
        if self.command('systemctl','is-active','--quiet',unit+'.timer',unit+'.service',check=False).returncode==0:
            fail('reboot_cancellation_failed')
        value['status']='CANCELLED'
        self.write(request,canonical(value),replace=True)

    def drain(self):
        self.stop()

    def restore_sysctl(self):
        if not self.sysctl.exists() or not (self.directory/'network-before.json').exists():
            return
        if read_private(self.sysctl,modes=(0o644,),owner=self.uid)!=SYSCTL:
            fail('retire_sysctl_drift')
        baseline=load(read_private(self.directory/'network-before.json',owner=self.uid))
        if baseline.get('ip_forward') not in ('0','1'):
            fail('sysctl_baseline')
        if self.command('sysctl','-n','net.ipv4.ip_forward').stdout.strip()!=b'1':
            fail('retire_forwarding_drift')
        self.sysctl.unlink()
        fsync_directory(self.sysctl.parent)
        self.command('sysctl','-w','net.ipv4.ip_forward='+baseline['ip_forward'])

    def retire(self):
        self.stop()
        plans=[]
        unit_names=[*['fc-rehearsal-'+name+'.service' for name in UNIT_NAMES],
                    'fc-rehearsal-expiry.timer','fc-rehearsal-expiry.service']
        allowed={'metadata.json','validated.json','awg.conf','tcp.json','publisher.env','firewall.nft',
                 'profile/gateway.json',*['units/'+name for name in unit_names]}
        for bundle_id in (self.permit['bundle_a'],self.permit['bundle_b']):
            config=self.configuration/bundle_id
            if not config.exists():
                continue
            checked(config,directory=True,owner=self.uid)
            files=[]
            for path in config.rglob('*'):
                checked(path,directory=path.is_dir(),owner=self.uid)
                relative=str(path.relative_to(config))
                if path.is_dir():
                    if relative not in ('profile','units'):
                        fail('retire_unowned_config_directory')
                elif relative not in allowed:
                    fail('retire_unowned_config_file')
                else:
                    files.append(path)
            plans.append((config,files))
        current = self.pointer()
        if current:
            for source in (self.configuration/current/'units').iterdir():
                target=self.path('/etc/systemd/system')/source.name
                if read_private(target,modes=(0o644,),owner=self.uid)!=source.read_bytes():
                    fail('retire_unit_drift')
            self.command('systemctl','disable','--now','fc-rehearsal-expiry.timer',
                         *['fc-rehearsal-'+name+'.service' for name in UNIT_NAMES])
        custody=dict(scope='DISPOSABLE_FLEET_REHEARSAL_FINAL_CUSTODY',instance_id=self.permit['instance_id'],
                     actual_bundle=current,disposition='SECRET_ERASURE_PENDING')
        if (self.directory/'identity.key').exists():
            identity=Ed25519PrivateKey.from_private_bytes(read_private(self.directory/'identity.key',owner=self.uid))
            custody=dict(body=custody,signature=base64.b64encode(identity.sign(canonical(custody))).decode())
        final_custody=self.directory/'final-custody.json'
        if not final_custody.exists():
            self.write(final_custody,canonical(custody))
        for name in ('slots','slots.pending'):
            directory=self.directory/name
            if not directory.exists():
                continue
            checked(directory,directory=True,owner=self.uid)
            from .materials import SLOTS
            if set(path.name for path in directory.iterdir())-{*SLOTS,'receipt.json'}:
                fail('retire_unowned_material_file')
            for path in directory.iterdir():
                remove_private(path,owner=self.uid)
            directory.rmdir()
            fsync_directory(directory.parent)
        if (self.directory/'network-before.json').exists():
            self.firewall(b'')
        self.restore_sysctl()
        for config,files in plans:
            for path in files:
                remove_private(path,owner=self.uid)
            for name in ('profile','units'):
                if (config/name).exists():
                    (config/name).rmdir()
            config.rmdir()
        for name in unit_names:
            path = self.path('/etc/systemd/system')/name
            if path.exists():
                remove_private(path,owner=self.uid)
        self.switch(None)
        self.command('systemctl','daemon-reload')
        if current and self.command('ip','link','show','dev','fcrh0',check=False).returncode==0:
            fail('retire_interface_still_present')
        if self.run_directory.exists():
            checked(self.run_directory,directory=True,owner=self.service_account()[0])
            if set(path.name for path in self.run_directory.iterdir())-{'ready.json','ready.json.lock'}:
                fail('retire_runtime_unowned_file')
            for path in self.run_directory.iterdir():
                remove_private(path,owner=self.service_account()[0])
            self.run_directory.rmdir()
            fsync_directory(self.run_directory.parent)
        for name in ('material.key','identity.key'):
            path = self.directory/name
            if path.exists():
                remove_private(path,owner=self.uid)
