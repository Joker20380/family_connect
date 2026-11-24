"""Minimal HMAC alias overlay over audited installed source; no keys or databases."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]


def build(baseline,output,source=ROOT):
    manifest=json.loads((source/'deploy/support-chat/pseudonym-baseline.json').read_text())
    delta=source/'deploy/support-chat/pseudonym-generation.patch'
    with tempfile.TemporaryDirectory() as directory:
        stage=Path(directory)
        for name,expected in manifest['files'].items():
            path=baseline/name
            if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
                raise ValueError('Installed source pin mismatch')
            target=stage/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(path.read_bytes())
        subprocess.run(['git','apply','--unidiff-zero','--check',str(delta)],cwd=stage,check=True,capture_output=True)
        subprocess.run(['git','apply','--unidiff-zero',str(delta)],cwd=stage,check=True,capture_output=True)
        if {str(path.relative_to(stage)) for path in stage.rglob('*') if path.is_file()}!=set(manifest['files']):
            raise ValueError('Unexpected delta member')
        added='control/friends/pseudonyms.py'
        (stage/added).write_bytes((source/added).read_bytes())
        for path in stage.rglob('*.py'):compile(path.read_bytes(),str(path.relative_to(stage)),'exec')
        shutil.copytree(stage,output)
    hashes={str(path.relative_to(output)):hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(output.rglob('*.py'))}
    report=dict(schema=1,baseline=manifest,patch_sha256=hashlib.sha256(delta.read_bytes()).hexdigest(),after=hashes,
                boundary='HMAC aliases only; no HTTP/paid/reconciler/APK/transport changes; no activation')
    (output/'receipt.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    build(args.baseline,args.output)
    print('Minimal source overlay prepared; no activation')


if __name__=='__main__':main()
