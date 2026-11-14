import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from scripts.ci_lifecycle import pipe_owners

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('code', [0, 7])
def test_pipeline_really_exits_and_preserves_child_failure(tmp_path, code):
    result = subprocess.run(['bash', 'scripts/ci_full_suite.sh', sys.executable, '-c',
        f"print('synthetic diagnostic'); raise SystemExit({code})"], cwd=ROOT,
        env=dict(os.environ, RUNNER_TEMP=str(tmp_path)), capture_output=True, text=True, timeout=10)
    assert result.returncode == code
    assert 'synthetic diagnostic' in (tmp_path / 'full-pytest.log').read_text()
    record = json.loads((tmp_path / 'full-pytest-lifecycle.jsonl').read_text())
    assert record['stage'] == 'pipeline_end'
    assert record['command_returncode'] == code
    assert record['tee_returncode'] == 0


def test_pipe_evidence_identifies_writer_without_command_arguments():
    process = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(20)',
                                'SYNTHETIC_SECRET_NOT_FOR_DIAGNOSTICS'], stdout=subprocess.PIPE)
    try:
        pipe = os.readlink(f'/proc/{process.pid}/fd/1')
        evidence = pipe_owners([dict(pid=process.pid, pgid=os.getpgrp(), fd1=pipe)])
        record = next(item for item in evidence['processes'] if item['pid'] == process.pid)
        assert record['known']
        assert dict(fd=1, pipe=pipe, access=os.O_WRONLY) in record['pipes']
        assert 'SYNTHETIC_SECRET' not in json.dumps(evidence)
    finally:
        process.terminate()
        process.wait(timeout=5)
        process.stdout.close()
