import hashlib
import json
from pathlib import Path
import sys


root = Path(__file__).resolve().parent
run = root / sys.argv[1]
receipts = json.loads((run / 'receipts.json').read_text())
assert len(receipts) == 6 and all(item['exit'] == 0 and item['reason'] == 'command_exit' for item in receipts)
rows = {}
adapters = {}
counts = {}
for receipt in receipts:
    label = receipt['label']
    source = run / (label + '.jsonl')
    assert hashlib.sha256(source.read_bytes()).hexdigest() == receipt['log_sha256']
    count = 0
    results = []
    adapters[label] = []
    for line in source.read_text().splitlines():
        event = json.loads(line)
        assert event.get('Action') != 'fail', event
        if event.get('Action') == 'pass' and event.get('Test'):
            count += 1
        text = event.get('Output', '')
        if 'THROUGHPUT_RESULT ' in text:
            results.append(json.loads(text.split('THROUGHPUT_RESULT ', 1)[1]))
        if 'ADAPTER_RESULT ' in text:
            values = dict(part.split('=', 1) for part in text.split('ADAPTER_RESULT ', 1)[1].split())
            adapters[label].append({key: value if key == 'variant' else int(value) for key, value in values.items()})
    counts[label] = count
    if label.startswith(('baseline-', 'candidate-')):
        assert len(results) == 13 * receipt['fixed_count']
        assert len(adapters[label]) == receipt['fixed_count']
        for row in results:
            assert row['bytes_identical'] and row['bytes'] == 1048576 and row['send_high_water'] <= 8
            identity = (row['variant'], row['case'])
            if identity in rows:
                assert rows[identity] == row, 'virtual result changed across repeats/race'
            rows[identity] = row
comparisons = []
for variant, name in sorted(rows):
    if variant != 'baseline':
        continue
    baseline = rows[(variant, name)]
    candidate = rows[('candidate', name)]
    comparisons.append(dict(case=name, baseline=baseline, candidate=candidate,
                            model_completion_speedup=round(baseline['virtual_ms']/candidate['virtual_ms'], 4)))
result = dict(scope='synthetic virtual-clock reliable-engine and real in-memory Stream adapter, not provider or device capacity',
              transfer_bytes=1048576, forward_one_way_ms=60, reverse_one_way_ms=60,
              modeled_data_serialization_ms=6, virtual_step_ms=10, tick_ms=100,
              fixed_normal_repeats=3, fixed_race_repeats=2,
              identical_virtual_results_across_repeats=True, comparisons=comparisons,
              runtime_adapter_samples=adapters, test_pass_events_including_subtests=counts,
              max_cpu_celsius=max(receipt['max_cpu_celsius'] for receipt in receipts),
              receipts=receipts)
(root / 'results.json').write_text(json.dumps(result, indent=2)+'\n')
for row in comparisons:
    print(row['case'], row['baseline']['virtual_ms'], row['candidate']['virtual_ms'],
          row['model_completion_speedup'], row['baseline']['retransmits'], row['candidate']['retransmits'])
print('MAX_CPU_CELSIUS', result['max_cpu_celsius'])
print('PASS_EVENTS', counts)
