import copy
import pytest
from .classify import classify


def incident(kind=6,known=True):
    return dict(session_tag='one',protocol_errors=1,mux_lifecycle=dict(first_unknown=dict(
        event=dict(index=9,id=91,kind=kind,stage='unknown',at=10582),known=known,
        stream=dict(id=91,created=1000,finished=9999,removed=10000,reason='reset'),failure_at=0,cancelled=False)))


def test_exact_retired_reset_not_all_unknowns():
    source=incident();before=copy.deepcopy(source)
    result=classify([source]);assert result['proven_late_resets']==1
    assert result['raw_protocol_errors']==1 and source==before
    for changed in (incident(4),incident(5),incident(6,False)):
        assert classify([changed])['remaining_unexplained']==1
    for kind in (7,8):
        assert classify([incident(kind)])['proven_late_controls']==1
        assert classify([incident(kind,False)])['remaining_unexplained']==1


def test_missing_events_and_primary_failure_are_not_success():
    source=incident();source['protocol_errors']=3
    assert classify([source])['remaining_unexplained']==2
    source['mux_lifecycle']['first_unknown']['failure_at']=10001
    result=classify([source]);assert result['proven_late_resets']==0
    assert result['events'][0]['classification']=='AFTER_PRIMARY_FAILURE_OR_CANCELLATION'


def test_no_cross_session_or_unknown_retired_history():
    first=incident();second=incident();second['session_tag']='two'
    with pytest.raises(ValueError):classify([first,second])
    first['mux_lifecycle']['first_unknown']['stream']['removed']=0
    assert classify([first])['remaining_unexplained']==1
