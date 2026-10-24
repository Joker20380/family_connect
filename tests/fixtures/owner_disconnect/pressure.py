"""Exact104 ->105 pressure drain; preserves queued frames without enlarging RTP window."""
import json
import os
from pathlib import Path
import shutil
import sys
import types

FIXTURE=Path(__file__).resolve().parent
sys.path.insert(0,str(FIXTURE))
import reorder
from deadline import patch as edit

ROOT=reorder.ROOT
BASE=ROOT/'state-client-build/owner-reorder104-20261022'
WORK=ROOT/'state-client-build/owner-pressure105-20261022'
SOURCE=WORK/'android-source'


def prepare():
    WORK.mkdir(mode=0o700)
    assert reorder.digest(BASE/'delivery/FamilyConnect-0.1.18-beta104-recovery.apk')=='828ffe3534e22a61cecacd261f0875d5333682522d9533cb854cb11309436c1a'
    before=reorder.inventory(BASE/'android-source')
    for name in before:
        target=SOURCE/name;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(BASE/'android-source'/name,target)
    assert reorder.inventory(SOURCE)==before
    edit(SOURCE/'clients/android/app/build.gradle',"            variant.outputs.all { versionCodeOverride = 104; versionNameOverride = '0.1.18-beta104-recovery' }",
        "            variant.outputs.all { versionCodeOverride = 105; versionNameOverride = '0.1.18-beta105-recovery' }")
    test=SOURCE/'carrier/telemost/owner_late_frame_test.go'
    old=test.read_text();new=(FIXTURE/'late_frame_test.go').read_text()
    edit(test,old,new)
    (WORK/'parent-inventory.json').write_text(json.dumps(before,indent=2)+'\n')


def patch():
    source=SOURCE/'carrier/telemost/rtp.go'
    edit(source,'''		for sequence, queued := range b.pkts {
			b.drop(queued, "window")
			b.recycle(queued)
			delete(b.pkts, sequence)
		}
		b.nextSeq = pkt.SequenceNumber''','''		for len(b.pkts) > 0 && uint16(pkt.SequenceNumber-b.nextSeq) >= reorderWindow {
			b.skipToOldest()
			b.drain(deliver)
		}
		if uint16(pkt.SequenceNumber-b.nextSeq) >= reorderWindow {
			b.nextSeq = pkt.SequenceNumber
		}''')
    reorder.subprocess.run([str(reorder.TOOLS/'go/bin/gofmt'),'-w',str(SOURCE/'carrier/telemost/owner_late_frame_test.go')],check=True)


def execute(action):
    source=(FIXTURE/'reorder.py').read_text()
    source=source.replace("BASE=ROOT/'state-client-build/owner-deadline103-20261022'","BASE=ROOT/'state-client-build/owner-reorder104-20261022'")
    source=source.replace('owner-reorder104-20261022','owner-pressure105-20261022')
    source=source.replace("BASE=ROOT/'state-client-build/owner-pressure105-20261022'","BASE=ROOT/'state-client-build/owner-reorder104-20261022'")
    source=source.replace("'TestOwnerCompleteLateFrames'","'TestOwnerWindowPressureDrainsCompleteFrames'")
    source=source.replace('all three packets arrived but complete carrier message was lost','window pressure discarded an already complete queued frame')
    source=source.replace(",'carrier/telemost/head_loss_test.go'",'')
    source=source.replace('FamilyConnect-0.1.18-beta103-recovery.apk','FamilyConnect-0.1.18-beta104-recovery.apk')
    source=source.replace("BASE/'delivery/FamilyConnect-0.1.18-beta104-recovery.apk'","BASE/'delivery/FamilyConnect-0.1.18-beta104-recovery.apk'")
    source=source.replace('version_code=104','version_code=105').replace("'beta104-recovery')","'beta105-recovery')")
    source=source.replace('COMPLETE_LATE_RTP_DROPPED_BY_100MS_REORDER_BOUND_OWNER_ACCEPTANCE_PENDING','QUEUED_FRAMES_DROPPED_ON_WINDOW_PRESSURE_OWNER_ACCEPTANCE_PENDING')
    source=source.replace('state-client-build/owner-deadline103-20261022/delivery/FamilyConnect-0.1.18-beta104-recovery.apk','state-client-build/owner-reorder104-20261022/delivery/FamilyConnect-0.1.18-beta104-recovery.apk')
    source=source.replace('0d274fe5e0250301242d0307ae69c345bb27e935d79248d859afde817693fb04','828ffe3534e22a61cecacd261f0875d5333682522d9533cb854cb11309436c1a')
    source=source.replace('metadata(baseline, 103, True), metadata(unsigned, 104, False)','metadata(baseline, 104, True), metadata(unsigned, 105, False)')
    source=source.replace('metadata(signed, 104, True)','metadata(signed, 105, True)')
    source=source.replace("'FamilyConnect-0.1.18-beta104-recovery.apk':'FamilyConnect-0.1.18-beta104-recovery.apk'","'FamilyConnect-0.1.18-beta98-support.apk':'FamilyConnect-0.1.18-beta105-recovery.apk'")
    source=source.replace("'FamilyConnect-0.1.18-beta98-support.apk':'FamilyConnect-0.1.18-beta104-recovery.apk'","'FamilyConnect-0.1.18-beta98-support.apk':'FamilyConnect-0.1.18-beta105-recovery.apk'")
    source=source.replace('"before[\'code\']==103"','"before[\'code\']==104"').replace('"after[\'code\']==104"','"after[\'code\']==105"')
    source=source.replace("'97d0bf793f8c4bb9975f32579f19369df0e7201786609ab9f46decdea3fec263'","'f6628021200408a317770cd189dd10afb7bd53b4da802b67b4b4f55f0c88e28d'")
    source=source.replace(".replace('FamilyConnect-0.1.18-beta98-support.apk','FamilyConnect-0.1.18-beta104-recovery.apk')",".replace('FamilyConnect-0.1.18-beta98-support.apk','FamilyConnect-0.1.18-beta105-recovery.apk')")
    source=source.replace('INSTALLED104_SETTINGS_OPEN','INSTALLED105_SETTINGS_OPEN')
    if action=='build':
        with (WORK/'executed-build-runner.py').open('x') as output:output.write(source)
    exec(compile(source,str(WORK/'executed-build-runner.py'),'exec'),dict(__name__='__main__',__file__=str(FIXTURE/'pressure.py')))


if __name__=='__main__':
    os.umask(0o077)
    if sys.argv[1]=='prepare':prepare()
    elif sys.argv[1]=='patch':patch()
    else:execute(sys.argv[1])
