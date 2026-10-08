"""Offline host JNI check; replaces only the external bootstrap endpoint/session plane."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[2]
REVISION = 'd2758a023cd7f4174a5a5fa4ff66e487d4342ba0'

def main():
    parser = argparse.ArgumentParser()
    for name in ('go', 'jdk', 'xray', 'work', 'json-jar', 'gson-jar'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    work = args.work
    source = ROOT / 'pilot/android-restricted'
    if work.exists():
        assert (work / 'overlay.json').is_file()
        assert (work / 'native/bridge.c').read_bytes() == (source / 'native/bridge.c').read_bytes()
    work.mkdir(parents=True, exist_ok=True)
    fixtures = source / 'startup-tests'
    native = work / 'native'
    native.mkdir(exist_ok=True)
    provenance = {}
    for path in (source / 'native').iterdir():
        raw = path.read_bytes()
        provenance[str(path.relative_to(ROOT))] = hashlib.sha256(raw).hexdigest()
        if raw.startswith(b'//go:build android\n'):
            raw = raw.split(b'\n', 1)[1]
        (native / path.name).write_bytes(raw)
    shutil.copytree(source / 'packet', work / 'packet', dirs_exist_ok=True)
    for name in ('go.mod', 'go.sum'):
        shutil.copy2(source / name, work / name)
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=args.xray, text=True).strip() == REVISION
    archive = work / 'xray.tar'
    subprocess.run(['git', 'archive', '--format=tar', '-o', str(archive), REVISION], cwd=args.xray, check=True)
    xray = work / 'xray'
    xray.mkdir(exist_ok=True)
    with tarfile.open(archive) as bundle:
        bundle.extractall(xray, filter='data')
    endpoint = xray / 'proxy/tun/family_endpoint.go'
    if endpoint.exists():
        addition = (source / 'xray-packet-boundary.patch').read_text().split('+++ b/proxy/tun/family_endpoint.go\n', 1)[1]
        expected = ''.join(line[1:] for line in addition.splitlines(keepends=True) if line.startswith('+'))
        assert not endpoint.is_symlink() and endpoint.read_text() == expected
        endpoint.unlink()
    subprocess.run(['git', 'apply', str(source / 'xray-packet-boundary.patch')], cwd=xray, check=True)
    subprocess.run([args.go, 'mod', 'edit', '-replace=github.com/xtls/xray-core='+str(xray), '-replace=github.com/Joker20380/family_connect/carrier='+str(ROOT / 'carrier')], cwd=work, check=True)
    (native / 'fixture.go').write_text('''package main
import "C"
import "github.com/Joker20380/family_connect/carrier/bootstrap"
//export fcStartupFixtureLate
func fcStartupFixtureLate(index int32) { bootstrap.LocalStaleFixture(int(index)) }
''')
    (native / 'fixture.c').write_text('''#include <jni.h>
#include <stdint.h>
extern void fcStartupFixtureLate(int32_t);
JNIEXPORT void JNICALL Java_com_familyconnect_app_NativeProbe_late(JNIEnv *env,jclass cls,jint index){fcStartupFixtureLate(index);}
''')
    replacements = {}
    for package in ('bootstrap', 'wholedevice'):
        generated = work / (package+'.go')
        generated.write_bytes((fixtures / (package+'.fixture')).read_bytes())
        replacements[str(ROOT / ('carrier/'+package+'/startup_local_fixture.go'))] = str(generated)
    original = ROOT / 'carrier/wholedevice/session.go'
    content = original.read_text()
    start = content.index('func OpenCached(')
    end = content.index('\nfunc OpenProvisioned(', start)
    old = content[start:end]
    replacement = old[:old.index('{')+1]+'\nreturn localStartupFixture(ctx, path)\n}\n'
    projected = work / 'wholedevice-session.go'
    projected.write_text(content[:start]+replacement+content[end:])
    replacements[str(original)] = str(projected)
    overlay = work / 'overlay.json'
    overlay.write_text(json.dumps({'Replace': replacements}, indent=2))
    for name, text in {
        'android/content/Context.java': '''package android.content; public class Context { private final java.io.File root; public Context(java.io.File path){root=path;root.mkdirs();} public java.io.File getNoBackupFilesDir(){return root;} }''',
        'android/net/VpnService.java': '''package android.net; public class VpnService { public boolean protect(int fd){throw new AssertionError("No network expected");} }''',
        'android/util/AtomicFile.java': '''package android.util; public class AtomicFile { private final java.io.File path; public AtomicFile(java.io.File value){path=value;} public java.io.File getBaseFile(){return path;} public java.io.FileOutputStream startWrite() throws java.io.IOException{return new java.io.FileOutputStream(path+".new");} public void finishWrite(java.io.FileOutputStream output)throws java.io.IOException{output.close();java.nio.file.Files.move(java.nio.file.Path.of(path+".new"),path.toPath(),java.nio.file.StandardCopyOption.REPLACE_EXISTING,java.nio.file.StandardCopyOption.ATOMIC_MOVE);} public void failWrite(java.io.FileOutputStream output)throws java.io.IOException{output.close();java.nio.file.Files.deleteIfExists(java.nio.file.Path.of(path+".new"));} public byte[] readFully()throws java.io.IOException{if(!path.exists())throw new java.io.FileNotFoundException();return java.nio.file.Files.readAllBytes(path.toPath());} }''',
    }.items():
        target = work / 'java' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
    android = ROOT / 'clients/android/app/src'
    main_java = android / 'main/java/com/familyconnect/app'
    owner_java = android / 'ownerDiagnostic/java/com/familyconnect/app'
    classes = work / 'classes'
    classes.mkdir(exist_ok=True)
    inputs = list((work / 'java').rglob('*.java')) + [main_java / 'NativeRestricted.java', main_java / 'Transport.java', main_java / 'ConnectivityOrchestrator.java', owner_java / 'StartupResult.java', owner_java / 'StartupDiagnostics.java', fixtures / 'NativeProbe.java']
    libraries = str(args.json_jar)+os.pathsep+str(args.gson_jar)
    subprocess.run([args.jdk / 'bin/javac', '-cp', libraries, '-d', classes, *inputs], check=True)
    environment = os.environ | {'GOOS':'linux', 'GOARCH':'amd64', 'CGO_ENABLED':'1', 'CC':'gcc', 'CGO_CFLAGS':f'-I{args.jdk}/include -I{args.jdk}/include/linux -Wno-error=incompatible-pointer-types', 'GOPROXY':'off', 'GOSUMDB':'off'}
    environment.pop('GOFLAGS', None)
    library = work / 'libfc_restricted.so'
    subprocess.run([args.go, 'build', '-overlay='+str(overlay), '-tags=fc_owner_diagnostic', '-trimpath', '-ldflags=-checklinkname=0', '-buildmode=c-shared', '-o', library, './native'], cwd=work, env=environment, check=True)
    subprocess.run([args.jdk / 'bin/java', '-Djava.library.path='+str(work), '-cp', str(classes)+os.pathsep+libraries, 'com.familyconnect.app.NativeProbe', 'owner', str(work / 'private-files')], check=True, timeout=60)
    public = work / 'public'
    public.mkdir(exist_ok=True)
    public_classes = public / 'classes'
    public_classes.mkdir(exist_ok=True)
    public_inputs = list((work / 'java').rglob('*.java')) + [main_java / 'NativeRestricted.java', main_java / 'Transport.java', main_java / 'ConnectivityOrchestrator.java', android / 'publicStartup/java/com/familyconnect/app/StartupDiagnostics.java', fixtures / 'PublicNativeProbe.java']
    subprocess.run([args.jdk / 'bin/javac', '-cp', args.json_jar, '-d', public_classes, *public_inputs], check=True)
    public_library = public / 'libfc_restricted.so'
    subprocess.run([args.go, 'build', '-overlay='+str(overlay), '-trimpath', '-ldflags=-checklinkname=0', '-buildmode=c-shared', '-o', public_library, './native'], cwd=work, env=environment, check=True)
    subprocess.run([args.jdk / 'bin/java', '-Djava.library.path='+str(public), '-cp', str(public_classes)+os.pathsep+str(args.json_jar), 'com.familyconnect.app.PublicNativeProbe', str(public / 'files')], check=True, timeout=30)
    (work / 'PROVENANCE.json').write_text(json.dumps(dict(source_inputs=provenance, binary_sha256=hashlib.sha256(library.read_bytes()).hexdigest(), public_binary_sha256=hashlib.sha256(public_library.read_bytes()).hexdigest(), xray_revision=REVISION, external_boundary='OpenCached fixture -> real bootstrap.requestTransport', real_boundaries=['native main.go', 'JNI bridge.c byte-identical', 'NativeRestricted.java byte-identical', 'owner StartupDiagnostics/StartupResult', 'public StartupDiagnostics'], not_executed=['Android ART', 'Android VpnService', 'Android AtomicFile implementation', 'Telemost/network', 'TUN']), indent=2)+'\n')

if __name__ == '__main__':
    main()
