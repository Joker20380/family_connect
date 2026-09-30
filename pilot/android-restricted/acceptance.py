"""Bounded EU-6 physical acceptance; never forwards Android traffic through ADB/SSH."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shlex
import subprocess
import time
import xml.etree.ElementTree as ET

HOST = 'root@186.246.45.246'
SSH = ['ssh', '-T', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10']
PACKAGE = 'com.familyconnect.app.eu6'


def run(command, **options):
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            timeout=options.pop('timeout', 30), **options)
    if result.returncode:
        labels = {'install', 'uninstall', 'am', 'start', 'uiautomator', 'dump', 'cat', 'run-as', 'force-stop', 'getprop'}
        operation = ' '.join(part for part in command if part in labels) or Path(command[0]).name
        raise RuntimeError('bounded command failed (' + operation + '); details redacted')
    return result.stdout


def rows(raw):
    if len(raw) > 4 * 1024 * 1024:
        raise RuntimeError('evidence bound exceeded')
    return [json.loads(line) for line in raw.decode().splitlines() if line.strip()]


def stages(samples):
    return [name for sample in samples for name in (sample.get('events') or [])]


def vpn_routes(raw):
    for line in raw.splitlines():
        if 'NetworkAgentInfo{' not in line or 'ni{VPN CONNECTED' not in line:
            continue
        if 'sessionId=Family restricted diagnostic' not in line:
            continue
        return {'active': True, 'ipv4_default': '0.0.0.0/0' in line, 'ipv6_default': '::/0' in line,
                'family_dns': 'DnsAddresses: [ /10.79.0.1 ]' in line,
                'not_bypassable': 'bypassable=false' in line, 'all_uids': 'Uids: <{0-99999}>' in line}
    return {'active': False}


def controlled_page(text, host):
    if host not in text or 'ERR_' in text:
        return False
    return any(phrase in text for phrase in ('Example Domain',
               'This domain is for use in documentation examples',
               'Este dominio está destinado al uso en ejemplos de documentación'))


def screen_ready(policy, power):
    return 'mIsShowing=false' in policy and 'mWakefulness=Awake' in power


def validate(prepared, recovered, gateway, browser, probes, failed, duration):
    if 'bootstrap_cache_stored' not in stages(prepared):
        raise RuntimeError('cache preparation absent')
    required = ['bootstrap_normal_control_unavailable', 'bootstrap_cache_loaded', 'bootstrap_carrier_connected',
                'bootstrap_family_auth', 'bootstrap_descriptor_received',
                'bootstrap_closed_before_dedicated', 'dedicated_data_ready', 'vpn_packet_ready']
    sequence = stages(recovered)
    if any(sequence.count(name) != 1 for name in required):
        raise RuntimeError('missing/duplicate restricted lifecycle stage')
    if [sequence.index(name) for name in required] != sorted(sequence.index(name) for name in required):
        raise RuntimeError('unsafe VPN ordering')
    if 'bootstrap_cache_stored' in sequence:
        raise RuntimeError('cache refreshed while restricted')
    server_events = [item.get('event') for item in gateway]
    server_required = ['bootstrap_seed_ready', 'bootstrap_family_auth', 'CREATING', 'CREATED',
                       'GATEWAY_JOINING', 'READY', 'CLIENT_ISSUED', 'bootstrap_handoff', 'family_auth', 'ACTIVE',
                       'dedicated_resources_closed']
    if any(server_events.count(name) != 1 for name in server_required):
        raise RuntimeError('broker/gateway proof incomplete')
    positions = [server_events.index(name) for name in server_required]
    if positions != sorted(positions):
        raise RuntimeError('descriptor issued before gateway READY')
    if len(browser) < 2 or not all(item['controlled_content'] and item['vpn_active'] for item in browser):
        raise RuntimeError('ordinary browser proof absent')
    packet = [sample['packet'] for sample in recovered if 'packet' in sample]
    if not packet or max(item['dns'] for item in packet) < 1 or max(item['tcp_peak'] for item in packet) < 3:
        raise RuntimeError('Family DNS/concurrent flow proof absent')
    for item in packet:
        mux, resources = item['mux'], item['resources']
        if (item['tcp_peak'] > 32 or item['peak'] > 48 or mux['MaxActiveStreams'] > 32
                or mux['ReceiveHighWater'] > 65536 or mux['SendHighWater'] > 16384
                or mux['RetainedHighWater'] > 6 * 1024 * 1024
                or resources['carrier_send_queue'] > 256 or resources['carrier_receive_queue'] > 16):
            raise RuntimeError('native resource bound exceeded')
    if not probes.get('vpn_active') or not probes.get('nxdomain') or not probes.get('ipv6_failed_closed'):
        raise RuntimeError('ordinary app probe failed')
    https = probes.get('https', [])
    if len(https) != 2 or not all(item.get('status') == 200 and item.get('tls_verified') for item in https):
        raise RuntimeError('ordinary Android HTTPS verification absent')
    if max(item['udp_denied'] for item in packet) < 1 or max(item['ipv6_denied'] for item in packet) < 1:
        raise RuntimeError('unsupported packet rejection absent')
    if not failed.get('vpn_active') or not failed.get('session_failed') or not failed.get('ordinary_tcp_failed') or not failed.get('owner_reports_unavailable'):
        raise RuntimeError('failure leaked or was not proven')
    if duration < 540:
        raise RuntimeError('sustained smoke too short')
    if not any(item.get('event') == 'bootstrap_seed_ready' for item in gateway):
        raise RuntimeError('real bootstrap seed absent')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--adb', required=True)
    parser.add_argument('--binary', type=Path, required=True)
    parser.add_argument('--apk', type=Path, required=True)
    parser.add_argument('--family-dir', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--seconds', type=int, default=540)
    args = parser.parse_args()
    token = os.environ.get('YANDEX_TELEMOST_OAUTH_TOKEN', '')
    if not token or len(token) > 4096 or any(character in token for character in '\r\n\0'):
        raise RuntimeError('provider credential unavailable; redacted')
    if os.environ.get('FC_TELEMOST_ROOM') or not 30 <= args.seconds <= 540:
        raise RuntimeError('manual room or unbounded duration rejected')

    def adb(*command, **options):
        return run([args.adb, *command], **options)

    def shell(command):
        return adb('shell', '-T', 'sh', '-c', shlex.quote(command))

    def private(command, **options):
        return adb('shell', '-T', 'run-as', PACKAGE, 'sh', '-c', shlex.quote(command), **options)

    def start(mode, *extras):
        result = adb('shell', 'am', 'start', '-W', '-n', PACKAGE + '/com.familyconnect.app.RestrictedDiagnosticActivity', '--es', 'mode', mode, *extras)
        if b'Error:' in result or b'Error type' in result:
            raise RuntimeError('diagnostic Activity did not start')

    def ui():
        path = '/data/local/tmp/fc-eu6-ui.xml'
        try:
            adb('shell', 'uiautomator', 'dump', path, timeout=20)
            raw = adb('shell', 'cat', path).decode(errors='replace')
        finally:
            adb('shell', 'rm', '-f', path)
        begin = raw.find('<?xml')
        end = raw.rfind('</hierarchy>')
        if begin < 0 or end < 0:
            return []
        return list(ET.fromstring(raw[begin:end + len('</hierarchy>')]).iter('node'))

    def consent():
        for node in ui():
            if node.get('resource-id') == 'android:id/button1' and node.get('text', '').lower() in ('ok', 'ок'):
                bounds = [int(value) for value in re.findall(r'\d+', node.get('bounds', ''))]
                if len(bounds) == 4:
                    adb('shell', 'input', 'tap', str((bounds[0]+bounds[2])//2), str((bounds[1]+bounds[3])//2))
                    return

    def vpn():
        raw = adb('shell', 'dumpsys', 'connectivity').decode(errors='replace')
        return vpn_routes(raw)['active']

    def battery():
        raw = adb('shell', 'dumpsys', 'battery').decode(errors='replace')
        return {name: int(match.group(1)) for name in ('level', 'temperature', 'status')
                if (match := re.search(r'^\s*'+name+r': (\d+)\s*$', raw, re.M))}

    def evidence(name):
        raw = private('head -c 1048577 files/restricted-evidence.jsonl 2>/dev/null || true')
        if token.encode() in raw or b'telemost.yandex.ru/j/' in raw or b'PRIVATE KEY' in raw:
            raise RuntimeError('sensitive evidence rejected')
        samples = rows(raw)
        (args.out / (name + '.jsonl')).write_bytes(raw)
        return samples

    def wait_state(target, name, limit=210):
        deadline = time.monotonic() + limit
        while time.monotonic() < deadline:
            samples = evidence(name)
            if any(sample.get('state') == target for sample in samples):
                return samples
            if any(sample.get('state') == 3 for sample in samples):
                raise RuntimeError('restricted native startup failed')
            time.sleep(1)
        raise RuntimeError('restricted startup timeout')

    def browser_visit(host):
        adb('shell', 'am', 'start', '-a', 'android.intent.action.VIEW', '-d',
            'https://' + host + '/?fc6=' + secrets.token_hex(4), '-p', 'com.android.chrome')
        deadline = time.monotonic() + 35
        while True:
            time.sleep(3)
            nodes = ui()
            text = ' '.join(node.get('text', '') + ' ' + node.get('content-desc', '') for node in nodes)
            if controlled_page(text, host) or 'ERR_' in text or time.monotonic() >= deadline:
                break
        result = {'site': host, 'vpn_active': vpn(), 'controlled_content': controlled_page(text, host),
                  'browser_error': any(word in text for word in ('ERR_', 'No internet', 'Нет подключения'))}
        print(json.dumps({'browser': result}), flush=True)
        return result

    if adb('shell', 'pm', 'list', 'packages', PACKAGE).strip():
        raise RuntimeError('preserve existing diagnostic installation')
    if not screen_ready(adb('shell', 'dumpsys', 'window', 'policy').decode(), adb('shell', 'dumpsys', 'power').decode()):
        raise RuntimeError('LIVE BLOCKED: unlock the physical phone before acceptance')
    connectivity = adb('shell', 'dumpsys', 'connectivity').decode(errors='replace')
    if adb('reverse', '--list').strip() or any('NetworkAgentInfo{' in line and 'ni{VPN CONNECTED' in line for line in connectivity.splitlines()):
        raise RuntimeError('existing forwarding/VPN rejected')
    if adb('shell', 'settings', 'get', 'global', 'wifi_on').strip() != b'0' or adb('shell', 'settings', 'get', 'global', 'mobile_data').strip() != b'1':
        raise RuntimeError('cellular ON/Wi-Fi OFF required')
    args.out.mkdir(mode=0o700, parents=True, exist_ok=False)
    directory = '/tmp/fc-eu6-' + secrets.token_hex(8)
    remote = log = None
    created = installed = False
    outcome = {'result': 'FAIL', 'production_changed': False, 'manual_room': False, 'traffic_forwarding': False}
    outcome['device'] = {name: adb('shell', 'getprop', prop).decode().strip() for name, prop in
                         [('model', 'ro.product.model'), ('android', 'ro.build.version.release'), ('abi', 'ro.product.cpu.abi')]}
    if outcome['device'] != {'model': 'Redmi Note 9 Pro', 'android': '12', 'abi': 'arm64-v8a'}:
        raise RuntimeError('unaccepted physical device')
    outcome['cellular_on_wifi_off'] = True
    prepared, recovered, browser, probes, failed = [], [], [], {}, {}
    duration = 0

    def stop_remote():
        code = ('import os,signal; from pathlib import Path; root=Path(' + repr(directory) + '); '
                'pid=int((root/"pid").read_text()); '
                'owned=Path("/proc/%s/exe"%pid).exists() and os.readlink("/proc/%s/exe"%pid)==str(root/"bootstrap-broker"); '
                'os.kill(pid,signal.SIGTERM) if owned else None')
        run([*SSH, HOST, 'python3 -c ' + shlex.quote(code)])

    try:
        run([*SSH, HOST, 'umask 077; mkdir ' + directory]); created = True
        for name, raw in [('bootstrap-broker', args.binary.read_bytes()), ('family.json', (args.family_dir / 'gateway.json').read_bytes())]:
            mode = '700' if name == 'bootstrap-broker' else '600'
            run([*SSH, HOST, f'umask 077; cat > {directory}/{name}; chmod {mode} {directory}/{name}'], input=raw, timeout=180)
        code = ('import os,sys; os.chdir(' + repr(directory) + '); '
                'os.environ["YANDEX_TELEMOST_OAUTH_TOKEN"]=sys.stdin.readline().rstrip("\\n"); '
                'open("pid","w").write(str(os.getpid())); '
                'os.execv("./bootstrap-broker",["./bootstrap-broker","--family-config","family.json","--duration","15m","--listen","186.246.45.246:18444"])')
        log = (args.out / 'gateway.jsonl').open('wb')
        remote = subprocess.Popen([*SSH, HOST, 'python3 -c ' + shlex.quote(code)], stdin=subprocess.PIPE, stdout=log, stderr=subprocess.DEVNULL)
        remote.stdin.write((token + '\n').encode()); remote.stdin.close()
        deadline = time.monotonic() + 90
        while time.monotonic() < deadline:
            if remote.poll() is not None:
                raise RuntimeError('bootstrap seed stopped')
            if any(item.get('event') == 'bootstrap_seed_ready' for item in rows((args.out / 'gateway.jsonl').read_bytes())):
                break
            time.sleep(.5)
        else:
            raise RuntimeError('bootstrap READY timeout')
        print('SEED_READY', flush=True)
        adb('install', '-t', str(args.apk), timeout=120); installed = True
        private('umask 077; mkdir -p no_backup/restricted; cat > no_backup/restricted/family.json',
                input=(args.family_dir / 'valid.json').read_bytes())
        start('refresh', '--es', 'control', 'https://186.246.45.246:18444')
        time.sleep(2); consent()
        prepared = wait_state(4, 'refresh')
        adb('shell', 'am', 'force-stop', PACKAGE)
        if shell('pidof ' + PACKAGE + ' || true').strip():
            raise RuntimeError('process restart not proven')
        private('test -s no_backup/restricted/bootstrap.json; : > files/restricted-evidence.jsonl')
        outcome['cache_survived_restart'] = True
        print('CACHE_RESTART_PASS', flush=True)
        start('recover')
        recovered = wait_state(2, 'recover')
        started = time.monotonic()
        outcome['vpn_active'] = vpn()
        outcome['routes'] = vpn_routes(adb('shell', 'dumpsys', 'connectivity').decode())
        outcome['battery_start'] = battery()
        if not all(outcome['routes'].values()):
            raise RuntimeError('VPN route/bypass/DNS evidence incomplete')
        print('VPN_PACKET_READY vpn=' + str(outcome['vpn_active']), flush=True)
        for host in ('example.com', 'example.org'):
            browser.append(browser_visit(host))
        start('probe')
        deadline = time.monotonic() + 90
        while time.monotonic() < deadline:
            raw = private('cat files/restricted-probes.json 2>/dev/null || true')
            if raw.strip():
                probes = json.loads(raw)
                break
            time.sleep(2)
        else:
            raise RuntimeError('ordinary app probe timeout')
        (args.out / 'probes.json').write_text(json.dumps(probes, indent=2) + '\n')
        next_visit = started + 120
        while time.monotonic() - started < args.seconds:
            recovered = evidence('recover')
            if any(sample.get('state') == 3 for sample in recovered):
                raise RuntimeError('dedicated session failed before injection')
            if time.monotonic() >= next_visit:
                browser.append(browser_visit('example.com' if len(browser) % 2 == 0 else 'example.org'))
                next_visit += 120
            time.sleep(5)
        duration = round(time.monotonic() - started, 1)
        outcome['battery_end'] = battery()
        recovered = evidence('recover')
        print('SMOKE_FINISHED seconds=' + str(duration), flush=True)
        stop_remote()
        deadline = time.monotonic() + 70
        while time.monotonic() < deadline:
            samples = evidence('failure')
            if any(sample.get('state') == 3 for sample in samples):
                failed['session_failed'] = True
                failed['owner_reports_unavailable'] = samples[-1].get('owner_health') == 'unavailable'
                break
            time.sleep(2)
        start('failure-probe')
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            raw = private('cat files/restricted-failure-probe.json 2>/dev/null || true')
            if raw.strip():
                failure_probe = json.loads(raw)
                failed['ordinary_tcp_failed'] = all(failure_probe.get(name) is True for name in ('ordinary_tcp_failed', 'vpn_before', 'vpn_after'))
                failed['owner_reports_unavailable'] = failure_probe.get('owner_health') == 'unavailable'
                break
            time.sleep(1)
        failure_visit = browser_visit('1.1.1.1')
        failed.update(vpn_active=vpn(), browser_blocked=failure_visit['browser_error'] and not failure_visit['controlled_content'])
        failed['routes'] = vpn_routes(adb('shell', 'dumpsys', 'connectivity').decode())
        (args.out / 'failure.json').write_text(json.dumps(failed, indent=2) + '\n')
        validate(prepared, recovered, rows((args.out / 'gateway.jsonl').read_bytes()), browser, probes, failed, duration)
        outcome['result'] = 'PASS'
    except KeyboardInterrupt:
        outcome['failure'] = 'operator stopped failed attempt for focused fix'
    except Exception as error:
        outcome['failure'] = str(error)
        print('ATTEMPT_FAILED: ' + str(error), flush=True)
    finally:
        cleanup = []
        if installed:
            try:
                start('stop'); time.sleep(5)
                outcome['graceful_vpn_stop'] = not vpn()
                adb('shell', 'am', 'force-stop', PACKAGE)
                adb('uninstall', PACKAGE)
                if adb('shell', 'pm', 'list', 'packages', PACKAGE).strip() or vpn():
                    cleanup.append('android_retained')
            except Exception:
                cleanup.append('android_cleanup_unverified')
        if created:
            code = ('import os,signal,time,shutil; from pathlib import Path; root=Path(' + repr(directory) + '); '
                    'pid=int((root/"pid").read_text()) if (root/"pid").exists() else 0; '
                    'owned=lambda: pid>1 and Path("/proc/%s/exe"%pid).exists() and os.readlink("/proc/%s/exe"%pid)==str(root/"bootstrap-broker"); '
                    'os.kill(pid,signal.SIGTERM) if owned() else None; time.sleep(3); '
                    'os.kill(pid,signal.SIGKILL) if owned() else None; time.sleep(.2); assert not owned(); shutil.rmtree(root)')
            try:
                run([*SSH, HOST, 'python3 -c ' + shlex.quote(code)], timeout=15)
            except Exception:
                cleanup.append('gateway_cleanup_unverified')
        if remote is not None:
            try:
                remote.wait(timeout=5)
            except subprocess.TimeoutExpired:
                remote.terminate()
                try:
                    remote.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    remote.kill(); remote.wait()
        if log is not None:
            log.close()
        outcome.update(cleanup_errors=cleanup, smoke_seconds=duration, browser=browser, probes=probes, failure_test=failed,
                       apk_sha256=hashlib.sha256(args.apk.read_bytes()).hexdigest(),
                       binary_sha256=hashlib.sha256(args.binary.read_bytes()).hexdigest())
        if cleanup:
            outcome['result'] = 'FAIL'
        (args.out / 'summary.json').write_text(json.dumps(outcome, indent=2) + '\n')
        print(json.dumps(outcome), flush=True)


if __name__ == '__main__':
    main()
