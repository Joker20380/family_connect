"""Bounded offline native prerequisite with durable, allowlisted receipts."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import tempfile

STAGES = frozenset(('input', 'configuration', 'device_parse', 'device_chain',
                    'device_admission', 'gateway_parse', 'gateway_chain',
                    'gateway_binding', 'family_negative', 'revision_negative',
                    'crl_negative', 'complete'))
REASONS = frozenset(('arguments', 'unreadable_or_oversized', 'rejected', 'malformed',
                     'successor_unavailable', 'unexpected_acceptance', 'validated'))
OBJECTS = frozenset(('operator', 'gateway_profile', 'device_certificate',
                     'gateway_certificate', 'crl', 'authority'))
COMPARISONS = frozenset(('not_evaluated', 'signed_claim_or_revocation', 'wrong_family',
                         'above_signed_revision', 'above_signed_sequence', 'positive_and_negatives'))
FIELDS = frozenset(('version', 'status', 'stage', 'reason', 'object', 'comparison'))


def parse(raw, exit_code):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate field')
            result[key] = value
        return result
    try:
        value = json.loads(raw, object_pairs_hook=unique)
        if (type(value) is not dict or set(value) != FIELDS
                or type(value['version']) is not int or value['version'] != 1
                or value['status'] not in ('PASS', 'FAIL')
                or value['stage'] not in STAGES or value['reason'] not in REASONS
                or value['object'] not in OBJECTS or value['comparison'] not in COMPARISONS):
            return None
        passing = dict(version=1, status='PASS', stage='complete', reason='validated',
                       object='authority', comparison='positive_and_negatives')
        if value['status'] == 'PASS':
            return value if exit_code == 0 and value == passing else None
        if exit_code != 1 or value['stage'] == 'complete' or value['reason'] == 'validated':
            return None
        return value
    except (ValueError, TypeError, UnicodeError, RecursionError):
        return None


def persist(path, value):
    path = Path(path)
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        metadata = os.fstat(directory)
        if metadata.st_uid != os.geteuid() or metadata.st_mode & 0o077:
            raise ValueError('Receipt directory must be owner-only')
        descriptor = os.open(path.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                             0o600, dir_fd=directory)
        with os.fdopen(descriptor, 'w') as stream:
            json.dump(value, stream, separators=(',', ':'))
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.fsync(directory)
    finally:
        os.close(directory)


def execute(binary, expected_sha256, profile, certificate, receipt_path, *, timeout=10):
    if Path(receipt_path).exists():
        raise ValueError('Existing receipt; inspect instead of replaying')
    record = dict(version=1, timestamp=datetime.now(timezone.utc).isoformat(),
                  attempt=secrets.token_hex(16), passed=False, classification='artifact_mismatch',
                  binary_sha256=None, exit=None, native=None)
    try:
        raw = Path(binary).read_bytes()
        record['binary_sha256'] = hashlib.sha256(raw).hexdigest()
        if record['binary_sha256'] == expected_sha256:
            with tempfile.TemporaryFile() as output:
                try:
                    result = subprocess.run([str(Path(binary).resolve()), str(Path(profile).resolve()),
                                             str(Path(certificate).resolve())], cwd='/',
                                            stdin=subprocess.DEVNULL, stdout=output,
                                            stderr=subprocess.DEVNULL, timeout=timeout, check=False)
                    record['exit'] = result.returncode
                    output.seek(0)
                    response = output.read(4097)
                    native = parse(response, result.returncode) if len(response) <= 4096 else None
                    record['native'] = native
                    record['classification'] = ('native_pass' if native['status'] == 'PASS' else 'native_rejected') if native else 'invalid_receipt'
                    record['passed'] = bool(native and native['status'] == 'PASS')
                    if hashlib.sha256(Path(binary).read_bytes()).hexdigest() != expected_sha256:
                        record.update(passed=False, classification='artifact_changed')
                except subprocess.TimeoutExpired:
                    record['classification'] = 'timeout'
    except OSError:
        record['classification'] = 'execution_unavailable'
    persist(receipt_path, record)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', type=Path, required=True)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--profile', type=Path, required=True)
    parser.add_argument('--certificate', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    arguments = parser.parse_args()
    result = execute(arguments.binary, arguments.sha256, arguments.profile,
                     arguments.certificate, arguments.receipt)
    print(json.dumps(result, separators=(',', ':')))
    raise SystemExit(0 if result['passed'] else 1)


if __name__ == '__main__':
    main()
