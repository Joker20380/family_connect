"""Isolated normal-path acceptance; not restricted/ISP-allowlist acceptance."""
import argparse
import base64
import datetime
import gzip
import json
from pathlib import Path
import re
import secrets
import shlex
import subprocess
import time
import uuid
import xml.etree.ElementTree as ET

from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, PublicFormat, NoEncryption
from acceptance import run, screen_ready, controlled_page

PACKAGE = 'com.familyconnect.app.orchestrator'
HOST = 'root@186.246.45.246'
SSH = ['ssh', '-T', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', HOST]


def browser_content(text, host):
    return controlled_page(text, host) or (host in text and 'ERR_' not in text
        and 'Este dominio' in text and 'ejemplos' in text and 'documentación' in text)


def validate_events(events, expected, state='CONNECTED'):
    attempted = [item['candidate'] for item in events if item['event'] == 'candidate_attempted']
    if attempted != expected or events[-1]['state'] != state:
        raise RuntimeError('unexpected bounded candidate sequence/state')
    if len(events) > 128 or any(set(item) - {'event', 'state', 'candidate', 'category', 'elapsed_ms'} for item in events):
        raise RuntimeError('diagnostic schema/bound exceeded')
    return [item['elapsed_ms'] for item in events if item['event'] == 'time_to_connected']


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--adb', required=True)
    parser.add_argument('--apk', type=Path, required=True)
    parser.add_argument('--xray', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--manual-ui', action='store_true')
    parser.add_argument('--lifecycle-only', action='store_true')
    parser.add_argument('--port', type=int, choices=(18444,18445), default=18445)
    args = parser.parse_args()
    args.out.mkdir(mode=0o700, parents=True, exist_ok=False)
    summary = {'result': 'FAIL', 'restricted': 'NOT RUN', 'production_changed': False}
    installed = created = False
    remote = None
    directory = '/tmp/fc-orchestrator-normal-' + secrets.token_hex(8)

    def adb(*command, **options):
        return run([args.adb, *command], **options)

    def private(command, **options):
        return adb('shell', '-T', 'run-as', PACKAGE, 'sh', '-c', shlex.quote(command), **options)

    def activity(name, mode, *extras):
        output = adb('shell', 'am', 'start', '-W', '-f', '0x18000000', '-n', PACKAGE + '/com.familyconnect.app.' + name,
                     '--es', 'mode', mode, *extras)
        if b'Error:' in output or b'Error type' in output:
            raise RuntimeError('activity unavailable')
        summary.setdefault('activity_receipts', []).append({'activity': name, 'mode': mode,
            'ok': b'Status: ok' in output, 'warning': b'Warning:' in output,
            'resolved': re.findall(r'^Activity: ([A-Za-z0-9_./]+)$', output.decode(errors='replace'), re.MULTILINE)})

    def ui():
        path = '/data/local/tmp/fc-orchestrator-ui.xml'
        try:
            adb('shell', 'uiautomator', 'dump', path, timeout=20)
            return ET.fromstring(adb('shell', 'cat', path).decode(errors='replace'))
        finally:
            adb('shell', 'rm', '-f', path)

    def tap(labels):
        for node in ui().iter('node'):
            if node.attrib.get('text', '').strip().lower() in labels:
                bounds = list(map(int, re.findall(r'\d+', node.attrib.get('bounds', ''))))
                if len(bounds) == 4:
                    adb('shell', 'input', 'tap', str((bounds[0]+bounds[2])//2), str((bounds[1]+bounds[3])//2))
                    return True
        return False

    def events():
        try:
            return json.loads(private('cat files/connectivity-events.json'))
        except (RuntimeError, json.JSONDecodeError):
            return []

    def wait_state(wanted, seconds=80):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            records = events()
            if records and records[-1]['state'] == wanted:
                return records
            if wanted=='CONNECTED' and records and records[-1]['state']=='FAILED':
                raise RuntimeError('candidate chain exhausted before CONNECTED')
            time.sleep(.25)
        raise RuntimeError('orchestrator state timeout: ' + wanted)

    def prepare(*extras):
        private('rm -f files/orchestrator-prepared.json')
        activity('OrchestratorDiagnosticActivity', 'prepare', '--ez', 'reset_hint', 'true', *extras)
        for attempt in range(20):
            try:
                ready = json.loads(private('cat files/orchestrator-prepared.json'))
            except RuntimeError:
                time.sleep(.25)
                continue
            if not ready.get('ready'):
                raise RuntimeError('diagnostic profile preparation failed: '+str(ready.get('failure')))
            time.sleep(1)
            return
        raise RuntimeError('diagnostic preparation timeout')

    def connect(permission=False):
        if args.manual_ui:
            print('USER_ACTION: press CONNECT in family_connect_pilot; approve Android VPN dialog if shown', flush=True)
            return
        if not tap({'connect', 'подключиться', 'подключить'}):
            raise RuntimeError('CONNECT button absent')
        if permission:
            time.sleep(1)
            if not tap({'ok', 'ок'}):
                raise RuntimeError('Android VPN permission absent')

    def stop():
        activity('RestrictedDiagnosticActivity', 'stop')
        wait_state('DISCONNECTED', 15)
        time.sleep(1)

    def routes():
        lines = adb('shell', 'dumpsys', 'connectivity').decode(errors='replace').splitlines()
        active = [line for line in lines if 'NetworkAgentInfo{' in line and 'ni{VPN CONNECTED' in line]
        return {'owners': len(active), 'ipv4': any('0.0.0.0/0' in line for line in active),
                'ipv6': any('::/0' in line for line in active),
                'no_bypass': any('bypassable=false' in line for line in active)}

    def browser():
        result = []
        for host in ('example.com', 'example.org'):
            print('PHASE: controlled Chrome HTTPS', flush=True)
            adb('shell', 'am', 'start', '-a', 'android.intent.action.VIEW', '-d', 'https://'+host+'/?fcauto='+secrets.token_hex(6), 'com.android.chrome')
            matched = False
            for attempt in range(8):
                time.sleep(3)
                text = ' '.join(node.attrib.get(field, '') for node in ui().iter('node') for field in ('text', 'content-desc'))
                if browser_content(text, host):
                    matched = True
                    break
            result.append({'controlled_content': matched, 'vpn': routes(),
                'errors': re.findall(r'ERR_[A-Z_]+', text), 'controlled_host_visible': host in text})
        return result

    try:
        if adb('shell', 'pm', 'list', 'packages', PACKAGE).strip():
            raise RuntimeError('preserve existing diagnostic installation')
        if not screen_ready(adb('shell', 'dumpsys', 'window', 'policy').decode(), adb('shell', 'dumpsys', 'power').decode()):
            raise RuntimeError('unlock physical phone')
        if adb('reverse', '--list').strip() or routes()['owners']:
            raise RuntimeError('existing forwarding/VPN rejected')
        if adb('shell', 'settings', 'get', 'global', 'wifi_on').strip() != b'0' or adb('shell', 'settings', 'get', 'global', 'mobile_data').strip() != b'1':
            raise RuntimeError('cellular ON/Wi-Fi OFF required')
        summary['device'] = {label: adb('shell', 'getprop', prop).decode().strip() for label, prop in
                             [('model', 'ro.product.model'), ('android', 'ro.build.version.release'), ('abi', 'ro.product.cpu.abi')]}
        if summary['device'] != {'model': 'Redmi Note 9 Pro', 'android': '12', 'abi': 'arm64-v8a'}:
            raise RuntimeError('wrong device')
        key = X25519PrivateKey.generate()
        encode = lambda raw: base64.urlsafe_b64encode(raw).rstrip(b'=').decode()
        device_id, short_id = str(uuid.uuid4()), secrets.token_hex(8)
        public = encode(key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw))
        tls_key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
        name=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'android.test')])
        now=datetime.datetime.now(datetime.timezone.utc)
        certificate=(x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(tls_key.public_key())
                     .serial_number(x509.random_serial_number()).not_valid_before(now-datetime.timedelta(days=1))
                     .not_valid_after(now+datetime.timedelta(days=1))
                     .add_extension(x509.SubjectAlternativeName([x509.DNSName('android.test')]),False).sign(tls_key,hashes.SHA256()))
        config = {'log': {'loglevel': 'none'}, 'inbounds': [{'listen': '186.246.45.246', 'port': args.port,
                  'protocol': 'vless', 'settings': {'clients': [{'id': device_id, 'flow': 'xtls-rprx-vision'}], 'decryption': 'none'},
                  'streamSettings': {'network': 'raw', 'security': 'reality', 'realitySettings': {'show': False,
                  'target': '127.0.0.1:1', 'xver': 0, 'serverNames': ['android.test'],
                  'privateKey': encode(key.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())), 'shortIds': [short_id]}}}],
                  'outbounds': [{'protocol': 'freedom'}]}
        run([*SSH, 'test -z "$(ss -H -lnt sport = :'+str(args.port)+')" && umask 077 && mkdir '+directory]); created = True
        run([*SSH, 'gzip -d > '+directory+'/xray && chmod 700 '+directory+'/xray'], input=gzip.compress(args.xray.read_bytes(), compresslevel=1), timeout=180)
        supervisor = ('import subprocess,sys,threading,json,time,ssl,socket,os,base64;from pathlib import Path;root=Path('+repr(directory)+');os.umask(0o077);'
                      'raw=sys.stdin.buffer.read(16385);assert len(raw)<=16384;bundle=json.loads(raw);'
                      '(root/"tls.pem").write_bytes(base64.b64decode(bundle["tls"]));'
                      'tls=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);tls.minimum_version=ssl.TLSVersion.TLSv1_3;tls.maximum_version=ssl.TLSVersion.TLSv1_3;'
                      'tls.set_alpn_protocols(["h2","http/1.1"]);tls.load_cert_chain(root/"tls.pem");'
                      'listener=socket.socket();listener.bind(("127.0.0.1",0));listener.listen(16);listener.settimeout(1);\n'
                      'def handle(connection):\n'
                      ' try:\n'
                      '  connection.settimeout(3)\n'
                      '  with tls.wrap_socket(connection,server_side=True) as secured: secured.recv(4096)\n'
                      ' except OSError: connection.close()\n'
                      'def accept():\n'
                      ' while True:\n'
                      '  try: connection,_=listener.accept();threading.Thread(target=handle,args=(connection,),daemon=True).start()\n'
                      '  except socket.timeout: pass\n'
                      'threading.Thread(target=accept,daemon=True).start()\n'
                      'config=bundle["xray"];config["inbounds"][0]["streamSettings"]["realitySettings"]["target"]="127.0.0.1:"+str(listener.getsockname()[1]);'
                      'raw=json.dumps(config).encode();'
                      'child=subprocess.Popen([str(root/"xray"),"run","-config","stdin:"],stdin=subprocess.PIPE);'
                      '(root/"pid").write_text(str(child.pid));child.stdin.write(raw);child.stdin.close();\n'
                      'def sample():\n'
                      ' peak=0\n'
                      ' while child.poll() is None:\n'
                      '  result=subprocess.run(["ss","-H","-nt","state","established","sport = :'+str(args.port)+'"],capture_output=True,timeout=3)\n'
                      '  peak=max(peak,len(result.stdout.splitlines()));(root/"counts.json").write_text(json.dumps({"established_peak":peak}));time.sleep(1)\n'
                      'threading.Thread(target=sample,daemon=True).start()\n'
                      'try: child.wait(timeout=600)\n'
                      'except subprocess.TimeoutExpired: child.terminate();child.wait(timeout=10)\n')
        command = 'python3 -c '+shlex.quote(supervisor)
        remote = subprocess.Popen([*SSH, command], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        tls_pem=certificate.public_bytes(Encoding.PEM)+tls_key.private_bytes(Encoding.PEM,PrivateFormat.PKCS8,NoEncryption())
        remote.stdin.write(json.dumps({'xray':config,'tls':base64.b64encode(tls_pem).decode()}).encode());remote.stdin.close()
        time.sleep(3)
        if remote.poll() is not None:
            raise RuntimeError('isolated normal fixture exited')
        adb('install', '-t', str(args.apk), timeout=120); installed = True
        profile = {'type': 'vless-reality-v1', 'server': '186.246.45.246', 'port': args.port, 'id': device_id,
                   'public_key': public, 'server_name': 'android.test', 'short_id': short_id}
        private('mkdir -p no_backup; umask 077; cat > no_backup/auto-tcp.profile', input=json.dumps(profile).encode())
        prepare();connect(permission=True)
        normal = wait_state('CONNECTED', 180 if args.manual_ui else 80);summary['normal_ttc_ms'] = validate_events(normal, ['tcp'])
        (args.out/'normal.json').write_text(json.dumps(normal))
        if not args.lifecycle_only:
            activity('RestrictedDiagnosticActivity', 'probe')
            for attempt in range(45):
                try:
                    summary['ordinary_probe'] = json.loads(private('cat files/restricted-probes.json'))
                    break
                except RuntimeError:
                    time.sleep(1)
        summary['browser'] = [] if args.lifecycle_only else browser()
        summary['browser_pass'] = bool(summary['browser']) and all(item['controlled_content'] and item['vpn']['owners'] == 1 for item in summary['browser'])
        activity('OrchestratorDiagnosticActivity', 'failure')
        deadline = time.monotonic()+60
        while time.monotonic()<deadline:
            restored = events()
            if any(item['event']=='restoration_succeeded' for item in restored):
                break
            time.sleep(.5)
        else:
            settings=ET.fromstring(private('cat shared_prefs/orchestrator-diagnostic.xml'))
            summary['injection_pending']=any(item.attrib.get('name')=='fail_active' and item.attrib.get('value')=='true' for item in settings)
            raise RuntimeError('restoration absent')
        (args.out/'restored.json').write_text(json.dumps(restored))
        summary['restored_routes'] = routes()
        activity('OrchestratorDiagnosticActivity', 'failure');terminal = wait_state('FAILED')
        (args.out/'terminal.json').write_text(json.dumps(terminal))
        activity('RestrictedDiagnosticActivity', 'failure-probe');time.sleep(7)
        summary['failure_probe'] = json.loads(private('cat files/restricted-failure-probe.json'))
        summary['failed_routes'] = routes()
        if not all(summary['failure_probe'].get(name) for name in ('vpn_before', 'vpn_after', 'ordinary_tcp_failed')):
            raise RuntimeError('failed connection not contained')
        stop()
        awg = ('[Interface]\nPrivateKey = '+base64.b64encode(secrets.token_bytes(32)).decode()+'\n'
               'Address = 10.78.0.4/32\nDNS = 1.1.1.1\nMTU = 1280\n'
               'Jc = 3\nJmin = 40\nJmax = 80\nS1 = 16\nS2 = 16\nS3 = 16\nS4 = 16\nH1 = 1\nH2 = 2\nH3 = 3\nH4 = 4\n'
               'HeaderProtectionKey = '+base64.b64encode(secrets.token_bytes(32)).decode()+'\n'
               'ContentPaddingAddition = 0-32\nRandomTrailers = true\nDisableCookies = false\n'
               '[Peer]\nPublicKey = '+base64.b64encode(key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)).decode()+'\n'
               'Endpoint = 186.246.45.246:18446\nAllowedIPs = 0.0.0.0/0, ::/0\nPersistentKeepalive = 25\n')
        private('umask 077; cat > no_backup/auto-awg.profile', input=awg.encode())
        prepare('--ez', 'deny_primary', 'true');connect()
        alternate = wait_state('CONNECTED', 180 if args.manual_ui else 80)
        summary['alternate_ttc_ms'] = validate_events(alternate, ['awg', 'tcp'])
        (args.out/'alternate.json').write_text(json.dumps(alternate));stop()
        prepare('--ez', 'deny_normal', 'true');connect();exhausted = wait_state('FAILED', 180 if args.manual_ui else 80)
        validate_events(exhausted, ['awg', 'tcp', 'restricted'], 'FAILED')
        (args.out/'exhausted.json').write_text(json.dumps(exhausted));stop()
        summary['result'] = 'NORMAL PARTIAL PASS / RESTRICTED LIVE BLOCKED'
        if args.lifecycle_only:
            summary['result'] = 'LIFECYCLE PARTIAL PASS / BROWSER NOT RUN / RESTRICTED LIVE BLOCKED'
        elif not summary['browser_pass']:
            summary['result'] = 'FAIL'
            summary['failure'] = 'normal browser proof incomplete; lifecycle results retained'
    except Exception as failure:
        summary['failure'] = str(failure) if isinstance(failure, RuntimeError) else type(failure).__name__
        if installed:
            records=events();(args.out/'last-events.json').write_text(json.dumps(records))
            if records and records[-1]['state']=='FAILED':
                try:
                    summary['failed_routes']=routes()
                    activity('RestrictedDiagnosticActivity','failure-probe');time.sleep(6)
                    summary['failure_probe']=json.loads(private('cat files/restricted-failure-probe.json'))
                except Exception:
                    summary['failure_probe']={'unavailable':True}
    finally:
        cleanup = {}
        if installed:
            try:
                activity('RestrictedDiagnosticActivity', 'stop');time.sleep(2)
                adb('shell', 'am', 'force-stop', PACKAGE);adb('uninstall', PACKAGE)
                cleanup['device'] = not adb('shell', 'pm', 'list', 'packages', PACKAGE).strip() and routes()['owners'] == 0
            except Exception:
                cleanup['device'] = False
        if created:
            try:
                summary['fixture_tcp'] = json.loads(run([*SSH, 'cat '+directory+'/counts.json']))
            except Exception:
                summary['fixture_tcp'] = {'sampling_unavailable': True}
            try:
                code = ('import os,signal,shutil;from pathlib import Path;root=Path('+repr(directory)+');'
                        'pid=int((root/"pid").read_text()) if (root/"pid").exists() else 0;'
                        'owned=pid>0 and Path("/proc/%s/exe"%pid).exists() and os.readlink("/proc/%s/exe"%pid)==str(root/"xray");'
                        'os.kill(pid,signal.SIGTERM) if owned else None;shutil.rmtree(root)')
                run([*SSH, 'python3 -c '+shlex.quote(code)])
                if remote is not None:remote.wait(timeout=15)
                cleanup['server'] = True
            except Exception:
                cleanup['server'] = False
        summary['cleanup'] = cleanup
        (args.out/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
        print(json.dumps(summary), flush=True)
    if summary['result'] == 'FAIL' or not all(cleanup.values()):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
