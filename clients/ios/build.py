import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import tarfile
import tempfile

from project import generate

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'clients/ios'
XRAY = 'd2758a023cd7f4174a5a5fa4ff66e487d4342ba0'
PATCH = ROOT / 'pilot/android-restricted/xray-packet-boundary.patch'


def run(*args, cwd=SOURCE, env=None):
    print('+', *map(str, args), flush=True)
    subprocess.run(list(map(str, args)), cwd=cwd, env=env, check=True)


def capture(*args, cwd=SOURCE, env=None):
    return subprocess.check_output(list(map(str, args)), cwd=cwd, env=env, text=True).strip()


def prepare(workspace, go):
    upstream = workspace / 'upstream'
    run('git', 'clone', '--quiet', '--depth=1', '--branch=v1.260327.0', 'https://github.com/XTLS/Xray-core.git', upstream)
    if capture('git', 'rev-parse', 'HEAD', cwd=upstream) != XRAY:
        raise RuntimeError('Xray pin mismatch')
    archive = workspace / 'xray.tar'
    run('git', 'archive', '--format=tar', '-o', archive, XRAY, cwd=upstream)
    xray = workspace / 'xray'
    xray.mkdir()
    with tarfile.open(archive) as bundle:
        bundle.extractall(xray, filter='data')
    run('git', 'apply', PATCH, cwd=xray, env=os.environ | {'GIT_CEILING_DIRECTORIES': str(workspace)})
    run('git', 'apply', SOURCE / 'xray-endpoint-only.patch', cwd=xray, env=os.environ | {'GIT_CEILING_DIRECTORIES': str(workspace)})
    module = workspace / 'ios.mod'
    shutil.copy2(SOURCE / 'go.mod', module)
    shutil.copy2(SOURCE / 'go.sum', module.with_suffix('.sum'))
    run(go, 'mod', 'edit', '-modfile='+str(module),
        '-replace=github.com/xtls/xray-core='+str(xray),
        '-replace=github.com/Joker20380/family_connect/carrier='+str(ROOT / 'carrier'),
        '-replace=github.com/Joker20380/family_connect/restrictedandroid='+str(ROOT / 'pilot/android-restricted'))
    return module


def closure(go, module, environment, output):
    flags = ['-tags=fc_packet_endpoint', '-mod=readonly', '-modfile='+str(module)]
    packages = capture(go, 'list', *flags, '-deps', '-f', '{{.ImportPath}}', './native', env=environment).splitlines()
    modules = capture(go, 'list', *flags, '-deps', '-f', '{{if .Module}}{{.Module.Path}}{{end}}', './native', env=environment).splitlines()
    if any('sagernet/sing' in name for name in modules):
        raise RuntimeError('Endpoint-only closure unexpectedly includes sing')
    records = []
    notices = output / 'notices'
    notices.mkdir(exist_ok=True)
    with tarfile.open(output / 'dependency-sources.tar.gz', 'w:gz') as sources:
        for name in sorted(set(modules)):
            if not name:
                continue
            text = capture(go, 'list', '-modfile='+str(module), '-m', '-json', name)
            record = json.loads(text)
            directory = Path(record['Dir'])
            local = name.startswith('github.com/Joker20380/family_connect/')
            records.append(dict(path=name, version=record.get('Version', 'source'), sum=record.get('Sum'),
                                source='repository' if local else 'dependency-sources.tar.gz'))
            if local:
                continue
            target = notices / name.replace('/', '_')
            target.mkdir(exist_ok=True)
            for path in directory.rglob('*'):
                if path.is_file() and path.name.upper().startswith(('LICENSE', 'NOTICE', 'COPYING', 'COPYRIGHT')):
                    relative = path.relative_to(directory)
                    destination = target / relative
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(path, destination)
            sources.add(directory, arcname=name, filter=lambda item: None if '/.git/' in item.name or item.name.endswith('/.git') else item)
    shutil.copy2(PATCH, notices / 'Xray-modifications.patch')
    shutil.copy2(SOURCE / 'xray-endpoint-only.patch', notices / 'Xray-endpoint-only.patch')
    shutil.copy2(Path(capture(go, 'env', 'GOROOT')) / 'LICENSE', notices / 'Go-LICENSE')
    shutil.copytree(ROOT / 'carrier/licenses', notices / 'carrier', dirs_exist_ok=True)
    (output / 'closure.json').write_text(json.dumps(dict(packages=packages, modules=records), indent=2)+'\n')
    run('git', 'archive', '--format=tar.gz', '-o', output / 'family-sources.tar.gz', 'HEAD',
        'clients/ios', 'carrier', 'pilot/android-restricted', 'LICENSE', cwd=ROOT)
    return notices


def build(args):
    output = args.out.resolve()
    output.mkdir(parents=True, exist_ok=False)
    go = str(Path(args.go).resolve())
    version = capture(go, 'version')
    if 'go1.26.1 ' not in version:
        raise RuntimeError('Go 1.26.1 required')
    run('git', 'diff', '--exit-code', 'HEAD', '--', 'clients/ios', 'carrier', 'pilot/android-restricted', cwd=ROOT)
    environment = {key: value for key, value in os.environ.items() if key not in ('GOFLAGS', 'FC_TELEMOST_ROOM', 'YANDEX_TELEMOST_OAUTH_TOKEN')}
    environment.update(GOTOOLCHAIN='local', GOWORK='off')
    manifest = dict(source_sha=capture('git', 'rev-parse', 'HEAD', cwd=ROOT), go=version, xray=XRAY,
                    patch_sha256=hashlib.sha256(PATCH.read_bytes()).hexdigest(), targets=[],
                    endpoint_patch_sha256=hashlib.sha256((SOURCE / 'xray-endpoint-only.patch').read_bytes()).hexdigest(),
                    system=platform.platform(), python=platform.python_version(), image=os.environ.get('ImageVersion'), real_vpn='NOT_RUN', telemost='NOT_RUN')
    with tempfile.TemporaryDirectory(prefix='fc-ios-') as directory:
        workspace = Path(directory)
        module = prepare(workspace, go)
        flags = ['-tags=fc_packet_endpoint', '-mod=readonly', '-modfile='+str(module)]
        run(go, 'test', *flags, '-v', '-race', '-count=3', '-timeout=90s', '-ldflags=-checklinkname=0', './bridge', env=environment)
        run(go, 'test', *flags, '-v', '-race', '-count=1', '-timeout=90s', '-ldflags=-checklinkname=0',
            'github.com/Joker20380/family_connect/restrictedandroid/packet', env=environment)
        run(go, 'test', '-mod=readonly', '-modfile='+str(module), '-v', '-race', '-count=1', '-timeout=90s',
            '-ldflags=-checklinkname=0', 'github.com/Joker20380/family_connect/restrictedandroid/packet', env=environment)
        if args.host_only:
            return
        if platform.system() != 'Darwin' or capture('xcodebuild', '-version') != 'Xcode 16.4\nBuild version 16F6':
            raise RuntimeError('macOS and Xcode 16.4 (16F6) required')
        manifest['xcode'] = capture('xcodebuild', '-version')
        manifest['swift'] = capture('xcrun', 'swift', '--version')
        manifest['clang'] = capture('xcrun', 'clang', '--version')
        for sdk, target in [('iphoneos', 'arm64-apple-ios16.0'), ('iphonesimulator', 'arm64-apple-ios16.0-simulator')]:
            sdkpath = capture('xcrun', '--sdk', sdk, '--show-sdk-path')
            if capture('xcrun', '--sdk', sdk, '--show-sdk-version') != '18.5':
                raise RuntimeError('iOS SDK 18.5 required')
            destination = output / sdk
            destination.mkdir()
            compiler = workspace / (sdk+'-clang')
            compiler.write_text('#!/bin/sh\nexec xcrun --sdk '+sdk+' clang -target '+target+' -isysroot "'+sdkpath+'" "$@"\n')
            compiler.chmod(0o755)
            native = environment | dict(GOOS='ios', GOARCH='arm64', CGO_ENABLED='1', CC=str(compiler))
            library = destination / 'libFamilyMesh.a'
            run(go, 'build', *flags, '-trimpath', '-ldflags=-checklinkname=0', '-buildmode=c-archive', '-o', library, './native', env=native)
            if sdk == 'iphoneos':
                notices = closure(go, module, native, output)
            project_dir = workspace / sdk
            project_dir.mkdir()
            project = generate(SOURCE, project_dir, destination, notices)
            run('xcodebuild', '-project', project, '-target', 'FamilyConnect', '-configuration', 'Release',
                '-sdk', sdk, '-arch', 'arm64', 'CODE_SIGNING_ALLOWED=NO', 'SYMROOT='+str(project_dir / 'products'), 'build', env=environment)
            app = project_dir / 'products' / ('Release-'+sdk) / 'FamilyConnect.app'
            shutil.copytree(app, destination / app.name)
            for name in ('FamilyConnect', 'MeshPacketTunnel'):
                binary = destination / 'FamilyConnect.app' / ('FamilyConnect' if name == 'FamilyConnect' else 'PlugIns/MeshPacketTunnel.appex/MeshPacketTunnel')
                symbols = capture('xcrun', 'nm', binary)
                for symbol in ('_fc_ios_start', '_fc_ios_write', '_fc_ios_read', '_fc_ios_commit_start', '_fc_ios_validate_material', 'wholedevice', 'tcpforward', 'familysession', 'bootstrap', 'telemost', 'xray-core/proxy/tun'):
                    if symbol not in symbols:
                        raise RuntimeError('Missing linked symbol: '+symbol)
                (destination / (name+'-symbols.txt')).write_text(symbols+'\n')
                loads = capture('xcrun', 'vtool', '-show-build', binary)
                if ('IOSSIMULATOR' if sdk == 'iphonesimulator' else 'platform IOS\n') not in loads:
                    raise RuntimeError('Wrong Mach-O platform: '+loads)
                (destination / (name+'-platform.txt')).write_text(loads+'\n')
                shutil.copy2(project_dir / (name+'.map'), destination)
            manifest['targets'].append(dict(sdk=sdk, sdk_version='18.5', target=target, goos='ios', goarch='arm64', signing='unsigned'))
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    hashes = {str(path.relative_to(output)): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in sorted(output.rglob('*')) if path.is_file()}
    (output / 'sha256.json').write_text(json.dumps(hashes, indent=2)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--go', default=shutil.which('go'))
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--host-only', action='store_true')
    build(parser.parse_args())
