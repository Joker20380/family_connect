"""Existing secure signer/installer; exact100 baseline, private101 only."""
import runpy
import sys
from prepare import ROOT, BASE, WORK


def main():
    action=sys.argv[1]
    assert action in ('sign','install')
    if action=='sign':
        source=runpy.run_path(str(ROOT/'tests/fixtures/support_automation/sign.py'))['source_code']()
        source=source.replace('support-automation-20261021','p1-lifecycle-101-20261021')
        source=source.replace('state-client-build/speed-candidate-20261021/delivery/FamilyConnect-0.1.18-beta97-speed.apk','state-client-build/p1-owner-acceptance-20261021/delivery/FamilyConnect-0.1.18-beta100-lifecycle.apk')
        source=source.replace('d7c02ef5e947733702490c2bf5b6afc0d17dbcb5f19b44eca478d621dfcf928f','1eb04cc6082f6a03380b99e8a47053d51efd8e6098c0c135075ac030228061e0')
        source=source.replace('metadata(baseline, 97, True), metadata(unsigned, 98, False)','metadata(baseline, 100, True), metadata(unsigned, 101, False)')
        source=source.replace('metadata(signed, 98, True)','metadata(signed, 101, True)')
    else:
        assert sys.argv[2:]==['--allow-owner-vpn-interruption']
        source=(ROOT/'tests/fixtures/support_automation/install.py').read_text()
        source=source.replace('support-automation-20261021','p1-lifecycle-101-20261021')
        source=source.replace("before['code']==97","before['code']==100").replace("after['code']==98","after['code']==101")
        source=source.replace('1fa75ee968ae75ad6446000e1907c35ae39a3993625220c51c76bf607f71ee82','da6be2bbee9d65dff074aef09c4dd795b7d6c3f4270545853968486ee134c35e')
        source=source.replace('INSTALLED98_SETTINGS_OPEN','INSTALLED101_SETTINGS_OPEN').replace("online_default='OFF'","online_consent='PRESERVED'")
        source=source.replace('ROOT=Path(__file__).resolve().parents[3]','ROOT=Path('+repr(str(ROOT))+')')
        sys.argv=[__file__,'--allow-owner-vpn-interruption']
    source=source.replace('FamilyConnect-0.1.18-beta98-support.apk','FamilyConnect-0.1.18-beta101-lifecycle.apk')
    exec(compile(source,__file__,'exec'),dict(__name__='__main__',__file__=__file__))


if __name__=='__main__':main()
