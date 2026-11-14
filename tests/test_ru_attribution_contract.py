import importlib.util
import json
from collections import Counter
from pathlib import Path


SPEC = importlib.util.spec_from_file_location('contract', Path(__file__).parents[1] / 'scripts/ru_attribution_contract.py')
contract = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(contract)


def fixture():
    records, ledger = [], []

    def add(kind, subject=42, generation=100, amount=0, remaining=0):
        records.append((len(records) * 10 + 5, 0, len(records) + 1, kind,
                        subject, generation, amount, remaining, 0, 0, 0))

    add(24)
    for index in range(64):
        before = len(records) * 10
        add(6, amount=3)
        add(7, amount=3)
        ledger.append(dict(begin=before, end=len(records) * 10, fd=3, tid=42, result=0))
    for generation in (1, 2):
        add(26, subject=999, generation=generation)
        add(12, subject=999, generation=generation, amount=100)
        add(14, subject=999, generation=generation, amount=50, remaining=100)
        add(14, subject=999, generation=generation, amount=50, remaining=50)
        add(16, subject=999, generation=generation)
    add(25)
    counts = Counter(record[3] for record in records)
    result = dict(events=records, producer_counts=[dict(cpu=0, kind=kind, hits=count, attempted=count)
                                                  for kind, count in counts.items()],
                  events_seen=len(records), invalid=0, stderr_bytes=0, evicted=0,
                  drain_complete=True, budget_ok=True, attached=True)
    return result, ledger


def test_exact_ledger_pairs_reuse_partial_not_loss():
    result, ledger = fixture()
    value = contract.audit(result, ledger, [0])
    assert value['pass_gate']
    assert value['enter'] == value['exit'] == value['paired'] == 64
    assert value['producer_fsync'] == 128
    assert value['observations']['valid_partial_completion'] == 2
    assert value['reused_addresses'] == 1
    assert contract.audit(json.loads(json.dumps(result)), ledger, [0]) == value


def test_equal_count_loss_and_duplicate_rejected():
    result, ledger = fixture()
    result['events'][3] = result['events'][1]
    value = contract.audit(result, ledger, [0])
    assert value['enter'] == 64
    assert value['exit'] == 64
    assert not value['pass_gate']
    assert value['errors']['prefix_gap_duplicate_or_tail']
    assert value['errors']['workload_probe_pair']


def test_prefix_tail_and_producer_loss_are_independent():
    for position in (0, -1, 10):
        result, ledger = fixture()
        result['events'].pop(position)
        value = contract.audit(result, ledger, [0])
        assert not value['pass_gate']
        assert value['errors']['producer_transport_parser_retention']


def test_same_pointer_generation_reuse_without_terminal_rejected():
    result, ledger = fixture()
    allocations = [record for record in result['events'] if record[3] == 26]
    second = allocations[1]
    result['events'][result['events'].index(second)] = (*second[:5], 1, *second[6:])
    assert contract.audit(result, ledger, [0])['errors']['generation_reuse_or_missing_terminal']


def test_pipe_success_does_not_override_resource_or_retention():
    for key, value in (('budget_ok', False), ('attached', False), ('evicted', 1)):
        result, ledger = fixture()
        result[key] = value
        assert not contract.audit(result, ledger, [0])['pass_gate']


def test_duplicate_completion_and_free_without_completion_rejected():
    result, ledger = fixture()
    partial = next(index for index, record in enumerate(result['events']) if record[3] == 14)
    record = result['events'][partial]
    result['events'][partial] = (*record[:6], 100, 100, *record[8:])
    assert contract.audit(result, ledger, [0])['errors']['completion_without_issue']
    result, ledger = fixture()
    completion = next(index for index, record in enumerate(result['events']) if record[3] == 14 and record[6] == record[7])
    record = result['events'][completion]
    result['events'][completion] = (*record[:6], 25, 50, *record[8:])
    assert contract.audit(result, ledger, [0])['errors']['free_before_completion']


def test_initial_requests_are_explicit_not_qualified_generations():
    result, ledger = fixture()
    allocation = next(index for index, record in enumerate(result['events']) if record[3] == 26)
    record = result['events'][allocation]
    result['events'][allocation] = (*record[:3], 12, *record[4:])
    value = contract.audit(result, ledger, [0])
    assert value['observations']['initial_or_unknown_request'] > 0
    assert not value['pass_gate']


def test_logical_flush_parent_is_not_a_missing_device_issue():
    result, ledger = fixture()
    issue = next(index for index, record in enumerate(result['events']) if record[3] == 12)
    record = result['events'][issue]
    result['events'][issue] = (*record[:3], 28, *record[4:6], 0, 0, *record[8:])
    completion = result['events'][issue + 1]
    result['events'][issue + 1] = (*completion[:6], 0, 0, *completion[8:])
    result['events'].pop(issue + 2)
    result['events'] = [(*event[:2], index + 1, *event[3:])
                        for index, event in enumerate(result['events'])]
    counts = Counter(event[3] for event in result['events'])
    result['producer_counts'] = [dict(cpu=0, kind=kind, hits=count, attempted=count)
                                 for kind, count in counts.items()]
    result['events_seen'] = len(result['events'])
    value = contract.audit(result, ledger, [0])
    assert value['pass_gate']
    assert value['observations']['logical_flush_completion_not_service'] == 1
    result['events'][issue] = (*record[:3], 11, *record[4:])
    assert contract.audit(result, ledger, [0])['errors']['completion_without_issue']


def test_flush_data_and_logical_completion_are_distinct():
    result, ledger = fixture()
    completion = next(index for index, event in enumerate(result['events']) if event[3] == 14)
    record = result['events'][completion]
    result['events'][completion] = (*record[:6], 100, 100, 2, 0, 0)
    record = result['events'][completion + 1]
    result['events'][completion + 1] = (*record[:6], 0, 0, 0, 0, 0)
    value = contract.audit(result, ledger, [0])
    assert value['pass_gate']
    assert value['observations']['flush_data_completed_pending_logical_end'] == 1
    assert value['observations']['logical_flush_completion_not_service'] == 1
    record = result['events'][completion]
    result['events'][completion] = (*record[:8], 0, 0, 0)
    assert contract.audit(result, ledger, [0])['errors']['completion_without_issue']


def test_internal_flush_completion_retires_on_reset_without_second_completion():
    result, ledger = fixture()
    for index, record in enumerate(result['events']):
        if record[3] == 26:
            result['events'][index] = (*record[:6], 1, *record[7:])
        elif record[3] == 14:
            result['events'][index] = (*record[:8], 2, 0, 0)
        elif record[3] == 16:
            result['events'][index] = (*record[:6], 2, *record[7:])
    value = contract.audit(result, ledger, [0])
    assert value['pass_gate']
    assert value['observations']['completed_reset'] == 2
    assert 'flush_data_completed_pending_logical_end' not in value['observations']
