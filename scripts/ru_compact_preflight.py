"""Finite exact-kernel transport feasibility, NOT full watcher qualification."""

import base64
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

from ru_compact_protocol import SIZES, occupied


def main():
    assert Path('/run/fc-attribution-disposable-vm').is_file()
    assert os.uname().release == '7.0.0-30-generic'
    assert hashlib.sha256(Path('/sys/kernel/btf/vmlinux').read_bytes()).hexdigest() == 'd7fca84d2c3f476afbeb2e37ddba3093eaac0af39b07b0cd1b61c11fdc1c89fb'
    groups = Path('/sys/fs/cgroup')
    diagnostic = groups / 'diagnostic'
    if Path('/proc/self/cgroup').read_text().strip() != '0::/diagnostic':
        (groups / 'cgroup.subtree_control').write_text('+cpu +memory +pids +io')
        for name in ('diagnostic', 'writer1'):
            (groups / name).mkdir()
        for name, value in (('cpu.max', '10000 100000'), ('memory.max', '268435456'),
                            ('memory.swap.max', '0'), ('pids.max', '24')):
            (diagnostic / name).write_text(value)
        (diagnostic / 'cgroup.procs').write_text(str(os.getpid()))
        os.execv(sys.executable, [sys.executable, '-u', __file__])
    setup_begin, setup_cpu = time.monotonic_ns(), time.process_time_ns()
    original = json.loads(Path('/compiled-layout.json').read_text())
    plan = json.loads(Path('/transport-plan.json').read_text())
    lines = [f"{row['cpu']} {row['kind']} {row['hits']}\n" for row in plan]
    Path('/run/plan').write_text(''.join(lines))
    output = dict(schema=3, scope='transport feasibility only, not Gate A/B/C',
                  compiled_layout=original,
                  sizes={str(kind): dict(payload=size, occupied=occupied(kind)) for kind, size in SIZES.items()},
                  v2_burst_records=sum(row['hits'] for row in plan),
                  compact_burst_bytes=sum(row['hits'] * occupied(row['kind']) for row in plan), runs=[])
    output['setup_cost'] = dict(cpu_ns=time.process_time_ns() - setup_cpu, wall_ns=time.monotonic_ns() - setup_begin)
    assert output['setup_cost']['cpu_ns'] <= 200000000 and output['setup_cost']['wall_ns'] <= 10000000000
    for index, mode in enumerate((0, 0, 0, 1, 2, 3, 4)):
        result_path = Path(f'/run/transport-{index}.json')
        error_path = Path(f'/run/transport-{index}.err')
        before = {name: (diagnostic / name).read_text() for name in ('cpu.stat', 'memory.peak', 'memory.events', 'pids.peak')}
        with result_path.open('xb') as result, error_path.open('xb') as error:
            completed = subprocess.run(['/transport', '/transport.bpf.o', '/run/plan', str(mode)], stdout=result,
                                       stderr=error, timeout=15)
        assert completed.returncode == 0, (mode, error_path.read_text()[:2000])
        assert result_path.stat().st_size < 1024 * 1024 and error_path.stat().st_size < 1024 * 1024
        audit_begin, audit_cpu = time.monotonic_ns(), time.process_time_ns()
        value = json.loads(result_path.read_text())
        error = error_path.read_text()
        save = re.search(r'FC_SAVE_COST (\{[^\n]+\})', error)
        assert save, error[:1000]
        value['save_cost'] = json.loads(save[1])
        value['case'] = index
        value['cgroup_before'] = before
        value['cgroup_after'] = {name: (diagnostic / name).read_text() for name in before}
        totals = {key: sum(row[key] for row in value['terminal']) for key in
                  ('ledger', 'hits', 'attempted', 'submitted', 'failed', 'discarded', 'overflow', 'received')}
        value['totals'] = totals
        value['per_key_conserved'] = all(row['ledger'] == row['hits'] == row['attempted'] == row['submitted'] == row['received']
                                         and not any(row[key] for key in ('failed', 'discarded', 'overflow'))
                                         for row in value['terminal'])
        value['pass_transport'] = bool(value['detached'] and value['terminal_stable'] and value['per_key_conserved'] and
                                      totals['ledger'] == totals['hits'] == totals['attempted'] == totals['submitted'] == totals['received'] == value['decoded'] == value['retained'] and
                                      value['starts'] == value['ends'] == 2 and
                                      not any(value[key] for key in ('invalid', 'evicted', 'sequence_errors', 'boundary_errors', 'guard_violations')) and
                                      not any(totals[key] for key in ('failed', 'discarded', 'overflow')) and
                                      value['save_cost']['cpu_ns'] <= 200000000 and value['save_cost']['wall_ns'] <= 10000000000 and value['drain_ns'] <= 8000000000)
        value['audit_cost'] = dict(cpu_ns=time.process_time_ns() - audit_cpu, wall_ns=time.monotonic_ns() - audit_begin)
        value['pass_transport'] &= value['audit_cost']['cpu_ns'] <= 200000000 and value['audit_cost']['wall_ns'] <= 10000000000
        output['runs'].append(value)
        print('FC_CASE ' + json.dumps(dict(case=index, mode=mode, totals=totals, pass_transport=value['pass_transport'])), flush=True)
    begin, cpu = time.monotonic(), time.process_time()
    data = json.dumps(output, separators=(',', ':')).encode()
    assert len(data) < 8 * 1024 * 1024
    Path('/run/preflight.json').write_bytes(data)
    cost = dict(cpu=time.process_time() - cpu, wall=time.monotonic() - begin)
    print('FC_PREFLIGHT ' + base64.b64encode(data).decode(), flush=True)
    print('FC_PREFLIGHT_SAVE ' + json.dumps(cost), flush=True)
    return 1 if (cost['cpu'] > .2 or cost['wall'] > 10 or
                 any(not run['pass_transport'] for run in output['runs'][:4]) or
                 any(run['pass_transport'] for run in output['runs'][4:])) else 2


if __name__ == '__main__':
    raise SystemExit(main())
