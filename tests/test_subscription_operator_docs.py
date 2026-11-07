import os
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]


def test_copied_operator_commands_choose_one_action_and_refuse_receipt_overwrite(tmp_path):
    guide = (ROOT / 'docs/operators/subscriptions.ru.md').read_text()
    blocks = [block for block in re.findall(r'```sh\n(.*?)```', guide, re.S)
              if '--db "$REGISTRY_DB"' in block and '"$PAID_OPERATOR_ARCHIVE"' in block]
    expected = {'status', 'activate', 'grace', 'expire', 'revoke'}
    actions = []
    receipts = []
    executable = tmp_path / 'python'
    executed = tmp_path / 'executed'
    executable.write_text('#!/bin/sh\nprintf executed > "$EXECUTED"\nprintf receipt\n')
    executable.chmod(0o700)
    for block in blocks:
        action = re.findall(r'--db "\$REGISTRY_DB" (\w+)', block)
        assert len(action) == 1
        actions.extend(action)
        variable, = re.findall(r'> "\$(PRIVATE_\w+_RECEIPT)"', block)
        receipts.append(variable)
        receipt = tmp_path / variable
        receipt.write_text('original receipt')
        environment = dict(os.environ, PATH=str(tmp_path) + ':' + os.environ['PATH'],
                           EXECUTED=str(executed), OPERATOR_PYTHON=str(executable),
                           PAID_OPERATOR_ARCHIVE='synthetic-operator.pyz', **{variable: str(receipt)})
        subprocess.run(['sh', '-n'], input=block, text=True, check=True)
        result = subprocess.run(['sh'], input=block, text=True, env=environment, capture_output=True)
        assert result.returncode != 0 and not executed.exists()
        assert receipt.read_text() == 'original receipt'
        receipt.unlink()
        subprocess.run(['sh'], input=block, text=True, env=environment, capture_output=True, check=True)
        assert receipt.read_text() == 'receipt' and receipt.stat().st_mode & 0o777 == 0o600
        executed.unlink()
    assert set(actions) == expected and len(actions) == len(expected)
    assert len(set(receipts)) == len(receipts)
