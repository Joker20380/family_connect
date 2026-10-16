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
regressions = 'Test(DeterministicFaultMatrix|WindowBoundsRetryAndStale|SelectiveRetryAndConsumedACKLoss|SlowReceiverAgeAndMalformedACK|MalformedAndConfigurationBounds|HeadLossAndDuplicateVirtualClock|DATA19ACKProofSemantics|AdapterBackpressureCancellation|AdapterExhaustionAndCancellation|CarrierStallAndClose|NegotiatedPayload|FreshACKWithoutProgressDoesNotResetRetryBudget|ExhaustionBranchesRetainBoundedEvidence|ExhaustionRecordedBeforeCarrierCleanup|EstablishedRetryFailurePrecedesCleanup)$'
checks = [
    ('baseline-normal', 'baseline', False, 3, 'TestThroughput'),
    ('candidate-normal', 'candidate', False, 3, 'Test(FastRecovery|Throughput)'),
    ('baseline-race', 'baseline', True, 2, 'TestThroughput'),
    ('candidate-race', 'candidate', True, 2, 'Test(FastRecovery|Throughput)'),
    ('regressions-normal', 'candidate', False, 1, regressions),
    ('regressions-race', 'candidate', True, 1, regressions),
]


def temperature():
    value = int(sensor.read_text())
    if not 0 < value < 120000:
        raise RuntimeError('invalid thermal sensor')
    return value


def interrupted(signum, frame):
    raise InterruptedError('host stop requested')


signal.signal(signal.SIGINT, interrupted)
signal.signal(signal.SIGTERM, interrupted)
receipts = []
batch_started = time.monotonic()
for label, variant, race, count, selected in checks:
    if temperature() >= 75000:
        raise SystemExit('CPU >=75C; not starting the next check')
    command = [str(tools / 'go/bin/go'), 'test', '-p=1', '-json', '-timeout=150s',
               '-count=' + str(count), '-run', selected]
    if race:
        command.append('-race')
    command.append('./reliablestream')
    started = time.monotonic()
    samples = []
    reason = 'command_exit'
    process = None
    logfile = output / (label + '.jsonl')
    print('START', label, flush=True)
    try:
        with logfile.open('xb') as log:
            process = subprocess.Popen(command, cwd=root / variant / 'carrier',
                                       env=environment | {'FC_PERF_VARIANT': variant},
                                       stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            while process.poll() is None:
                samples.append(temperature())
                if samples[-1] >= 85000:
                    reason = 'thermal_cutoff_85C'
                    break
                if time.monotonic() - started >= 240 or time.monotonic() - batch_started >= 900:
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
        receipt = dict(label=label, variant=variant, race=race, fixed_count=count,
                       selected=selected, reason=reason, exit=None if process is None else process.returncode,
                       elapsed_seconds=round(time.monotonic()-started, 3),
                       max_cpu_celsius=max(samples)/1000 if samples else None,
                       log_sha256=hashlib.sha256(logfile.read_bytes()).hexdigest())
        receipts.append(receipt)
        (output / 'receipts.json').write_text(json.dumps(receipts, indent=2) + '\n')
    print('END', json.dumps(receipt), flush=True)
    if reason != 'command_exit' or process.returncode != 0:
        raise SystemExit('STOP: failed check retained; no automatic retry')
