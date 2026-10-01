"""Build the opt-in adapter using the product's pinned Xray packet engine."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[2]
REVISION = 'd2758a023cd7f4174a5a5fa4ff66e487d4342ba0'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--xray', type=Path, required=True)
    parser.add_argument('--go', required=True)
    parser.add_argument('--ndk', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    revision = subprocess.check_output(['git', '-C', str(args.xray), 'rev-parse', 'HEAD'], text=True).strip()
    if revision != REVISION or args.out.exists():
        raise RuntimeError('Pinned source and fresh output required')
    source = ROOT / 'pilot/android-restricted'
    with tempfile.TemporaryDirectory(prefix='fc-eu6-build-') as directory:
        workspace = Path(directory)
        archive = workspace / 'xray.tar'
        subprocess.run(['git', '-C', str(args.xray), 'archive', '--format=tar', '-o', str(archive), REVISION], check=True)
        xray = workspace / 'xray'
        xray.mkdir()
        with tarfile.open(archive) as bundle:
            bundle.extractall(xray, filter='data')
        subprocess.run(['git', 'apply', str(source / 'xray-packet-boundary.patch')], cwd=xray,
                       env=os.environ | {'GIT_CEILING_DIRECTORIES': str(workspace)}, check=True)
        module = workspace / 'native.mod'
        shutil.copy2(source / 'go.mod', module)
        shutil.copy2(source / 'go.sum', module.with_suffix('.sum'))
        subprocess.run([args.go, 'mod', 'edit', '-modfile='+str(module),
                        '-replace=github.com/xtls/xray-core='+str(xray),
                        '-replace=github.com/Joker20380/family_connect/carrier='+str(ROOT / 'carrier')], cwd=source, check=True)
        output = args.out / 'jniLibs/arm64-v8a/libfc_restricted.so'
        output.parent.mkdir(parents=True)
        compiler = args.ndk / 'toolchains/llvm/prebuilt/linux-x86_64/bin/aarch64-linux-android26-clang'
        environment = os.environ | {'GOOS': 'android', 'GOARCH': 'arm64', 'CGO_ENABLED': '1', 'CC': str(compiler),
                                    'CGO_LDFLAGS': '-Wl,-z,max-page-size=16384'}
        environment.pop('YANDEX_TELEMOST_OAUTH_TOKEN', None)
        environment.pop('FC_TELEMOST_ROOM', None)
        subprocess.run([args.go, 'build', '-modfile='+str(module), '-trimpath', '-ldflags=-checklinkname=0', '-buildmode=c-shared', '-o', str(output), './native'], cwd=source, env=environment, check=True)
        assets = args.out / 'assets/restricted-licenses'
        assets.mkdir(parents=True)
        shutil.copy2(xray / 'LICENSE', assets / 'Xray.txt')
        gvisor = Path(subprocess.check_output([args.go, 'list', '-modfile='+str(module), '-m', '-f', '{{.Dir}}', 'gvisor.dev/gvisor'], cwd=source, text=True).strip())
        shutil.copy2(gvisor / 'LICENSE', assets / 'gVisor.txt')
        shutil.copytree(ROOT / 'carrier/licenses', assets / 'carrier', dirs_exist_ok=True)
        shutil.copy2(source / 'xray-packet-boundary.patch', assets / 'Xray-modifications.patch')
        manifest = {'xray_revision': REVISION, 'gvisor_version': 'v0.0.0-20260122175437-89a5d21be8f0',
                    'patch_sha256': hashlib.sha256((source / 'xray-packet-boundary.patch').read_bytes()).hexdigest(),
                    'binary_sha256': hashlib.sha256(output.read_bytes()).hexdigest(), 'diagnostic_only': True}
        (args.out / 'assets/restricted-build.json').write_text(json.dumps(manifest, indent=2)+'\n')
        print(json.dumps(manifest))


if __name__ == '__main__':
    main()
