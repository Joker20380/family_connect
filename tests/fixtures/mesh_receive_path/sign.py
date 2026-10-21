"""Reuse existing protected signing; never overwrite90 or a signed91 artifact."""

import os
import sys

from preserve import ROOT, WORK, digest


def main():
    os.umask(0o077)
    original = ROOT / 'tests/fixtures/mesh_throughput_trace/sign.py'
    assert digest(original) == 'e9d703553ab073ce25a0e76312827a5b650c6cb5ce2a2ab854f1f5d672ab56e3'
    source = original.read_text()
    replacements = {
        "WORK = ROOT / 'state-client-build/mesh-throughput-trace-20261019'": 'WORK = ROOT / "state-client-build/mesh-receive-path-20261020"',
        "state-client-build/beta87-product-fix-20261019/delivery/FamilyConnect-0.1.18-beta88-recovery.apk": "state-client-build/tunnel-restart-20261019/delivery/FamilyConnect-0.1.18-beta90-stability.apk",
        '968a61724f4e71ac0335e330960eb9b54e5ede59bae81df0b6e8499e4ce6c2ce': '68cbcccfb5adf8656e8203436126330e780de099670ee2031d71019baadc3e9a',
        'metadata(baseline, 88, True), metadata(unsigned, 89, False)': 'metadata(baseline, 90, True), metadata(unsigned, 91, False)',
        'FamilyConnect-0.1.18-beta89-mesh-trace.apk': 'FamilyConnect-0.1.18-beta91-receive-trace.apk',
        'metadata(signed, 89, True)': 'metadata(signed, 91, True)',
    }
    for old, new in replacements.items():
        assert old in source, old
        source = source.replace(old, new)
    namespace = dict(__name__='scoped_signing', __file__=str(original))
    exec(compile(source, str(original), 'exec'), namespace)
    namespace['main']()


if __name__ == '__main__':
    try:
        main()
    except Exception:
        print('SIGNING_STOPPED_NO_SECRET_OUTPUT')
        sys.exit(1)
