import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

os.umask(0o077)
root = Path('/mnt/data/PycharmProjects/family_connect/state-client-build/owner-disconnections-20261022')
destination = root / ('raw-entry-' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
destination.mkdir(parents=True, exist_ok=False)
serial = '31ce63ba'
package = 'com.familyconnect.app.friends'
records = []


def capture(name, arguments, timeout=30):
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    monotonic = time.monotonic_ns()
    try:
        result = subprocess.run(arguments, capture_output=True, timeout=timeout)
        stdout, stderr, code = result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired as failure:
        stdout, stderr, code = failure.stdout or b'', failure.stderr or b'', 'TIMEOUT'
    for suffix, content in [('', stdout), ('.stderr', stderr)]:
        path = destination / (name + suffix)
        path.write_bytes(content)
        path.chmod(0o400)
    records.append(dict(file=name, argv=arguments, started_utc=started,
                        completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                        start_monotonic_ns=monotonic, end_monotonic_ns=time.monotonic_ns(),
                        returncode=code, bytes=len(stdout), sha256=hashlib.sha256(stdout).hexdigest(),
                        stderr_sha256=hashlib.sha256(stderr).hexdigest()))
    return stdout


def adb(name, *arguments, timeout=30):
    return capture(name, ['adb', '-s', serial, *arguments], timeout)


snapshot = adb('diagnostic.json', 'exec-out', 'content', 'read', '--uri',
               'content://' + package + '.owner.support/snapshot')
adb('clock.txt', 'shell', 'date -u +%Y-%m-%dT%H:%M:%S%z; date +%s; cat /proc/uptime; cat /proc/sys/kernel/random/boot_id')
adb('package.txt', 'shell', 'dumpsys', 'package', package)
adb('logcat-app.txt', 'exec-out', 'logcat', '-b', 'all', '-d', '-v', 'epoch', '--uid=10283', timeout=60)
adb('logcat-system-lifecycle.txt', 'exec-out', 'logcat', '-b', 'main', '-b', 'system', '-b', 'crash', '-d', '-v', 'epoch',
    'ActivityManager:I', 'ActivityTaskManager:I', 'ConnectivityService:I', 'Vpn:I', 'AndroidRuntime:V', 'libc:F', 'DEBUG:F', '*:S', timeout=60)
adb('logcat-buffer-stats.txt', 'shell', 'logcat', '-g')
adb('services.txt', 'shell', 'dumpsys', 'activity', 'services', package)
adb('processes.txt', 'shell', 'ps -A -o USER,PID,PPID,NAME,ETIME; pidof ' + package)
adb('process-exit-info.txt', 'shell', 'dumpsys', 'activity', 'exit-info', package)
adb('connectivity.txt', 'shell', 'dumpsys', 'connectivity')
adb('network.txt', 'shell', 'ip -details link; ip addr; ip rule; ip route show table all; ls -l /dev/tun /dev/net/tun')
adb('power.txt', 'shell', 'dumpsys', 'power')
adb('device.txt', 'shell', 'getprop ro.product.model; getprop ro.build.version.release; getprop ro.build.version.sdk; getprop ro.product.cpu.abilist')
paths = adb('apk-path.txt', 'shell', 'pm', 'path', package).decode().splitlines()
for index, path in enumerate(paths):
    if path.startswith('package:'):
        target = destination / ('installed-' + str(index) + '.apk')
        capture('apk-pull-' + str(index) + '.txt', ['adb', '-s', serial, 'pull', path[8:], str(target)], 120)
        if target.exists():
            records.append(dict(file=target.name, sha256=hashlib.sha256(target.read_bytes()).hexdigest(), bytes=target.stat().st_size))
            target.chmod(0o400)
manifest = destination / 'acquisition-manifest.json'
manifest.write_text(json.dumps(records, indent=2) + '\n')
manifest.chmod(0o400)
print('EVIDENCE_DIRECTORY', destination)
try:
    value = json.loads(snapshot)
    print('JSON_SNAPSHOT_VALID', isinstance(value, dict))
except Exception:
    print('JSON_SNAPSHOT_UNAVAILABLE', 'USB_SUPPORT_CONSENT_REQUIRED' if b'SecurityException' in snapshot else 'INSPECT_ERROR')
print('FILES', len(records), 'MANIFEST_SHA256', hashlib.sha256(manifest.read_bytes()).hexdigest())
