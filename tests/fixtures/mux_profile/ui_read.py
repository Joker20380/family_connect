"""Read normal UI despite continuous animation; no APK or transport API installed."""

import os
import subprocess
import xml.etree.ElementTree as ElementTree
from prepare import WORK, TOOLS, FIXTURE

target=WORK/'ui-reader';target.mkdir(exist_ok=True)
platform=TOOLS/'android/platforms/android-35'
classpath=os.pathsep.join(str(platform/name) for name in ('android.jar','uiautomator.jar','optional/android.test.base.jar'))
if True:
    subprocess.run([TOOLS/'jdk/bin/javac','-classpath',classpath,'-d',target,FIXTURE/'OwnerUi.java'],check=True)
    subprocess.run([TOOLS/'jdk/bin/java','-cp',TOOLS/'android/build-tools/35.0.0/lib/d8.jar','com.android.tools.r8.D8','--min-api','26','--lib',platform/'android.jar','--output',target,target/'OwnerUi.class'],check=True)
    subprocess.run([TOOLS/'jdk/bin/jar','cf',target/'owner-ui.jar','-C',target,'classes.dex'],check=True)
    subprocess.run(['adb','push',str(target/'owner-ui.jar'),'/data/local/tmp/fc-mux-profile-ui.jar'],check=True,stdout=subprocess.DEVNULL)
result=subprocess.run(['adb','shell','uiautomator','runtest','/system/framework/android.test.base.jar','/data/local/tmp/fc-mux-profile-ui.jar','-c','OwnerUi'],capture_output=True,text=True,timeout=30)
(target/'buttons-run.log').write_text(result.stdout+result.stderr)
result.check_returncode()
for line in result.stdout.splitlines():
    if line.startswith('OWNER_BUTTON '):print(line)
