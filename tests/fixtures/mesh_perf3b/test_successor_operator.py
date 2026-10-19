import contextlib
import importlib.util
import json
from pathlib import Path

import pytest

from test_successor_lifecycle import saved, successor, handoff, prepare, finish, current


spec = importlib.util.spec_from_file_location('successor_live_operator', Path(__file__).with_name('successor_live_operator.py'))
operator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(operator)


def config(case, directory):
    return dict(operation='mesh-perf-3b-test-02', generation=2, deadline=case[2]+2400,
        owner_guard_identity=dict(device=case[1].reference), archive=str(directory/'original.pyz'),
        database=str(case[0].access.path),material=str(directory))


def test_new_operator_allocator_uses_history_not_empty_table(successor, tmp_path):
    service, owner, now, *_ = successor
    settings=config(successor,tmp_path)
    operator.validate_config(tmp_path/settings['operation'],settings)
    result=operator.allocation_gate(service,handoff,settings,dict(family='a'*32,gateway='b'*32),now)
    assert result['generation']==2 and result['predecessor']=='retired-01'
    prepare(successor,settings['operation'])
    with pytest.raises(RuntimeError,match='EXISTING_OPERATION_READBACK_NOT_RESTART'):
        operator.allocation_gate(service,handoff,settings,dict(family='a'*32,gateway='b'*32),now)


@pytest.mark.parametrize('change', [dict(generation=1),dict(generation='2'),dict(operation='../other'),dict(operation='mesh-perf-3b-other')])
def test_stage_and_generation_are_exact(successor,tmp_path,change):
    settings=config(successor,tmp_path)
    stage=tmp_path/settings['operation']
    settings.update(change)
    with pytest.raises(RuntimeError):operator.validate_config(stage,settings)


@pytest.mark.parametrize('action',['arm','return','cleanup','abort-unarmed'])
def test_stale_operator_has_no_file_or_service_side_effects(successor,tmp_path,monkeypatch,action):
    service, owner, now, first, _ = successor
    settings=config(successor,tmp_path)
    prepare(successor);finish(successor)
    prepare(successor,'successor-03')
    before=current(successor)
    settings.update(operation='successor-02',generation=2)
    candidate=tmp_path/'friends-http-successor.pyz'
    (tmp_path/'directory.json').write_text(json.dumps(first['directory']))
    monkeypatch.setattr(operator,'sha',lambda file:operator.CANDIDATE_API if file==candidate else operator.BASE_API)
    monkeypatch.setattr(operator,'lock',lambda file:contextlib.nullcontext())
    monkeypatch.setattr(operator,'private',lambda file:json.dumps(dict(coordinator_state=str(tmp_path),operation='successor-02',generation=2)).encode())
    monkeypatch.setattr(operator,'load_service',lambda *_:(service,handoff,{}))
    monkeypatch.setattr(operator,'state',lambda *_:dict(ActiveState='active',NRestarts='0',MainPID='123',InvocationID='c'*32))
    monkeypatch.setattr(operator,'process_inputs',lambda *_:([str(candidate)],{}))
    def forbidden(*args,**kwargs):raise AssertionError('stale command attempted a side effect')
    monkeypatch.setattr(operator,'exclusive',forbidden)
    monkeypatch.setattr(operator,'run',forbidden)
    with pytest.raises(ValueError):
        if action=='abort-unarmed':operator.abort_unarmed(tmp_path,settings)
        else:operator.transition(tmp_path,settings,action)
    assert current(successor)==before


def test_never_armed_common_check_does_not_bypass_floor(successor,tmp_path,monkeypatch):
    service, owner, now, first, _ = successor
    prepare(successor)
    settings=config(successor,tmp_path)
    (tmp_path/'directory.json').write_text(json.dumps(first['directory']))
    monkeypatch.setattr(operator.time,'time',lambda:now)
    before=current(successor)
    operator.require_common_preserves(service,before,settings)
    older=dict(first['directory'],issued_at='2020-01-01T00:00:00Z')
    (tmp_path/'directory.json').write_text(json.dumps(older))
    with pytest.raises(ValueError):operator.require_common_preserves(service,before,settings)
    assert current(successor)==before


def test_inspection_distinguishes_retained_floor_from_new_capture(successor,tmp_path,monkeypatch):
    settings=config(successor,tmp_path)
    prepare(successor,settings['operation'])
    monkeypatch.setattr(operator,'state',lambda *_:dict(ActiveState='active'))
    monkeypatch.setattr(operator,'sha',lambda *_:operator.BASE_API)
    result=operator.inspect(tmp_path,settings)
    assert result['retained_floor_present'] and not result['floor_captured']
    assert result['generation']==2
