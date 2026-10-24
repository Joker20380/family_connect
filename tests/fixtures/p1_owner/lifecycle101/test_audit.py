import importlib.util
from pathlib import Path

spec=importlib.util.spec_from_file_location('audit101',Path(__file__).with_name('audit.py'))
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


def test_pending_crossing_cannot_hide_unrelated_raw_error():
    life=dict(expected_crossings=1,actual_violations=0,unclassified=0,incident_dropped=0,
              incidents=[dict(**{'class':'expected'},stream=dict(removed=0))])
    result=module.classify(dict(protocol_errors=1,mux_lifecycle=life))
    assert not result['clean'] and result['expected_raw']==0


def test_removed_crossing_retains_raw_counter_and_checks_completeness():
    life=dict(expected_crossings=1,actual_violations=0,unclassified=0,incident_dropped=0,
              incidents=[dict(**{'class':'expected'},stream=dict(removed=123))])
    diagnostic=dict(protocol_errors=1,mux_lifecycle=life)
    assert module.classify(diagnostic)['clean'] and diagnostic['protocol_errors']==1
    life['incident_dropped']=1
    assert not module.classify(diagnostic)['clean']


def test_unclassified_and_absent_history_never_clean():
    assert not module.classify(dict(protocol_errors=0))['clean']
    life=dict(expected_crossings=0,actual_violations=0,unclassified=1,incident_dropped=0,
              incidents=[dict(**{'class':'unclassified'},stream=dict(removed=123))])
    assert not module.classify(dict(protocol_errors=1,mux_lifecycle=life))['clean']
