import importlib.util
from pathlib import Path
import pytest


specification = importlib.util.spec_from_file_location(
    'pack_assets', Path(__file__).with_name('android_cold_pack_assets.py'))
pack_assets = importlib.util.module_from_spec(specification)
specification.loader.exec_module(pack_assets)


def test_pkcs12_signer_does_not_read_one_line_password_file_twice(tmp_path):
    command = pack_assets.signer_command(tmp_path, tmp_path, tmp_path / 'signed.apk',
                                         tmp_path / 'aligned.apk')
    assert command.count('file:' + str(tmp_path / 'test-signing.pass')) == 1
    assert '--ks-pass' in command
    assert '--key-pass' not in command
    assert command[command.index('--ks-key-alias') + 1] == 'cold-runtime'
    assert command[command.index('--min-sdk-version') + 1] == '27'


@pytest.mark.parametrize('value', [b'', b'a' * 64, b'a' * 64 + b'\n'])
def test_invalid_egress_digest_rejected_before_packaging(tmp_path, value):
    (tmp_path / 'egress.sha256').write_bytes(value)
    with pytest.raises(ValueError, match='EGRESS_DIGEST_MUST_BE_32_RAW_BYTES'):
        pack_assets.main(tmp_path)
    assert not (tmp_path / 'apk-final').exists()
