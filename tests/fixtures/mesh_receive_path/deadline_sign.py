"""Same offline signer, ordinary diagnostics, exact92 reference; no install."""

import sys

from deadline import WORK
from late_arrival import ROOT, digest


def main():
    original = ROOT / 'tests/fixtures/mesh_throughput_trace/sign.py'
    assert digest(original) == 'e9d703553ab073ce25a0e76312827a5b650c6cb5ce2a2ab854f1f5d672ab56e3'
    source = original.read_text()
    replacements = {
        "ROOT = Path(__file__).resolve().parents[3]": 'ROOT = Path('+repr(str(ROOT))+')',
        "WORK = ROOT / 'state-client-build/mesh-throughput-trace-20261019'": 'WORK = Path('+repr(str(WORK))+')',
        "state-client-build/beta87-product-fix-20261019/delivery/FamilyConnect-0.1.18-beta88-recovery.apk": 'state-client-build/mesh-receive-path-20261020/normal92/delivery/FamilyConnect-0.1.18-beta92-stability.apk',
        '968a61724f4e71ac0335e330960eb9b54e5ede59bae81df0b6e8499e4ce6c2ce': '1e73167c8bfdba68f96249088cf08ea3dfb9d3614d5bedb8a0a7bdd8716e4e7b',
        'metadata(baseline, 88, True), metadata(unsigned, 89, False)': 'metadata(baseline, 92, True), metadata(unsigned, 93, False)',
        "manifest['build_tags'] == ['fc_perf_diagnostic']": "manifest['build_tags'] == []",
        'FamilyConnect-0.1.18-beta89-mesh-trace.apk': 'FamilyConnect-0.1.18-beta93-rtp-deadline.apk',
        'metadata(signed, 89, True)': 'metadata(signed, 93, True)',
        'VERIFIED_UNSIGNED_OBSERVATION_ONLY': 'VERIFIED_UNSIGNED_B125_NOT_ACCEPTED',
        'SIGNED_PRIVATE_OBSERVATION_NOT_SPEED_FIX': 'SIGNED_PRIVATE_B125_NOT_ACCEPTED',
    }
    for old, new in replacements.items():
        assert old in source, old
        source = source.replace(old, new)
    if '--baseline' in sys.argv:
        source = source.replace('WORK = Path('+repr(str(WORK))+')', 'WORK = Path('+repr(str(WORK/'normal94'))+')')
        source = source.replace("'build/", "'android-build/")
        source = source.replace('metadata(unsigned, 93, False)', 'metadata(unsigned, 94, False)')
        source = source.replace('metadata(signed, 93, True)', 'metadata(signed, 94, True)')
        source = source.replace('FamilyConnect-0.1.18-beta93-rtp-deadline.apk', 'FamilyConnect-0.1.18-beta94-stability.apk')
        source = source.replace("== ['lib/arm64-v8a/libfc_restricted.so']", '== []')
        source = source.replace('B125_NOT_ACCEPTED', 'BASELINE_RETURN_NOT_INSTALLED')
    exec(compile(source, str(original), 'exec'), dict(__name__='__main__', __file__=str(original)))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        print('SIGNING_STOPPED_NO_SECRET_OUTPUT')
        sys.exit(1)
