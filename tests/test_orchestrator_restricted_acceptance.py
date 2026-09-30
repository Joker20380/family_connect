import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location('auto_acceptance', Path(__file__).resolve().parents[1] / 'pilot/android-restricted/auto_acceptance.py')
AUTO = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUTO)


def connected():
    events = []
    for candidate in ('awg', 'wg', 'tcp', 'restricted'):
        events.append({'event': 'candidate_attempted', 'candidate': candidate, 'state': 'CONNECTING'})
        events.append({'event': 'candidate_succeeded' if candidate == 'restricted' else 'candidate_failed',
                       'candidate': candidate, 'state': 'CONNECTED' if candidate == 'restricted' else 'CONNECTING',
                       'category': 'TRANSPORT_UNAVAILABLE'})
    return events


def test_all_normals_must_fail_before_one_restricted_success():
    AUTO.validate_connected(connected())
    for candidate in ('awg', 'wg', 'tcp', 'restricted'):
        with pytest.raises(RuntimeError):
            AUTO.validate_connected([event for event in connected() if event['candidate'] != candidate])
    with pytest.raises(RuntimeError):
        AUTO.validate_connected(connected() * 2)


def test_loss_is_bounded_without_restarting_failed_restricted():
    events = connected() + [{'event': 'restoration_attempted', 'state': 'RESTORING'},
                            {'event': 'restoration_failed', 'state': 'FAILED'}]
    AUTO.validate_failed(events)
    with pytest.raises(RuntimeError):
        AUTO.validate_failed(events + events[-2:])
    with pytest.raises(RuntimeError):
        AUTO.validate_failed(events[:-1] + [{'event': 'candidate_attempted', 'state': 'FAILED'}])


def test_profiles_are_disposable_and_cover_all_approved_normal_types():
    profiles = AUTO.normal_profiles()
    assert set(profiles) == {'awg', 'wg', 'tcp'}
    assert AUTO.normal_profiles() != profiles
    assert 'Jc = 3' in profiles['awg'] and 'Jc' not in profiles['wg']
