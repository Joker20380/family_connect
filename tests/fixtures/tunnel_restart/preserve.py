"""Preserve existing diagnostics and bounded read-only runtime evidence."""

import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[3]
WORK = Path(os.environ.get('TUNNEL_RESTART_OUT', ROOT / 'state-client-build/tunnel-restart-20261019'))
PACKAGE = 'com.familyconnect.app.friends'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command, timeout=25):
    return subprocess.check_output(command, stderr=subprocess.PIPE, timeout=timeout, text=True).strip()


def main():
    os.umask(0o077)
    WORK.mkdir(mode=0o700, exist_ok=False)
    source = Path('/home/joker/snap/telegram-desktop/7169/.local/share/TelegramDesktop/tdata/temp_data/FamilyConnect-diagnostics (1) (4).json')
    (WORK / 'owner-export.json').write_bytes(source.read_bytes())
    metadata = run(['adb', 'shell', 'dumpsys', 'package', PACKAGE])
    apk = run(['adb', 'shell', 'pm', 'path', PACKAGE]).removeprefix('package:')
    native = run(['adb', 'shell', 'find', re.search(r'legacyNativeLibraryDir=(\S+)', metadata)[1], '-name', 'libfc_restricted.so'])
    phone = dict(code=int(re.search(r'versionCode=(\d+)', metadata)[1]),
                 apk_sha256=run(['adb', 'shell', 'sha256sum', apk]).split()[0],
                 native_sha256=run(['adb', 'shell', 'sha256sum', native]).split()[0],
                 pid=run(['adb', 'shell', 'pidof', PACKAGE]),
                 uid=re.search(r'userId=(\d+)', metadata)[1])
    for name, args in [('services', ['dumpsys', 'activity', 'services', PACKAGE]),
                       ('exit-info', ['dumpsys', 'activity', 'exit-info', PACKAGE]),
                       ('connectivity', ['dumpsys', 'connectivity']),
                       ('interfaces', ['ip', '-j', 'addr']),
                       ('process', ['cat', '/proc/' + phone['pid'] + '/stat'])]:
        try:
            (WORK / ('android-' + name + '.txt')).write_text(run(['adb', 'shell', *args]))
        except subprocess.CalledProcessError as error:
            (WORK / ('android-' + name + '.error')).write_bytes(error.stderr)
    with (WORK / 'android-logcat.txt').open('x') as output:
        subprocess.run(['adb', 'logcat', '-d', '-t', '2500', '-v', 'epoch', '--pid=' + phone['pid']], stdout=output, stderr=subprocess.PIPE, timeout=25, check=True)
    receipt = dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   checkpoint=run(['git', 'rev-parse', 'HEAD']), phone=phone,
                   files={path.name: dict(sha256=digest(path), bytes=path.stat().st_size)
                          for path in WORK.iterdir() if path.is_file()})
    (WORK / 'preservation.json').write_text(json.dumps(receipt, indent=2))
    export = json.loads((WORK / 'owner-export.json').read_bytes())
    print(json.dumps(dict(receipt=receipt, export_version=export['ring'].get('version_code'),
                          export_state=export['ring'].get('state'))))


if __name__ == '__main__':
    main()
