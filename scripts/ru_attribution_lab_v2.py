"""Disposable exact-kernel initial gate with independent ledger and CPU fences."""

import base64
import ctypes
import hashlib
import json
import os
from pathlib import Path
import time

import ru_attribution_contract as contract
import ru_attribution_program as producer
import ru_attribution_recorder as recorder


def wait_file(name, seconds=150):
    deadline = time.monotonic() + seconds
    while not Path(name).exists():
        if time.monotonic() >= deadline:
            raise TimeoutError(name)
        time.sleep(.01)


def workload(pace=0):
    ledger, cycles = [], []
    for cycle in range(16):
        started = time.monotonic_ns()
        for name, size in (('state', 42862), ('attempt', 83)):
            pending = Path('/test') / (name + '.pending')
            with pending.open('wb') as stream:
                stream.write(b'0' * size)
                stream.flush()
                fsync(stream.fileno(), ledger)
            pending.replace(pending.with_suffix('.json'))
            descriptor = os.open('/test', os.O_RDONLY | os.O_DIRECTORY)
            try:
                fsync(descriptor, ledger)
            finally:
                os.close(descriptor)
        cycles.append(time.monotonic_ns() - started)
        if pace:
            time.sleep(pace)
    return dict(ledger=ledger, cycles_ns=cycles)


def fsync(descriptor, ledger):
    before = time.monotonic_ns()
    os.fsync(descriptor)
    after = time.monotonic_ns()
    ledger.append(dict(tid=os.getpid(), fd=descriptor, begin=before, end=after, result=0))


def readiness_repro(diagnostic):
    (diagnostic / 'cgroup.procs').write_text(str(os.getpid()))
    for mode in ('begin', 'attached'):
        marker = Path(f'/run/{mode}-ready')
        failure = Path(f'/run/{mode}-failure')
        watcher = os.fork()
        if watcher == 0:
            wait_file(marker)
            value = workload()
            Path(f'/run/{mode}-ledger').write_text(json.dumps(value))
            pending = failure.with_suffix('.pending')
            pending.write_text('{"budget":1e-9,"elapsed":1}')
            pending.replace(failure)
            os._exit(0)
        source = '''BEGIN { printf("E %llu %u 0 20 0 0 0 0 0 0 0\\n", nsecs(monotonic), cpu); }
tracepoint:syscalls:sys_enter_fsync /pid == $1/ {
  @sequence[cpu] = @sequence[cpu] + 1;
  printf("E %llu %u %llu 6 %u %llu 0 0 0 0 0\\n", nsecs(monotonic), cpu, @sequence[cpu], tid, curtask->start_boottime);
}
tracepoint:syscalls:sys_exit_fsync /pid == $1/ {
  @sequence[cpu] = @sequence[cpu] + 1;
  printf("E %llu %u %llu 7 %u %llu 0 0 0 0 %lld\\n", nsecs(monotonic), cpu, @sequence[cpu], tid, curtask->start_boottime, args.ret);
}
END { printf("E %llu %u 0 21 0 0 0 0 0 0 0\\n", nsecs(monotonic), cpu); clear(@sequence); }
'''
        path = Path('/run/repro.bt')
        path.write_text(source)
        callbacks = {}

        def notify(name):
            callbacks[name] = time.monotonic_ns()
            if name == mode:
                marker.touch(exist_ok=False)

        value = recorder.record(['/usr/bin/bpftrace', '-q', '-B', 'none', str(path), str(watcher)],
                                failure, 60, ready=lambda: notify('begin'), attached=lambda: notify('attached'),
                                environment=dict(os.environ, __BPFTRACE_NOTIFY_PROBES_ATTACHED='1'))
        os.waitpid(watcher, 0)
        events = value['events']
        ledger = json.loads(Path(f'/run/{mode}-ledger').read_text())['ledger']
        print('FC_READINESS ' + json.dumps(dict(mode=mode, callbacks=callbacks,
              begin_kernel_ns=next((event[0] for event in events if event[3] == 20), None),
              ledger=len(ledger), enter=sum(event[3] == 6 for event in events), exit=sum(event[3] == 7 for event in events),
              drain_complete=value['drain_complete'], stderr_bytes=value['stderr_bytes'],
              budget_ok=value['budget_ok'])), flush=True)
    return 0


def main():
    assert Path('/run/fc-attribution-disposable-vm').exists()
    assert os.uname().release == '7.0.0-30-generic'
    assert os.sysconf('SC_CLK_TCK') == 100
    assert hashlib.sha256(Path('/sys/kernel/btf/vmlinux').read_bytes()).hexdigest() == 'd7fca84d2c3f476afbeb2e37ddba3093eaac0af39b07b0cd1b61c11fdc1c89fb'
    groups = Path('/sys/fs/cgroup')
    (groups / 'cgroup.subtree_control').write_text('+cpu +memory +pids +io')
    for name in ('diagnostic', 'writer1', 'writer2'):
        (groups / name).mkdir()
    diagnostic = groups / 'diagnostic'
    for name, value in (('cpu.max', '10000 100000'), ('memory.max', '268435456'),
                        ('memory.swap.max', '0'), ('pids.max', '24')):
        (diagnostic / name).write_text(value)
    if os.environ.get('FC_LAB_MODE') == 'readiness':
        return readiness_repro(diagnostic)
    cpus = sorted(os.sched_getaffinity(0))
    baseline = workload()
    controller = os.fork()
    if controller == 0:
        wait_file('/run/attached')
        library = ctypes.CDLL(None)
        for cpu in cpus:
            os.sched_setaffinity(0, {cpu})
            library.getpgid(producer.START)
        wait_file('/run/fence-stop')
        for cpu in cpus:
            os.sched_setaffinity(0, {cpu})
            library.getpgid(producer.STOP)
        os._exit(0)
    watcher = os.fork()
    if watcher == 0:
        (groups / 'writer1/cgroup.procs').write_text(str(os.getpid()))
        wait_file('/run/ready')
        result = workload(float(os.environ.get('FC_LAB_PACE', '0')))
        Path('/run/workload.json').write_text(json.dumps(result))
        elapsed = sum(result['cycles_ns']) / 1e9
        Path('/run/failure.pending').write_text(json.dumps(dict(elapsed=elapsed, budget=1e-9)))
        Path('/run/failure.pending').replace('/run/failure')
        wait_file('/run/finished')
        os._exit(0)
    ticks = Path(f'/proc/{watcher}/stat').read_text().rsplit(')', 1)[1].split()[19]
    device = os.stat('/dev/vda').st_rdev
    Path('/run/trace.bt').write_text(producer.program())
    command = ['/usr/bin/bpftrace', '-B', 'none', '-q', '/run/trace.bt', str(watcher), ticks,
               str(os.major(device)), str((groups / 'writer1').stat().st_ino),
               str((groups / 'writer2').stat().st_ino), str(os.minor(device)), str(controller)]
    started, stopped = set(), set()

    def receive(value):
        if value[3] == 24:
            started.add(value[1])
            if started == set(cpus) and not Path('/run/ready').exists():
                Path('/run/ready').touch(exist_ok=False)
        if value[3] == 25:
            stopped.add(value[1])

    (diagnostic / 'cgroup.procs').write_text(str(os.getpid()))
    environment = dict(os.environ, __BPFTRACE_NOTIFY_PROBES_ATTACHED='1')
    result = recorder.record(command, Path('/run/failure'), 120,
                             attached=lambda: Path('/run/attached').touch(exist_ok=False),
                             event_received=receive,
                             prepare_stop=lambda: Path('/run/fence-stop').touch(exist_ok=True),
                             stop_ready=lambda: stopped == set(cpus) or not started,
                             environment=environment,
                             legacy_read_warning=True,
                             error_received=lambda raw: print('FC_ERROR ' + repr(raw), flush=True),
                             invalid_record=lambda raw: print('FC_INVALID ' + repr(raw), flush=True))
    Path('/run/finished').touch()
    workload_result = json.loads(Path('/run/workload.json').read_text()) if Path('/run/workload.json').exists() else dict(ledger=[])
    result['workload'] = workload_result
    result['mode'] = 'paced_lifecycle' if os.environ.get('FC_LAB_PACE') else 'burst_admission'
    result['clock_ticks'] = os.sysconf('SC_CLK_TCK')
    result['page_size'] = os.sysconf('SC_PAGE_SIZE')
    result['baseline'] = baseline
    audit_start, audit_cpu = time.monotonic(), time.process_time()
    result['gate'] = contract.audit(result, workload_result['ledger'], cpus)
    result['audit_cost'] = dict(cpu=time.process_time() - audit_cpu, wall=time.monotonic() - audit_start)
    if result['audit_cost']['cpu'] > recorder.CPU_LIMIT or result['audit_cost']['wall'] > recorder.WALL_LIMIT:
        result['guard_violations'].append(dict(stage='audit', **result['audit_cost']))
        result['budget_ok'] = False
        result['gate']['pass_gate'] = False
    result['failure_unchanged'] = bool(result['first_failure']) and result['first_failure'] == recorder.failure_receipt(Path('/run/failure'))
    kinds = {event[3] for event in result['events']}
    result['admission'] = dict(stream=result['gate']['pass_gate'],
                              probe_controls={1, 3, 6, 7, 12, 14, 16, 26}.issubset(kinds),
                              partial_kernel_control=bool(result['gate']['observations'].get('valid_partial_completion')),
                              first_failure=result['failure_unchanged'],
                              drain=result['drain_complete'] and result['stop_elapsed'] is not None and result['stop_elapsed'] <= 8,
                              resources=result['budget_ok'], burst=result['mode'] == 'burst_admission')
    result['diagnostic'] = {name: (diagnostic / name).read_text() for name in
                            ('cpu.stat', 'memory.peak', 'memory.events', 'pids.peak')}
    begin, cpu = time.monotonic(), time.process_time()
    recorder.save(Path('/run/final-v2.json'), result)
    result['save_cost'] = dict(cpu=time.process_time() - cpu, wall=time.monotonic() - begin)
    recorder.save(Path('/run/save-cost-v2.json'), result['save_cost'])
    result['admission']['serialization'] = result['save_cost']['cpu'] <= .2 and result['save_cost']['wall'] <= 10
    capture = Path('/run/final-v2.json').read_bytes()
    print('FC_CAPTURE ' + base64.b64encode(capture).decode(), flush=True)
    result['capture_sha256'] = hashlib.sha256(capture).hexdigest()
    result['events'] = []
    result['analysis']['intervals'] = []
    result['baseline'] = {}
    result['workload'] = {}
    print('FC_RESULT ' + json.dumps(result), flush=True)
    if result['mode'] == 'paced_lifecycle':
        print('FC_DECISION PACED_DIAGNOSTIC_ONLY_NOT_ADMISSION', flush=True)
        return 0
    if not all(result['admission'].values()):
        print('FC_DECISION NO_GO_INITIAL_GATE', flush=True)
        return 1
    print('FC_DECISION INITIAL_GATE_PASS_FULL_MATRIX_REQUIRED', flush=True)
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
