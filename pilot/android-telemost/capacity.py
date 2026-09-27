#!/usr/bin/env python3
"""Explicit bounded physical performance points, gated by a canonical baseline."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def baseline_result(path):
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    candidates = [row for row in rows if row.get('event') == 'probe_result'
                  and row.get('payload_bytes') == 16384 and row.get('elapsed_s', 0) >= 60
                  and row.get('byte_equal') and row.get('carrier_mode') == 'vp8']
    if not any(row.get('event') == 'family_auth' and row.get('accepted') for row in rows):
        raise ValueError('Baseline is not Family authenticated')
    if not candidates:
        raise ValueError('No canonical >=60s 16KiB baseline')
    result = candidates[-1]
    if not 1600 <= result['mean_rtt_ms'] <= 2500 or not 0.05 <= result['useful_oneway_mbit_s'] <= 0.08:
        raise ValueError('Baseline mismatch; performance sweep must stop')
    if not any(row.get('event') == 'android_exit' and row.get('code') == 0 for row in rows):
        raise ValueError('Baseline did not terminate successfully')
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--adb', required=True)
    parser.add_argument('--binary', type=Path, required=True)
    parser.add_argument('--family-dir', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--windows', type=int, nargs='+', default=[1, 2, 4, 8, 16, 32, 64])
    parser.add_argument('--rates', type=float, nargs='+')
    parser.add_argument('--payload', type=int, default=16384)
    parser.add_argument('--seconds', type=int, default=60)
    args = parser.parse_args()
    baseline = baseline_result(args.baseline)
    if not 1 <= args.seconds <= 300 or not 1024 <= args.payload <= 65536 or any(window not in (1, 2, 4, 8, 16, 32, 64, 128) for window in args.windows):
        parser.error('point exceeds bounded test scope')
    if args.rates and any(rate not in (0.1, 0.25, 0.5, 1, 2, 4) for rate in args.rates):
        parser.error('rate exceeds approved sweep')
    args.out.mkdir(mode=0o700, parents=True, exist_ok=False)
    metadata = {'baseline': baseline, 'binary_sha256': hashlib.sha256(args.binary.read_bytes()).hexdigest(),
                'classification': 'accepted_duration_candidate' if args.seconds >= 60 else 'discovery_only'}
    (args.out / 'metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
    points = [(128, rate) for rate in args.rates] if args.rates else [(window, 0) for window in args.windows]
    for window, rate in points:
        name = f'rate-{rate:g}' if rate else f'window-{window}'
        config = args.out / (name + '.json')
        config.write_text(json.dumps({'window': window, 'rate_mbit_s': rate, 'payload': args.payload,
                                     'seconds': args.seconds, 'warmup_seconds': 5}) + '\n')
        print('POINT_START', name, args.payload, args.seconds, flush=True)
        result = subprocess.run([sys.executable, str(Path(__file__).with_name('live.py')),
                                 '--adb', args.adb, '--binary', str(args.binary), '--family-dir', str(args.family_dir),
                                 '--independent-observer', '--performance-config', str(config), '--out', str(args.out / name)])
        evidence = args.out / name / 'A.jsonl'
        rows = [json.loads(line) for line in evidence.read_text().splitlines()] if evidence.exists() else []
        measurements = [row for row in rows if row.get('event') == 'perf_result']
        if measurements:
            point = measurements[-1]
            print('POINT_RESULT', name, point['status'], point['reason'], point['delivered_mbit_s'],
                  point.get('avg_rtt_ms'), point['errors'], flush=True)
        if result.returncode:
            raise SystemExit('POINT_FAILED; evidence retained; no automatic retry or higher load')


if __name__ == '__main__':
    main()
