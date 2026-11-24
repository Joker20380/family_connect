"""V3 transport framing/admission, not a qualified replacement for v2 probes."""

import struct
from collections import Counter

HEADER = struct.Struct('<QIBBBB')
SIZES = {**dict.fromkeys((24, 25), 16),
         **dict.fromkeys((1, 2, 3, 4, 5, 8, 9, 17, 18, 19, 23), 24),
         **dict.fromkeys((6, 7, 16, 27, 28, 29), 32),
         **dict.fromkeys((10, 14, 26), 40),
         **dict.fromkeys((11, 12, 13, 15), 48)}


def occupied(kind):
    return (SIZES[kind] + 8 + 7) & ~7


def decode(raw):
    if len(raw) < HEADER.size:
        raise ValueError('partial_header')
    stamp, sequence, version, kind, cpu, size = HEADER.unpack_from(raw)
    if version != 3 or cpu >= 2 or not sequence or not stamp:
        raise ValueError('version_identity_or_range')
    if kind not in SIZES or size != SIZES[kind] or len(raw) != size:
        raise ValueError('kind_size_or_partial_record')
    return dict(stamp=stamp, sequence=sequence, kind=kind, cpu=cpu, payload=raw[16:])


def audit(records, terminal, detached, expected):
    errors = Counter()
    received = Counter()
    sequences = {0: [], 1: []}
    kinds = {0: [], 1: []}
    if len(records) > 4096:
        errors['retention_capacity'] += len(records) - 4096
    for raw in records[:4096]:
        try:
            value = decode(raw)
        except ValueError:
            errors['decode'] += 1
            continue
        received[value['cpu'], value['kind']] += 1
        sequences[value['cpu']].append(value['sequence'])
        kinds[value['cpu']].append(value['kind'])
    if terminal is None or not detached:
        errors['missing_terminal_or_live_producer'] += 1
    terminal = terminal or {}
    if len(terminal) > 256:
        errors['terminal_capacity'] += 1
        terminal = dict(list(terminal.items())[:256])
    for key in expected.keys() | received.keys() | terminal.keys():
        count = terminal.get(key)
        if count is None:
            errors['missing_terminal_key'] += 1
            continue
        if key[0] not in (0, 1) or key[1] not in SIZES or any(
                type(count.get(field)) is not int or not 0 <= count[field] < 2**64
                for field in ('hits', 'attempted', 'submitted', 'failed', 'discarded', 'overflow')):
            errors['terminal_range_or_schema'] += 1
            continue
        if count['hits'] != expected.get(key, 0) or count['attempted'] != count['submitted'] + count['failed']:
            errors['producer_accounting'] += 1
        if count['hits'] != count['attempted'] or count['submitted'] != received[key]:
            errors['transfer_accounting'] += 1
        if count['failed'] or count['discarded'] or count['overflow']:
            errors['failed_discarded_overflow'] += 1
    for cpu in (0, 1):
        if sequences[cpu] != list(range(1, len(sequences[cpu]) + 1)):
            errors['sequence'] += 1
        if not kinds[cpu] or kinds[cpu][0] != 24 or kinds[cpu][-1] != 25:
            errors['boundary'] += 1
        if kinds[cpu].count(24) != 1 or kinds[cpu].count(25) != 1:
            errors['boundary_count'] += 1
    return dict(pass_transport=not errors, errors=dict(errors), decoded=sum(received.values()))
