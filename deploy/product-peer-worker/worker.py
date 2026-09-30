"""Bounded fresh reconciliation processes inside one long-lived container."""
import argparse
import json
import os
import signal
import subprocess
import sys
import threading


def run_cycle(command, timeout):
    process = subprocess.Popen(command, start_new_session=True,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        return process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()
        return 124


def run_loop(command, stop, interval=15, timeout=60):
    while not stop.is_set():
        try:
            status = run_cycle(command, timeout)
        except OSError:
            status = 127
        print(json.dumps({'event': 'peer-reconcile-cycle', 'exit_code': status}), flush=True)
        stop.wait(interval)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--database', required=True)
    parser.add_argument('--gateways', required=True)
    args = parser.parse_args()
    stop = threading.Event()
    for signum in (signal.SIGTERM, signal.SIGINT):
        signal.signal(signum, lambda *_: stop.set())
    command = [sys.executable, '-m', 'control.product.admin', '--database',
               args.database, 'reconcile-peers', '--gateways', args.gateways]
    run_loop(command, stop)


if __name__ == '__main__':
    main()
