"""Validate a protected unsigned request with pinned deployed validators; never sign.

Runs actual historical signature and request checks, then in-memory negative cases.
No production connections, credential generation, or live file mutation occurs.
"""

import argparse
import base64
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import resource
import stat
import sys
import time


PINS = {
    'api.pyz': '12ca0c72a89ff20c1b3c70a1182a2d5d98d4d78d25e7a079bb4d75bdf34060ed',
    'credential_renewal.py': 'fb83d851b4ac88b7ad90b97c59f516ee327bc7bbb92a642a031da08bbc50d25c',
    'expired_recovery.py': '92fc24346df6b86b0621210e7847a2d17c11a69e8c2ae73bf32609fa2f2ab99e',
    'grant_cutover.py': '434881ff8b1878eabb040c9c8b06bd32ad430410fbec90a24e3343b51a222f85',
    'sign_authority_offline.py': '2de81e84c6b5fb39cbf5ca840e7a4791edec256bbb6e3fe7924efc24319ba5f6',
}


def protected_read(path):
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) != 0o600:
        raise ValueError('PRIVATE_FILE_PERMISSIONS')
    return path.read_bytes()


def main():
    os.umask(0o077)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--offline-dir', type=Path, required=True)
    parser.add_argument('--expected-sha256', required=True)
    parser.add_argument('--expected-operation', required=True)
    parser.add_argument('--expected-anchor-sha256', required=True)
    parser.add_argument('--summary-output', type=Path, required=True)
    args = parser.parse_args()
    offline = args.offline_dir.resolve()
    for name, expected in PINS.items():
        if hashlib.sha256(protected_read(offline / name)).hexdigest() != expected:
            raise ValueError('OFFLINE_SOURCE_PIN_CHANGED')
    raw = protected_read(args.request)
    if len(raw) > 1048576 or b'PRIVATE KEY' in raw or hashlib.sha256(raw).hexdigest() != args.expected_sha256:
        raise ValueError('REQUEST_HASH_OR_BOUND')
    anchor = base64.b64decode(protected_read(offline / 'anchor.pub').strip(), validate=True)
    if hashlib.sha256(anchor).hexdigest() != args.expected_anchor_sha256:
        raise ValueError('ANCHOR_PIN_CHANGED')
    sys.dont_write_bytecode = True
    sys.path[:0] = [str(offline), str(offline / 'api.pyz')]
    from credential_renewal import Rejected, Validator, canonical, parse
    from control.friends.restricted import delegation
    from cryptography import x509
    from expired_recovery import request_check

    request = parse(raw)
    if request['operation_id'] != args.expected_operation:
        raise ValueError('OPERATION_MISMATCH')
    now = int(time.time())
    validator = Validator(anchor, delegation)
    predecessor = request_check(request, validator, now)
    successor = x509.load_pem_x509_certificate(request['successor_payload']['authority'].encode())
    successor.verify_directly_issued_by(successor)
    results = []
    cases = [
        ('purpose', ('purpose',), 'UNAPPROVED_RECOVERY', 'RECOVERY_PURPOSE'),
        ('predecessor_digest', ('predecessor_sha256',), '0' * 64, 'RECOVERY_PREDECESSOR_DIGEST'),
        ('scope', ('scope', 'family'), 'invalid', 'RECOVERY_SCOPE_OR_FLOOR'),
        ('crl_floor', ('floors', 'crl'), request['floors']['crl'] - 1, 'RECOVERY_SCOPE_OR_FLOOR'),
        ('authority_sequence', ('successor_payload', 'sequence'), request['floors']['authority'], 'RECOVERY_SCOPE_OR_FLOOR'),
        ('grant_scope', ('grant_scope',), request['grant_scope'][:-1], 'RECOVERY_GRANT_SCOPE'),
        ('update_scope', ('updates',), [name for name in request['updates'] if name != 'crl'], 'RECOVERY_UPDATE_SCOPE'),
        ('expired_request', ('expires_at',), now, 'RECOVERY_APPROVAL_EXPIRED'),
        ('authority_validity_extension', ('successor_payload', 'expires_at'), request['successor_payload']['expires_at'] + 1, 'RECOVERY_SUCCESSOR_INVALID'),
        ('old_ca_substitution', ('successor_payload', 'authority'), predecessor.trust['authority'], 'RECOVERY_INTERVAL'),
        ('predecessor_signature', ('predecessor', 'authority', 'signature'), base64.b64encode(bytes(64)).decode(), 'RECOVERY_PREDECESSOR_UNTRUSTED'),
    ]
    for name, keys, value, expected in cases:
        changed = copy.deepcopy(request)
        target = changed
        for key in keys[:-1]:
            target = target[key]
        target[keys[-1]] = value
        try:
            request_check(changed, validator, now)
        except Rejected as error:
            if str(error) != expected:
                raise ValueError('UNEXPECTED_NEGATIVE_RESULT') from None
            results.append({'case': name, 'result': 'REJECTED', 'cause': expected})
        else:
            raise ValueError('TAMPERED_REQUEST_ACCEPTED')
    wrong_anchor = bytes([anchor[0] ^ 1]) + anchor[1:]
    try:
        request_check(request, Validator(wrong_anchor, delegation), now)
    except Rejected as error:
        if str(error) != 'RECOVERY_PREDECESSOR_UNTRUSTED':
            raise ValueError('UNEXPECTED_ANCHOR_RESULT') from None
        results.append({'case': 'wrong_anchor', 'result': 'REJECTED', 'cause': str(error)})
    else:
        raise ValueError('WRONG_ANCHOR_ACCEPTED')
    try:
        delegation(request['predecessor']['authority'], anchor, now)
    except ValueError:
        results.append({'case': 'expired_predecessor_as_live_authority', 'result': 'REJECTED'})
    else:
        raise ValueError('EXPIRED_LIVE_AUTHORITY_ACCEPTED')
    if protected_read(args.request) != raw:
        raise ValueError('REQUEST_CHANGED_DURING_TEST')
    summary = dict(
        result='PASS_UNSIGNED_REQUEST_ONLY', utc=datetime.now(timezone.utc).isoformat(),
        request_sha256=hashlib.sha256(raw).hexdigest(), operation_id=request['operation_id'],
        source_pins=PINS, historical_signature_checks=True, request_check=True,
        successor_self_signature=True, root_signer_invoked=False, request_unchanged=True,
        negative_cases=results, negative_pass_count=len(results),
        successor_ca_pem_sha256=hashlib.sha256(request['successor_payload']['authority'].encode()).hexdigest(),
        successor_payload_sha256=hashlib.sha256(canonical(request['successor_payload'])).hexdigest(),
        physical_or_signed_successor_acceptance=False,
    )
    args.summary_output.write_text(json.dumps(summary, indent=2) + '\n')
    args.summary_output.chmod(0o600)
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        print(json.dumps({'result': 'FAIL_CLOSED', 'details': 'suppressed; no signing or automatic retry'}))
        raise SystemExit(1) from None
