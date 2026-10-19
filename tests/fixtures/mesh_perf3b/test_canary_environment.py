import importlib.util
from pathlib import Path

import pytest


spec = importlib.util.spec_from_file_location('stage_canary', Path(__file__).with_name('stage_canary.py'))
staging = importlib.util.module_from_spec(spec)
spec.loader.exec_module(staging)
PROVIDER = '/opt/apps/family_connect/friends-restricted/provider.env'


def test_uses_existing_file_without_token_in_arguments():
    arguments = staging.provider_options(PROVIDER, 0, 0o600, ['YANDEX_TELEMOST_OAUTH_TOKEN'], True)
    assert arguments == ['--property=EnvironmentFile=' + PROVIDER]
    assert 'YANDEX_TELEMOST_OAUTH_TOKEN=' not in ''.join(arguments)


@pytest.mark.parametrize('uid,mode,keys,present', [
    (1000, 0o600, ['YANDEX_TELEMOST_OAUTH_TOKEN'], True),
    (0, 0o644, ['YANDEX_TELEMOST_OAUTH_TOKEN'], True),
    (0, 0o600, ['YANDEX_TELEMOST_OAUTH_TOKEN','FC_FATAL_RECEIPT_DIR'], True),
    (0, 0o600, ['YANDEX_TELEMOST_OAUTH_TOKEN'], False),
])
def test_rejects_unreviewed_provider_environment(uid, mode, keys, present):
    with pytest.raises(AssertionError):
        staging.provider_options(PROVIDER, uid, mode, keys, present)


def test_remote_runs_same_provider_validation_before_process_start():
    compile(staging.REMOTE, '<remote>', 'exec')
    assert staging.REMOTE.index('provider=provider_options(') < staging.REMOTE.index('run(arguments,timeout=30)')
    assert '--setenv=YANDEX_TELEMOST_OAUTH_TOKEN=' not in staging.REMOTE
    assert 'arguments += provider' in staging.REMOTE
