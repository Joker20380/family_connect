import getpass
import importlib.machinery
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import warnings

import pytest

from fleet.contracts import canonical, load
from fleet.role_config import publisher_config


SCRIPT = Path(__file__).resolve().parents[2] / 'scripts/fleet-rehearsal-publisher-input'
loader = importlib.machinery.SourceFileLoader('rehearsal_publisher_input', str(SCRIPT))
spec = importlib.util.spec_from_loader(loader.name, loader)
module = importlib.util.module_from_spec(spec)
loader.exec_module(module)
TOKEN = 'synthetic-only-not-a-real-provider-token'


def test_private_input_matches_material_contract_without_disclosure(tmp_path, capsys):
    tmp_path.chmod(0o700)
    directory = tmp_path / 'input'
    receipt = module.store(directory, lambda prompt: TOKEN)
    destination = directory / 'publisher-material.json'
    raw = destination.read_bytes()
    assert publisher_config(raw) == ('YANDEX_TELEMOST_OAUTH_TOKEN=' + TOKEN + '\n').encode()
    assert load(raw) == dict(scope=module.SCOPE, token=TOKEN)
    assert directory.stat().st_mode & 0o777 == 0o700
    assert destination.stat().st_mode & 0o777 == 0o600
    assert destination.stat().st_uid == os.geteuid()
    assert TOKEN.encode() not in canonical(receipt)
    assert capsys.readouterr() == ('', '')
    assert receipt['credential_validity'] == 'NOT_CHECKED'


@pytest.mark.parametrize('token', ['', 'short', TOKEN + '\n', TOKEN + '\0', 'a' * 4097, 'secret value'])
def test_invalid_token_never_written(tmp_path, token):
    tmp_path.chmod(0o700)
    with pytest.raises(ValueError):
        module.store(tmp_path / 'input', lambda prompt: token)
    assert not (tmp_path / 'input/publisher-material.json').exists()


def test_existing_input_never_replaced_or_prompted(tmp_path):
    tmp_path.chmod(0o700)
    directory = tmp_path / 'input'
    module.store(directory, lambda prompt: TOKEN)
    with pytest.raises(ValueError, match='existing input retained'):
        module.store(directory, lambda prompt: pytest.fail('unexpected input prompt'))
    assert load((directory / 'publisher-material.json').read_bytes())['token'] == TOKEN


@pytest.mark.parametrize('unsafe', ['symlink-directory', 'symlink-file', 'public-directory', 'public-parent'])
def test_unsafe_destination_rejected_before_input(tmp_path, unsafe):
    tmp_path.chmod(0o700)
    directory = tmp_path / 'input'
    if unsafe == 'symlink-directory':
        directory.symlink_to(tmp_path, target_is_directory=True)
    else:
        directory.mkdir(mode=0o700)
    if unsafe == 'symlink-file':
        (directory / 'publisher-material.json').symlink_to(tmp_path / 'absent')
    if unsafe == 'public-directory':
        directory.chmod(0o755)
    if unsafe == 'public-parent':
        tmp_path.chmod(0o755)
    with pytest.raises(ValueError):
        module.store(directory, lambda prompt: pytest.fail('unexpected input prompt'))


def test_getpass_echo_fallback_rejected(tmp_path):
    tmp_path.chmod(0o700)
    def unsafe_prompt(prompt):
        warnings.warn('echo fallback', getpass.GetPassWarning)
        return TOKEN
    with pytest.raises(getpass.GetPassWarning):
        module.store(tmp_path / 'input', unsafe_prompt)
    assert not (tmp_path / 'input/publisher-material.json').exists()


@pytest.mark.parametrize('arguments', [[], [TOKEN]])
def test_noninteractive_or_argv_secret_rejected_without_echo(arguments):
    result = subprocess.run([sys.executable, str(SCRIPT), *arguments], input=TOKEN,
                            capture_output=True, text=True, check=False)
    assert result.returncode == 1
    assert load(result.stdout)['result'] == 'REJECTED'
    assert TOKEN not in result.stdout + result.stderr
