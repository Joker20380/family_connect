"""Existing pinned offline vault workflow. --check-only never asks for credentials."""
import sys
from prepare import ROOT, WORK, BASE, digest


def main():
    original=ROOT/'tests/fixtures/mesh_throughput_trace/sign.py'
    assert digest(original)=='e9d703553ab073ce25a0e76312827a5b650c6cb5ce2a2ab854f1f5d672ab56e3'
    source=original.read_text()
    replacements={
        'ROOT = Path(__file__).resolve().parents[3]':'ROOT = Path('+repr(str(ROOT))+')',
        "WORK = ROOT / 'state-client-build/mesh-throughput-trace-20261019'":'WORK = Path('+repr(str(WORK))+')',
        'state-client-build/beta87-product-fix-20261019/delivery/FamilyConnect-0.1.18-beta88-recovery.apk':'state-client-build/mux-profile-20261020/delivery/FamilyConnect-0.1.18-beta95-mux-profile.apk',
        '968a61724f4e71ac0335e330960eb9b54e5ede59bae81df0b6e8499e4ce6c2ce':'e36a24601d459ea13553d9236486befe514dca496d8b2933290e6867d97c4159',
        'metadata(baseline, 88, True), metadata(unsigned, 89, False)':'metadata(baseline, 95, True), metadata(unsigned, 96, False)',
        "== ['lib/arm64-v8a/libfc_restricted.so']":'== []',
        "manifest['build_tags'] == ['fc_perf_diagnostic']":"manifest['build_tags'] == []",
        'FamilyConnect-0.1.18-beta89-mesh-trace.apk':'FamilyConnect-0.1.18-beta96-bootstrap.apk',
        'metadata(signed, 89, True)':'metadata(signed, 96, True)',
        'VERIFIED_UNSIGNED_OBSERVATION_ONLY':'VERIFIED_UNSIGNED_BOOTSTRAP_FIELD_NOT_RUN',
        'SIGNED_PRIVATE_OBSERVATION_NOT_SPEED_FIX':'SIGNED_PRIVATE_BOOTSTRAP_FIELD_NOT_RUN',
    }
    for old,new in replacements.items():
        assert old in source,old
        source=source.replace(old,new)
    exec(compile(source,str(original),'exec'),dict(__name__='__main__',__file__=str(original)))


if __name__=='__main__':main()
