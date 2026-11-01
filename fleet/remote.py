"""Operator-only SSH adapter; no Django SSH and no generic live override."""

import base64
import io
from pathlib import Path
import shlex
import subprocess
import time
import zipfile

from cryptography.hazmat.primitives import serialization

from . import permit, preflight
from .bundle import verify as verify_bundle
from .contracts import canonical, digest, fail, load


def public_hex(key):
    return key.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw).hex()


def build_agent():
    root = Path(__file__).parent
    if not (root/'remote_agent.py').is_file():
        fail('qualified_remote_agent_required')
    members = {str(path.relative_to(root.parent)): path.read_bytes() for path in sorted(root.glob('*.py'))}
    members['__main__.py'] = b'from fleet.remote_agent import main\nmain()\n'
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_STORED) as archive:
        for name, content in sorted(members.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.external_attr = 0o100444 << 16
            archive.writestr(info, content)
    return output.getvalue()


class RemoteInstaller:
    def __init__(self, *, host, user, known_hosts, fingerprint, authorization, permit_key,
                 bundle, bundle_key, runner=subprocess.run, clock=time.time):
        self.agent = build_agent()
        self.permit = authorization
        self.permit_key = permit_key
        self.bundle_key = bundle_key
        self.bundle = Path(bundle)
        self.clock = clock
        self.host = host
        self.fingerprint = fingerprint
        self.manifest, self.contents = verify_bundle(bundle, bundle_key)
        if self.manifest['scope'] != 'rehearsal':
            fail('rehearsal_bundle_required')
        self.authorize('preflight')
        self.ssh = preflight.SSH(host, user, known_hosts, fingerprint, runner=runner)
        self.preflight_at = None

    def authorize(self, action):
        return permit.verify(self.permit, self.permit_key, host=self.host, fingerprint=self.fingerprint,
            bundle_id=self.manifest['bundle_id'], action=action, agent_sha256=digest(self.agent),
            bundle_signer_sha256=digest(bytes.fromhex(public_hex(self.bundle_key))), now=self.clock())

    def preflight(self, instance, ports, *, dry_run=False):
        self.authorize('preflight')
        if dry_run:
            return dict(scope=permit.SCOPE, action='preflight', dry_run=True, remote_writes=0)
        if instance['instance_id'] != self.permit['body']['instance_id'] or instance['ipv4'] != self.host:
            fail('rehearsal_instance_binding')
        started = self.clock()
        report = self.ssh.probe(instance, ports)
        preflight.accept(report, instance)
        if report['cpu'] < 2 or report['ram_mb'] < 1900 or report['disk_mb'] < 18000:
            fail('rehearsal_host_resources')
        self.preflight_at = self.clock()
        return dict(report=report, elapsed_seconds=self.clock()-started, remote_writes=0)

    def execute(self, action, operation_id, parameters=None, *, dry_run=False):
        self.authorize(action)
        operation = dict(operation_id=operation_id, action=action, bundle_id=self.manifest['bundle_id'],
                         parameters={} if parameters is None else parameters)
        permit.replay_binding(None, self.permit, operation)
        if dry_run:
            return dict(scope=permit.SCOPE, action=action, dry_run=True, remote_writes=0)
        if self.preflight_at is None or not 0 <= self.clock()-self.preflight_at <= 300:
            fail('fresh_remote_preflight_required')
        files = {path.name: base64.b64encode(path.read_bytes()).decode() for path in self.bundle.iterdir() if path.is_file()}
        request = dict(permit=self.permit, permit_key=public_hex(self.permit_key), bundle_key=public_hex(self.bundle_key),
                       agent=base64.b64encode(self.agent).decode(), operation=operation, bundle=files, upload_only=True)
        source = Path(__file__).with_name('remote_bootstrap.py').read_text()
        command = 'python3 -I -B -c ' + shlex.quote(source)
        uploaded = self.call(command, request)
        if uploaded != dict(agent_sha256=digest(self.agent), mode='0500', scope=permit.SCOPE):
            fail('remote_upload_readback')
        request['upload_only'] = False
        return self.call(command, request)

    def call(self, command, request):
        try:
            result = self.ssh.runner(self.ssh.argv + [command], input=canonical(request).decode(),
                                     capture_output=True, text=True, timeout=660)
        except (OSError, subprocess.TimeoutExpired):
            fail('remote_transport_failure')
        if result.returncode:
            fail('remote_operation_rejected')
        return load(result.stdout)
