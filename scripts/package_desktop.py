"""Package only public application files. No state, profiles, tokens or keys."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tarfile

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--release-files',action='store_true')
    args=parser.parse_args();version=(ROOT/'VERSION').read_text().strip()
    if not all(part.isdigit() for part in version.split('.')) or len(version.split('.'))!=3:
        raise ValueError('invalid release version')
    if not args.release_files:
        output=ROOT/'artifacts/clients';output.mkdir(parents=True,exist_ok=True)
        with tarfile.open(output/f'FamilyConnect-Linux-{version}.tar.gz','w:gz') as archive:
            for name in ('app.py','backend.py','profile_config.py','updates.py','update.pub','install-linux.sh'):
                archive.add(ROOT/'clients/desktop'/name,arcname=f'FamilyConnect-Linux-{version}/{name}')
        return
    output=ROOT/'release-files';output.mkdir(exist_ok=True)
    names=[f'FamilyConnect-Linux-{version}.tar.gz',f'FamilyConnect-Setup-{version}-pilot-unsigned.exe']
    records=[]
    for name in names:
        matches=list((ROOT/('release-linux' if name.endswith('.gz') else 'release-windows')).rglob(name))
        if len(matches)!=1:raise ValueError('missing or ambiguous release artifact')
        shutil.copyfile(matches[0],output/name)
        records.append(dict(file=name,size=(output/name).stat().st_size,
                            sha256=hashlib.sha256((output/name).read_bytes()).hexdigest()))
    (output/'SHA256SUMS').write_text(''.join(f'{r["sha256"]}  {r["file"]}\n' for r in records))
    # Informational catalog only. Clients must not use this unsigned JSON for
    # unattended execution; signed update metadata is a separate planned feature.
    (output/'release.json').write_text(json.dumps(dict(version=version,channel='pilot',
        installation='manual',update_metadata_signed=False,artifacts=records),indent=2)+'\n')


if __name__=='__main__':main()
