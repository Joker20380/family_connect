"""Fixed-route read-only snapshot and existing bounded renewal dispatch."""
import base64
from dataclasses import dataclass
import os
from pathlib import Path
import resource
import stat
import subprocess
import sys
import tempfile
import time

from . import profile_store as store

CONFIGURATION_PATH = Path('/etc/fc-profile-snapshot.json')
SNAPSHOT_REQUEST = dict(schema=1, operation='READ_ONLY_SECURITY_SNAPSHOT')
PROFILE_FIELDS = ('authority', 'certificate', 'revocations', 'family', 'gateway', 'minimum_revision', 'minimum_crl')


@dataclass(frozen=True, repr=False)
class Configuration:
    locator: store.Locator
    helper: Path
    helper_sha256: str
    helper_metadata: dict

    @classmethod
    def load(cls):
        path = CONFIGURATION_PATH
        info = path.lstat()
        store.require(info.st_uid == 0 and stat.S_IMODE(info.st_mode) in (0o600, 0o640), 'SNAPSHOT_CONFIG_INVALID')
        value = store.parse(store.read_regular(path, store.metadata(info), 8192), 8192)
        store.require(type(value) is dict and set(value) == {'schema', 'profile_locator', 'profile_locator_sha256',
            'renewal_helper', 'renewal_helper_sha256', 'renewal_helper_metadata'} and
            type(value['schema']) is int and value['schema'] == 1, 'SNAPSHOT_CONFIG_INVALID')
        locator_path = Path(value['profile_locator'])
        raw = store.read_regular(locator_path, store.metadata(locator_path.lstat()), 16384)
        store.require(store.digest(raw) == value['profile_locator_sha256'], 'PROFILE_LOCATOR_CHANGED')
        locator = store.Locator.load(locator_path)
        helper = Path(value['renewal_helper'])
        store.absolute(helper)
        expected = value['renewal_helper_metadata']
        store.require(type(expected) is dict and set(expected) == {'uid', 'gid', 'mode'} and
                      type(expected['uid']) is int and expected['uid'] == 0 and type(expected['gid']) is int and
                      expected['gid'] >= 0 and type(expected['mode']) is int and expected['mode'] in (0o750, 0o755),
                      'SNAPSHOT_CONFIG_INVALID')
        result = cls(locator, helper, value['renewal_helper_sha256'], expected)
        result.validate_helper()
        return result

    def validate_helper(self):
        raw = store.read_regular(self.helper, self.helper_metadata, 65536,
                                 publisher_parent=self.locator.directory_port.publisher_parent)
        store.require(store.digest(raw) == self.helper_sha256, 'RENEWAL_HELPER_CHANGED')


def snapshot(locator, request, *, now=None):
    store.require(len(request) <= 20000, 'INPUT_TOO_LARGE')
    value = store.parse(request, 20000)
    store.require(value == SNAPSHOT_REQUEST and type(value['schema']) is int, 'MAINTENANCE_TRANSACTION_REQUIRED')
    locator.validate_reader()
    raw = store.read_regular(locator.profile, locator.profile_metadata, 49152)
    instant = time.time() if now is None else now
    profile = store.profile_material(raw, instant)[0]
    directory_raw, _ = locator.directory_port.snapshot(profile, instant)
    projection = {name: profile[name] for name in PROFILE_FIELDS}
    store.require(store.read_regular(locator.profile, locator.profile_metadata, 49152) == raw, 'PROFILE_CHANGED_DURING_READ')
    return store.encode(dict(schema=1, profile=projection, directory=base64.b64encode(directory_raw).decode()))


def dispatch(config, request, *, now=None, run=subprocess.run):
    value = store.parse(request, 1048576)
    if value == SNAPSHOT_REQUEST and type(value['schema']) is int:
        return 0, snapshot(config.locator, request, now=now)
    store.require(type(value) is dict and set(value) == {'schema', 'operation', 'request'} and
                  type(value['schema']) is int and value['schema'] == 1 and
                  value['operation'] == 'CREDENTIAL_RENEWAL_RPC' and type(value['request']) is dict,
                  'MAINTENANCE_TRANSACTION_REQUIRED')
    config.validate_helper()
    with tempfile.TemporaryFile() as output:
        def bounded():
            resource.setrlimit(resource.RLIMIT_FSIZE, (1048576, 1048576))
        result = run(['/usr/bin/sudo', '-n', '--', str(config.helper)], input=store.encode(value['request']),
                     stdout=output, stderr=subprocess.DEVNULL, timeout=120, preexec_fn=bounded,
                     env={'PATH': '/usr/bin:/bin', 'LANG': 'C'})
        output.seek(0)
        response = output.read(1048577)
    store.require(len(response) <= 1048576, 'OUTPUT_TOO_LARGE')
    return result.returncode, response


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ['--help']:
        print('Fixed canonical profile snapshot; existing renewal RPC only; no path or action overrides.')
        return 0
    try:
        store.require(not args and os.environ.get('SSH_ORIGINAL_COMMAND') == 'restricted-sync', 'INVALID_REQUEST')
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        config = Configuration.load()
        code, response = dispatch(config, sys.stdin.buffer.read(1048577))
        sys.stdout.buffer.write(response)
        return code
    except Exception:
        sys.stderr.write('Restricted snapshot route rejected\n')
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
