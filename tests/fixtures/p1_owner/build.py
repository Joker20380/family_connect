"""Build observation100 with existing pinned offline tools, not repository main."""
import os
from pathlib import Path
import runpy
import sys

ROOT=Path(__file__).resolve().parents[3]
WORK=ROOT/'state-client-build/p1-owner-acceptance-20261021'
BASE=ROOT/'state-client-build/support-cadence99-20261021'
sys.path.insert(0,str(ROOT/'tests/fixtures/speed_candidate'))
from prepare import write


def main():
    source=(ROOT/'state-client-build/support-automation-20261021/executed-android-build.py').read_text()
    source=source.replace('support-automation-20261021','p1-owner-acceptance-20261021')
    source=source.replace('version_code=98','version_code=100').replace('0.1.18-beta98-support','0.1.18-beta100-lifecycle')
    source=source.replace("parent = Path('/mnt/data/PycharmProjects/family_connect/state-client-build/speed-candidate-20261021/android-source')",'parent = Path('+repr(str(BASE/'android-source'))+')')
    assert 'parent = Path('+repr(str(BASE/'android-source'))+')' in source
    source=source.replace('FamilyConnect-0.1.18-beta97-speed.apk','FamilyConnect-0.1.18-beta99-support.apk')
    source=source.replace("'SupportSnapshotTest',","'SupportSnapshotTest', 'SupportUploadScheduleTest', 'MuxLifecycleTest',")
    target=WORK/'android-source/clients/android/app/src/test/java/com/familyconnect/app/MuxLifecycleTest.java'
    write(target,Path(__file__).with_name('MuxLifecycleTest.java').read_text())
    os.environ['GIT_DIR']=str(ROOT/'state-client-build/mux-profile-20261020/android-source/.git')
    os.environ['GIT_WORK_TREE']=str(WORK/'android-source')
    runner=WORK/'executed-android-build.py';write(runner,source)
    exec(compile(source,str(runner),'exec'),dict(__name__='__main__',__file__=str(runner)))


if __name__=='__main__':main()
