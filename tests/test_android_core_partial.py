import hashlib
import json

import pytest

from android_core_partial import readiness_metadata


@pytest.mark.parametrize('gateway', ['nl-amsterdam-1', 'nl-amsterdam-2'])
def test_receipt_projects_inner_readiness_without_credentials(gateway):
    response = dict(expires_at=123, minimum_crl=7, certificate='synthetic-private-fixture')
    envelope = dict(gateway_id=gateway, response=response) if gateway.endswith('2') else response
    raw = json.dumps(envelope).encode()
    assert readiness_metadata(raw) == dict(gateway=gateway, ready=None, expires=123, crl=7,
                                           sha256=hashlib.sha256(raw).hexdigest())


def test_unavailable_response_never_invents_credential_bounds():
    raw = b'{"gateway_id":"nl-amsterdam-2","response":{"status":"not_ready"}}'
    receipt = readiness_metadata(raw)
    assert receipt['expires'] is None and receipt['crl'] is None
