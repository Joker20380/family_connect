import json
import io
import os
from pathlib import Path
import subprocess
import sys
import time

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
    assert record['console_returncode'] == 0


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


def test_inherited_pipe_is_distinct_from_parent_completion(tmp_path):
    release = tmp_path / 'release'
    identity = tmp_path / 'identity'
    child = ('import os,sys,time; from pathlib import Path; '
             'Path(sys.argv[2]).write_text(str(os.getpid())); deadline=time.monotonic()+5\n'
             'while not Path(sys.argv[1]).exists() and time.monotonic()<deadline: time.sleep(.01)')
    parent = subprocess.Popen([sys.executable, '-c',
        'import subprocess,sys; subprocess.Popen([sys.executable,"-c",sys.argv[1],*sys.argv[2:]]); '
        'raise SystemExit(7)', child, str(release), str(identity)], stdout=subprocess.PIPE)
    tee = subprocess.Popen(['tee', str(tmp_path / 'pipe.log')], stdin=parent.stdout, stdout=subprocess.DEVNULL)
    try:
        assert parent.wait(timeout=5) == 7
        deadline = time.monotonic() + 3
        while not identity.exists() and time.monotonic() < deadline:
            time.sleep(.01)
        child_pid = int(identity.read_text())
        pipe = os.readlink(f'/proc/{os.getpid()}/fd/{parent.stdout.fileno()}')
        parent.stdout.close()
        assert tee.poll() is None
        evidence = pipe_owners([dict(pid=parent.pid, pgid=os.getpgrp(), fd1=pipe)])
        record = next(item for item in evidence['processes'] if item['pid'] == child_pid)
        assert dict(fd=1, pipe=pipe, access=os.O_WRONLY) in record['pipes']
    finally:
        release.touch()
        parent.wait(timeout=5)
        tee.wait(timeout=6)


@pytest.mark.parametrize('code', [0, 7])
def test_fixture_wrapper_returns_real_child_status(tmp_path, code):
    program = ('from scripts import ci_release_fixtures as wrapper; import sys; '
               'wrapper.environment=lambda *args: {}; '
               'sys.argv=["wrapper", "run", "--fixtures", sys.argv[1], "--go", "/unused", '
               '"--nginx", "/unused", "--", sys.executable, "-c", '
               '"raise SystemExit(' + str(code) + ')"]; wrapper.main()')
    result = subprocess.run([sys.executable, '-c', program, str(tmp_path)], cwd=ROOT,
                            env=dict(os.environ, FC_CI_LIFECYCLE_LOG=str(tmp_path / 'wrapper.jsonl')),
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == code
    records = [json.loads(line.removeprefix('CI_LIFECYCLE ')) for line in result.stdout.splitlines()]
    assert records[-2]['stage'] == 'wrapper_child_end'
    assert records[-1]['stage'] == 'wrapper_end'
    assert records[-1]['returncode'] == code


@pytest.mark.parametrize('code', [0, 7])
def test_megabyte_inventory_line_retained_without_unbounded_console(tmp_path, code):
    result = subprocess.run(['bash', 'scripts/ci_full_suite.sh', sys.executable, '-c',
        f"print('x' * 1048685); print('COLLECTION_FAILURE_DETAIL'); raise SystemExit({code})"],
        cwd=ROOT, env=dict(os.environ, RUNNER_TEMP=str(tmp_path)),
        capture_output=True, timeout=10)
    assert result.returncode == code
    assert max(map(len, result.stdout.splitlines())) < 2048
    assert b'COLLECTION_FAILURE_DETAIL' in result.stdout
    assert (tmp_path / 'full-pytest.log').read_bytes() == b'x' * 1048685 + b'\nCOLLECTION_FAILURE_DETAIL\n'
    record = json.loads((tmp_path / 'full-pytest-lifecycle.jsonl').read_text())
    assert record['command_returncode'] == code
    assert record['tee_returncode'] == record['console_returncode'] == 0


def test_console_stream_bounds_chunks_and_preserves_short_binary_lines():
    from scripts.ci_console import relay
    raw = b'a\xff\r\n' + b'z' * 9000 + b'\nlast\x00line'
    output = io.BytesIO()
    relay(io.BytesIO(raw), output)
    assert output.getvalue().startswith(b'a\xff\r\nCI_LOG line=2 bytes=9001 ')
    assert output.getvalue().endswith(b'\nlast\x00line')


def test_pipeline_preserves_tee_failure(tmp_path):
    (tmp_path / 'full-pytest.log').mkdir()
    result = subprocess.run(['bash', 'scripts/ci_full_suite.sh', sys.executable, '-c', "print('sample')"],
        cwd=ROOT, env=dict(os.environ, RUNNER_TEMP=str(tmp_path)), capture_output=True, timeout=10)
    assert result.returncode != 0
    record = json.loads((tmp_path / 'full-pytest-lifecycle.jsonl').read_text())
    assert record['command_returncode'] == record['console_returncode'] == 0
    assert record['tee_returncode'] != 0
