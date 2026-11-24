"""Admission is stricter than pipe completion; bounded ledger and window checks."""

from collections import Counter, defaultdict


def audit(result, ledger, cpus):
    events = result['events']
    errors = Counter()
    observations = Counter()
    streams = defaultdict(list)
    for event in events:
        if event[3] not in (20, 21):
            streams[event[1]].append(event)
    received = Counter((event[1], event[3]) for event in events if event[3] not in (20, 21))
    producer = {(entry['cpu'], entry['kind']): entry for entry in result['producer_counts']}
    if set(streams) != set(cpus):
        errors['cpu_window_set'] += 1
    for cpu, records in streams.items():
        ordered = sorted(records, key=lambda event: event[2])
        if [event[2] for event in ordered] != list(range(1, len(ordered) + 1)):
            errors['prefix_gap_duplicate_or_tail'] += 1
        if ordered[0][3] != 24 or ordered[-1][3] != 25:
            errors['missing_fence'] += 1
        if sum(event[3] == 24 for event in ordered) != 1 or sum(event[3] == 25 for event in ordered) != 1:
            errors['duplicate_fence'] += 1
    for key in received.keys() | producer.keys():
        entry = producer.get(key, {})
        if entry.get('hits') != entry.get('attempted') or entry.get('attempted') != received[key]:
            errors['producer_transport_parser_retention'] += 1
    window_errors = sum(errors.values())
    enters = [event for event in events if event[3] == 6]
    exits = [event for event in events if event[3] == 7]
    matched_enter, matched_exit = set(), set()
    paired = 0
    for operation in ledger:
        matching = [[event for event in candidates
                     if event[4] == operation['tid'] and event[6] == operation['fd']
                     and operation['begin'] <= event[0] <= operation['end']]
                    for candidates in (enters, exits)]
        if operation['result'] != 0 or len(matching[0]) != 1 or len(matching[1]) != 1:
            errors['workload_probe_pair'] += 1
            continue
        enter, exit_event = matching[0][0], matching[1][0]
        if enter[5] != exit_event[5] or enter[0] > exit_event[0] or exit_event[10] != 0:
            errors['inconsistent_pair'] += 1
            continue
        enter_id, exit_id = tuple(enter[1:3]), tuple(exit_event[1:3])
        if enter_id in matched_enter or exit_id in matched_exit:
            errors['reused_pair'] += 1
            continue
        matched_enter.add(enter_id)
        matched_exit.add(exit_id)
        paired += 1
    if len(enters) != paired or len(exits) != paired:
        errors['extra_or_unpaired_phase'] += 1
    phase_errors = sum(errors.values()) - window_errors
    live = {}
    stages = {}
    internal_flush = set()
    generations = defaultdict(set)
    allocated_generations = defaultdict(set)
    completed = set()
    for event in sorted(events):
        stamp, cpu, sequence, kind, address, generation, amount, remaining, owner, executor, code = event
        if kind == 26:
            if address in live or not generation or generation in generations[address]:
                errors['generation_reuse_or_missing_terminal'] += 1
            live[address] = generation
            stages[address] = 'allocated'
            if amount == 1:
                internal_flush.add(address)
            else:
                internal_flush.discard(address)
            generations[address].add(generation)
            if amount == 0:
                allocated_generations[address].add(generation)
        elif 11 <= kind <= 16 or kind == 28:
            if address not in live:
                observations['initial_or_unknown_request'] += 1
                continue
            if live[address] != generation:
                errors['wrong_generation'] += 1
            stage = stages[address]
            if kind == 28:
                if stage != 'allocated':
                    errors['invalid_flush_parent'] += 1
                if amount == 0:
                    stages[address] = 'flush_parent'
            elif kind == 11:
                if stage not in ('allocated', 'requeued'):
                    errors['invalid_insert'] += 1
                stages[address] = 'queued'
            elif kind == 12:
                if stage not in ('allocated', 'queued', 'requeued'):
                    errors['invalid_issue'] += 1
                stages[address] = 'service'
            elif kind == 13:
                if stage != 'service':
                    errors['invalid_requeue'] += 1
                stages[address] = 'requeued'
            if kind == 14:
                if stage in ('flush_parent', 'flush_wait') and amount == remaining == 0 and not owner & 2:
                    observations['logical_flush_completion_not_service'] += 1
                elif stage != 'service':
                    errors['completion_without_issue'] += 1
                if amount < remaining:
                    observations['valid_partial_completion'] += 1
                elif amount == remaining:
                    if owner & 2 and address not in internal_flush:
                        observations['flush_data_completed_pending_logical_end'] += 1
                        stages[address] = 'flush_wait'
                    else:
                        completed.add((address, generation))
                        stages[address] = 'completed'
                else:
                    errors['invalid_completion'] += 1
            elif kind == 16:
                observations[{0: 'single_free', 1: 'batch_free', 2: 'completed_reset'}.get(amount, 'unknown_free_path')] += 1
                if stage not in ('allocated', 'completed', 'merged'):
                    errors['free_before_completion'] += 1
                if stage == 'allocated':
                    observations['unused_cached_free'] += 1
                del live[address]
                del stages[address]
                internal_flush.discard(address)
            elif kind == 15:
                if stage not in ('allocated', 'queued', 'requeued'):
                    errors['invalid_merge'] += 1
                stages[address] = 'merged'
        elif kind in (23, 27):
            errors['producer_lifecycle_or_capacity'] += 1
    observations['requests_open_at_fence'] = len(live)
    lifecycle_errors = sum(errors.values()) - window_errors - phase_errors
    for name in ('invalid', 'stderr_bytes', 'evicted'):
        count = result[name] - (result.get('known_warning_bytes', 0) if name == 'stderr_bytes' else 0)
        if count:
            errors[name] += count
    if not result['drain_complete'] or not result['budget_ok'] or not result['attached']:
        errors['process_resource_or_attach'] += 1
    return dict(errors=dict(errors), observations=dict(observations),
                ledger=len(ledger), enter=len(enters), exit=len(exits), paired=paired,
                producer_fsync=sum(entry['hits'] for entry in producer.values() if entry['kind'] in (6, 7)),
                parsed=result['events_seen'], retained=len(events), evicted=result['evicted'],
                allocations=sum(map(len, generations.values())),
                reused_addresses=sum(len(values) > 1 for values in generations.values()),
                reused_allocated_addresses=sum(len(values) > 1 for values in allocated_generations.values()),
                completed_new_requests=len(completed),
                window_complete=not window_errors and not result['invalid'] and not result['evicted']
                and result['drain_complete'] and result['attached']
                and result['stderr_bytes'] == result.get('known_warning_bytes', 0),
                phase_complete=not phase_errors and paired == len(ledger),
                lifecycle_valid=not lifecycle_errors and not window_errors,
                pass_gate=not errors and len(ledger) == 64 and paired == 64
                and bool(completed) and any(len(values) > 1 for values in generations.values()))
