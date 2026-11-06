"""Run the existing scheduled controller without racing its directory publisher."""
import argparse
import json
from pathlib import Path
import signal
import subprocess
import sys
import time


TIMER = 'family-connect-restricted-directory-sync.timer'
SERVICE = 'family-connect-restricted-directory-sync.service'


def systemctl(*arguments):
    return subprocess.check_output(['systemctl', *arguments], text=True, timeout=20)


def state(unit, control=systemctl):
    raw = control('show', unit, '-p', 'LoadState', '-p', 'ActiveState', '-p', 'MainPID')
    values = dict(line.split('=', 1) for line in raw.splitlines())
    if values.get('LoadState') != 'loaded':
        raise RuntimeError('DIRECTORY_UNIT_UNAVAILABLE')
    return values


def run_serialized(controller, *, control=systemctl, clock=time.monotonic, sleep=time.sleep):
    before = state(TIMER, control)
    if before['ActiveState'] not in ('active', 'inactive'):
        raise RuntimeError('DIRECTORY_TIMER_TRANSITION')
    restore = before['ActiveState'] == 'active'
    try:
        control('stop', TIMER)
        deadline = clock() + 120
        while True:
            current = state(SERVICE, control)
            if current['ActiveState'] in ('inactive', 'failed') and current.get('MainPID') == '0':
                break
            if clock() >= deadline:
                raise RuntimeError('DIRECTORY_WRITER_NOT_QUIESCENT')
            sleep(1)
        return controller()
    finally:
        if restore:
            control('start', TIMER)
            if state(TIMER, control)['ActiveState'] != 'active':
                raise RuntimeError('DIRECTORY_TIMER_NOT_RESTORED')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--config', type=Path, required=True)
    arguments = parser.parse_args()
    configuration = json.loads(arguments.config.read_text())
    if configuration.get('schema') != 2 or configuration.get('approved_leaf_crl_schedule') is not True:
        raise RuntimeError('APPROVED_FLEET_SCHEDULE_REQUIRED')

    def interrupted(signum, frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, interrupted)
    command = [sys.executable, '-E', '-s', '-B', str(arguments.runtime / 'runtime_controller.py'),
               '--config', str(arguments.config), '--mode', 'scheduled']
    return run_serialized(lambda: subprocess.run(command, check=False).returncode)


if __name__ == '__main__':
    raise SystemExit(main())
