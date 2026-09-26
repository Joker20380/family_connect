"""Build user-facing Linux artifacts: AppImage + .deb, keep the legacy tar.gz.

The AppImage and .deb bundle the Friends-capable desktop client (the paired
preview file set) plus pinned Python deps from provisioning/requirements.lock.
GTK 4 / libadwaita / GI / NetworkManager stay host dependencies because `gi`
cannot be pip-installed and bundling GTK without a matching GI runtime is not
reliable. State always lives under $HOME and is never packaged.
"""
import argparse
import ast
import base64
import hashlib
import gzip
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[1]
PACKAGING = ROOT / 'packaging' / 'linux'

DESKTOP_RUNTIME = (
    'app.py', 'backend.py', 'profile_config.py', 'updates.py', 'update.pub',
    'friends_qr.py', 'friends_ui.py',
)
DEVICE_IDENTITY = ('__init__.py', 'device.py', 'friends.py')
PROVISIONING = (
    '__init__.py', 'ack.py', 'application.py', 'auth.py', 'cache.py',
    'configuration.py', 'control_route.py', 'envelope.py', 'models.py',
    'relay.py', 'reticulum.py', 'runtime.py', 'transaction.py',
    'friends.py', 'friends_application.py', 'friends_catalog.py',
    'friends_owner.py', 'friends_store.py', 'requirements.lock',
)
LEGACY_TAR = ('app.py', 'backend.py', 'profile_config.py', 'updates.py', 'update.pub', 'install-linux.sh')

FORBIDDEN_NAMES = ('.env', 'state-v2', 'state-product', 'friends-identity', '__pycache__')
FORBIDDEN_BYTES = (
    b'PRIVATE KEY', b'BEGIN OPENSSH', b'BEGIN ENCRYPTED', b'ghp_', b'gho_',
    b'github_pat_', b'client_secret',
)


def fail(message):
    raise SystemExit('package_linux: ' + message)


def read_version():
    value = (ROOT / 'VERSION').read_text().strip()
    if len(value.split('.')) != 3 or not all(part.isdigit() for part in value.split('.')):
        fail('invalid release version: ' + value)
    return value


def read_icon_png():
    source = ROOT / 'clients' / 'desktop' / 'app.py'
    tree = ast.parse(source.read_text())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == 'ICON_PNG' for t in node.targets
        ):
            return base64.b64decode(node.value.value)
    fail('ICON_PNG not found in app.py')


def safe_copy(source, target):
    if source.is_symlink() or not source.is_file():
        fail('missing or unsafe public source: ' + source)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)


def assemble_bundle(destination):
    """Copy the paired-preview runtime file set into the package layout."""
    desktop = ROOT / 'clients' / 'desktop'
    for name in DESKTOP_RUNTIME:
        safe_copy(desktop / name, destination / 'clients' / 'desktop' / name)
    for name in DEVICE_IDENTITY:
        safe_copy(ROOT / 'device_identity' / name, destination / 'device_identity' / name)
    for name in PROVISIONING:
        safe_copy(ROOT / 'provisioning' / name, destination / 'provisioning' / name)
    safe_copy(PACKAGING / 'launcher.py', destination / 'launcher.py')


def vendor_pip(destination):
    subprocess.run(
        [sys.executable, '-m', 'pip', 'install', '--no-compile', '--no-deps',
         '--target', str(destination), '-r', str(ROOT / 'provisioning' / 'requirements.lock')],
        check=True,
    )


def vendor_from_site(site, destination):
    """Offline local fallback: copy exactly the locked distributions via RECORD."""
    lock = {}
    for line in (ROOT / 'provisioning' / 'requirements.lock').read_text().splitlines():
        line = line.split('#', 1)[0].strip()
        if not line:
            continue
        name, sep, spec = line.partition('==')
        if not sep:
            fail('unsupported requirement pin: ' + line)
        lock[name.strip().lower()] = spec.strip()
    site = Path(site)
    destination.mkdir(parents=True, exist_ok=True)
    copied = set()
    for meta in site.glob('*.dist-info'):
        metadata = meta / 'METADATA'
        if not metadata.is_file():
            continue
        name = None
        for line in metadata.read_text(errors='replace').splitlines():
            if line.startswith('Name:'):
                name = line.split(':', 1)[1].strip()
                break
        if name is None or name.lower() not in lock:
            continue
        record = meta / 'RECORD'
        if not record.is_file():
            continue
        for line in record.read_text(errors='replace').splitlines():
            if not line.strip():
                continue
            relative = line.split(',')[0]
            if '__pycache__' in relative or relative.endswith(('.pyc', '.pyo')):
                continue
            source = site / relative
            if not source.is_file():
                continue
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        copied.add(name.lower())
    missing = set(lock) - copied
    if missing:
        fail('missing vendored distributions: ' + ', '.join(sorted(missing)))


TEXT_SUFFIXES = ('', '.py', '.json', '.lock', '.txt', '.desktop', '.sh', '.md', '.in')


def audit(directory):
    """Refuse to package identity, tokens, keys, state or caches.

    Key-literal scanning applies only to text files. Vendored third-party
    binaries legitimately contain OpenSSL label strings and are not byte-scanned.
    """
    for path in sorted(directory.rglob('*')):
        if not path.is_file():
            continue
        if path.is_symlink():
            fail('package contains symlink: ' + str(path))
        relative = str(path.relative_to(directory))
        if any(bad in relative for bad in FORBIDDEN_NAMES):
            fail('package contains forbidden path: ' + relative)
        if relative.endswith(('.pyc', '.pyo')):
            fail('package contains bytecode: ' + relative)
        if Path(relative).suffix not in TEXT_SUFFIXES:
            continue
        parts = path.relative_to(directory).parts
        if 'vendor' in parts:
            continue
        data = path.read_bytes()
        if any(bad in data for bad in FORBIDDEN_BYTES):
            fail('package contains forbidden content: ' + relative)


def installed_size(root):
    total = 0
    for path in root.rglob('*'):
        if path.is_file():
            total += path.stat().st_size
    return (total + 1023) // 1024


def build_deb(bundle, version, output):
    staging = output / 'build' / 'deb' / ('family-connect_' + version + '_amd64')
    if staging.exists():
        shutil.rmtree(staging)
    (staging / 'DEBIAN').mkdir(parents=True)
    (staging / 'usr' / 'bin').mkdir(parents=True)
    shutil.copytree(bundle, staging / 'usr' / 'lib' / 'family-connect')
    shutil.copy2(PACKAGING / 'postinst', staging / 'DEBIAN' / 'postinst')
    shutil.copy2(PACKAGING / 'prerm', staging / 'DEBIAN' / 'prerm')
    (staging / 'DEBIAN' / 'postinst').chmod(0o755)
    (staging / 'DEBIAN' / 'prerm').chmod(0o755)

    (staging / 'usr' / 'bin' / 'family-connect').write_text(
        '#!/bin/sh\n'
        'export PYTHONNOUSERSITE=1\n'
        'export PYTHONDONTWRITEBYTECODE=1\n'
        'exec /usr/bin/python3 /usr/lib/family-connect/launcher.py "$@"\n'
    )
    (staging / 'usr' / 'bin' / 'family-connect').chmod(0o755)

    (staging / 'usr' / 'share' / 'applications').mkdir(parents=True)
    shutil.copy2(PACKAGING / 'com.familyconnect.Client.desktop',
                 staging / 'usr' / 'share' / 'applications' / 'com.familyconnect.Client.desktop')
    (staging / 'usr' / 'share' / 'icons' / 'hicolor' / '256x256' / 'apps').mkdir(parents=True)
    (staging / 'usr' / 'share' / 'icons' / 'hicolor' / '256x256' / 'apps' / 'com.familyconnect.Client.png').write_bytes(
        read_icon_png())
    (staging / 'usr' / 'share' / 'doc' / 'family-connect').mkdir(parents=True)
    shutil.copy2(PACKAGING / 'copyright', staging / 'usr' / 'share' / 'doc' / 'family-connect' / 'copyright')

    control = (
        'Package: family-connect\n'
        f'Version: {version}\n'
        'Architecture: amd64\n'
        'Maintainer: Family Connect <maintainers@family-connect.invalid>\n'
        f'Installed-Size: {installed_size(staging / "usr")}\n'
        'Depends: python3 (>= 3.10), python3-gi, python3-gi-cairo, gir1.2-gtk-4.0, gir1.2-adw-1, librsvg2-common, network-manager, libqrencode4, libzbar0\n'
        'Section: net\n'
        'Priority: optional\n'
        'Homepage: https://github.com/Joker20380/family_connect\n'
        'Description: Family Connect desktop client\n'
        ' Private family VPN client (GTK 4 / libadwaita).\n'
        ' Bundled application dependencies; GTK/GI/NetworkManager are host deps.\n'
    )
    (staging / 'DEBIAN' / 'control').write_text(control)

    audit(staging / 'usr')

    output.mkdir(parents=True, exist_ok=True)
    target = output / f'FamilyConnect_{version}_amd64.deb'
    subprocess.run(['dpkg-deb', '--build', '--root-owner-group', str(staging), str(target)], check=True)
    return target


def appdir_desktop():
    text = (PACKAGING / 'com.familyconnect.Client.desktop').read_text()
    return text.replace('Exec=family-connect %u', 'Exec=AppRun')


def build_appdir(bundle, version, output):
    appdir = output / 'build' / 'AppDir' / ('FamilyConnect-' + version + '-x86_64.AppDir')
    if appdir.exists():
        shutil.rmtree(appdir)
    shutil.copytree(bundle, appdir / 'usr' / 'lib' / 'family-connect')
    shutil.copy2(PACKAGING / 'AppRun', appdir / 'AppRun')
    (appdir / 'AppRun').chmod(0o755)
    (appdir / 'com.familyconnect.Client.desktop').write_text(appdir_desktop())
    icon = read_icon_png()
    (appdir / 'com.familyconnect.Client.png').write_bytes(icon)
    (appdir / '.DirIcon').write_bytes(icon)
    audit(appdir)
    return appdir


def build_appimage(appdir, version, output, tool):
    if not tool:
        print('appimagetool not provided; leaving AppDir at ' + str(appdir))
        return None
    output.mkdir(parents=True, exist_ok=True)
    target = output / f'FamilyConnect-{version}-x86_64.AppImage'
    env = dict(os.environ, ARCH='x86_64')
    subprocess.run([tool, str(appdir), str(target)], check=True, env=env)
    return target


def build_legacy_tar(version, output):
    """Reproduce the six-file archive the signed update catalog expects."""
    output.mkdir(parents=True, exist_ok=True)
    target = output / f'FamilyConnect-Linux-{version}.tar.gz'
    with target.open('wb') as stream, gzip.GzipFile(fileobj=stream, mode='wb', filename='', mtime=0) as compressed, tarfile.open(fileobj=compressed, mode='w') as archive:
        for name in LEGACY_TAR:
            source = ROOT / 'clients' / 'desktop' / name
            if source.is_symlink() or not source.is_file():
                fail('missing or unsafe public source: ' + name)
            data = source.read_bytes()
            entry = tarfile.TarInfo(f'FamilyConnect-Linux-{version}/{name}')
            entry.size, entry.mode, entry.mtime = len(data), 0o600, 0
            archive.addfile(entry, io.BytesIO(data))
    return target


def build_release_files(version, output):
    """Assemble release-files/ for GitHub Releases (deb + AppImage + legacy + windows)."""
    destination = ROOT / 'release-files'
    destination.mkdir(exist_ok=True)
    records = []
    # Windows carries its own version (currently 0.2.15 while VERSION is 0.2.11);
    # resolve it by a single wildcard instead of the shared VERSION string.
    names = (
        f'FamilyConnect-{version}-x86_64.AppImage',
        f'FamilyConnect_{version}_amd64.deb',
        f'FamilyConnect-Linux-{version}.tar.gz',
        'FamilyConnect-Setup-*-pilot-unsigned.exe',
    )
    for name in names:
        directory = 'release-windows' if name.endswith('.exe') else 'release-linux'
        matches = [m for m in (ROOT / directory).rglob(name) if m.is_file()]
        if len(matches) != 1:
            fail('missing or ambiguous release artifact: ' + name)
        shutil.copyfile(matches[0], destination / matches[0].name)
        records.append(dict(file=matches[0].name, size=(destination / matches[0].name).stat().st_size,
                            sha256=hashlib.sha256((destination / matches[0].name).read_bytes()).hexdigest()))
    (destination / 'SHA256SUMS').write_text(''.join(f'{r["sha256"]}  {r["file"]}\n' for r in records))
    (destination / 'release.json').write_text(json.dumps(dict(version=version, channel='pilot',
        installation='manual', update_metadata_signed=False, artifacts=records), indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'artifacts' / 'clients')
    parser.add_argument('--vendor-from', type=Path, default=None,
                        help='offline: copy locked dists from an existing site-packages directory')
    parser.add_argument('--appimagetool', type=Path, default=None)
    parser.add_argument('--release-files', action='store_true')
    args = parser.parse_args()
    version = read_version()

    if args.release_files:
        build_release_files(version, args.output)
        return

    build = args.output / 'build'
    bundle = build / 'bundle'
    if bundle.exists():
        shutil.rmtree(bundle)
    assemble_bundle(bundle)
    if args.vendor_from:
        vendor_from_site(args.vendor_from, bundle / 'vendor')
    else:
        vendor_pip(bundle / 'vendor')
    audit(bundle)

    legacy = build_legacy_tar(version, args.output)
    deb = build_deb(bundle, version, args.output)
    appdir = build_appdir(bundle, version, args.output)
    appimage = build_appimage(appdir, version, args.output, args.appimagetool)

    print('built:')
    print('  deb      ', deb)
    print('  appimage ', appimage or appdir)
    print('  legacy   ', legacy)


if __name__ == '__main__':
    main()
