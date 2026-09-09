import traceback

import pytest

from telemetry.events import FailureCode, FailureReport, Platform


BASE = dict(code='HANDSHAKE_TIMEOUT', platform='windows', app_version='0.2.0')


def test_failure_round_trip_has_only_bounded_fields():
    report = FailureReport.from_dict(BASE)
    assert report.to_dict() == BASE
    assert report.code is FailureCode.HANDSHAKE_TIMEOUT


@pytest.mark.parametrize('field', ['url', 'dns_history', 'packet_payload', 'private_key', 'message', 'ip'])
def test_sensitive_extra_fields_are_rejected_without_echo(field):
    secret = 'https://private.example/secret?PrivateKey=confidential'
    with pytest.raises(ValueError) as error:
        FailureReport.from_dict({**BASE, field: secret})
    assert secret not in ''.join(traceback.format_exception(error.value))


@pytest.mark.parametrize('field', list(BASE))
def test_allowed_fields_cannot_carry_exception_strings(field):
    secret = 'PrivateKey=confidential https://private.example'
    with pytest.raises(ValueError) as error:
        FailureReport.from_dict({**BASE, field: secret})
    assert secret not in ''.join(traceback.format_exception(error.value))


@pytest.mark.parametrize('value', [None, [], True, 42, {'nested': 'secret'}])
def test_non_string_values_are_rejected(value):
    with pytest.raises(ValueError):
        FailureReport.from_dict({**BASE, 'code': value})


def test_direct_construction_cannot_bypass_validation():
    with pytest.raises(ValueError):
        FailureReport('arbitrary exception', Platform.LINUX, '0.2.0')
    with pytest.raises(ValueError):
        FailureReport(FailureCode.DNS_FAILURE, Platform.LINUX, 'url.example')
