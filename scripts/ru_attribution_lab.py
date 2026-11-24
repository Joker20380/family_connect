"""Finite guest-only initial qualification gate; synthetic files on /dev/vda."""

import hashlib
import base64
from collections import Counter
import json
import os
from pathlib import Path
import subprocess
import time

import ru_attribution_recorder as recorder


def cycle():
    started = time.monotonic_ns()
    for name, size in (('state', 42862), ('attempt', 83)):
        pending = Path('/test') / (name + '.pending')
        with pending.open('wb') as stream:
            stream.write(b'0' * size)
            stream.flush()
            os.fsync(stream.fileno())
        pending.replace(pending.with_suffix('.json'))
        descriptor = os.open('/test', os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    return time.monotonic_ns() - started


def main():
    assert Path('/run/fc-attribution-disposable-vm').exists()
    assert os.uname().release == '7.0.0-30-generic'
    assert os.sysconf('SC_CLK_TCK') == 100
    assert any(line.split()[1:3] == ['/test', 'ext4'] for line in Path('/proc/mounts').read_text().splitlines())
    groups = Path('/sys/fs/cgroup')
    (groups / 'cgroup.subtree_control').write_text('+cpu +memory +pids +io')
    for name in ('diagnostic', 'writer1', 'writer2'):
        (groups / name).mkdir()
    diagnostic = groups / 'diagnostic'
    for name, value in (('cpu.max', '10000 100000'), ('memory.max', '268435456'),
                        ('memory.swap.max', '0'), ('pids.max', '24')):
        (diagnostic / name).write_text(value)
    baseline = [cycle() for _ in range(16)]
    watcher = os.fork()
    if watcher == 0:
        (groups / 'writer1/cgroup.procs').write_text(str(os.getpid()))
        deadline = time.monotonic() + 160
        while not Path('/run/ready').exists():
            if time.monotonic() > deadline:
                os._exit(2)
            time.sleep(.05)
        times = [cycle() for _ in range(16)]
        Path('/run/workload.json').write_text(json.dumps(times))
        elapsed = sum(times) / 1e9
        test_budget = 0.000000001
        assert elapsed > test_budget
        Path('/run/failure.pending').write_text(json.dumps(dict(elapsed=elapsed, budget=test_budget)))
        Path('/run/failure.pending').replace('/run/failure')
        time.sleep(1)
        os._exit(0)
    ticks = Path(f'/proc/{watcher}/stat').read_text().rsplit(')', 1)[1].split()[19]
    command = ['/usr/bin/bpftrace', '-q', '/ru_attribution_trace.bt', str(watcher), ticks,
               '253', str((groups / 'writer1').stat().st_ino), str((groups / 'writer2').stat().st_ino), '0']
    device = os.stat('/dev/vda').st_rdev
    command[-4] = str(os.major(device))
    before_cpu = Path('/proc/stat').read_text().splitlines()[0]
    (diagnostic / 'cgroup.procs').write_text(str(os.getpid()))
    controls = (
        ('begin', 'BEGIN { printf("CONTROL_OK\\n"); exit(); }'),
        ('syscall', 'tracepoint:syscalls:sys_enter_fsync { @calls = count(); } interval:s:1 { exit(); }'),
        ('task_btf', 'rawtracepoint:sched_switch { $task = (struct task_struct *)arg1; @last = $task->pid; } interval:s:1 { exit(); }'),
        ('request_btf', 'rawtracepoint:block_rq_issue { $request = (struct request *)arg0; @last = $request->__data_len; } interval:s:1 { exit(); }'),
    )
    controls_ok = True
    for name, source in controls:
        try:
            check = subprocess.run(['/usr/bin/bpftrace', '-q', '-e', source], capture_output=True, timeout=25)
            print('FC_CONTROL ' + json.dumps(dict(name=name, code=check.returncode,
                  stdout=check.stdout.decode(errors='replace')[:2048],
                  stderr=check.stderr.decode(errors='replace')[:4096])), flush=True)
            controls_ok &= check.returncode == 0
        except subprocess.TimeoutExpired:
            controls_ok = False
            print('FC_CONTROL ' + json.dumps(dict(name=name, timeout=True)), flush=True)
    diagnostic_before = (diagnostic / 'cpu.stat').read_text()
    result = recorder.record(command, Path('/run/failure'), 120,
                             ready=lambda: Path('/run/ready').touch(exist_ok=False),
                             invalid_record=lambda raw: print('FC_INVALID ' + repr(raw), flush=True))
    after_cpu = Path('/proc/stat').read_text().splitlines()[0]
    save_start, save_cpu = time.monotonic(), time.process_time()
    recorder.save(Path('/run/final.json'), result)
    save_cost = dict(cpu=time.process_time() - save_cpu, wall=time.monotonic() - save_start)
    capture = Path('/run/final.json').read_bytes()
    print('FC_CAPTURE ' + base64.b64encode(capture).decode(), flush=True)
    result['capture_sha256'] = hashlib.sha256(capture).hexdigest()
    result['save_cost'] = save_cost
    result['diagnostic_cpu_before_record'] = diagnostic_before
    result['kind_counts'] = dict(Counter(event[3] for event in result['events']))
    result['zero_request_generations'] = sum(11 <= event[3] <= 16 and event[5] == 0 for event in result['events'])
    result['events_sha256'] = hashlib.sha256(recorder.encode(result['events'])).hexdigest()
    result['events'] = []
    result['analysis']['intervals'] = []
    result['kernel'] = os.uname().release
    result['btf_sha256'] = hashlib.sha256(Path('/sys/kernel/btf/vmlinux').read_bytes()).hexdigest()
    result['baseline_cycles_ns'] = baseline
    result['guest_cpu_before'] = before_cpu
    result['guest_cpu_after'] = after_cpu
    result['diagnostic'] = {name: (diagnostic / name).read_text() for name in
                            ('cpu.stat', 'memory.peak', 'memory.events', 'pids.peak')}
    result['workload_ns'] = json.loads(Path('/run/workload.json').read_text()) if Path('/run/workload.json').exists() else None
    result['failure_unchanged'] = result['first_failure'] == recorder.failure_receipt(Path('/run/failure')) if result['first_failure'] else None
    result['clean_gate'] = dict(request_generation=result['zero_request_generations'] == 0,
                                fsync_enters=result['kind_counts'].get(6, 0) == 64,
                                fsync_exits=result['kind_counts'].get(7, 0) == 64,
                                device_service=bool(result['analysis']['union_ns'].get('device_service')))
    print('FC_RESULT ' + json.dumps(result), flush=True)
    if not result['drain_complete'] or not result['budget_ok'] or not result['workload_ns'] or not all(result['clean_gate'].values()) or save_cost['cpu'] > recorder.CPU_LIMIT or save_cost['wall'] > recorder.WALL_LIMIT:
        print('FC_DECISION ' + ('NO_GO_INITIAL_GATE' if controls_ok else 'BLOCKED_INITIAL_GATE'), flush=True)
        return 1
    print('FC_DECISION INITIAL_GATE_ONLY_NOT_FULL_GO', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
