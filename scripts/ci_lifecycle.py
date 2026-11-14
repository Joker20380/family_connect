"""Bounded CI lifecycle evidence without argv, environment or file contents."""
import json
import os
from pathlib import Path
import sys
import time


def mark(stage, **values):
    record = dict(stage=stage, monotonic=time.monotonic(), pid=os.getpid(),
                  ppid=os.getppid(), pgid=os.getpgrp(), **values)
    for descriptor in (1, 2):
        try:
            target = os.readlink(f'/proc/self/fd/{descriptor}')
            if target.startswith('pipe:['):
                record[f'fd{descriptor}'] = target
        except OSError:
            pass
    text = json.dumps(record, sort_keys=True)
    destination = os.environ.get('FC_CI_LIFECYCLE_LOG')
    if destination:
        with open(destination, 'a') as output:
            output.write(text + '\n')
    print('CI_LIFECYCLE ' + text, flush=True)


def pipe_owners(records):
    pipes = {record[key] for record in records for key in ('fd1', 'fd2') if key in record}
    groups = {record['pgid'] for record in records}
    known = {record['pid'] for record in records}
    result = []
    unreadable = 0
    for process in sorted(Path('/proc').iterdir()):
        if not process.name.isdigit():
            continue
        try:
            stat = (process / 'stat').read_text().rsplit(')', 1)[1].split()
            pid, parent, group = int(process.name), int(stat[1]), int(stat[2])
            owners = []
            for descriptor in (process / 'fd').iterdir():
                try:
                    target = os.readlink(descriptor)
                    if target in pipes:
                        info = (process / 'fdinfo' / descriptor.name).read_text()
                        flags = next(line.split()[1] for line in info.splitlines() if line.startswith('flags:'))
                        owners.append(dict(fd=int(descriptor.name), pipe=target,
                                           access=int(flags, 8) & os.O_ACCMODE))
                except (OSError, StopIteration):
                    continue
            if owners or group in groups or pid in known or parent in known:
                result.append(dict(pid=pid, ppid=parent, pgid=group, state=stat[0],
                                   start_ticks=int(stat[19]), known=pid in known,
                                   same_group=group in groups, pipes=owners))
        except OSError:
            unreadable += 1
    return dict(monotonic=time.monotonic(), processes=result, unreadable=unreadable)


def watch(log, output):
    started = time.monotonic()
    completed = None
    while time.monotonic() - started < 1490:
        records = []
        if log.exists():
            for line in log.read_text().splitlines():
                try:
                    records.append(json.loads(line))
                except ValueError:
                    pass
        if any(record['stage'] == 'pipeline_end' for record in records):
            return
        if any(record['stage'] == 'coverage_end' for record in records) and completed is None:
            completed = time.monotonic()
        if (completed is not None and time.monotonic() - completed >= 10) or time.monotonic() - started >= 900:
            output.write_text(json.dumps(pipe_owners(records), indent=2) + '\n')
            return
        time.sleep(1)


if __name__ == '__main__':
    watch(Path(sys.argv[1]), Path(sys.argv[2]))
