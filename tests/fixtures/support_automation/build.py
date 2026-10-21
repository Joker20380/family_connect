"""Build one compatible owner APK from installed97, with the original pinned tools."""
import os
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tests/fixtures/speed_candidate'))
from prepare import write,replace,digest

WORK=ROOT/'state-client-build/support-automation-20261021'
BASE=ROOT/'state-client-build/speed-candidate-20261021'


def main():
    source=(BASE/'executed-android-build.py').read_text()
    source=source.replace(str(BASE),str(WORK)).replace("version_code=97, version='0.1.18-beta97-speed'","version_code=98, version='0.1.18-beta98-support'")
    source=source.replace("'SpeedReceiptTest',", "'SpeedReceiptTest', 'SupportSnapshotTest',")
    source=source.replace('speed-candidate-20261021/build/receipt.json','support-automation-20261021/build/receipt.json')
    source=source.replace("parent = Path("+repr(str(ROOT/'state-client-build/mobile-bootstrap-20261020/android-source'))+")", "parent = Path("+repr(str(BASE/'android-source'))+")")
    source=source.replace('FamilyConnect-0.1.18-beta96-bootstrap.apk','FamilyConnect-0.1.18-beta97-speed.apk')
    os.environ['GIT_DIR']=str(ROOT/'state-client-build/mux-profile-20261020/android-source/.git')
    os.environ['GIT_WORK_TREE']=str(WORK/'android-source')
    runner=WORK/'executed-android-build.py';write(runner,source)
    exec(compile(source,str(runner),'exec'),dict(__name__='__main__',__file__=str(runner)))


if __name__=='__main__':main()
