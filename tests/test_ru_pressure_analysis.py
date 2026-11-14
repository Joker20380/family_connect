import copy
import json
from pathlib import Path
import subprocess
import sys

import pytest

from scripts.ru_pressure_analysis import analyze, analyze_window, delta, distribution, interval


def sample(seconds, counter):
    process = dict(pid=42, start_ticks=100, name='synthetic-watcher', cgroup='/test',
                   cpu_ticks=counter * 10, majflt=counter, rss_pages=3, VmSwap=2,
                   read_bytes=counter * 100, write_bytes=counter * 200)
    group = {'io': f'252:0 rbytes={counter * 100} wbytes={counter * 200}',
             'memory': dict(pgmajfault=counter, anon=100 - counter), 'events': dict(oom=0),
             'memory.current': 4096, 'memory.swap.current': 0}
    return dict(mono_ns=int(seconds * 1e9), wall=1000 + seconds, sample_seconds=.25,
                sample_cpu_seconds=.1, processes=[process], cgroups={'/test': group},
                processes_omitted=0, cgroups_omitted=0, races=1,
                pressure={'io': f'some avg10=0 total={counter * 1000000}\nfull avg10=0 total=0'},
                vm=dict(pswpin=counter, pswpout=0, pgmajfault=counter, nr_dirty=100-counter),
                disk=[f'252 0 vda {counter} 0 {counter * 2} {counter * 10} {counter} 0 {counter * 4} {counter * 20} 0 {counter * 15} {counter * 30}'])


def captures():
    metadata = dict(boot_id='synthetic-boot', watcher=42, invocation_id='synthetic-run',
                    source_sha256='source', trace_sha256='trace', archive_sha256='archive',
                    gateway_sha256='gateway', clock_ticks=1000, page_size=8192, started_at=1000)
    phases = [dict(kind='F', phase=1, mono_ns=int(seconds * 1e9), duration_ns=1000000,
                   result=0, bytes=50) for seconds in (2, 3, 6)]
    samples = [sample(1, 1), sample(4, 2), sample(7, 3)]
    summary = dict(counts={'F1': 6}, duration_ns={'F1': 9000000}, maxima_ns={'F1': 4000000},
                   bytes={'F1': 300}, elapsed=8, reason='sample_cost_limit')
    final = dict(metadata=metadata, phases=phases, samples=samples, summary=summary)
    slow = copy.deepcopy(dict(metadata=metadata, phases=phases[:1], samples=samples[:1], trigger=phases[0]))
    return [('start.json', metadata), ('slow.json', slow), ('final.json', final)]


def test_duplicate_exports_and_overlap_are_not_new_runs_or_events(tmp_path):
    directories = [tmp_path / name for name in ('first', 'duplicate')]
    for directory in directories:
        directory.mkdir()
        for name, value in captures():
            (directory / name).write_text(json.dumps(value))
    result = analyze(directories, [dict(files={'ru_pressure_observer.py': 'source', 'ru_pressure_trace.bt': 'trace'})])
    assert len(result['windows']) == 1
    window = result['windows'][0]
    assert window['unique_phase_span']['count'] == 3
    assert window['unique_sample_span']['count'] == 3
    assert window['processed_phase_count'] == 6
    assert window['accumulated_mean_ms']['F1'] == 1.5
    assert window['retained_distributions_ms']['F1']['maximum'] == 1
    assert len(window['slow_brackets']) == 1


def test_counter_units_and_identity_not_pid_alone():
    metadata = captures()[0][1]
    before, after = sample(1, 1), sample(4, 3)
    result = interval(before, after, metadata)
    assert result['seconds'] == 3
    assert result['swap_bytes']['pswpin'] == 2 * 8192
    assert result['disk']['write_bytes'] == 8 * 512
    assert result['pressure_seconds']['io']['some'] == 2
    assert result['processes'][0]['cpu_seconds'] == .02
    assert result['processes'][0]['rss_bytes'] == 3 * 8192
    assert result['processes'][0]['swap_bytes'] == 2 * 1024
    assert result['vm_gauges']['nr_dirty'] == [99, 97]
    assert 'anon' not in result['cgroups']['/test']['memory_counters']
    after['processes'][0]['start_ticks'] += 1
    assert interval(before, after, metadata)['processes'] == []
    assert delta({'counter': 5}, {'counter': 2}) == {'counter': None}


def test_bracket_uses_completed_before_sample_and_actual_after_sample():
    values = captures()
    values[-1][1]['samples'][0]['sample_seconds'] = 1.5
    values[1][1]['samples'][0]['sample_seconds'] = 1.5
    result = analyze_window(values)
    assert result['slow_brackets'][0]['interval'] is None
    result = analyze_window(captures())
    assert result['slow_brackets'][0]['interval']['before_ns'] == 1000000000
    assert result['slow_brackets'][0]['interval']['after_ns'] == 4000000000


@pytest.mark.parametrize('cpu,wall,expected', [(.202841517, 2, (True, False)), (.1, 11, (False, True)), (.2, 10, (False, False))])
def test_terminating_sample_and_strict_cost_guards(cpu, wall, expected):
    values = captures()
    values[-1][1]['samples'][-1].update(sample_cpu_seconds=cpu, sample_seconds=wall)
    result = analyze_window(values)
    assert tuple(result['cost_guard'].values()) == expected
    assert result['last_samples'][-1]['sample_cpu_seconds'] == cpu


def test_conflicting_final_metadata_and_sample_rejected():
    values = captures()
    duplicate = copy.deepcopy(values[-1])
    duplicate[1]['summary']['elapsed'] += 1
    with pytest.raises(ValueError, match='conflicting final'):
        analyze_window(values + [duplicate])
    values = captures()
    values[1][1]['samples'][0]['races'] = 5
    with pytest.raises(ValueError, match='Conflicting records'):
        analyze_window(values)
    values = captures()
    values[0] = ('start.json', dict(values[0][1], boot_id='other-boot'))
    with pytest.raises(ValueError, match='metadata mismatch'):
        analyze_window(values)


def test_cli_exclusive_private_output_and_unchanged_input(tmp_path):
    directory = tmp_path / 'capture'
    directory.mkdir()
    for name, value in captures():
        (directory / name).write_text(json.dumps(value))
    original = {path.name: path.read_bytes() for path in directory.iterdir()}
    manifest = tmp_path / 'manifest.json'
    manifest.write_text(json.dumps(dict(files={'ru_pressure_observer.py': 'source', 'ru_pressure_trace.bt': 'trace'})))
    output = tmp_path / 'analysis.json'
    command = [sys.executable, str(Path(__file__).resolve().parents[1] / 'scripts/ru_pressure_analysis.py'),
               str(directory), '--manifest', str(manifest), '--output', str(output)]
    assert subprocess.run(command, capture_output=True, timeout=10).returncode == 0
    raw = output.read_bytes()
    assert output.stat().st_mode & 0o777 == 0o600
    assert subprocess.run(command, capture_output=True, timeout=10).returncode != 0
    assert output.read_bytes() == raw
    assert {path.name: path.read_bytes() for path in directory.iterdir()} == original


def test_nearest_rank_percentile_and_unknown_source(tmp_path):
    assert distribution(list(range(1, 21)))['p95_nearest_rank'] == 19
    assert distribution([]) is None
    (tmp_path / 'start.json').write_text(json.dumps(captures()[0][1]))
    with pytest.raises(ValueError, match='Unapproved'):
        analyze([tmp_path], [])
