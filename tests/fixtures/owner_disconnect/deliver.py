"""Existing protected vault signer and in-place installer, exact101 -> diagnostic102."""
import runpy
import sys
from prepare import ROOT,BASE,WORK

def main():
    action=sys.argv[1]
    if action=='sign':
        source=runpy.run_path(str(ROOT/'tests/fixtures/support_automation/sign.py'))['source_code']()
        changes={
            'support-automation-20261021':'owner-disconnections-20261022',
            'state-client-build/speed-candidate-20261021/delivery/FamilyConnect-0.1.18-beta97-speed.apk':'state-client-build/p1-lifecycle-101-20261021/delivery/FamilyConnect-0.1.18-beta101-lifecycle.apk',
            'd7c02ef5e947733702490c2bf5b6afc0d17dbcb5f19b44eca478d621dfcf928f':'3c023e39d95e29fe0561dc462e28f1e643b9e14558cf49700d58df528b2963d9',
            'metadata(baseline, 97, True), metadata(unsigned, 98, False)':'metadata(baseline, 101, True), metadata(unsigned, 102, False)',
            'metadata(signed, 98, True)':'metadata(signed, 102, True)',
            "== ['lib/arm64-v8a/libfc_restricted.so']":'== []',
            'SIGNED_PRIVATE_SUPPORT_NOT_SPEED_FIX':'SIGNED_DIAGNOSTIC_CANDIDATE_NOT_FIELD_READY',
            'FamilyConnect-0.1.18-beta98-support.apk':'FamilyConnect-0.1.18-beta102-recovery.apk',
        }
        for old,new in changes.items():assert old in source,old;source=source.replace(old,new)
    elif action=='install':
        assert sys.argv[2:]==['--allow-owner-vpn-interruption']
        source=(ROOT/'tests/fixtures/support_automation/install.py').read_text()
        source=source.replace('support-automation-20261021','owner-disconnections-20261022').replace("before['code']==97","before['code']==101").replace("after['code']==98","after['code']==102")
        source=source.replace('1fa75ee968ae75ad6446000e1907c35ae39a3993625220c51c76bf607f71ee82','97d0bf793f8c4bb9975f32579f19369df0e7201786609ab9f46decdea3fec263')
        source=source.replace('FamilyConnect-0.1.18-beta98-support.apk','FamilyConnect-0.1.18-beta102-recovery.apk').replace('INSTALLED98_SETTINGS_OPEN','INSTALLED102_SETTINGS_OPEN').replace("online_default='OFF'","online_consent='PRESERVED'")
        source=source.replace('ROOT=Path(__file__).resolve().parents[3]','ROOT=Path('+repr(str(ROOT))+')')
        sys.argv=[__file__,'--allow-owner-vpn-interruption']
    else:raise ValueError('Use sign or install')
    exec(compile(source,__file__,'exec'),dict(__name__='__main__',__file__=__file__))

if __name__=='__main__':main()
