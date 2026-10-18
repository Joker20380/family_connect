import importlib.util
from configparser import ConfigParser
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


def assert_normal_profile_directives(profiles):
    parsed = {}
    for name in ('awg', 'wg'):
        config = ConfigParser(interpolation=None)
        config.read_string(profiles[name])
        parsed[name] = config
    assert parsed['awg'].get('Interface', 'Jc', fallback=None) == '3'
    assert not any(parsed['wg'].has_option(section, 'Jc') for section in parsed['wg'].sections())


def test_profiles_are_disposable_and_cover_all_approved_normal_types():
    profiles = AUTO.normal_profiles()
    assert set(profiles) == {'awg', 'wg', 'tcp'}
    assert AUTO.normal_profiles() != profiles
    assert_normal_profile_directives(profiles)


@pytest.fixture
def profiles_with_jc_key_values():
    key = 'Jc' + 'A' * 41 + '='
    profile = f'[Interface]\nPrivateKey = {key}\n[Peer]\nPublicKey = {key}\n'
    return {'wg': profile, 'awg': profile.replace('[Interface]\n', '[Interface]\nJc = 3\n', 1)}


def test_profile_directives_allow_jc_inside_private_and_public_keys(profiles_with_jc_key_values):
    assert_normal_profile_directives(profiles_with_jc_key_values)


@pytest.mark.parametrize('section', ['Interface', 'Peer'])
def test_profile_directives_reject_actual_wg_jc(profiles_with_jc_key_values, section):
    profiles_with_jc_key_values['wg'] = profiles_with_jc_key_values['wg'].replace(
        f'[{section}]\n', f'[{section}]\n  Jc = 3\n', 1)
    with pytest.raises(AssertionError):
        assert_normal_profile_directives(profiles_with_jc_key_values)


def test_profile_directives_require_awg_jc(profiles_with_jc_key_values):
    profiles_with_jc_key_values['awg'] = profiles_with_jc_key_values['awg'].replace('Jc = 3\n', '', 1)
    with pytest.raises(AssertionError):
        assert_normal_profile_directives(profiles_with_jc_key_values)


def test_profile_directives_require_expected_awg_jc_value(profiles_with_jc_key_values):
    profiles_with_jc_key_values['awg'] = profiles_with_jc_key_values['awg'].replace('Jc = 3\n', 'Jc = 4\n', 1)
    with pytest.raises(AssertionError):
        assert_normal_profile_directives(profiles_with_jc_key_values)
