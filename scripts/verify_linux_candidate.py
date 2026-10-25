"""Compare both exact artifact inventories; no installation or application startup."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile

from scripts.package_linux import audit, LEGACY_TAR


def verify(directory):
    delivery = json.loads((directory / 'candidate-delivery.json').read_text())
    for name, expected in delivery['artifacts'].items():
        path = directory / name
        if path.stat().st_size != expected['size'] or hashlib.sha256(path.read_bytes()).hexdigest() != expected['sha256']:
            raise ValueError('Artifact delivery hash mismatch')
    version = delivery['internal_version']
    with tempfile.TemporaryDirectory(prefix='fc-candidate-artifacts-') as temporary:
        work = Path(temporary)
        subprocess.run(['dpkg-deb', '-x', str(directory / ('FamilyConnect_' + version + '_amd64.deb')), str(work / 'deb')], check=True)
        subprocess.run(['dpkg-deb', '-e', str(directory / ('FamilyConnect_' + version + '_amd64.deb')), str(work / 'control')], check=True)
        subprocess.run([str((directory / ('FamilyConnect-' + version + '-x86_64.AppImage')).resolve()), '--appimage-extract'],
                       cwd=work, check=True, stdout=subprocess.DEVNULL)
        deb = work / 'deb/usr/lib/family-connect'
        appimage = work / 'squashfs-root/usr/lib/family-connect'
        spec = importlib.util.spec_from_file_location('candidate_verifier', deb / 'candidate_runtime.py')
        runtime = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runtime)
        first, second = runtime.verify(deb), runtime.verify(appimage)
        if first != second or first['build_id'] != delivery['build_id']:
            raise ValueError('AppImage and DEB candidate identities differ')
        for root in (deb, appimage):
            audit(root)
        for path in ('usr/lib/systemd/user/family-connect-chat.service',
                     'usr/share/dbus-1/services/com.familyconnect.Chat1.service',
                     'usr/share/applications/com.familyconnect.Client.desktop'):
            if (work / 'deb' / path).read_bytes() != (deb / 'integration' / Path(path).name).read_bytes():
                raise ValueError('DEB integration differs from inventory')
        for name in ('postinst', 'prerm'):
            if (work / 'control' / name).read_bytes() != (deb / 'integration' / name).read_bytes():
                raise ValueError('DEB maintainer script differs from inventory')
        if (work / 'squashfs-root/AppRun').read_bytes() != (appimage / 'integration/AppRun').read_bytes():
            raise ValueError('AppImage launcher differs from inventory')
        with tarfile.open(directory / ('FamilyConnect-Linux-' + version + '.tar.gz')) as archive:
            members = archive.getmembers()
            if len(members) != 6 or {Path(member.name).name for member in members} != set(LEGACY_TAR) or not all(member.isfile() for member in members):
                raise ValueError('Legacy updater shape changed')
            for member in members:
                name = Path(member.name).name
                if name != 'install-linux.sh' and archive.extractfile(member).read() != (deb / 'clients/desktop' / name).read_bytes():
                    raise ValueError('Legacy/client source mismatch')
        return dict(result='PASS', candidate=first['build_id'], user_members=len(first['files']),
                    source_commit=first['source_commit'], source_dirty=first['source_dirty'], system=first['system'],
                    artifacts=delivery['artifacts'], legacy_members=6)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    print(json.dumps(verify(parser.parse_args().directory), sort_keys=True, indent=2))
