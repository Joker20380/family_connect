"""Owned network-none panel PG and native console probe; never original mounts."""
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import tempfile
import time
import uuid

from scripts import control_ha_owner_runtime as owner
from scripts.control_ha_import import encoded
from scripts.control_ha_rehearsal import private_file, require

LABEL = 'family-connect.ha-owner-joint'
PROBE_TIMEOUT = 900


class OwnerLab:
    def __init__(self, root):
        self.root = Path(root)
        require(self.root.is_absolute() and ',' not in str(self.root) and '..' not in self.root.parts and
                self.root.resolve().is_relative_to(Path(tempfile.gettempdir()).resolve())
                and all(not parent.is_symlink() for parent in (self.root, *self.root.parents)), 'PRIVATE_LAB_ROOT')
        self.root.mkdir(mode=0o700)
        self.token = uuid.uuid4().hex
        self.name = 'fc-ha-owner-joint-' + self.token
        self.volume = self.name + '-data'
        self.container = None
        self.password, self.secret = secrets.token_hex(32), secrets.token_hex(32)
        self.environment = {name:value for name,value in os.environ.items() if not name.startswith(('DOCKER_', 'PG'))}

    def docker(self, *arguments, data=None, timeout=180):
        result = subprocess.run(['docker', '--host', 'unix:///var/run/docker.sock', *arguments],
                                input=data, capture_output=True, timeout=timeout, env=self.environment)
        if result.returncode:
            private_file(self.root / ('error-' + uuid.uuid4().hex + '.log'), result.stderr)
            raise ValueError('OWNED_OWNER_LAB_COMMAND_REFUSED')
        return result.stdout

    def owned(self):
        info = json.loads(self.docker('inspect', self.container))[0]
        require(info['Image'] == owner.IMAGES['postgres'] and info['Config']['Labels'].get(LABEL) == self.token
                and info['HostConfig']['NetworkMode'] == 'none', 'OWNER_LAB_OWNERSHIP')

    def __enter__(self):
        try:
            self.docker('volume', 'create', '--label', LABEL+'='+self.token, self.volume)
            private_file(self.root/'postgres.env', ('POSTGRES_DB=fc_control_plane\nPOSTGRES_USER=fc_control_plane\n'
                'POSTGRES_PASSWORD='+self.password+'\n').encode())
            self.container = self.docker('run', '-d', '--pull=never', '--name', self.name, '--label', LABEL+'='+self.token,
                '--network', 'none', '--read-only', '--user', '70:70', '--cap-drop', 'ALL', '--security-opt',
                'no-new-privileges', '--memory', '512m', '--cpus', '1', '--tmpfs', '/tmp', '--tmpfs',
                '/var/run/postgresql', '--mount', 'type=volume,source='+self.volume+',target=/var/lib/postgresql/data',
                '--env-file', str(self.root/'postgres.env'), owner.IMAGES['postgres']).decode().strip()
            self.owned()
            private_file(self.root/'container.id',self.container.encode())
            for attempt in range(80):
                result = subprocess.run(['docker','--host','unix:///var/run/docker.sock','exec',self.container,
                    'pg_isready','-h','127.0.0.1','-U','fc_control_plane','-d','fc_control_plane'],capture_output=True,
                    env=self.environment,timeout=5)
                if result.returncode == 0: return self
                time.sleep(.25)
            raise ValueError('OWNER_LAB_NOT_READY')
        except BaseException:
            self.__exit__(None,None,None)
            raise

    def restore(self, backup, *, replace=False):
        self.owned()
        if replace:
            for statement in ('DROP DATABASE fc_control_plane WITH (FORCE)', 'CREATE DATABASE fc_control_plane'):
                self.docker('exec',self.container,'psql','-U','fc_control_plane','-d','postgres','-v','ON_ERROR_STOP=1',
                            '-c',statement)
        self.docker('exec','-i',self.container,'pg_restore','-U','fc_control_plane','-d','fc_control_plane',
                    '--no-owner','--no-acl','--exit-on-error','--single-transaction',data=backup)

    def dump(self, name):
        self.owned()
        raw = self.docker('exec',self.container,'pg_dump','-U','fc_control_plane','-d','fc_control_plane',
                          '--format=custom','--no-owner','--no-acl')
        private_file(self.root/name,raw)
        return raw

    def probe(self, config, aliases, envelope, label):
        self.owned()
        require(re.fullmatch('[a-z][a-z0-9-]{0,63}',label) and config['mode'] in
                ('baseline','ingest','readback','stale'), 'PROBE_SCOPE')
        destination = self.root/label
        destination.mkdir(mode=0o700)
        private_file(destination/'probe.json',encoded(config | dict(password=self.password,secret=self.secret)))
        private_file(destination/'panel-aliases.json',aliases)
        private_file(destination/'envelope.json',encoded(envelope))
        name = 'fc-ha-owner-probe-' + uuid.uuid4().hex
        try:
            result = self.docker('run','--rm','-i','--pull=never','--name',name,'--label',LABEL+'='+self.token,
                '--network','container:'+self.container,'--read-only','--cap-drop','ALL','--security-opt',
                'no-new-privileges','--pids-limit','128','--memory','256m','--user',f'{os.getuid()}:{os.getgid()}',
                '--mount',f'type=bind,source={destination},destination=/app/control_plane/.local,readonly',
                '--workdir','/app/control_plane','--env','PYTHONDONTWRITEBYTECODE=1','--env',
                'PYTHONPATH=/app:/app/control_plane','--entrypoint','python',owner.IMAGES['console'],'-B','-',
                data=Path(__file__).with_name('control_ha_owner_joint_probe.py').read_bytes(),timeout=PROBE_TIMEOUT)
            require(len(result)<32768,'PROBE_RESPONSE_BOUNDS')
            receipt = owner.document(result)
            private_file(destination/'receipt.json',result)
            return receipt
        finally:
            found = self.docker('ps','-aq','--filter','name=^/'+name+'$').decode().strip()
            if found:
                info = json.loads(self.docker('inspect',found))[0]
                require(info['Image']==owner.IMAGES['console'] and info['Config']['Labels'].get(LABEL)==self.token,
                        'PROBE_CLEANUP_OWNERSHIP')
                self.docker('rm','-f',found)

    def __exit__(self,*args):
        if self.container is None:
            found = self.docker('ps','-aq','--no-trunc','--filter','name=^/'+self.name+'$').decode().strip()
            if found: self.container = found
        if self.container:
            self.owned()
            self.docker('rm','-f',self.container)
        volumes = self.docker('volume','ls','-q','--filter','label='+LABEL+'='+self.token).decode().splitlines()
        require(all(name==self.volume for name in volumes),'VOLUME_OWNERSHIP')
        for name in volumes: self.docker('volume','rm',name)
