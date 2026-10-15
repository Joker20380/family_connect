import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import zipfile

parser=argparse.ArgumentParser()
for name in ('source','retained','tools','native','out','awg','radio','python'):
    parser.add_argument('--'+name,type=Path,required=True)
args=parser.parse_args()
base='f5240994869826c6a28f59e58e38256c688cf6eb'
args.out.mkdir(parents=True,exist_ok=False)
source=args.out/'source'
subprocess.run(['git','clone','--no-checkout','--shared',str(args.retained),str(source)],check=True)
subprocess.run(['git','-C',str(source),'checkout','--detach',base],check=True)
shutil.copytree(args.source,source,dirs_exist_ok=True)
def git(*command):return subprocess.check_output(['git','-C',str(source),*command],text=True).strip()
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
names=set(git('diff','--name-only').splitlines()+git('ls-files','--others','--exclude-standard').splitlines())
inventory={name:digest(source/name) for name in sorted(names)}
delta=hashlib.sha256(json.dumps(inventory,sort_keys=True,separators=(',',':')).encode()).hexdigest()
(args.out/'cumulative-source.json').write_text(json.dumps({'base':base,'source_delta_sha256':delta,'files':inventory},indent=2)+'\n')
native=args.out/'native'
(native/'jniLibs/arm64-v8a').mkdir(parents=True);(native/'assets').mkdir()
shutil.copy2(args.native/'normal/libfc_restricted.so',native/'jniLibs/arm64-v8a/libfc_restricted.so')
manifest=json.loads((args.retained.parent/'restricted-native/assets/restricted-build.json').read_text())
manifest.update(binary_sha256=digest(native/'jniLibs/arm64-v8a/libfc_restricted.so'),source_revision=base,source_tree=git('rev-parse',base+'^{tree}'),source_delta_sha256=delta,local_diagnostic_derivative=True,actual_build_receipt='native-build/receipt.json',accepted_candidate=False)
(native/'assets/restricted-build.json').write_text(json.dumps(manifest,indent=2)+'\n')
assets=args.out/'research-assets';assets.mkdir()
asset=json.loads((args.retained.parent/'research-assets/provisioning-seam-build.json').read_text())
asset.update(source_delta_sha256=delta,public_release=False,local_diagnostic_derivative=True)
(assets/'provisioning-seam-build.json').write_text(json.dumps(asset,indent=2)+'\n')
init=args.out/'android.init.gradle'
init.write_text("allprojects { project -> project.plugins.withId('com.android.application') {\n"+
    f"project.android.ndkPath = '{args.tools}/android/ndk/28.2.13676358'\n"+
    "project.android.ndkVersion = '28.2.13676358'\n"+
    f"project.layout.buildDirectory.set(new File('{args.out}/android/' + project.name))\n"+
    ''.join(f"project.android.sourceSets.main.{kind}.srcDir('{args.awg}/{directory}')\n" for kind,directory in [('java','java'),('jniLibs','jniLibs'),('assets','assets')])+"} }\n")
env=dict(os.environ,JAVA_HOME=str(args.tools/'jdk'),ANDROID_HOME=str(args.tools/'android'),ANDROID_SDK_ROOT=str(args.tools/'android'),GRADLE_USER_HOME=str(args.tools/'gradle-home'))
env['PATH']=str(args.tools/'jdk/bin')+os.pathsep+env['PATH']
command=[str(args.tools/'gradle-8.11.1/bin/gradle'),'--no-daemon','--max-workers=1','--offline','-I',str(init),'--project-cache-dir',str(args.out/'cache'),'-PfcTargetAbi=arm64-v8a','-PfcFriendsCi=false','-PfcProvisioningSeamSource='+delta,'-PfcProvisioningSeamAssets='+str(assets),'-PfcBuildPython='+str(args.python),'-PfcRadioNative='+str(args.radio),'-PfcFriendsRestrictedDirectory='+str(native),':app:assembleResearchProvisioning',':app:testResearchProvisioningUnitTest','--tests','com.familyconnect.app.StartupFidelityTest','--tests','com.familyconnect.app.RestrictedStartupTest','--tests','com.familyconnect.app.DiagnosticRingTest']
receipt={'command':command,'source_delta_sha256':delta,'variant':'researchProvisioning','native_sha256':manifest['binary_sha256'],'device_tests':'NOT_RUN'}
with (args.out/'gradle.log').open('wb') as output:
    try: receipt['exit']=subprocess.run(command,cwd=source/'clients/android',env=env,stdout=output,stderr=subprocess.STDOUT,timeout=900).returncode
    except subprocess.TimeoutExpired:receipt['exit']='TIMEOUT'
receipt['log_sha256']=digest(args.out/'gradle.log')
for apk in (args.out/'android/app/outputs/apk').glob('**/*.apk'):
    with zipfile.ZipFile(apk) as bundle:
        embedded=hashlib.sha256(bundle.read('lib/arm64-v8a/libfc_restricted.so')).hexdigest()
        assert embedded==manifest['binary_sha256'],'embedded native changed'
        receipt['apk']={'name':apk.name,'sha256':digest(apk),'embedded_native_sha256':embedded,'size':apk.stat().st_size}
(args.out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt),flush=True)
