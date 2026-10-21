"""Existing protected vault signing; no password in CLI or logs."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]


def source_code():
    source=(ROOT/'tests/fixtures/mesh_throughput_trace/sign.py').read_text()
    replacements={
        'ROOT = Path(__file__).resolve().parents[3]':'ROOT = Path('+repr(str(ROOT))+')',
        'mesh-throughput-trace-20261019':'support-automation-20261021',
        'state-client-build/beta87-product-fix-20261019/delivery/FamilyConnect-0.1.18-beta88-recovery.apk':'state-client-build/speed-candidate-20261021/delivery/FamilyConnect-0.1.18-beta97-speed.apk',
        '968a61724f4e71ac0335e330960eb9b54e5ede59bae81df0b6e8499e4ce6c2ce':'d7c02ef5e947733702490c2bf5b6afc0d17dbcb5f19b44eca478d621dfcf928f',
        'metadata(baseline, 88, True), metadata(unsigned, 89, False)':'metadata(baseline, 97, True), metadata(unsigned, 98, False)',
        "manifest['build_tags'] == ['fc_perf_diagnostic']":"manifest['build_tags'] == []",
        'FamilyConnect-0.1.18-beta89-mesh-trace.apk':'FamilyConnect-0.1.18-beta98-support.apk',
        'metadata(signed, 89, True)':'metadata(signed, 98, True)',
        'VERIFIED_UNSIGNED_OBSERVATION_ONLY':'VERIFIED_UNSIGNED_SUPPORT_AUTOMATION',
        'SIGNED_PRIVATE_OBSERVATION_NOT_SPEED_FIX':'SIGNED_PRIVATE_SUPPORT_NOT_SPEED_FIX',
    }
    for old,new in replacements.items():
        assert old in source,old
        source=source.replace(old,new)
    return source


def main():
    exec(compile(source_code(),__file__,'exec'),dict(__name__='__main__',__file__=__file__))


if __name__=='__main__':main()
