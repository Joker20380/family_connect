"""Reuse existing protected signer and guarded owner in-place installer."""
import argparse
from pathlib import Path
import runpy
import sys

ROOT=Path(__file__).resolve().parents[3]
BASE_APK='state-client-build/support-cadence99-20261021/delivery/FamilyConnect-0.1.18-beta99-support.apk'
BASE_SHA='fae38b81f39b4f813d172f07380b3fd6265b0c3bee3a99ff1d7539d4f1213b0e'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['sign','install'])
    parser.add_argument('--check-only',action='store_true')
    parser.add_argument('--allow-owner-vpn-interruption',action='store_true')
    args=parser.parse_args()
    assert not args.check_only or args.action=='sign'
    assert args.allow_owner_vpn_interruption==(args.action=='install')
    if args.action=='sign':
        source=runpy.run_path(str(ROOT/'tests/fixtures/support_automation/sign.py'))['source_code']()
        source=source.replace('support-automation-20261021','p1-owner-acceptance-20261021')
        source=source.replace('state-client-build/speed-candidate-20261021/delivery/FamilyConnect-0.1.18-beta97-speed.apk',BASE_APK)
        source=source.replace('d7c02ef5e947733702490c2bf5b6afc0d17dbcb5f19b44eca478d621dfcf928f',BASE_SHA)
        source=source.replace('metadata(baseline, 97, True), metadata(unsigned, 98, False)','metadata(baseline, 99, True), metadata(unsigned, 100, False)')
        source=source.replace('metadata(signed, 98, True)','metadata(signed, 100, True)')
        source=source.replace('FamilyConnect-0.1.18-beta98-support.apk','FamilyConnect-0.1.18-beta100-lifecycle.apk')
    else:
        source=(ROOT/'tests/fixtures/support_automation/install.py').read_text()
        source=source.replace('support-automation-20261021','p1-owner-acceptance-20261021')
        source=source.replace("before['code']==97","before['code']==99")
        source=source.replace('1fa75ee968ae75ad6446000e1907c35ae39a3993625220c51c76bf607f71ee82','3f700aef7952c67de69de1de7cd6878287ed51d6b97be28c464d304a4cfb6673')
        source=source.replace('FamilyConnect-0.1.18-beta98-support.apk','FamilyConnect-0.1.18-beta100-lifecycle.apk')
        source=source.replace("after['code']==98","after['code']==100").replace('INSTALLED98_SETTINGS_OPEN','INSTALLED100_SETTINGS_OPEN')
        source=source.replace("online_default='OFF'","online_consent='PRESERVED_IF_PREVIOUSLY_ENABLED'")
        sys.argv=[__file__,'--allow-owner-vpn-interruption']
    exec(compile(source,__file__,'exec'),dict(__name__='__main__',__file__=__file__))


if __name__=='__main__':main()
