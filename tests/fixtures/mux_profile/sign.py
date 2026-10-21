"""Use the existing offline vault signer for the owner-only95 artifact."""

import sys
from prepare import ROOT, WORK, APK, digest


def main():
    original=ROOT/'tests/fixtures/mesh_throughput_trace/sign.py'
    assert digest(original)=='e9d703553ab073ce25a0e76312827a5b650c6cb5ce2a2ab854f1f5d672ab56e3'
    source=original.read_text()
    replacements={
        'ROOT = Path(__file__).resolve().parents[3]':'ROOT = Path('+repr(str(ROOT))+')',
        "WORK = ROOT / 'state-client-build/mesh-throughput-trace-20261019'":'WORK = Path('+repr(str(WORK))+')',
        'state-client-build/beta87-product-fix-20261019/delivery/FamilyConnect-0.1.18-beta88-recovery.apk':'state-client-build/rtp-deadline-20261020/normal94/delivery/FamilyConnect-0.1.18-beta94-stability.apk',
        '968a61724f4e71ac0335e330960eb9b54e5ede59bae81df0b6e8499e4ce6c2ce':APK,
        'metadata(baseline, 88, True), metadata(unsigned, 89, False)':'metadata(baseline, 94, True), metadata(unsigned, 95, False)',
        "manifest['build_tags'] == ['fc_perf_diagnostic']":"manifest['build_tags'] == []",
        'FamilyConnect-0.1.18-beta89-mesh-trace.apk':'FamilyConnect-0.1.18-beta95-mux-profile.apk',
        'metadata(signed, 89, True)':'metadata(signed, 95, True)',
        'VERIFIED_UNSIGNED_OBSERVATION_ONLY':'VERIFIED_UNSIGNED_MUX_PROFILE_OWNER_ONLY',
        'SIGNED_PRIVATE_OBSERVATION_NOT_SPEED_FIX':'SIGNED_PRIVATE_MUX_PROFILE_NOT_SPEED_ACCEPTED',
    }
    for old,new in replacements.items():
        assert old in source,old
        source=source.replace(old,new)
    source=source.replace('def main():', "stage = 'input verification'\n\ndef main():\n    global stage")
    for anchor,stage in [
        ("    vault = Path(namespace['choose']", 'vault selection'),
        ('    subprocess.run = namespace[', 'protected vault unlock'),
        ('    names, total, count =', 'bounded archive metadata'),
        ("    member = namespace['choose']", 'keystore selection'),
        ('    store, password = sign_android_vault.credentials', 'certificate pin verification'),
        ('    checksum = sign_android_vault.sign', 'APK signing'),
        ('    actual = metadata(signed,', 'signed artifact verification'),
    ]:
        assert anchor in source
        source=source.replace(anchor, '    stage = '+repr(stage)+'\n'+anchor)
    source=source.replace("print('SIGNING_STOPPED_NO_SECRET_OUTPUT')", "print('SIGNING_STOPPED_AT_' + stage + '; private diagnostics suppressed')")
    exec(compile(source,str(original),'exec'),dict(__name__='__main__',__file__=str(original)))


if __name__=='__main__':
    try:main()
    except Exception:
        print('SIGNING_STOPPED_NO_SECRET_OUTPUT')
        sys.exit(1)
