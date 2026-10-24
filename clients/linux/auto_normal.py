"""Single AWG/TCP attempts using the installed helpers, under the Auto guard."""
import copy
import json
import os
from pathlib import Path
import secrets
import signal
import subprocess
import time

from auto_guard import candidate
from auto_policy import Failure, require
from mesh_system import ENV, private_read, private_write
from profile_config import parse, parse_tcp, MAX_PROFILE

WORKER = Path('/usr/local/lib/family-connect-mesh/auto_normal_worker.py')


def unlink_durable(path):
    path.unlink()
    descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


class HelperRunner:
    def __init__(self, guard):
        self.guard = guard

    def __call__(self, operation, profile, context):
        context.check()
        self.guard._owned()
        require(operation in ('install', 'up', 'down', 'forget', 'health'))
        require(isinstance(profile, str) and len(profile.encode()) <= MAX_PROFILE)
        payload = json.dumps(dict(schema=1, operation=operation, profile=profile), separators=(',', ':')).encode()
        process = subprocess.Popen(['/usr/bin/python3', '-I', str(WORKER), str(self.guard.lock)],
            stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            env=ENV, close_fds=True, pass_fds=(self.guard.lock,), start_new_session=True)
        try:
            while True:
                context.check()
                try:
                    process.communicate(payload, timeout=min(.1, max(.001, context.deadline-time.monotonic())))
                    break
                except subprocess.TimeoutExpired:
                    payload = None
            context.check()
            if process.returncode:
                raise Failure('NETWORK' if operation in ('up', 'health') and process.returncode == 2 else 'INTERNAL')
        finally:
            payload = None
            if process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                try:
                    process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    process.wait(timeout=2)
            process.stdin.close()


class NormalCandidate:
    def __init__(self, guard, runner=None):
        self.guard = guard
        self.runner = runner or HelperRunner(guard)
        self.path = guard.directory / 'normal.json'
        self.record, self.profile = None, None
        self.index = 0

    def prepare(self, configuration, kind, context):
        context.check()
        self.guard._owned()
        require(self.guard.record['current']['mode'] == 'blocked' and self.guard.record['pending'] is None)
        require(self.record is None and not os.path.lexists(self.path))
        require(kind in ('awg', 'tcp'))
        profile = getattr(configuration, kind)
        if kind == 'awg':
            fields = parse(profile, allow_awg=True, allow_awg31=True)
            endpoint, port = fields['Peer']['Endpoint'].rsplit(':', 1)
        else:
            fields = parse_tcp(profile)
            endpoint, port = fields['server'], fields['port']
        selected = candidate(kind, 'fc'+kind+secrets.token_hex(4), endpoint, int(port))
        record = dict(schema=1, uid=self.guard.uid, generation=self.guard.generation, selected=selected)
        private_write(self.path, record)
        require(private_read(self.path) == record)
        self.record, self.profile = record, profile
        context.check()
        return copy.deepcopy(selected)

    def open(self, context):
        context.check()
        require(self.record is not None and self.profile is not None)
        require(private_read(self.path) == self.record)
        require(self.guard.record['current']['mode'] == 'probe' and
                self.guard.record['current']['selected'] == self.record['selected'])
        self.runner('install', self.profile, context)
        self.profile = None
        self.runner('up', '', context)
        context.check()
        links = [link for link in self.guard.system.links() if link.get('ifname') == self.record['selected']['interface']]
        require(len(links) == 1 and type(links[0].get('ifindex')) is int and links[0]['ifindex'] > 0)
        require('UP' in links[0].get('flags', []) and
                links[0].get('linkinfo', {}).get('info_kind') in ('tun', 'wireguard'))
        self.index = links[0]['ifindex']
        return self.index, False

    def health(self, context):
        require(self.record is not None and self.index > 0)
        self.guard.snapshot()
        self.runner('health', '', context)
        return True

    def close(self, context):
        self.profile = None
        self.guard._owned()
        require(self.guard.record['current']['mode'] == 'blocked')
        if self.record is None:
            try:
                self.record = private_read(self.path)
            except FileNotFoundError:
                return
        require(self.record == private_read(self.path) and self.record['uid'] == self.guard.uid and
                self.record['generation'] == self.guard.generation)
        self.runner('down', '', context)
        self.runner('forget', '', context)
        require(not any(link.get('ifname') == self.record['selected']['interface'] for link in self.guard.system.links()))
        unlink_durable(self.path)
        self.record, self.index = None, 0

    def release(self, context):
        context.check()
        require(self.record is None and not os.path.lexists(self.path))
        self.profile = None
