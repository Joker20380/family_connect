import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


root = Path(__file__).resolve().parent
tools = root.parent / 'field65-export16/diag-source-freeze-1/resume-tools'
output = root / sys.argv[1]
output.mkdir(mode=0o700)
sensor = next(zone / 'temp' for zone in Path('/sys/class/thermal').glob('thermal_zone*')
              if (zone / 'type').read_text().strip() == 'x86_pkg_temp')
environment = os.environ | {
    'GOMAXPROCS': '1', 'GOTOOLCHAIN': 'local', 'GOWORK': 'off',
    'GOPROXY': 'off', 'GOSUMDB': 'off', 'GOFLAGS': '-mod=readonly',
    'GOCACHE': str(tools / 'go-cache'), 'GOPATH': str(tools / 'gopath'),
    'GOMODCACHE': str(tools / 'gopath/pkg/mod'),
}
receipts = []
batch_start = time.monotonic()


def temperature():
    value = int(sensor.read_text())
    if not 0 < value < 120000:
        raise RuntimeError('invalid thermal sensor')
    return value


def interrupt(signum, frame):
    raise InterruptedError('host requested stop')


signal.signal(signal.SIGINT, interrupt)
signal.signal(signal.SIGTERM, interrupt)


def run(label, command, cwd, extra=None):
    if temperature() >= 75000:
        raise SystemExit('CPU >=75C; not starting')
    started = time.monotonic()
    samples = []
    process = None
    reason = 'command_exit'
    logfile = output / (label + '.log')
    print('START', label, flush=True)
    try:
        with logfile.open('xb') as log:
            process = subprocess.Popen(command, cwd=cwd, env=environment | (extra or {}),
                                       stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            while process.poll() is None:
                samples.append(temperature())
                if samples[-1] >= 85000:
                    reason = 'thermal_cutoff_85C'
                    break
                if time.monotonic() - started > 420 or time.monotonic() - batch_start > 1500:
                    reason = 'finite_runtime_limit'
                    break
                time.sleep(1)
    except BaseException as error:
        reason = type(error).__name__
        raise
    finally:
        if process is not None and process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=5)
        receipt = dict(label=label, reason=reason, exit=None if process is None else process.returncode,
                       elapsed_seconds=round(time.monotonic()-started, 3),
                       max_cpu_celsius=max(samples)/1000 if samples else None,
                       log_sha256=hashlib.sha256(logfile.read_bytes()).hexdigest())
        receipts.append(receipt)
        (output / 'receipts.json').write_text(json.dumps(receipts, indent=2)+'\n')
    print('END', json.dumps(receipt), flush=True)
    if reason != 'command_exit' or process.returncode != 0:
        raise SystemExit('failed check retained; no automatic retry')


for mode, count in [('normal', 1), ('race', 1)]:
    binaries = {}
    for variant in ('baseline', 'candidate'):
        binary = output / (variant + '-' + mode)
        command = [str(tools / 'go/bin/go'), 'test', '-p=1', '-c', '-o', str(binary)]
        if mode == 'race':
            command.append('-race')
        command.append('./telemost')
        run('build-'+variant+'-'+mode, command, root / ('gateway-'+variant) / 'carrier')
        binaries[variant] = binary
    run('matrix-'+mode, [str(binaries['candidate']), '-test.v', '-test.failfast', '-test.run=^TestFullStackMatrix$',
                        '-test.count='+str(count), '-test.timeout=400s'], root,
        {'FC_STACK_BASELINE': str(root/'run-2'/('baseline-'+mode)),
         'FC_STACK_CANDIDATE': str(root/'run-2'/('candidate-'+mode)),
         'FC_STACK_SERVER_BASELINE': str(binaries['baseline']), 'FC_STACK_SERVER_CANDIDATE': str(binaries['candidate'])})
(output / 'binaries.json').write_text(json.dumps({filename.name: hashlib.sha256(filename.read_bytes()).hexdigest()
    for filename in output.iterdir() if filename.is_file() and filename.suffix == ''}, indent=2)+'\n')
