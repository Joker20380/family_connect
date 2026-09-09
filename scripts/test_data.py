"""RU/EN: real HTTPS transfer across relay loss; isolated namespaces only."""
import json
import subprocess
import time
from pathlib import Path

COMPOSE = ['docker', 'compose', '-f', 'compose.data.yaml']
ARTIFACTS = Path('artifacts/data3')
SIZE = 8 * 1024 * 1024


def run(*args, check=True, timeout=30):
    return subprocess.run([*COMPOSE, *args], check=check, capture_output=True,
                          text=True, timeout=timeout)


def request(url, seconds=10):
    return run('exec', '-T', 'client-wg', 'curl', '-4', '-fsS',
               '--max-time', str(seconds), url, check=False, timeout=seconds+10)


def main():
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    download = None
    if run('ps', '--status', 'running', '-q', 'control').stdout.strip():
        topology = run('exec', '-T', 'control', 'python', '-c',
            "import json; print(','.join(n['name'] for n in json.load(open('/state/network.json'))['nodes']))").stdout
        if 'relay-remote' in topology:
            raise RuntimeError('distributed catalog active; use test_distributed.py from the operator laptop')
    try:
        # Fresh namespaces remove old firewall/interface state; no host routes change.
        run('down', timeout=60)
        run('up', '-d', '--no-build', 'control', 'gateway', 'relay-a', 'relay-b',
            'gateway-wg', timeout=90)
        run('up', '-d', '--no-build', 'client', 'client-wg', timeout=90)
        trace = None
        for _ in range(12):
            response = request('https://www.cloudflare.com/cdn-cgi/trace', 5)
            if response.returncode == 0:
                trace = dict(line.split('=', 1) for line in response.stdout.splitlines() if '=' in line)
                break
            time.sleep(1)
        if trace is None or trace.get('ip') != '185.251.89.19':
            raise RuntimeError('expected Russian gateway egress not observed')
        before = run('logs', '--no-color', 'client').stdout
        if before.count('packet tunnel ready; inner_quic_connections=1') != 1:
            raise RuntimeError('expected exactly one ready inner connection')
        if 'authenticated relay path changed' in before:
            raise RuntimeError('path changed before controlled failure; retry cleanly')
        # One curl invocation, no retry/resume; TLS verifies the public server.
        with (ARTIFACTS/'download.json').open('w') as output, (ARTIFACTS/'download.stderr').open('w') as errors:
            download = subprocess.Popen([*COMPOSE, 'exec', '-T', 'client-wg', 'curl',
                '-4', '-f', '-sS', '--max-time', '120', '--limit-rate', '256k',
                '--output', '/tmp/fc-download.bin', '--write-out', '%{json}',
                f'https://speed.cloudflare.com/__down?bytes={SIZE}'], stdout=output, stderr=errors)
            partial = 0
            for _ in range(40):
                if download.poll() is not None:
                    raise RuntimeError('download finished/failed before relay loss')
                probe = run('exec', '-T', 'client-wg', 'stat', '-c', '%s', '/tmp/fc-download.bin', check=False)
                partial = int(probe.stdout.strip() or 0)
                if partial >= 256*1024:
                    break
                time.sleep(0.5)
            if not 0 < partial < SIZE:
                raise RuntimeError('no active partial download')
            run('kill', '-s', 'SIGKILL', 'relay-a')
            if download.wait(timeout=135) != 0:
                raise RuntimeError('HTTPS transfer did not survive relay failure')
        metrics = json.loads((ARTIFACTS/'download.json').read_text())
        if metrics['http_code'] != 200 or int(metrics['size_download']) != SIZE or metrics['num_connects'] != 1:
            raise RuntimeError('unexpected download size/status or application reconnect')
        digest = run('exec', '-T', 'client-wg', 'sha256sum', '/tmp/fc-download.bin').stdout.split()[0]
        logs = run('logs', '--no-color', 'client').stdout
        switches = logs.count('authenticated relay path changed')
        if switches < 1 or logs.count('packet tunnel ready; inner_quic_connections=1') != 1:
            raise RuntimeError('missing route switch or unexpected tunnel recreation')
        (ARTIFACTS/'client.log').write_text(logs)
        # IPv6 is intentionally black-holed through WG; no direct fallback.
        ipv6 = run('exec', '-T', 'client-wg', 'curl', '-6', '-fsS', '--max-time', '3',
                   'https://www.cloudflare.com/cdn-cgi/trace', check=False)
        if ipv6.returncode == 0:
            raise RuntimeError('unexpected IPv6 egress')
        # Remove the only remaining relay: a new public connection MUST fail.
        run('kill', '-s', 'SIGKILL', 'relay-b')
        for target in ['https://www.cloudflare.com/cdn-cgi/trace', 'https://1.1.1.1/cdn-cgi/trace']:
            if request(target, 5).returncode == 0:
                raise RuntimeError('public traffic bypassed both stopped relays')
        result = {'gateway_ip': trace['ip'], 'country': trace.get('loc'),
                  'bytes': SIZE, 'bytes_before_relay_loss': partial, 'sha256_observed': digest,
                  'https_connections': metrics['num_connects'], 'seconds': metrics['time_total'],
                  'inner_quic_connections': 1, 'relay_switches': switches,
                  'ipv6_egress': 'blocked', 'both_relays_down': 'no public connectivity',
                  'environment': 'single-host Linux/WireGuard namespaces; public HTTPS destination'}
        (ARTIFACTS/'result.json').write_text(json.dumps(result, indent=2)+'\n')
        print(json.dumps(result, indent=2))
    finally:
        if download is not None and download.poll() is None:
            download.terminate()
            download.wait(timeout=10)
        # Recreate together: a restarted core alone would orphan its WG sidecar namespace.
        run('down', timeout=60)
        run('up', '-d', '--no-build', 'control', 'gateway', 'relay-a', 'relay-b', 'gateway-wg',
            timeout=90)


if __name__ == '__main__':
    main()
