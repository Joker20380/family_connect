"""Finalize one immutable assets-only field APK; never publish or install it."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile
import time
import zipfile

SIGNER = '67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a'
PACKAGE = 'com.familyconnect.app.friends'
NATIVE = '773d760dc8f5a7894ed7008b5f6c30b830bd663f66a8935d470f5262ebc50d26'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def entries(apk):
    with zipfile.ZipFile(apk) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError('duplicate APK entry')
        return {name: archive.read(name) for name in names}


def verified_locator(verifier, locator, anchor, node):
    result = subprocess.run([str(verifier), '--verify-locator', str(locator), '--anchor', str(anchor), '--node', node],
                            capture_output=True, timeout=10)
    if result.returncode != 0:
        raise ValueError('locator verification rejected')
    return json.loads(result.stdout)


def check_window(locator, ready, *, now, handoff_seconds):
    if not 0 <= handoff_seconds <= 120:
        raise ValueError('invalid finite handoff allowance')
    if (ready.get('phase') != 'LOCATOR_VERIFIED_SEED_CONNECTED' or
            ready.get('locator_sha256') != locator['locator_sha256'] or
            ready.get('expires_at') != locator['expires_at'] or
            not 0 <= now-ready.get('observed_at', 0) <= 90):
        raise ValueError('entry evidence stale or mismatched; recheck running entry')
    if locator['expires_at']-now < 200+handoff_seconds:
        raise ValueError('insufficient locator window; do not extend TTL')


def compare_payload(prepared, signed):
    expected, actual = entries(prepared), entries(signed)
    extra = set(actual)-set(expected)
    if any(not re.fullmatch(r'META-INF/[^/]+\.(SF|RSA|DSA|EC)|META-INF/MANIFEST.MF', name) for name in extra):
        raise ValueError('unexpected signed APK entries')
    if any(actual.get(name) != raw for name, raw in expected.items()):
        raise ValueError('signed APK payload mismatch')


def prepare(args):
    receipt = json.loads(args.verification.read_bytes())
    if receipt.get('unsigned') is not True or receipt.get('package') != PACKAGE or receipt.get('version_code') != 120:
        raise ValueError('not the reserved field prebuild')
    if digest(args.unsigned.read_bytes()) != receipt['apk_sha256']:
        raise ValueError('prebuild hash mismatch')
    payload = entries(args.unsigned)
    if digest(payload['lib/arm64-v8a/libfc_restricted.so']) != NATIVE:
        raise ValueError('unaccepted ARM64 JNI')
    if any(name.startswith('assets/provisioning/') for name in payload):
        raise ValueError('prebuild contains an old locator')
    if payload['assets/control-anchor.pub'].strip() != args.anchor.read_bytes().strip():
        raise ValueError('APK and authority trust differ')
    if (args.ready.parent/'stopped.json').exists():
        raise ValueError('entry stopped')
    locator = verified_locator(args.verifier, args.locator, args.anchor, args.node)
    ready = json.loads(args.ready.read_bytes())
    check_window(locator, ready, now=int(time.time()), handoff_seconds=args.handoff_seconds)
    args.output.mkdir(parents=True, exist_ok=False)
    with tempfile.TemporaryDirectory(prefix='cold-apk-', dir=args.output) as staging:
        staged = Path(staging)/'unaligned.apk'
        with zipfile.ZipFile(args.unsigned) as source, zipfile.ZipFile(staged, 'x') as target:
            for item in source.infolist():
                target.writestr(item, payload[item.filename])
            target.writestr('assets/provisioning/'+args.node+'.json', args.locator.read_bytes())
        target = args.output/'FamilyConnect-Test-0.1.18-beta120-fresh-unsigned.apk'
        subprocess.run([str(args.zipalign), '-P', '16', '4', str(staged), str(target)], check=True, capture_output=True)
    final = entries(target)
    allowed = 'assets/provisioning/'+args.node+'.json'
    if set(final)-set(payload) != {allowed} or any(final.get(name) != raw for name, raw in payload.items()):
        raise ValueError('non-locator payload changed')
    if digest(final[allowed]) != locator['locator_sha256']:
        raise ValueError('locator changed while packaging')
    check_window(locator, ready, now=int(time.time()), handoff_seconds=args.handoff_seconds)
    result = dict(prebuild_sha256=receipt['apk_sha256'], apk_sha256=digest(target.read_bytes()),
                  locator=locator, native_sha256=NATIVE, signed=False, installed=False, distributed=False,
                  connect_not_after=locator['expires_at']-200, entry_liveness='RECHECK_ON_SERVER_BEFORE_HANDOFF')
    (args.output/'preparation.json').write_text(json.dumps(result, indent=2)+'\n')
    return result


def verify_signed(args):
    compare_payload(args.prepared, args.apk)
    result = subprocess.run([str(args.apksigner), 'verify', '--verbose', '--print-certs', str(args.apk)],
                            capture_output=True, text=True, timeout=20)
    if result.returncode or re.findall(r'Signer #\d+ certificate SHA-256 digest: ([0-9a-f]{64})', result.stdout) != [SIGNER]:
        raise ValueError('field signature differs from beta113')
    badging = subprocess.check_output([str(args.aapt), 'dump', 'badging', str(args.apk)], text=True, timeout=10)
    if ("package: name='"+PACKAGE+"' versionCode='120'" not in badging or "sdkVersion:'27'" not in badging or
            "native-code: 'arm64-v8a'" not in badging or 'application-debuggable' in badging):
        raise ValueError('field package incompatible')
    subprocess.run([str(args.zipalign), '-c', '-P', '16', '4', str(args.apk)], capture_output=True, check=True, timeout=10)
    payload = entries(args.apk)
    if digest(payload['lib/arm64-v8a/libfc_restricted.so']) != NATIVE or payload['assets/control-anchor.pub'].strip() != args.anchor.read_bytes().strip():
        raise ValueError('final native/trust mismatch')
    with tempfile.TemporaryDirectory(prefix='cold-public-locator-') as staging:
        path = Path(staging)/'locator.json'
        path.write_bytes(payload['assets/provisioning/'+args.node+'.json'])
        locator = verified_locator(args.verifier, path, args.anchor, args.node)
    if locator['expires_at']-int(time.time()) < 200:
        raise ValueError('expired handoff window')
    return dict(apk_sha256=digest(args.apk.read_bytes()), certificate_sha256=SIGNER, locator=locator,
                connect_not_after=locator['expires_at']-200, payload_matches=True, installed=False, distributed=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    staging = commands.add_parser('prepare')
    for name in ('unsigned', 'verification', 'locator', 'ready', 'zipalign', 'output'):
        staging.add_argument('--'+name, type=Path, required=True)
    staging.add_argument('--handoff-seconds', type=int, default=60)
    signed = commands.add_parser('verify-signed')
    for name in ('prepared', 'apk', 'apksigner', 'aapt', 'zipalign'):
        signed.add_argument('--'+name, type=Path, required=True)
    for command in (staging, signed):
        command.add_argument('--verifier', type=Path, required=True)
        command.add_argument('--anchor', type=Path, required=True)
        command.add_argument('--node', choices=('nl-amsterdam-1', 'nl-amsterdam-2'), required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(prepare(args) if args.command == 'prepare' else verify_signed(args), indent=2))
    except Exception:
        parser.exit(1, 'FIELD_APK_REJECTED_NO_HANDOFF\n')


if __name__ == '__main__':
    main()
