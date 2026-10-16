import argparse
import json
import os
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('label', choices=['current', 'beta60', 'candidate'])
parser.add_argument('--full', action='store_true')
parser.add_argument('--screens', default='all')
parser.add_argument('--only-compact', action='store_true')
args = parser.parse_args()
adb = [os.environ.get('UI60_ADB','adb'), '-P', '5040', '-s', 'emulator-5580']
destination = root / ('renders-' + args.label)
destination.mkdir(exist_ok=True)
subprocess.run(adb + ['install', '--no-incremental', '-r', str(root / args.label / 'renderer-debug.apk')], check=True, timeout=240)
cases = [('ru', '392', '780', '1'), ('en', '392', '780', '1')]
if args.full:
    cases += [('ru', '320', '640', '1.5'), ('en', '780', '392', '1')]
if args.only_compact:
    cases = [('ru', '320', '640', '1.5'), ('en', '780', '392', '1')]
for language, width, height, font in cases:
    command = adb + ['shell', 'am', 'instrument', '-w']
    for key, value in dict(label=args.label, language=language, width=width, height=height, font=font,screens=args.screens).items():
        command += ['-e', key, value]
    command += ['com.familyconnect.app.friends/com.familyconnect.app.UiFixtureInstrumentation']
    result = subprocess.run(command, capture_output=True, text=True, timeout=300)
    (destination / f'{language}-{width}-{height}-{font}.log').write_text(result.stdout + result.stderr)
    if result.returncode or 'INSTRUMENTATION_CODE: -1' not in result.stdout or 'INSTRUMENTATION_RESULT: error=' in result.stdout:
        raise RuntimeError(result.stdout + result.stderr)
    print(args.label, language, width, height, font, 'RENDERED', flush=True)
subprocess.run(adb + ['pull', '/sdcard/Android/data/com.familyconnect.app.friends/files/ui60-fixtures', str(destination)], check=True, timeout=120)
