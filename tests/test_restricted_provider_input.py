import importlib.util
from pathlib import Path

import pytest


SPEC = importlib.util.spec_from_file_location('provider_input', Path(__file__).resolve().parents[1]
                                             / 'deploy/friends/restricted/provision-provider-env.py')
PROVIDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROVIDER)


@pytest.mark.parametrize('value', ['synthetic-test', '"\\$` #= synthetic', 'тест'])
def test_systemd_quoted_roundtrip(value):
    assert PROVIDER.parse(PROVIDER.encode(value)) == value


@pytest.mark.parametrize('value', ['', 'synthetic\nvalue', 'synthetic\rvalue', 'synthetic\0value', 'x' * 4097])
def test_provider_schema_rejects_invalid_input(value):
    with pytest.raises(ValueError, match='^provider configuration rejected$'):
        PROVIDER.encode(value)


@pytest.mark.parametrize('raw', [b'OTHER="synthetic"\n', b'YANDEX_TELEMOST_OAUTH_TOKEN=""\n',
                               b'YANDEX_TELEMOST_OAUTH_TOKEN="synthetic"\nEXTRA=1\n',
                               b'YANDEX_TELEMOST_OAUTH_TOKEN="\\z"\n'])
def test_parser_rejects_extra_or_noncanonical_fields(raw):
    with pytest.raises(ValueError):
        PROVIDER.parse(raw)


def test_no_tty_never_prompts_or_touches_runtime(monkeypatch):
    monkeypatch.setattr(PROVIDER.os, 'geteuid', lambda: 0)
    monkeypatch.setattr(PROVIDER.os, 'getegid', lambda: 0)
    monkeypatch.setattr(PROVIDER.os, 'umask', lambda mode: None)
    monkeypatch.setattr(PROVIDER.resource, 'setrlimit', lambda *args: None)
    monkeypatch.setattr(PROVIDER.sys, 'argv', ['helper'])
    monkeypatch.setattr(PROVIDER.sys.stdin, 'isatty', lambda: False)
    monkeypatch.setattr(PROVIDER, 'runtime_guard', lambda: pytest.fail('runtime inspected before TTY guard'))
    monkeypatch.setattr(PROVIDER.getpass, 'getpass', lambda *args: pytest.fail('unsafe prompt'))
    with pytest.raises(ValueError, match='interactive terminal required'):
        PROVIDER.main()


def test_existing_destination_never_truncated(tmp_path):
    path = tmp_path / 'provider.env'
    path.write_bytes(b'synthetic-existing')
    directory = PROVIDER.os.open(tmp_path, PROVIDER.os.O_RDONLY | PROVIDER.os.O_DIRECTORY)
    try:
        with pytest.raises(FileExistsError):
            PROVIDER.write_new(directory, 'synthetic-new')
        assert path.read_bytes() == b'synthetic-existing'
    finally:
        PROVIDER.os.close(directory)
