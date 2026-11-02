"""Operator-container AWG3.1/REALITY checks; receives disposable probe input on stdin."""

import hashlib
import ipaddress
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

from clients.desktop.profile_config import parse, parse_tcp, tcp_config

NATIVE = {
    'amneziawg-go': 'e7f00e47d6df853ade5dcd2fe79240f01ff897d75088c768316a444c27c87e0f',
    'awg': '906d6795af1dd4adee7b11bf1e7fa133d4795c8a8d6e2099b34a026f810a3278',
    'xray': '4f7a4436f86798bbb5c875014e352021a1673710a45e170ccc507c5f59341940',
}


def require(condition):
    if not condition:
        raise ValueError('standby external check rejected')


def configuration(value):
    require(set(value) == {'target', 'private_key', 'tcp_id', 'template'})
    target = value['target']
    require(str(ipaddress.IPv4Address(target)) == target)
    require(target not in ('185.251.89.19', '185.10.158.212', '186.246.45.246', '186.246.51.201'))
    template = value['template']
    require(set(template) == {'country', 'awg', 'tcp'} and template['country'] == 'nl')
    require(template['tcp']['id'] == 'DEVICE_CREDENTIAL')
    require(template['awg'].count('LOCAL_DEVICE_KEY') == 1 and template['awg'].count('ASSIGNED_ADDRESS') == 1)
    tcp = parse_tcp(json.dumps(dict(template['tcp'], id=value['tcp_id'])))
    require(tcp['server'] == target and tcp['port'] == 443)
    profile = template['awg'].replace('LOCAL_DEVICE_KEY', value['private_key']).replace('ASSIGNED_ADDRESS', '10.83.255.254/32')
    parsed = parse(profile, allow_awg=True, allow_awg31=True)
    require(parsed['Peer']['Endpoint'] == target + ':51823')
    awg = '\n'.join(line for line in profile.splitlines() if not line.startswith(('Address =', 'DNS =', 'MTU ='))) + '\n'
    config = tcp_config(tcp, 'fctcp12345678')
    config['outbounds'][0]['streamSettings'].pop('sockopt')
    config['inbounds'] = [dict(listen='127.0.0.1', port=19728, protocol='socks', settings=dict(auth='noauth', udp=False))]
    return awg.encode(), json.dumps(config).encode()


def run(argv, timeout=60):
    result = subprocess.run(argv, capture_output=True, timeout=timeout)
    require(result.returncode == 0)
    return result.stdout


def web(target, options):
    run(['curl', '--silent', '--show-error', '--fail', '--max-time', '45', *options, 'https://example.com/'])
    trace = run(['curl', '--silent', '--show-error', '--fail', '--max-time', '45', *options,
                 'https://www.cloudflare.com/cdn-cgi/trace'])
    require(('ip=' + target).encode() in trace.splitlines())


def stop(process):
    if process.poll() is None:
        process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def accept(value):
    require(Path('/.dockerenv').is_file() and os.geteuid() == 0)
    awg, tcp = configuration(value)
    for name, digest in NATIVE.items():
        require(hashlib.sha256(Path('/native', name).read_bytes()).hexdigest() == digest)
    target = value['target']
    results = {'awg': 'NOT_RUN', 'tcp': 'NOT_RUN', 'operator_cleanup': 'NOT_RUN', 'mesh': 'NOT_RUN'}
    with tempfile.TemporaryDirectory(prefix='ordinary-probe-') as folder:
        directory = Path(folder)
        awg_path, tcp_path = directory / 'awg.conf', directory / 'tcp.json'
        awg_path.write_bytes(awg)
        tcp_path.write_bytes(tcp)
        awg_path.chmod(0o600)
        tcp_path.chmod(0o600)
        run(['/native/xray', 'run', '-test', '-config', str(tcp_path)])
        process = subprocess.Popen(['/native/xray', 'run', '-config', str(tcp_path)],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            time.sleep(1)
            require(process.poll() is None)
            web(target, ['--socks5-hostname', '127.0.0.1:19728'])
            results['tcp'] = 'AUTH_DNS_HTTPS_EGRESS_PASS'
        finally:
            stop(process)
        process = subprocess.Popen(['/native/amneziawg-go', '-f', 'fcprobe0'],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        route = rule = False
        started = int(time.time())
        try:
            for attempt in range(50):
                if subprocess.run(['ip', 'link', 'show', 'fcprobe0'], capture_output=True).returncode == 0:
                    break
                time.sleep(.1)
            run(['/native/awg', 'setconf', 'fcprobe0', str(awg_path)])
            run(['ip', 'address', 'add', '10.83.255.254/32', 'dev', 'fcprobe0'])
            run(['ip', 'link', 'set', 'fcprobe0', 'mtu', '1280', 'up'])
            run(['ip', 'route', 'add', 'default', 'dev', 'fcprobe0', 'table', '50028'])
            route = True
            run(['ip', 'rule', 'add', 'priority', '12028', 'from', '10.83.255.254', 'table', '50028'])
            rule = True
            answers = run(['dig', '-b', '10.83.255.254', '@1.1.1.1', 'example.com', 'A', '+short']).decode().splitlines()
            require(answers and all(ipaddress.IPv4Address(answer) for answer in answers))
            options = ['--interface', '10.83.255.254', '--resolve', 'example.com:443:' + answers[0]]
            addresses = run(['dig', '-b', '10.83.255.254', '@1.1.1.1', 'www.cloudflare.com', 'A', '+short']).decode().splitlines()
            addresses = [answer for answer in addresses if all(character in '0123456789.' for character in answer)]
            require(addresses)
            web(target, options + ['--resolve', 'www.cloudflare.com:443:' + str(ipaddress.IPv4Address(addresses[0]))])
            handshake = run(['/native/awg', 'show', 'fcprobe0', 'latest-handshakes']).split()
            require(len(handshake) == 2 and int(handshake[1]) >= started)
            results['awg'] = 'HANDSHAKE_DNS_HTTPS_EGRESS_PASS'
        finally:
            try:
                if rule:
                    run(['ip', 'rule', 'del', 'priority', '12028', 'from', '10.83.255.254', 'table', '50028'])
                if route:
                    run(['ip', 'route', 'del', 'default', 'dev', 'fcprobe0', 'table', '50028'])
            finally:
                stop(process)
                if subprocess.run(['ip', 'link', 'show', 'fcprobe0'], capture_output=True).returncode == 0:
                    run(['ip', 'link', 'delete', 'fcprobe0'])
        results['operator_cleanup'] = 'PASS'
    return results


if __name__ == '__main__':
    os.umask(0o077)
    try:
        print(json.dumps(accept(json.loads(sys.stdin.buffer.read(16385)))))
    except Exception:
        print('{"result":"EXTERNAL_CHECK_FAILED","target_cleanup":"REQUIRED"}')
        sys.exit(1)
