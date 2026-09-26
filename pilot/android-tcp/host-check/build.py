"""Build host-only tests for the Android TCP bridge against its pinned Xray source."""
import argparse
from pathlib import Path
import shutil
import subprocess

PIN = 'd2758a023cd7f4174a5a5fa4ff66e487d4342ba0'
ROOT = Path(__file__).resolve().parents[3]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--core', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    core = args.core.resolve(); output = args.output.resolve()
    revision = subprocess.check_output(['git','-C',str(core),'rev-parse','HEAD'],text=True).strip()
    if revision != PIN or PIN not in (ROOT/'pilot/android-awg/build.py').read_text():
        raise SystemExit('Xray source pin mismatch')
    if subprocess.check_output(['git','-C',str(core),'status','--porcelain','--untracked-files=no']):
        raise SystemExit('Xray checkout modified')
    output.mkdir(mode=0o700)  # New directory only, no existing build outputs overwritten.
    for name in ('main.go','protect.c','profile_test.go'):
        shutil.copy2(Path(__file__).parent/name, output/name)
    shutil.copy2(ROOT/'pilot/android-tcp/tcp-android.go',output/'tcp-android.go')
    # Quote filesystem path as a Go module string (JSON is the same grammar here).
    import json
    (output/'go.mod').write_text('module family-connect-xhttp-host-check\n\ngo 1.26\n\nrequire github.com/xtls/xray-core v0.0.0\nreplace github.com/xtls/xray-core => '+json.dumps(str(core))+'\n')
    for command in (['go','mod','tidy'], ['go','test','./...'], ['go','build','-o','android-host-driver','.']):
        subprocess.run(command,cwd=output,check=True)


if __name__ == '__main__': main()
