import os
from pathlib import Path
import signal
import subprocess
import threading
import time


def stop(process):
    if process.poll() is None:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass


def start(command, environment, log, record, observe=None, on_abort=None):
    process = subprocess.Popen(
        ['systemd-run', '--user', '--scope', '--quiet', '-p', 'CPUQuota=100%', '--'] + command,
        env=environment, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)

    def watch():
        began = time.monotonic()
        try:
            while process.poll() is None:
                cpu = []
                for device in Path('/sys/class/hwmon').glob('hwmon*'):
                    if (device / 'name').read_text().strip() in ('coretemp', 'k10temp'):
                        cpu.extend(int(path.read_text()) / 1000 for path in device.glob('temp*_input'))
                if not cpu:
                    raise RuntimeError('CPU_TEMPERATURE_UNAVAILABLE')
                cpu_max = max(cpu)
                gpu = int(subprocess.check_output(
                    ['nvidia-smi', '--query-gpu=temperature.gpu', '--format=csv,noheader,nounits'],
                    text=True, timeout=5).strip().splitlines()[0])
                record['peak_cpu_c'] = max(record.get('peak_cpu_c', cpu_max), cpu_max)
                record['peak_gpu_c'] = max(record.get('peak_gpu_c', gpu), gpu)
                frame = observe(False) if observe else None
                if cpu_max >= 85 or gpu >= 80 or time.monotonic() - began >= 180:
                    record['host_safety_abort'] = True
                    record['guard_cpu_c'] = cpu_max
                    record['guard_gpu_c'] = gpu
                    record['guard_elapsed_seconds'] = time.monotonic() - began
                    if on_abort:
                        on_abort(frame)
                    stop(process)
                    return
                time.sleep(3)
        except Exception:
            record['host_safety_monitor_failed'] = True
            stop(process)

    threading.Thread(target=watch, daemon=True).start()
    return process
