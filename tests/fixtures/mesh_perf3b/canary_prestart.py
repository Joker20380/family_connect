import json
import os
from pathlib import Path
import shlex
import stat
import subprocess
import sys


PROVIDER = '/opt/apps/family_connect/friends-restricted/provider.env'
REQUIRED = 'YANDEX_TELEMOST_OAUTH_TOKEN'


def validate(manifest, environment, properties, uid, gid, file_info):
    if file_info is None:
        return 'PROVIDER_FILE_MISSING'
    if not stat.S_ISREG(file_info.st_mode) or file_info.st_uid != 0 or stat.S_IMODE(file_info.st_mode) != 0o600:
        return 'PROVIDER_FILE_PERMISSIONS'
    if not environment.get(REQUIRED, '').strip():
        return 'PROVIDER_VARIABLE_EMPTY_OR_ABSENT'
    if uid != manifest['uid'] or gid != manifest['gid']:
        return 'SERVICE_ACCOUNT_MISMATCH'
    if properties.get('EnvironmentFiles') != PROVIDER + ' (ignore_errors=no)':
        return 'ENVIRONMENT_FILE_NOT_WIRED'
    expected = dict(WorkingDirectory=manifest['working_directory'], Restart='no',
                    ReadWritePaths=manifest['working_directory'], ProtectSystem='strict',
                    User=manifest['user'], Group=str(manifest['gid']), UnsetEnvironment='')
    if any(properties.get(key) != value for key, value in expected.items()):
        return 'UNIT_CONFIGURATION_MISMATCH'
    assignments = dict(value.split('=', 1) for value in shlex.split(properties.get('Environment', '')))
    if assignments != manifest['environment']:
        return 'UNIT_ENVIRONMENT_OVERRIDE'
    if any(environment.get(key) != value for key, value in assignments.items()):
        return 'EFFECTIVE_ENVIRONMENT_MISMATCH'
    for key in environment:
        if key.startswith(('FC_', 'TELEMOST_', 'RELIABLESTREAM_')) and key not in assignments:
            return 'UNEXPECTED_TRANSPORT_ENVIRONMENT'
    command = properties.get('ExecStart', '')
    marker = 'argv[]='
    if marker not in command or command.count('path=') != 1:
        return 'EXECSTART_MISMATCH'
    actual = command.split(marker, 1)[1].split(' ;', 1)[0]
    if shlex.split(actual) != manifest['executable_arguments']:
        return 'EXECSTART_MISMATCH'
    return 'PASS'


def main():
    manifest = json.loads(Path(sys.argv[1]).read_bytes())
    names = ['EnvironmentFiles', 'Environment', 'User', 'Group', 'WorkingDirectory',
             'Restart', 'ReadWritePaths', 'ProtectSystem', 'UnsetEnvironment', 'ExecStart']
    raw = subprocess.check_output(['systemctl', 'show', manifest['unit'], '--property=' + ','.join(names)],
                                  text=True, stderr=subprocess.DEVNULL, timeout=10)
    properties = dict(line.split('=', 1) for line in raw.splitlines())
    try:
        info = Path(PROVIDER).lstat()
    except FileNotFoundError:
        info = None
    result = validate(manifest, os.environ, properties, os.getuid(), os.getgid(), info)
    receipt = dict(result=result, unit=manifest['unit'], operation=manifest['operation'],
                   required_names=[REQUIRED], values_recorded=False, provider_requests=0)
    descriptor = os.open(manifest['receipt'], os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, 'w') as handle:
        json.dump(receipt, handle, sort_keys=True)
        handle.flush()
        os.fsync(handle.fileno())
    print(json.dumps(receipt))
    return 0 if result == 'PASS' else 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as failure:
        print(json.dumps(dict(result='VALIDATOR_FAILURE', error_type=type(failure).__name__)))
        sys.exit(1)
