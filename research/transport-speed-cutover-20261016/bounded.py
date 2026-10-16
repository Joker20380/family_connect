import json
import os
from pathlib import Path
import signal
import subprocess
import time


root = Path(__file__).resolve().parent
sensor = next(zone/'temp' for zone in Path('/sys/class/thermal').glob('thermal_zone*')
              if (zone/'type').read_text().strip() == 'x86_pkg_temp')


def temperature():
    value = int(sensor.read_text())
    if not 0 < value < 120000:
        raise RuntimeError('Invalid CPU temperature')
    return value


def interrupt(signum, frame):
    raise InterruptedError('Host requested stop')


if temperature() >= 75000:
    raise RuntimeError('CPU >=75C; not starting')
signal.signal(signal.SIGTERM, interrupt)
signal.signal(signal.SIGINT, interrupt)
started = time.monotonic()
reason = 'command_exit'
process = None
samples = []
try:
    process = subprocess.Popen(['python3', str(root/'build.py')], start_new_session=True)
    while process.poll() is None:
        samples.append(temperature())
        if samples[-1] >= 85000:
            reason = 'temperature_limit_85C'
            break
        if time.monotonic() - started >= 1800:
            reason = 'bounded_runtime_limit'
            break
        time.sleep(2)
except BaseException as error:
    reason = type(error).__name__
    raise
finally:
    if process is not None:
        try:
            os.killpg(process.pid, signal.SIGTERM)
            time.sleep(2)
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait(timeout=10)
    receipt = dict(reason=reason, elapsed_seconds=round(time.monotonic()-started,3),
                   exit=None if process is None else process.returncode,
                   maximum_cpu_celsius=max(samples)/1000 if samples else None,
                   cpu_quota='50%', start_limit_celsius=75, stop_limit_celsius=85, emulator=False)
    (root/'thermal.json').write_text(json.dumps(receipt,indent=2)+'\n')
raise SystemExit(process.returncode if reason == 'command_exit' else 2)
