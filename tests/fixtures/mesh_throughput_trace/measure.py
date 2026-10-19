"""Small evidence gate, then bounded alternating phone-side HTTPS body reads."""

import concurrent.futures
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import threading
import time

from capture import Capture
from correlate import correlate, reconstruct
from rollout import GATEWAY

ROOT = Path(__file__).resolve().parents[3]
WORK = ROOT / 'state-client-build/mesh-throughput-trace-20261019'


def adb(command, timeout=25):
    return subprocess.run(['adb', 'shell', command], text=True, capture_output=True, timeout=timeout)


def topology():
    response = adb('dumpsys connectivity')
    response.check_returncode()
    lines = [line for line in response.stdout.splitlines() if line.strip().startswith('NetworkAgentInfo{')
             and 'ni{VPN' in line and 'OwnerUid: 10283' in line]
    assert len(lines) == 1 and 'Uids: <{0-99999}>' in lines[0] and '10.79.0.1' in lines[0], 'MESH TUN not established'
    value = dict(interface=re.search(r'InterfaceName: (\S+)', lines[0])[1],
                 underlay=re.search(r'UnderlyingNetworks: \[([^\]]*)\]', lines[0])[1],
                 transports=re.search(r'Transports: (.*?) Capabilities:', lines[0])[1])
    assert adb('id -u').stdout.strip() == '2000'
    assert 'dev ' + value['interface'] in adb('ip route get 1.1.1.1').stdout
    return value


def main():
    os.umask(0o077)
    mode = sys.argv[1]
    assert mode in ('small', 'small-return', 'baseline', 'baseline-repeat', 'candidate-small', 'candidate-small-recheck', 'candidate-bulk', 'candidate-repeat')
    is_small = 'small' in mode
    is_candidate = mode.startswith('candidate')
    gateway = json.loads((WORK / 'candidate/artifact.json').read_text())['sha256'] if is_candidate else GATEWAY
    if not is_small:
        gate = sys.argv[2] if len(sys.argv) > 2 else ('candidate-small' if is_candidate else 'small')
        assert gate in (('candidate-small', 'candidate-small-recheck') if is_candidate else ('small', 'small-return'))
        gate_result = json.loads((WORK / gate / 'result.json').read_text())
        assert gate_result['small_gate_pass'] and gate_result['source_gateway'] == gateway
    out = WORK / mode
    assert not out.exists(), 'Retain earlier evidence; use an explicitly separate attempt'
    phone = adb('dumpsys package com.familyconnect.app.friends').stdout
    assert re.search(r'versionCode=(\d+)', phone)[1] == '89'
    initial_topology = topology()
    remote = """
import hashlib,json,subprocess
from pathlib import Path
from cryptography import x509
import datetime
unit='family-connect-restricted-bootstrap.service'
state=dict(line.split('=',1) for line in subprocess.check_output(['systemctl','show',unit,'--property=MainPID,ActiveState,NRestarts,InvocationID'],text=True).splitlines())
assert state['ActiveState']=='active'
assert hashlib.sha256((Path('/proc')/state['MainPID']/'exe').read_bytes()).hexdigest()=='GATEWAY_HASH'
profile=json.loads(Path('/opt/apps/family_connect/friends-restricted/gateway.json').read_bytes())
expiry=x509.load_pem_x509_certificate(profile['certificate'].encode()).not_valid_after_utc
assert (expiry-datetime.datetime.now(datetime.timezone.utc)).total_seconds()>900
print(json.dumps(state))
""".replace('GATEWAY_HASH', gateway)
    response = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=8', 'root@186.246.45.246',
                               'python3 -B -'], input=remote, capture_output=True, text=True, timeout=25)
    response.check_returncode()
    nl = json.loads(response.stdout)
    out.mkdir(mode=0o700, exist_ok=False)
    (out / 'preflight.json').write_text(json.dumps(dict(nl=nl, topology=initial_topology, utc=datetime.datetime.now(datetime.timezone.utc).isoformat()), indent=2))
    remote_root = '/data/local/tmp/fc-mesh-trace-' + mode + '-20261019'
    adb('umask 077; mkdir ' + remote_root).check_returncode()
    stop = threading.Event()
    deadline = time.monotonic() + (150 if is_small else 600)
    lock = threading.Lock()
    requests = []
    capture = Capture(out / 'capture', 160 if is_small else 610)
    sampling = r'''
import json,select,subprocess,sys,time
deadline=time.monotonic()+610
while time.monotonic()<deadline:
 if select.select([sys.stdin],[],[],0)[0] and not sys.stdin.readline():break
 raw=subprocess.check_output(['ss','-H','-tnp','state','all','( dport = :443 )'],text=True,timeout=3)
 print(json.dumps(dict(epoch=time.time(),pid=PID,sockets=[line for line in raw.splitlines() if 'pid=PID,' in line])),flush=True)
 time.sleep(1)
'''.replace('PID', nl['MainPID'])
    socket_file = (out / 'nl-sockets-private.jsonl').open('x')
    socket_error = (out / 'nl-sockets.stderr').open('x')
    sampler = subprocess.Popen(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=8', 'root@186.246.45.246',
                                'python3 -B -c ' + shlex.quote(sampling)], stdin=subprocess.PIPE,
                               stdout=socket_file, stderr=socket_error)
    fields = ('http_code', 'http_version', 'ssl_verify_result', 'remote_ip', 'local_port', 'num_connects',
              'size_download', 'time_namelookup', 'time_connect', 'time_appconnect', 'time_starttransfer', 'time_total')

    def request(name, size):
        base = remote_root + '/' + name
        args = ['/system/bin/curl', '-4', '--http1.1', '--noproxy', '*', '--retry', '0', '--connect-timeout', '15',
                '--max-time', '150', '--max-filesize', str(size), '-H', 'Accept-Encoding: identity', '-H', 'Cache-Control: no-cache',
                '--silent', '--show-error', '--output', base + '.body', '--dump-header', base + '.headers',
                '--write-out', ''.join(key + '=%{' + key + '}\n' for key in fields), 'https://speed.cloudflare.com/__down?bytes=' + str(size)]
        command = 'umask 077; read uptime rest < /proc/uptime; echo BEGIN=$uptime; ' + shlex.join(args)
        command += '; result=$?; read uptime rest < /proc/uptime; echo END=$uptime; echo CURL_EXIT=$result; if test -f ' + base + '.body; then echo BODY_BYTES=$(wc -c < ' + base + '.body); echo BODY_SHA256=$(sha256sum ' + base + '.body | cut -d " " -f 1); fi; echo HEADER_BEGIN; cat ' + base + '.headers'
        started = time.time()
        response = adb(command, 170)
        (out / (name + '.stdout')).write_text(response.stdout)
        (out / (name + '.stderr')).write_text(response.stderr)
        text, _, headers = response.stdout.partition('HEADER_BEGIN')
        metrics = dict(line.split('=', 1) for line in text.splitlines() if '=' in line)
        header_map = {key.strip().lower(): value.strip() for key, value in
                      (line.split(':', 1) for line in headers.splitlines() if ':' in line)}
        valid = (response.returncode == 0 and metrics.get('CURL_EXIT') == '0' and metrics.get('http_code') == '200'
                 and metrics.get('ssl_verify_result') == '0' and metrics.get('http_version') == '1.1'
                 and int(metrics.get('BODY_BYTES', '0')) == size and float(metrics.get('size_download', '0')) == size
                 and header_map.get('content-encoding', 'identity').lower() in ('', 'identity')
                 and header_map.get('cf-cache-status', '').upper() not in ('HIT', 'STALE', 'UPDATING')
                 and float(header_map.get('age', '0')) == 0)
        record = dict(name=name, intended_bytes=size, start_epoch=started, end_epoch=time.time(), metrics=metrics,
                      headers=header_map, valid=valid, observed_hash_not_origin_acceptance=True)
        if valid:
            record['mbit_s'] = size * 8 / float(metrics['time_total']) / 1e6
        else:
            stop.set()
        with lock:
            requests.append(record)
            with (out / 'requests.jsonl').open('a') as handle:
                handle.write(json.dumps(record) + '\n')
        adb('rm -f ' + base + '.body ' + base + '.headers').check_returncode()
        print(json.dumps(dict(name=name, valid=valid, status=metrics.get('http_code'), seconds=metrics.get('time_total'), mbit_s=record.get('mbit_s'))), flush=True)
        return record

    parallel = []
    try:
        time.sleep(6)
        if is_small:
            request('small', 65536)
        else:
            for number in range(2):
                assert topology() == initial_topology
                if stop.is_set() or capture.cap_reached or time.monotonic() > deadline - 155:
                    break
                request('single-' + str(number), 2097152)
                if stop.is_set() or capture.cap_reached or time.monotonic() > deadline - 155:
                    break
                with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                    pair = list(pool.map(lambda index: request('parallel-' + str(number) + '-' + str(index), 2097152), range(2)))
                if all(item['valid'] for item in pair):
                    wall = max(float(item['metrics']['END']) for item in pair) - min(float(item['metrics']['BEGIN']) for item in pair)
                    parallel.append(dict(cell=number, wall_seconds=wall, bytes=4194304, aggregate_mbit_s=4194304 * 8 / wall / 1e6))
        time.sleep(7)
    finally:
        capture_result = capture.stop()
        sampler.stdin.close()
        try:
            sampler.wait(timeout=12)
        except subprocess.TimeoutExpired:
            sampler.kill()
            sampler.wait()
        socket_file.close()
        socket_error.close()
        adb('rmdir ' + remote_root)
    records, parser_errors = {}, {}
    for node in ('NL', 'Android'):
        with (out / 'capture' / (node + '-raw.jsonl')).open() as handle:
            records[node], parser_errors[node] = reconstruct(handle)
    result = correlate(records)
    result['parser_errors'] = parser_errors
    (out / 'correlation-private.json').write_text(json.dumps(result, indent=2))
    both = [value for value in result['logical_data'] if len(value['nodes']) == 2 and value['first_submission_observed']
            and value['consumes'] == 1 and 'new' in value['receive_results']]
    socket_rows = [json.loads(line) for line in (out / 'nl-sockets-private.jsonl').read_text().splitlines()]
    matched = sum(any(item['metrics'].get('remote_ip', 'INVALID') + ':443' in entry
                      for row in socket_rows for entry in row['sockets']) for item in requests)
    summary = dict(small_gate_pass=bool(is_small and both and requests and all(item['valid'] for item in requests)
                    and not result['errors'] and not any(parser_errors.values()) and matched == len(requests) and not capture_result['cap_reached']),
                   two_sided_logical_blocks=len(both), snapshot_counts={node: len(values) for node, values in records.items()},
                   parser_error_counts={node: len(values) for node, values in parser_errors.items()},
                   matched_requests=matched, requests=len(requests), parallel=parallel, capture=capture_result,
                   source_gateway=gateway, node_invocation=nl['InvocationID'], application_bytes=sum(int(item['metrics'].get('BODY_BYTES', '0')) for item in requests))
    final_topology = topology()
    summary['topology_stable'] = final_topology == initial_topology
    summary['final_topology'] = final_topology
    summary['small_gate_pass'] = summary['small_gate_pass'] and summary['topology_stable']
    (out / 'result.json').write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary), flush=True)


if __name__ == '__main__':
    main()
