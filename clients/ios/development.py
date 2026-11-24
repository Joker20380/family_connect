import argparse
import datetime
import fnmatch
import hashlib
import json
from pathlib import Path
import plistlib
import subprocess

from project import generate


def validate_profile(profile, *, team, bundle, service):
    entitlements = profile.get('Entitlements', {})
    prefixes = profile.get('ApplicationIdentifierPrefix', [])
    expiry = profile.get('ExpirationDate')
    if (profile.get('TeamIdentifier') != [team] or len(prefixes) != 1
            or not isinstance(expiry, datetime.datetime)
            or expiry.replace(tzinfo=datetime.timezone.utc) <= datetime.datetime.now(datetime.timezone.utc)
            or not profile.get('ProvisionedDevices') or entitlements.get('get-task-allow') is not True
            or entitlements.get('application-identifier') != prefixes[0] + '.' + bundle
            or entitlements.get('com.apple.developer.team-identifier') != team
            or 'packet-tunnel-provider' not in entitlements.get('com.apple.developer.networking.networkextension', [])):
        raise ValueError('Development provisioning identity/capability/device/expiry mismatch')
    group = prefixes[0] + '.' + service
    if not any(fnmatch.fnmatchcase(group, grant) for grant in entitlements.get('keychain-access-groups', [])):
        raise ValueError('Provisioning does not grant the app-specific Keychain group')
    return prefixes[0]


def main(args):
    root = Path(__file__).resolve().parents[2]
    result = args.unsigned.resolve()
    manifest = json.loads((result / 'manifest.json').read_text())
    for relative, expected in json.loads((result / 'sha256.json').read_text()).items():
        path = (result / relative).resolve()
        if not path.is_relative_to(result) or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('Unsigned artifact hash mismatch')
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    if manifest['source_sha'] != head:
        raise ValueError('Unsigned artifact source must equal this checkout HEAD')
    subprocess.run(['git', 'diff', '--exit-code', 'HEAD', '--', 'clients/ios'], cwd=root, check=True, stdout=subprocess.DEVNULL)
    profiles = []
    for path in (args.app_profile, args.tunnel_profile):
        if path.resolve().is_relative_to(root):
            raise ValueError('Keep provisioning outside the repository')
        profiles.append(plistlib.loads(subprocess.check_output(['security', 'cms', '-D', '-i', str(path)], stderr=subprocess.DEVNULL)))
    prefixes = [validate_profile(profile, team=args.team, bundle=args.bundle + suffix, service=args.bundle+'.materials')
                for profile, suffix in zip(profiles, ('', '.tunnel'))]
    if prefixes[0] != prefixes[1]:
        raise ValueError('App and extension must share the actual provisioning App ID prefix')
    output = args.out.resolve()
    if output.is_relative_to(root):
        raise ValueError('Keep development products outside the repository')
    output.mkdir(parents=True, exist_ok=False)
    project = generate(root / 'clients/ios', output, result / 'iphoneos', result / 'notices',
                       bundle=args.bundle, team=args.team, app_profile=profiles[0]['UUID'], tunnel_profile=profiles[1]['UUID'])
    subprocess.run(['xcodebuild', '-project', str(project), '-target', 'FamilyConnect', '-configuration', 'Release',
                    '-sdk', 'iphoneos', '-destination', 'generic/platform=iOS', 'ARCHS=arm64',
                    'CONFIGURATION_BUILD_DIR='+str(output / 'products'), 'build'], check=True)
    app = output / 'products/FamilyConnect.app'
    for product, bundle in ((app / 'PlugIns/MeshPacketTunnel.appex', args.bundle+'.tunnel'), (app, args.bundle)):
        subprocess.run(['codesign', '--verify', '--strict', str(product)], check=True)
        signed = plistlib.loads(subprocess.check_output(['codesign', '-d', '--entitlements', ':-', str(product)], stderr=subprocess.DEVNULL))
        group = prefixes[0]+'.'+args.bundle+'.materials'
        info = plistlib.loads((product / 'Info.plist').read_bytes())
        if (signed.get('keychain-access-groups') != [group]
                or signed.get('application-identifier') != prefixes[0]+'.'+bundle
                or signed.get('com.apple.developer.team-identifier') != args.team
                or signed.get('get-task-allow') is not True
                or 'packet-tunnel-provider' not in signed.get('com.apple.developer.networking.networkextension', [])
                or info.get('CFBundleIdentifier') != bundle or info.get('FCKeychainGroup') != group
                or info.get('FCMaterialService') != args.bundle+'.materials'
                or info.get('FCTunnelBundleID') != args.bundle+'.tunnel'):
            raise ValueError('Signed entitlements and app/extension parameters do not match')
    receipt = {'source_sha': head, 'unsigned_manifest_sha256': hashlib.sha256((result / 'manifest.json').read_bytes()).hexdigest(),
               'development_signed': True, 'device_install': 'NOT_RUN', 'physical_VPN': 'NOT_RUN'}
    (output / 'development-receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print('Signed development candidate verified locally. Installation/device acceptance remain separate.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--unsigned', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--team', required=True)
    parser.add_argument('--bundle', required=True)
    parser.add_argument('--app-profile', type=Path, required=True)
    parser.add_argument('--tunnel-profile', type=Path, required=True)
    main(parser.parse_args())
