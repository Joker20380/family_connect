"""Offline analysis of immutable pressure captures; no host access or mutation."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
import os
from pathlib import Path
import statistics


def distribution(values):
    values = sorted(values)
    if not values:
        return None
    return dict(count=len(values), minimum=values[0], mean=statistics.mean(values),
                median=statistics.median(values),
                p95_nearest_rank=values[math.ceil(len(values) * .95) - 1], maximum=values[-1])


def span(records):
    times = [record['mono_ns'] for record in records]
    return dict(count=len(times), first_ns=min(times) if times else None,
                last_ns=max(times) if times else None)


def deduplicate(records, keys=('mono_ns',)):
    unique = {}
    for record in records:
        key = tuple(record[name] for name in keys)
        if key in unique and unique[key] != record:
            raise ValueError('Conflicting records at one monotonic timestamp')
        unique[key] = record
    return sorted(unique.values(), key=lambda record: record['mono_ns'])


def delta(before, after):
    return {key: after[key] - before[key] if after[key] >= before[key] else None
            for key in before.keys() & after.keys()}


def pressure(raw):
    return {line.split()[0]: int(dict(field.split('=') for field in line.split()[1:])['total'])
            for line in raw.splitlines()}


def io_counters(raw):
    return {line.split()[0]: {key: int(value) for key, value in
                             (field.split('=') for field in line.split()[1:])}
            for line in raw.splitlines()}


def interval(before, after, metadata):
    elapsed = (after['mono_ns'] - before['mono_ns']) / 1e9
    if elapsed <= 0:
        raise ValueError('Nonpositive counter interval')
    result = dict(seconds=elapsed, before_wall=before['wall'], after_wall=after['wall'],
                  before_ns=before['mono_ns'], after_ns=after['mono_ns'],
                  before_sample_seconds=before['sample_seconds'],
                  after_sample_seconds=after['sample_seconds'],
                  counter_interval_bounds_seconds=[max(0, elapsed - before['sample_seconds']),
                                                   elapsed + after['sample_seconds']],
                  vm=delta({key: value for key, value in before['vm'].items() if key not in ('nr_dirty', 'nr_writeback')},
                           {key: value for key, value in after['vm'].items() if key not in ('nr_dirty', 'nr_writeback')}),
                  vm_gauges={key: [before['vm'].get(key), after['vm'].get(key)] for key in ('nr_dirty', 'nr_writeback')},
                  pressure_seconds={}, processes=[], cgroups={})
    for name in before['pressure'].keys() & after['pressure'].keys():
        result['pressure_seconds'][name] = {key: value / 1e6 if value is not None else None
            for key, value in delta(pressure(before['pressure'][name]), pressure(after['pressure'][name])).items()}
    result['swap_bytes'] = {key: result['vm'][key] * metadata['page_size']
                           if result['vm'].get(key) is not None else None for key in ('pswpin', 'pswpout')}
    old = {(item['pid'], item['start_ticks']): item for item in before['processes']}
    new = {(item['pid'], item['start_ticks']): item for item in after['processes']}
    result['unmatched_processes'] = dict(before_only=len(old.keys() - new.keys()), after_only=len(new.keys() - old.keys()))
    for identity in sorted(old.keys() & new.keys()):
        first, last = old[identity], new[identity]
        keys = ('cpu_ticks', 'majflt', 'read_bytes', 'write_bytes', 'cancelled_write_bytes')
        changes = delta({key: first[key] for key in keys if key in first},
                        {key: last[key] for key in keys if key in last})
        result['processes'].append(dict(pid=identity[0], start_ticks=identity[1], name=last['name'],
            cgroup=last['cgroup'], delta=changes,
            cpu_seconds=changes['cpu_ticks'] / metadata['clock_ticks'] if changes.get('cpu_ticks') is not None else None,
            rss_bytes=last['rss_pages'] * metadata['page_size'],
            swap_bytes=last['VmSwap'] * 1024 if 'VmSwap' in last else None,
            kernel_io_sampled=last.get('kernel_io_sampled')))
    for name in before['cgroups'].keys() & after['cgroups'].keys():
        first, last = before['cgroups'][name], after['cgroups'][name]
        old_io, new_io = io_counters(first['io']), io_counters(last['io'])
        counter_names = ('pgmajfault', 'pgscan', 'pgsteal', 'workingset_refault_anon', 'workingset_refault_file')
        result['cgroups'][name] = dict(io={device: delta(old_io[device], new_io[device])
            for device in old_io.keys() & new_io.keys()}, memory_counters=delta(
                {key: first['memory'][key] for key in counter_names if key in first['memory']},
                {key: last['memory'][key] for key in counter_names if key in last['memory']}),
            events=delta(first['events'], last['events']), memory_bytes=last['memory.current'],
            swap_bytes=last['memory.swap.current'])
    if before['disk'] and after['disk']:
        first, last = before['disk'][0].split(), after['disk'][0].split()
        if first[:3] != last[:3]:
            raise ValueError('Disk identity changed')
        names = {3: 'reads', 5: 'read_sectors', 6: 'read_ms', 7: 'writes', 9: 'write_sectors',
                 10: 'write_ms', 12: 'busy_ms', 13: 'weighted_ms'}
        result['disk'] = delta({name: int(first[index]) for index, name in names.items()},
                               {name: int(last[index]) for index, name in names.items()})
        for direction in ('read', 'write'):
            sectors = result['disk'][direction + '_sectors']
            result['disk'][direction + '_bytes'] = sectors * 512 if sectors is not None else None
    return result


def phase_stats(phases):
    grouped = defaultdict(list)
    for event in phases:
        grouped[event['kind'] + str(event['phase'])].append(event['duration_ns'] / 1e6)
    return {name: distribution(values) for name, values in sorted(grouped.items())}


def analyze_window(captures):
    finals = [value for name, value in captures if name == 'final.json']
    if not finals or any(value != finals[0] for value in finals):
        raise ValueError('Missing or conflicting final capture')
    final = finals[0]
    metadata, summary = final['metadata'], final['summary']
    for name, value in captures:
        if (value if name == 'start.json' else value['metadata']) != metadata:
            raise ValueError('Capture metadata mismatch')
    phases = deduplicate([event for name, value in captures for event in value.get('phases', [])], ('mono_ns', 'kind', 'phase'))
    samples = deduplicate([sample for name, value in captures for sample in value.get('samples', [])])
    if not samples or metadata['clock_ticks'] <= 0 or metadata['page_size'] <= 0:
        raise ValueError('Missing samples or invalid units')
    identities = {(item['pid'], item['start_ticks']) for sample in samples for item in sample['processes']
                  if item['pid'] == metadata['watcher']}
    if len(identities) != 1:
        raise ValueError('Watcher identity changed or absent')
    phase_counts = Counter(event['kind'] + str(event['phase']) for event in phases)
    if any(count > summary['counts'].get(name, 0) for name, count in phase_counts.items()):
        raise ValueError('Retained phases exceed accumulated counts')
    result = dict(identity={key: metadata[key] for key in ('boot_id', 'watcher', 'invocation_id',
        'source_sha256', 'trace_sha256', 'archive_sha256', 'gateway_sha256', 'clock_ticks', 'page_size', 'started_at')},
        watcher_start_ticks=next(iter(identities))[1], summary=summary,
        end_wall_approx=metadata['started_at'] + summary['elapsed'],
        processed_phase_count=sum(summary['counts'].values()), unique_phase_span=span(phases),
        unique_sample_span=span(samples), retained_distributions_ms=phase_stats(phases),
        accumulated_mean_ms={name: summary['duration_ns'][name] / count / 1e6
                             for name, count in summary['counts'].items() if count},
        capture_spans=[dict(name=name, phases=span(value.get('phases', [])),
                           samples=span(value.get('samples', []))) for name, value in captures],
        sample_cpu_seconds=distribution([sample['sample_cpu_seconds'] for sample in samples]),
        sample_wall_seconds=distribution([sample['sample_seconds'] for sample in samples]),
        sample_spacing_seconds=distribution([(last['mono_ns'] - first['mono_ns']) / 1e9
                                            for first, last in zip(samples, samples[1:])]),
        last_samples=[{key: sample[key] for key in ('wall', 'mono_ns', 'sample_seconds', 'sample_cpu_seconds')}
                      for sample in samples[-5:]],
        omissions={key: dict(total=sum(sample[key] for sample in samples), maximum=max(sample[key] for sample in samples))
                   for key in ('races', 'processes_omitted', 'cgroups_omitted')},
        sample_period=interval(samples[0], samples[-1], metadata),
        adjacent_intervals=[interval(first, last, metadata) for first, last in zip(samples, samples[1:])],
        counter_wall_range=[samples[0]['wall'], samples[-1]['wall'] + samples[-1]['sample_seconds']],
        phase_wall_range_approx=[samples[0]['wall'] + (event['mono_ns'] - samples[0]['mono_ns']) / 1e9
                                 for event in (phases[0], phases[-1])] if phases else [],
        nonzero_phase_results=sum(event['result'] != 0 for event in phases), slow_brackets=[])
    last = samples[-1]
    result['cost_guard'] = dict(cpu_exceeded=last['sample_cpu_seconds'] > .2, wall_exceeded=last['sample_seconds'] > 10)
    if phases:
        result['phase_tail_before_last_sample_seconds'] = (last['mono_ns'] - phases[-1]['mono_ns']) / 1e9
    triggers = deduplicate([value['trigger'] for name, value in captures if 'trigger' in value], ('mono_ns', 'kind', 'phase'))
    for event in triggers:
        start = event['mono_ns'] - event['duration_ns']
        before = [sample for sample in samples if sample['mono_ns'] + sample['sample_seconds'] * 1e9 <= start]
        after = [sample for sample in samples if sample['mono_ns'] >= event['mono_ns']]
        result['slow_brackets'].append(dict(event=event, interval=interval(before[-1], after[0], metadata)
                                          if before and after else None))
    return result


def analyze(directories, manifests):
    groups = defaultdict(list)
    hashes = {}
    approved = {item['files']['ru_pressure_observer.py']: item['files']['ru_pressure_trace.bt'] for item in manifests}
    for directory in directories:
        for path in sorted(directory.iterdir()):
            if path.name not in ('start.json', 'slow.json', 'final.json', 'trace-errors.txt'):
                continue
            raw = path.read_bytes()
            hashes[str(path)] = hashlib.sha256(raw).hexdigest()
            if path.name == 'trace-errors.txt':
                continue
            value = json.loads(raw)
            metadata = value if path.name == 'start.json' else value['metadata']
            if approved.get(metadata['source_sha256']) != metadata['trace_sha256']:
                raise ValueError('Unapproved source/trace pair')
            key = (metadata['boot_id'], metadata['watcher'], metadata['invocation_id'], metadata['started_at'])
            groups[key].append((path.name, value))
    return dict(schema=1, input_sha256=hashes, windows=[analyze_window(captures) for captures in groups.values()])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directories', type=Path, nargs='+')
    parser.add_argument('--manifest', type=Path, action='append', required=True)
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    result = analyze(arguments.directories, [json.loads(path.read_text()) for path in arguments.manifest])
    descriptor = os.open(arguments.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, 'w') as output:
        json.dump(result, output, indent=2, sort_keys=True)
        output.write('\n')


if __name__ == '__main__':
    main()
