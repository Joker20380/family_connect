"""Existing protected vault process; --check-only never prompts or installs."""

from prepare import ROOT, WORK, APK_SHA, digest


def main():
    original = ROOT / 'tests/fixtures/mesh_throughput_trace/sign.py'
    assert digest(original) == 'e9d703553ab073ce25a0e76312827a5b650c6cb5ce2a2ab854f1f5d672ab56e3'
    source = original.read_text()
    replacements = {
        'ROOT = Path(__file__).resolve().parents[3]': 'ROOT = Path(' + repr(str(ROOT)) + ')',
        "WORK = ROOT / 'state-client-build/mesh-throughput-trace-20261019'": 'WORK = Path(' + repr(str(WORK)) + ')',
        'state-client-build/beta87-product-fix-20261019/delivery/FamilyConnect-0.1.18-beta88-recovery.apk': 'state-client-build/mobile-bootstrap-20261020/delivery/FamilyConnect-0.1.18-beta96-bootstrap.apk',
        '968a61724f4e71ac0335e330960eb9b54e5ede59bae81df0b6e8499e4ce6c2ce': APK_SHA,
        'metadata(baseline, 88, True), metadata(unsigned, 89, False)': 'metadata(baseline, 96, True), metadata(unsigned, 97, False)',
        "manifest['build_tags'] == ['fc_perf_diagnostic']": "manifest['build_tags'] == []",
        'FamilyConnect-0.1.18-beta89-mesh-trace.apk': 'FamilyConnect-0.1.18-beta97-speed.apk',
        'metadata(signed, 89, True)': 'metadata(signed, 97, True)',
        'VERIFIED_UNSIGNED_OBSERVATION_ONLY': 'VERIFIED_UNSIGNED_OWNER_SPEED_NOT_MEASURED',
        'SIGNED_PRIVATE_OBSERVATION_NOT_SPEED_FIX': 'SIGNED_PRIVATE_CANDIDATE_NOT_SPEED_ACCEPTANCE',
    }
    for old, new in replacements.items():
        assert old in source, old
        source = source.replace(old, new)
    exec(compile(source, str(original), 'exec'), dict(__name__='__main__', __file__=str(original)))


if __name__ == '__main__':
    main()
