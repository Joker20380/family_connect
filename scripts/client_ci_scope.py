"""Select platform jobs without treating Android-only edits as desktop changes."""
import json
import os
from pathlib import Path
import subprocess


COMMON = ('carrier/', 'clients/shared/', 'control/', 'device_identity/', 'provisioning/',
          'messenger/', 'packaging/', 'scripts/ci_release_fixtures.py', 'VERSION')


def platforms(paths):
    return {
        'android': any(path.startswith(COMMON + ('clients/android/', 'pilot/android-', 'pilot/awg31/',
                                                '.github/workflows/clients.yml')) for path in paths),
        'windows': any(path.startswith(COMMON + ('clients/windows/', 'clients/desktop/', 'pilot/windows-',
                                                'scripts/package_desktop.py', 'scripts/ci_desktop_env.sh')) for path in paths),
        'linux': any(path.startswith(COMMON + ('clients/linux/', 'clients/desktop/', 'scripts/package_linux.py',
                                              'scripts/package_desktop.py', 'scripts/ci_desktop_env.sh')) for path in paths),
    }


def main():
    event = json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text())
    if os.environ['GITHUB_EVENT_NAME'] == 'workflow_dispatch' or os.environ['GITHUB_REF'].startswith('refs/tags/'):
        result = dict.fromkeys(('android', 'windows', 'linux'), True)
    else:
        base = event.get('pull_request', {}).get('base', {}).get('sha', event.get('before'))
        if not base or set(base) == {'0'}:
            result = dict.fromkeys(('android', 'windows', 'linux'), True)
        else:
            paths = subprocess.check_output(['git', 'diff', '--name-only', base, os.environ['GITHUB_SHA']], text=True).splitlines()
            result = platforms(paths)
    with Path(os.environ['GITHUB_OUTPUT']).open('a') as output:
        output.write(''.join(f'{name}={str(enabled).lower()}\n' for name, enabled in result.items()))
    print(json.dumps(result))


if __name__ == '__main__':
    main()
