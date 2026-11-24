"""Finite RU-only counter/phase observation; never changes access or persistence."""
import argparse
from collections import Counter, deque
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import selectors
import signal
import socket
import subprocess
import time

NODE = Path('/opt/apps/family_connect/friends-awg')
ARCHIVE_SHA = '125c796a30c3fba1772c47b96963517350087ad04aad675b6f33a31a5383276c'
GATEWAY_SHA = '9023d2c3f7c3a5127d67c509a16eb2d974810ff54d5b76cc225cd9b93e0b4234'
UNIT = 'family-connect-paid-watch.service'
OUTPUT = Path('/run/family-connect-ru-pressure')
SAMPLE_BYTES = 96 * 1024
CAPTURE_BYTES = 8 * 1024 * 1024
INTERVAL = 5
VM_KEYS = {'pswpin', 'pswpout', 'pgmajfault', 'pgpgin', 'pgpgout', 'nr_dirty', 'nr_writeback',
           'allocstall_normal', 'pgscan_direct', 'pgscan_kswapd', 'pgsteal_direct', 'pgsteal_kswapd'}
MEM_KEYS = {'MemTotal', 'MemAvailable', 'SwapTotal', 'SwapFree', 'Dirty', 'Writeback'}
CG_KEYS = {'anon', 'file', 'kernel', 'pagetables', 'swapcached', 'pgmajfault', 'pgscan', 'pgsteal',
           'workingset_refault_anon', 'workingset_refault_file'}


def text(path, limit=65536):
    with path.open() as stream:
        value = stream.read(limit + 1)
    if len(value) > limit:
        raise ValueError('counter_too_large')
    return value


def counters(raw, keys):
    result = {}
    for line in raw.splitlines():
        fields = line.replace(':', ' ').split()
        if len(fields) >= 2 and fields[0] in keys:
            result[fields[0]] = int(fields[1])
    return result


def process(path):
    raw = text(path / 'stat', 4096)
    closing = raw.rindex(')')
    fields = raw[closing + 2:].split()
    result = dict(pid=int(path.name), name=raw[raw.index('(') + 1:closing][:64], state=fields[0],
                  majflt=int(fields[9]), cpu_ticks=int(fields[11]) + int(fields[12]),
                  start_ticks=int(fields[19]), rss_pages=int(fields[21]))
    if int(fields[6]) & 0x00200000:
        result.update(kernel=True, cgroup='/', kernel_io_sampled=result['name'].startswith('jbd2/'))
        if result['kernel_io_sampled']:
            result.update(counters(text(path / 'io', 4096), {'read_bytes', 'write_bytes', 'cancelled_write_bytes'}))
        return result
    result.update(counters(text(path / 'io', 4096), {'read_bytes', 'write_bytes', 'cancelled_write_bytes'}))
    result.update(counters(text(path / 'status', 8192), {'VmRSS', 'VmSwap'}))
    result['cgroup'] = next(line[3:] for line in text(path / 'cgroup', 4096).splitlines() if line.startswith('0::'))
    return result


def cgroup(path):
    result = {name: int(text(path / name, 128)) for name in ('memory.current', 'memory.swap.current')}
    result['memory'] = counters(text(path / 'memory.stat'), CG_KEYS)
    result['events'] = counters(text(path / 'memory.events'), {'low', 'high', 'max', 'oom', 'oom_kill'})
    result['io'] = text(path / 'io.stat', 8192)
    result['pressure'] = {name: text(path / (name + '.pressure'), 1024) for name in ('cpu', 'memory', 'io')}
    return result


def encode(value):
    return json.dumps(value, separators=(',', ':'), sort_keys=True).encode()


def bounded_sample(value):
    size = len(encode(value))
    while size > SAMPLE_BYTES:
        while size > SAMPLE_BYTES:
            if len(value['processes']) > 1:
                size -= len(encode(value['processes'].pop())) + 1
                value['processes_omitted'] += 1
            elif value['cgroups']:
                name = next(reversed(value['cgroups']))
                size -= len(encode({name: value['cgroups'].pop(name)})) - 1
                value['cgroups_omitted'] += 1
            else:
                raise ValueError('sample_budget_exceeded')
        size = len(encode(value))
    return value


def sample(watcher, proc=Path('/proc'), groups=Path('/sys/fs/cgroup')):
    started = time.monotonic()
    cpu_started = time.process_time()
    result = dict(wall=time.time(), mono_ns=time.monotonic_ns(), processes=[], cgroups={},
                  processes_omitted=0, cgroups_omitted=0, races=0)
    result['mem'] = counters(text(proc / 'meminfo'), MEM_KEYS)
    result['vm'] = counters(text(proc / 'vmstat'), VM_KEYS)
    result['pressure'] = {name: text(proc / 'pressure' / name, 1024) for name in ('cpu', 'memory', 'io')}
    result['disk'] = [line for line in text(proc / 'diskstats').splitlines() if line.split()[2] == 'vda']
    result['cpu'] = text(proc / 'stat').splitlines()[0]
    paths = sorted((path for path in proc.iterdir() if path.name.isdigit()), key=lambda path: int(path.name))
    result['processes_omitted'] = max(0, len(paths) - 512)
    for path in sorted(paths, key=lambda path: int(path.name) != watcher)[:512]:
        try:
            result['processes'].append(process(path))
        except (OSError, ValueError, IndexError, StopIteration):
            result['races'] += 1
    result['processes'].sort(key=lambda item: (item['pid'] == watcher, item.get('VmSwap', 0), item['rss_pages']), reverse=True)
    names = list(dict.fromkeys(item['cgroup'] for item in result['processes']))
    result['cgroups_omitted'] = max(0, len(names) - 64)
    for name in names[:64]:
        if '..' in Path(name).parts:
            continue
        try:
            result['cgroups'][name] = cgroup(groups / name.lstrip('/'))
        except (OSError, ValueError):
            result['races'] += 1
    bounded_sample(result)
    result['sample_seconds'] = time.monotonic() - started
    result['sample_cpu_seconds'] = time.process_time() - cpu_started
    return result


def phase(line):
    fields = line.split()
    if len(fields) != 7 or fields[0] != 'EV' or fields[1] not in ('F', 'R', 'Q'):
        return None
    values = [int(value) for value in fields[2:]]
    if any(value < 0 for value in values[:3]) or values[4] < 0 or values[1] > {'F': 4, 'R': 2, 'Q': 2}[fields[1]]:
        raise ValueError('invalid_phase')
    return dict(kind=fields[1], mono_ns=values[0], phase=values[1], duration_ns=values[2], result=values[3], bytes=values[4])


def health(root=NODE):
    state = json.loads(text(root / 'transport-state.json', 4 * 1024 * 1024))
    attempt = json.loads(text(root / 'transport-attempt.json', 4096))
    records = list(state['records'].values())
    allowed = [value for value in records if value.get('applied', {}).get('allowed')]
    return dict(observed_at=state['observed_at'], attempt=attempt.get('result'), attempt_at=attempt['observed_at'],
                records=len(records), allowed=len(allowed), applied=sum(value.get('applied', {}).get('result') == 'applied' for value in records),
                lease_min=min((value['decision']['valid_until'] for value in allowed), default=None),
                lease_max=max((value['decision']['valid_until'] for value in allowed), default=None))


def first_failure(path):
    raw = text(path, 65536)
    value = json.loads(raw)
    fields = ('schema', 'mode', 'phase', 'exception_class', 'reason', 'pid', 'invocation_id',
              'observed_at', 'elapsed', 'budget', 'boundary', 'calls_dropped', 'stage_counts')
    result = {name: value[name] for name in fields if name in value}
    call_fields = ('kind', 'role', 'entered', 'started', 'finished', 'duration', 'completed',
                   'boundary', 'remaining', 'replace_completed', 'major_faults', 'input_blocks',
                   'output_blocks', 'user_cpu', 'system_cpu', 'voluntary_switches', 'involuntary_switches')
    result['calls'] = [{name: call[name] for name in call_fields if name in call} for call in value.get('calls', [])[:24]]
    result['sha256'] = hashlib.sha256(raw.encode()).hexdigest()
    return result


def save(path, value):
    raw = encode(value)
    if len(raw) > CAPTURE_BYTES:
        raise ValueError('capture_budget_exceeded')
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'wb') as stream:
        stream.write(raw)


def trace_limits():
    resource.setrlimit(resource.RLIMIT_FSIZE, (1024 * 1024, 1024 * 1024))


def run(output, seconds, watcher, trace):
    samples, phases = deque(maxlen=60), deque(maxlen=4096)
    started = time.monotonic()
    metadata = dict(schema=1, started_at=time.time(), deadline_at=time.time() + seconds,
                    archive_sha256=ARCHIVE_SHA, gateway_sha256=GATEWAY_SHA, watcher=watcher,
                    boot_id=text(Path('/proc/sys/kernel/random/boot_id')).strip(), interval=INTERVAL,
                    source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    trace_sha256=hashlib.sha256(trace.read_bytes()).hexdigest(),
                    clock_ticks=os.sysconf('SC_CLK_TCK'), page_size=os.sysconf('SC_PAGE_SIZE'),
                    phase_names={'F': ['unknown', 'state_file', 'attempt_file', 'state_directory', 'attempt_directory'],
                                 'R': ['unknown', 'state_replace', 'attempt_replace'], 'Q': ['unknown_child', 'awg_child', 'tcp_child']})
    metadata['timers'] = subprocess.check_output(['systemctl', 'list-timers', '--all', '--no-pager', '--no-legend'], timeout=5).decode()[:32768]
    metadata['invocation_id'] = subprocess.check_output(['systemctl', 'show', UNIT, '-p', 'InvocationID', '--value'], timeout=5).decode().strip()
    save(output / 'start.json', metadata)
    counts, total_ns, byte_counts, maxima = Counter(), Counter(), Counter(), Counter()
    lost = 0
    failure = None
    reason = 'duration_limit'
    slow_saved = False
    stopped = []
    trace_errors = output / 'trace-errors.txt'
    original_start = process(Path('/proc') / str(watcher))['start_ticks']
    with trace_errors.open('xb') as errors:
        child = subprocess.Popen(['/usr/bin/bpftrace', '-q', '-B', 'line', str(trace), str(watcher)],
                                 stdout=subprocess.PIPE, stderr=errors, start_new_session=True,
                                 preexec_fn=trace_limits,
                                 env=dict(os.environ, BPFTRACE_MAP_KEYS_MAX='256', BPFTRACE_PERF_RB_PAGES='8'))
        old_handlers = {number: signal.signal(number, lambda number, frame: stopped.append(number))
                        for number in (signal.SIGTERM, signal.SIGINT)}
        selector = selectors.DefaultSelector()
        os.set_blocking(child.stdout.fileno(), False)
        selector.register(child.stdout, selectors.EVENT_READ)
        pending = b''
        next_sample = started
        try:
            while time.monotonic() - started < seconds:
                if stopped:
                    reason = 'operator_stop'
                    break
                if child.poll() is not None:
                    reason = 'tracer_exited'
                    break
                for key, unused in selector.select(timeout=max(0, min(0.5, next_sample - time.monotonic()))):
                    chunk = os.read(key.fd, 65536)
                    if not chunk:
                        continue
                    pending += chunk
                    if len(pending) > 131072:
                        raise ValueError('trace_buffer_limit')
                    while b'\n' in pending:
                        raw, pending = pending.split(b'\n', 1)
                        line = raw.decode(errors='replace')
                        event = phase(line)
                        if event:
                            phases.append(event)
                            label = event['kind'] + str(event['phase'])
                            counts[label] += 1
                            total_ns[label] += event['duration_ns']
                            byte_counts[label] += event['bytes']
                            maxima[label] = max(maxima[label], event['duration_ns'])
                            if event['duration_ns'] >= 500_000_000 and not slow_saved and samples:
                                save(output / 'slow.json', dict(metadata=metadata, trigger=event, samples=list(samples), phases=list(phases)))
                                slow_saved = True
                        elif 'lost' in line.lower():
                            lost += 1
                if time.monotonic() < next_sample:
                    continue
                current = sample(watcher)
                samples.append(current)
                next_sample = time.monotonic() + INTERVAL
                failure_path = NODE / 'transport-failure.json'
                if failure_path.exists():
                    failure = first_failure(failure_path)
                    reason = 'first_failure'
                    break
                current['health'] = health()
                if not any(item['pid'] == watcher and item['start_ticks'] == original_start for item in current['processes']):
                    reason = 'watcher_changed'
                    break
                if current['mem'].get('MemAvailable', 0) < 262144:
                    reason = 'memory_floor'
                    break
                if current['sample_seconds'] > 10 or current['sample_cpu_seconds'] > 0.2:
                    reason = 'sample_cost_limit'
                    break
                if time.monotonic() - started > 45 and not counts:
                    reason = 'no_phase_events'
                    break
        except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
            reason = type(error).__name__
        finally:
            selector.close()
            if child.poll() is None:
                os.killpg(child.pid, signal.SIGINT)
                try:
                    child.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid, signal.SIGKILL)
                    child.wait(timeout=2)
            child.stdout.close()
            for number, handler in old_handlers.items():
                signal.signal(number, handler)
    with trace_errors.open() as stream:
        error_text = stream.read(1024 * 1024)
    lost += sum('lost' in line.lower() for line in error_text.splitlines())
    usage = resource.getrusage(resource.RUSAGE_SELF)
    summary = dict(reason=reason, elapsed=time.monotonic() - started, counts=dict(counts),
                   duration_ns=dict(total_ns), maxima_ns=dict(maxima), bytes=dict(byte_counts),
                   lost_indications=lost, failure=failure, self_cpu=usage.ru_utime + usage.ru_stime,
                   self_maxrss_kib=usage.ru_maxrss, tracer_returncode=child.returncode,
                   tracer_errors_truncated=trace_errors.stat().st_size > 1024 * 1024)
    save(output / 'final.json', dict(metadata=metadata, summary=summary, samples=list(samples), phases=list(phases)))
    print(json.dumps(summary))
    return 0 if reason in ('duration_limit', 'first_failure', 'watcher_changed', 'memory_floor', 'sample_cost_limit', 'operator_stop') else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seconds', type=int, required=True)
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    if not 180 <= arguments.seconds <= 86400:
        parser.error('Duration must be 180..86400 seconds')
    if os.geteuid() != 0 or socket.gethostname() != 'box-932982':
        parser.error('Only root on the authorized RU host')
    if arguments.output.parent != OUTPUT or not re.fullmatch(r'[a-zA-Z0-9-]+', arguments.output.name):
        parser.error('Output must be a fresh child of the fixed runtime directory')
    if OUTPUT.is_symlink() or OUTPUT.stat().st_uid != 0 or OUTPUT.stat().st_mode & 0o077:
        parser.error('Unsafe runtime directory')
    if not any(line.split()[1:3] == ['/run', 'tmpfs'] for line in text(Path('/proc/mounts')).splitlines()):
        parser.error('RAM-only /run mount required')
    for name, expected in (('paid-transport.pyz', ARCHIVE_SHA), ('awg-gateway.py', GATEWAY_SHA)):
        if hashlib.sha256((NODE / name).read_bytes()).hexdigest() != expected:
            parser.error('Installed baseline changed')
    if (NODE / 'transport-failure.json').exists():
        parser.error('Preserve existing failure before starting a new observation')
    watcher = int(subprocess.check_output(['systemctl', 'show', UNIT, '-p', 'MainPID', '--value'], timeout=5))
    if watcher <= 0:
        parser.error('Watcher is not running; preserve failure and use controlled recovery')
    arguments.output.mkdir(mode=0o700)
    return run(arguments.output, arguments.seconds, watcher, Path(__file__).with_name('ru_pressure_trace.bt'))


if __name__ == '__main__':
    raise SystemExit(main())
