import importlib.util
from pathlib import Path
import struct

import pytest


SPEC = importlib.util.spec_from_file_location('compact', Path(__file__).parents[1] / 'scripts/ru_compact_protocol.py')
compact = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(compact)


def fixture():
    records, terminal, expected = [], {}, {}
    for cpu in (0, 1):
        for sequence, kind in enumerate((24, 6, 7, 25), 1):
            size = compact.SIZES[kind]
            records.append(compact.HEADER.pack(sequence * 100, sequence, 3, kind, cpu, size) + bytes(size - 16))
            terminal[cpu, kind] = dict(hits=1, attempted=1, submitted=1, failed=0, discarded=0, overflow=0)
            expected[cpu, kind] = 1
    return records, terminal, expected


def test_transport_conservation_and_sizes():
    records, terminal, expected = fixture()
    assert compact.audit(records, terminal, True, expected)['pass_transport']
    assert compact.HEADER.size == 16
    assert set(compact.SIZES.values()) == {16, 24, 32, 40, 48}
    assert all(compact.occupied(kind) == size + 8 for kind, size in compact.SIZES.items())


@pytest.mark.parametrize('fault', ['missing', 'live', 'failed', 'discarded', 'unreceived', 'counter_overflow'])
def test_terminal_is_independent_and_required(fault):
    records, terminal, expected = fixture()
    detached = True
    if fault == 'missing': terminal = None
    elif fault == 'live': detached = False
    elif fault == 'counter_overflow': terminal[0, 6]['overflow'] = 1
    elif fault == 'unreceived': records.pop(1)
    else: terminal[0, 6][fault] = 1
    assert not compact.audit(records, terminal, detached, expected)['pass_transport']


def test_equal_total_loss_duplicate_rejected():
    records, terminal, expected = fixture()
    records[1] = records[2]
    assert len(records) == 8
    value = compact.audit(records, terminal, True, expected)
    assert not value['pass_transport'] and value['errors']['sequence']


@pytest.mark.parametrize('mutation', ['partial_header', 'partial_payload', 'version', 'size', 'cpu', 'zero_sequence'])
def test_corruption_and_ranges(mutation):
    records, terminal, expected = fixture()
    raw = bytearray(records[1])
    if mutation == 'partial_header': raw = raw[:10]
    elif mutation == 'partial_payload': raw = raw[:-1]
    elif mutation == 'version': raw[12] = 2
    elif mutation == 'size': raw[15] = 48
    elif mutation == 'cpu': raw[14] = 2
    else: raw[8:12] = bytes(4)
    records[1] = bytes(raw)
    value = compact.audit(records, terminal, True, expected)
    assert not value['pass_transport'] and value['errors']['decode']


def test_ranges_do_not_wrap():
    with pytest.raises(struct.error):
        compact.HEADER.pack(1, 2**32, 3, 24, 0, 16)
    records, terminal, expected = fixture()
    terminal[0, 6]['hits'] = 2**64
    assert compact.audit(records, terminal, True, expected)['errors']['terminal_range_or_schema']


def test_boundary_sequence_and_capacity():
    records, terminal, expected = fixture()
    records[0], records[1] = records[1], records[0]
    value = compact.audit(records, terminal, True, expected)
    assert value['errors']['boundary'] and value['errors']['sequence']
    value = compact.audit(records * 600, terminal, True, expected)
    assert value['errors']['retention_capacity'] == 704
    terminal.update({(cpu, 1): dict(hits=0, attempted=0, submitted=0, failed=0, discarded=0, overflow=0)
                     for cpu in range(300)})
    assert compact.audit(records, terminal, True, expected)['errors']['terminal_capacity']


def test_compiled_layout_requires_every_kind_and_helper_size():
    layout_spec = importlib.util.spec_from_file_location('layout', Path(__file__).parents[1] / 'scripts/ru_compact_layout.py')
    layout = importlib.util.module_from_spec(layout_spec)
    layout_spec.loader.exec_module(layout)
    fragments = []
    for kind in sorted(set(range(1, 20)) | {23, 24, 25, 26, 27, 28}):
        fragments.append(f'''define i64 @probe_{kind}(ptr %0) {{
  %kind = getelementptr %printf_args_t.9, ptr %58, i32 0, i32 3
  store i8 {kind}, ptr %kind, align 1
  %error = call i64 inttoptr (i64 130 to ptr)(ptr @ringbuf, ptr %runtime_error_t, i64 20, i64 0)
  %output = call i64 inttoptr (i64 130 to ptr)(ptr @ringbuf, ptr %record, i64 56, i64 0)
}}
''')
    result = layout.inspect(''.join(fragments))
    assert len(result) == 25 and all(value == dict(payload=56, occupied=64) for value in result.values())
    with pytest.raises(ValueError, match='missing_or_unexpected'):
        layout.inspect(''.join(fragments[:-1]))
    with pytest.raises(ValueError, match='inconsistent_compiled'):
        layout.inspect(''.join(fragments) + fragments[0].replace('i64 56', 'i64 72'))
