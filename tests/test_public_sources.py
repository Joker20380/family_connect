import os
from pathlib import Path
import subprocess
import sys
import shutil
import pytest

from scripts.check_public_sources import violations


def test_forbidden_paths_and_known_credentials():
    for path in ("state-client-build/root", "backup/user.sqlite", ".env.prod", "keys/root.key", "backup/vault.kdbx", "keys/vault.keyx"):
        assert violations(path, b"ordinary data")
    samples = [b"-----BEGIN " + b"PRIVATE KEY-----", b"ghp_" + b"a" * 36,
               b"AKIA" + b"A" * 16, b"PrivateKey = " + b"a" * 43 + b"="]
    for raw in samples:
        assert violations("docs/innocent.md", raw)
    assert not violations("deploy/.env.example", b"TOKEN=replace-me")
    assert not violations("tests/vectors/TEST-ONLY-identity.json", b'{"test_only":true}')
    fixture = "clients/desktop/tests/test_awg.py"
    assert not violations(fixture, b"PrivateKey = " + b"A" * 43 + b"=")
    assert violations(fixture, b"PrivateKey = " + b"B" * 43 + b"=")


@pytest.mark.skipif(shutil.which("git") is None, reason="Git index integration requires git")
def test_index_bytes_not_worktree_and_no_secret_output(tmp_path):
    script = Path(__file__).resolve().parents[1] / "scripts/check_public_sources.py"
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    def git(*args):
        subprocess.run(["git", *args], cwd=tmp_path, env=env, check=True, capture_output=True)
    def scan():
        return subprocess.run([sys.executable, str(script)], cwd=tmp_path, env=env, capture_output=True)
    git("init")
    secret = b"ghp_" + b"Q" * 36
    file = tmp_path / "note.txt"
    file.write_bytes(secret)
    git("add", "note.txt")
    file.write_text("safe working copy")
    blocked = scan()
    assert blocked.returncode == 1
    assert b"github-token" in blocked.stdout
    assert secret not in blocked.stdout + blocked.stderr
    git("add", "note.txt")
    file.write_bytes(secret)
    assert scan().returncode == 0
