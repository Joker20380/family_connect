"""Stop only this DEB's per-user owner during explicit package removal."""
import os
from pathlib import Path
import pwd
import stat
import subprocess
import sys


def main():
    if os.geteuid() != 0 or sys.argv[1:] != ['remove']:
        raise SystemExit('Explicit package removal required')
    for directory in Path('/run/user').glob('*'):
        if not directory.name.isdecimal() or int(directory.name) == 0:
            continue
        info = directory.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != int(directory.name) or stat.S_IMODE(info.st_mode) != 0o700:
            continue
        if not (directory / 'bus').exists():
            continue
        account = pwd.getpwuid(info.st_uid)
        command = ['/usr/bin/setpriv', '--reuid', str(info.st_uid), '--regid', str(account.pw_gid),
                   '--init-groups', '/usr/bin/systemctl', '--user']
        environment = {'PATH': '/usr/bin:/bin', 'XDG_RUNTIME_DIR': str(directory),
                       'DBUS_SESSION_BUS_ADDRESS': 'unix:path=' + str(directory / 'bus')}
        fragment = subprocess.run(command + ['show', 'family-connect-chat.service', '-p', 'FragmentPath', '--value'],
                                  env=environment, capture_output=True, text=True, timeout=10, check=True).stdout.strip()
        if fragment == '/usr/lib/systemd/user/family-connect-chat.service':
            subprocess.run(command + ['stop', 'family-connect-chat.service'], env=environment, check=True, timeout=50)


if __name__ == '__main__':
    main()
