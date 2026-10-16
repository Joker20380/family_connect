import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

root=Path(__file__).resolve().parent
state=root.parents[1]
tools=state/'field65-export16/diag-source-freeze-1/resume-tools'
build_tools=tools/'android/build-tools/35.0.0'
android=tools/'android/platforms/android-35/android.jar'
env=dict(os.environ,JAVA_HOME=str(tools/'jdk'))
env['PATH']=str(tools/'jdk/bin')+':'+env['PATH']
label=sys.argv[1]
if label=='beta60': base=state/'field60-owner/installed-beta60.apk'
elif label=='current': base=state/'bootstrap-pre-hello-correlation-1/gradle-native-export-final/android/app/outputs/apk/researchProvisioning/app-researchProvisioning-unsigned.apk'
else: base=Path(sys.argv[2]).resolve()
destination=root/label;destination.mkdir(exist_ok=True)
classes=destination/'classes';classes.mkdir(exist_ok=True)
subprocess.run([str(tools/'jdk/bin/javac'),'-source','17','-target','17','-classpath',str(android),'-d',str(classes),
    *[str(path) for path in (root/'java').rglob('*.java')]],env=env,check=True)
dex=destination/'dex';dex.mkdir(exist_ok=True)
subprocess.run([str(build_tools/'d8'),'--lib',str(android),'--min-api','26','--output',str(dex),*[str(path) for path in classes.rglob('*.class')]],env=env,check=True)
manifest=destination/'manifest.apk'
subprocess.run([str(build_tools/'aapt2'),'link','-I',str(android),'--manifest',str(root/'AndroidManifest.xml'),'-o',str(manifest)],env=env,check=True)
unsigned=destination/'renderer-unsigned.apk'
with zipfile.ZipFile(base) as original,zipfile.ZipFile(manifest) as linked,zipfile.ZipFile(unsigned,'w',compression=zipfile.ZIP_DEFLATED) as output:
    names=original.namelist()
    for name in names:
        if name.startswith(('META-INF/','lib/')) or name=='AndroidManifest.xml': continue
        output.writestr(original.getinfo(name),original.read(name))
    output.writestr('AndroidManifest.xml',linked.read('AndroidManifest.xml'))
    count=sum(name.startswith('classes') and name.endswith('.dex') and '/' not in name for name in names)
    output.writestr('classes'+str(count+1)+'.dex',(dex/'classes.dex').read_bytes())
aligned=destination/'renderer-aligned.apk'
subprocess.run([str(build_tools/'zipalign'),'-f','4',str(unsigned),str(aligned)],env=env,check=True)
signed=destination/'renderer-debug.apk'
subprocess.run([str(build_tools/'apksigner'),'sign','--ks',str(Path.home()/'.android/debug.keystore'),'--ks-pass','pass:android',
    '--out',str(signed),str(aligned)],env=env,check=True)
receipt=dict(label=label,original_apk_sha256=hashlib.sha256(base.read_bytes()).hexdigest(),
    renderer_apk_sha256=hashlib.sha256(signed.read_bytes()).hexdigest(),only_disposable_renderer=True,
    production_key_used=False,internet_permission=False,native_libraries=False,original_ui_dex_and_resources=True,
    original_oncreate_onresume_not_invoked=True,secure_flag=True)
(destination/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
