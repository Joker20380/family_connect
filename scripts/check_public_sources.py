"""Check Git index blobs without printing secret values; stdlib only.

This is a bounded publication guard, not a complete secret detector or history audit.
It reads staged bytes, never ignored/untracked runtime files or the working copy.
"""
from pathlib import PurePosixPath
import re
import subprocess


PATTERNS = {
    "private-key-pem": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH |ENCRYPTED )?PRIVATE KEY-----"),
    "github-token": re.compile(rb"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{50,})\b"),
    "aws-access-key": re.compile(rb"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "slack-token": re.compile(rb"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
    "wireguard-private-key": re.compile(rb"(?im)^\s*PrivateKey\s*=\s*[A-Za-z0-9+/]{43}=\s*$"),
}


def violations(path: str, raw: bytes) -> list[str]:
    p = PurePosixPath(path)
    reasons = []
    if any(part == "state" or part.startswith("state-") for part in p.parts):
        reasons.append("runtime-state-path")
    if p.name == ".env" or (p.name.startswith(".env.") and p.name not in {".env.example", ".env.template"}):
        reasons.append("environment-file")
    if p.suffix.lower() in {".key", ".p12", ".pfx", ".jks", ".keystore", ".db", ".sqlite", ".sqlite3", ".apk"}:
        reasons.append("private-or-runtime-file")
    for name, pattern in PATTERNS.items():
        matches = list(pattern.finditer(raw))
        # Existing public parser fixtures use an all-zero key. No directory-wide
        # exception: any other value in these same files is still rejected.
        if name == "wireguard-private-key" and path in {
            "clients/desktop/tests/test_awg.py", "clients/desktop/tests/test_profile.py"
        }:
            matches = [m for m in matches if m.group().split(b"=", 1)[1].strip() != b"A" * 43 + b"="]
        if matches:
            reasons.append(name)
    return reasons


def check_index() -> int:
    records = subprocess.check_output(["git", "ls-files", "--stage", "-z"]).split(b"\0")
    failed = 0
    count = 0
    for record in records:
        if not record:
            continue
        meta, name = record.split(b"\t", 1)
        mode, oid, stage = meta.split()
        path = name.decode("utf-8", "backslashreplace")
        # A submodule does not expose its contents to this repository's scanner.
        if stage != b"0" or mode not in {b"100644", b"100755"}:
            reasons = ["unsupported-index-entry"]
        else:
            raw = subprocess.check_output(["git", "cat-file", "blob", oid.decode("ascii")])
            reasons = violations(path, raw)
        count += 1
        if reasons:
            failed += 1
            # repr prevents a crafted filename from injecting terminal/log lines.
            print(f"BLOCK {path!r}: {', '.join(reasons)}")
    print(f"Public source guard: {count} index entries, {failed} blocked files")
    return int(bool(failed))


if __name__ == "__main__":
    raise SystemExit(check_index())
