import copy

import pytest

from backend import mesh_presentation


def snapshot(state='CONNECTED', profile='P1', send=32, receive=32, mux='CREDIT128', window=131072):
    return dict(state=state, desired_connected=True, native=dict(native=dict(
        selected_profile=profile, tun_ready=True, packet=dict(diagnostic=dict(
            speed_profile=profile, reliable_limits=dict(effective_send=send, local_receive=receive),
            mux_profile=mux, mux_window=window)))))


def test_selected_profile_never_substitutes_actual_negotiation():
    value = snapshot(send=16, mux='LEGACY64', window=65536)
    view = mesh_presentation(value)
    assert view['selected_profile'] == 'P1'
    assert view['effective'] == 'RS16/32 · LEGACY64'
    assert view['owned'] and view['connected'] and not view['pending']


@pytest.mark.parametrize('state', ['CONNECTING', 'RESTORING', 'STOPPING', 'FAILED', 'DISCONNECTED'])
def test_no_negotiated_profile_from_previous_session(state):
    view = mesh_presentation(snapshot(state=state))
    assert not view['connected'] and view['effective'] is None
    assert view['owned']


def test_ready_is_required_not_only_requested_p1():
    value = snapshot()
    value['native']['native']['tun_ready'] = False
    assert mesh_presentation(value)['effective'] is None
    assert mesh_presentation(snapshot())['effective'] == 'RS32/32 · CREDIT128'


@pytest.mark.parametrize('path', [('native',), ('native','native'), ('native','native','packet'),
                                ('native','native','packet','diagnostic'),
                                ('native','native','packet','diagnostic','reliable_limits')])
@pytest.mark.parametrize('malformed', [None, [], 'private data'])
def test_malformed_native_diagnostics_cannot_crash_or_echo_data(path, malformed):
    value = copy.deepcopy(snapshot())
    target = value
    for name in path[:-1]:
        target = target[name]
    target[path[-1]] = malformed
    view = mesh_presentation(value)
    assert view['effective'] is None and 'private data' not in str(view)


@pytest.mark.parametrize('send,receive,mux,window', [(True,32,'CREDIT128',131072),
                        (32,64,'CREDIT128',131072), (32,32,'CREDIT128',65536), (32,32,'Q1',131072)])
def test_unknown_effective_parameters_are_not_claimed(send, receive, mux, window):
    assert mesh_presentation(snapshot(send=send,receive=receive,mux=mux,window=window))['effective'] is None


def test_guard_or_service_failure_retains_disconnect_action():
    value = mesh_presentation(dict(state='FAILED',desired_connected=True))
    assert value['owned'] and not value['connected']
    value = mesh_presentation(dict(state='DISCONNECTED',desired_connected=False))
    assert not value['owned'] and not value['pending']
