import hashlib


SOURCE_PATH = 'carrier/roombroker/authorization.go'
EXCHANGE_HANDLER = b'\tconfig.CredentialRenewal = binding.credentialHandler(path, secured)\n'


def legacy_source(original):
    assert original.count(EXCHANGE_HANDLER) == 1, 'Unknown shared runtime; legacy overlay refused'
    assert b'config.LeaseRenewal = binding.dynamicHandler(access)' in original
    return original.replace(EXCHANGE_HANDLER, b'', 1)


def describe(original, altered, driver, source, baseline):
    assert altered == legacy_source(original)
    assert driver != baseline, 'Legacy overlay was not compiled; unchanged driver refused'
    digest = lambda raw: hashlib.sha256(raw).hexdigest()
    return dict(schema=1, scope='legacy-peer-compatibility-fixture-not-online-runtime-acceptance',
                source_commit=source, source_path=SOURCE_PATH, original_sha256=digest(original),
                overlay_sha256=digest(altered), driver_sha256=digest(driver),
                normal_driver_sha256=digest(baseline),
                credential_exchange=False, lease_renewal=True,
                change='omit credential-exchange handler only; shared TLS/broker/lease/profile reader unchanged')
