import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time


parser = argparse.ArgumentParser()
parser.add_argument('--repo', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
repo = args.repo.resolve()
output = args.output.resolve()
output.mkdir(mode=0o700)
fixtures = Path(__file__).resolve().parent
state = repo / 'state-client-build'
tools = state / 'field65-export16/diag-source-freeze-1/resume-tools'
sources = {
    'candidate': state / 'transport-speed-cutover-1/source/carrier',
    'previous': state / 'ui60-layout-current-style-1/source/carrier',
}
selected = ['go.mod', 'go.sum', 'wholedevice/session.go', 'tcpforward/mux.go',
            'tcpforward/mux_stream.go', 'tcpforward/mux_dns.go', 'tcpforward/policy.go',
            'tcpforward/integration_test.go', 'familysession/session.go',
            'reliablestream/engine.go', 'roombroker/lease_control.go']
def digest(filename):
    return hashlib.sha256(filename.read_bytes()).hexdigest()

before = {variant: {name: digest(source / name) for name in selected}
          for variant, source in sources.items()}
for name in ('wholedevice/session.go', 'tcpforward/mux.go', 'tcpforward/mux_stream.go',
             'tcpforward/mux_dns.go', 'roombroker/lease_control.go'):
    assert before['candidate'][name] == before['previous'][name], name
assert before['candidate']['reliablestream/engine.go'] != before['previous']['reliablestream/engine.go']
inputs = dict(sources=before, fixtures={name: digest(fixtures / name) for name in
    ['run.py', 'admission_export_test.go', 'browser_admission_test.go']})
(output / 'inputs.json').write_text(json.dumps(inputs, indent=2) + '\n')
sensor = next(zone / 'temp' for zone in Path('/sys/class/thermal').glob('thermal_zone*')
              if (zone / 'type').read_text().strip() == 'x86_pkg_temp')
environment = os.environ | dict(GOMAXPROCS='1', GOTOOLCHAIN='local', GOWORK='off',
    GOPROXY='off', GOSUMDB='off', GOFLAGS='-mod=readonly', GOCACHE=str(tools / 'go-cache'),
    GOPATH=str(tools / 'gopath'), GOMODCACHE=str(tools / 'gopath/pkg/mod'))
receipts = []
batch_started = time.monotonic()

def temperature():
    value = int(sensor.read_text())
    if not 0 < value < 120000:
        raise RuntimeError('invalid CPU sensor')
    return value

def interrupt(signum, frame):
    raise InterruptedError('host stop')

signal.signal(signal.SIGTERM, interrupt)
signal.signal(signal.SIGINT, interrupt)
try:
    for mode, count in [('normal', 2), ('race', 1)]:
        for variant, source in sources.items():
            if temperature() >= 75000:
                raise RuntimeError('CPU >=75C; not starting')
            label = variant + '-' + mode
            mapping = {}
            for name in ('admission_export_test.go', 'browser_admission_test.go'):
                target = source / 'tcpforward' / name
                assert not target.exists(), target
                mapping[str(target)] = str(fixtures / name)
            overlay = output / (label + '-overlay.json')
            overlay.write_text(json.dumps({'Replace': mapping}))
            command = [str(tools / 'go/bin/go'), 'test', '-overlay=' + str(overlay),
                       '-p=1', '-count=' + str(count), '-failfast', '-timeout=120s', '-v']
            if mode == 'race':
                command.append('-race')
            command += ['./tcpforward', '-run', '^TestBrowserAdmission']
            process = None
            started = time.monotonic()
            samples = []
            reason = 'command_exit'
            logfile = output / (label + '.log')
            print('START', label, flush=True)
            try:
                with logfile.open('xb') as log:
                    process = subprocess.Popen(command, cwd=source, env=environment,
                        stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                    while process.poll() is None:
                        samples.append(temperature())
                        if samples[-1] >= 85000:
                            reason = 'thermal_cutoff_85C'
                            break
                        if time.monotonic() - started > 240 or time.monotonic() - batch_started > 700:
                            reason = 'finite_time_limit'
                            break
                        time.sleep(1)
            except BaseException as error:
                reason = type(error).__name__
                raise
            finally:
                if process is not None and process.poll() is None:
                    os.killpg(process.pid, signal.SIGTERM)
                    try:
                        process.wait(timeout=8)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait(timeout=5)
                receipt = dict(label=label, count=count, reason=reason,
                    exit=None if process is None else process.returncode,
                    seconds=round(time.monotonic() - started, 3),
                    max_cpu_celsius=max(samples)/1000 if samples else None,
                    log_sha256=digest(logfile))
                receipts.append(receipt)
                (output / 'receipts.json').write_text(json.dumps(receipts, indent=2)+'\n')
            print('END', json.dumps(receipt), flush=True)
            if reason != 'command_exit' or process.returncode != 0:
                raise RuntimeError('failed check retained; no automatic retry')
finally:
    after = {variant: {name: digest(source / name) for name in selected}
             for variant, source in sources.items()}
    unchanged = before == after
    (output / 'source-unchanged.json').write_text(json.dumps({'selected_sources_unchanged': unchanged})+'\n')
    assert unchanged, 'retained source changed'
