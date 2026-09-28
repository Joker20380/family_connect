"""One authenticated physical session per case; no retries or gate promotion."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

from tcp_acceptance import Fixture


def validate_mux_evidence(case, android, gateway):
    for rows in (android, gateway):
        admitted = [row for row in rows if row.get('event') == 'family_auth' and row.get('accepted')]
        if len(admitted) != 1:
            raise RuntimeError('exactly one Family admission required per endpoint')
    result = [row for row in android if row.get('event') == 'mux_result']
    if len(result) != 1 or result[0]['status'] != 'PASS':
        raise RuntimeError('mux case incomplete')
    guards = [row for row in android if row.get('event') == 'mux_dns_guard']
    if len(guards) != 2 or guards[0].get('negative_probe_blocked') is not True or guards[-1].get('phase') != 'final' or guards[-1].get('post_probe_calls') != 0:
        raise RuntimeError('negative local DNS condition or zero local lookup proof missing')
    if not any(row.get('event') == 'android_start' and row.get('network') == 'cellular' for row in android):
        raise RuntimeError('cellular environment not proven')
    dns = [row for row in android if row.get('event') == 'mux_dns']
    if len(dns) < 3 or not all(row['passed'] for row in dns):
        raise RuntimeError('Family DNS proof failed')
    if not {1, 28}.issubset({row['query_type'] for row in dns}) or not any(row['nxdomain'] and row['rcode'] == 3 for row in dns):
        raise RuntimeError('A/AAAA/NXDOMAIN incomplete')
    if case == 'public':
        https = [row for row in android if row.get('event') == 'mux_https']
        if len(https) != 4 or len({row['stream_id'] for row in https}) != 4 or not all(row['passed'] and row['end_site_tls_verified'] and row['http_status'] == 200 for row in https):
            raise RuntimeError('four verified public HTTPS streams required')
    else:
        bulk = [row for row in android if row.get('event') == 'mux_bulk']
        if len(bulk) != 1 or not bulk[0]['passed'] or bulk[0]['seconds'] < 300 or bulk[0]['bytes_each_direction'] < 10 * 1024 * 1024:
            raise RuntimeError('mixed bulk acceptance incomplete')
        small = [row for row in android if row.get('event') == 'mux_stream']
        if len(small) != 4 or not all(row['passed'] and row['stream']['Sent'] > 0 for row in small):
            raise RuntimeError('interactive streams missing')
        isolation = [row for row in android if row.get('event') == 'mux_isolation']
        if len(isolation) != 3 or not all(row['passed'] for row in isolation):
            raise RuntimeError('live stream isolation missing')
    final = [row for row in gateway if row.get('event') == 'mux_gateway']
    if len(final) != 1 or final[0]['stats']['ActiveSockets'] != 0 or final[0]['stats']['RetainedBytes'] != 0:
        raise RuntimeError('gateway socket/buffer cleanup unproven')
    return result[0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--adb', required=True)
    parser.add_argument('--binary', type=Path, required=True)
    parser.add_argument('--family-dir', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--case', choices=['public', 'mixed'], required=True)
    args = parser.parse_args()
    if not os.environ.get('FC_TELEMOST_ROOM'):
        raise RuntimeError('private room environment missing')
    args.out.mkdir(mode=0o700, parents=True, exist_ok=False)
    fixture = None
    try:
        config = {'mode': args.case}
        if args.case == 'mixed':
            fixture = Fixture('186.246.45.246', args.out / 'fixture.jsonl', Path(__file__).with_name('mux_fixture.py'))
            config.update(seconds=300, port=fixture.start('echo', False))
        path = args.out / 'request.json'
        path.write_text(json.dumps(config))
        command = [sys.executable, str(Path(__file__).with_name('live.py')), '--adb', args.adb,
                   '--binary', str(args.binary), '--family-dir', str(args.family_dir),
                   '--independent-observer', '--mux-config', str(path), '--upload-timeout', '180', '--out', str(args.out / 'flow')]
        if fixture:
            command += ['--tcp-test-loopback-port', str(config['port'])]
        with (args.out / 'runner.log').open('wb') as output:
            run = subprocess.run(command, stdout=output, stderr=output, timeout=1600)
        if run.returncode:
            raise RuntimeError('mux runner failed; preserve attempt')
        android = [json.loads(line) for line in (args.out / 'flow/A.jsonl').read_text().splitlines()]
        gateway = [json.loads(line) for line in (args.out / 'flow/B.jsonl').read_text().splitlines()]
        result = validate_mux_evidence(args.case, android, gateway)
        if fixture:
            target = [row for row in fixture.collect() if row.get('event') == 'fixture_result']
            if len(target) != 7 or sum(row['eof'] and row['bytes'] > 128 for row in target) != 5:
                raise RuntimeError('fixture EOF incomplete')
            bulk = next(row for row in android if row.get('event') == 'mux_bulk')
            if max(row['bytes'] for row in target) != bulk['bytes_each_direction']:
                raise RuntimeError('target bulk count mismatch')
            if max(target, key=lambda row: row['bytes'])['sha256'] != bulk['sha256']:
                raise RuntimeError('target bulk hash mismatch')
        print(json.dumps({'case': args.case, 'result': result}), flush=True)
    finally:
        if fixture:
            fixture.close()


if __name__ == '__main__':
    main()
