"""Package only public application files. No state, profiles, tokens or keys."""
import argparse
import hashlib
import gzip
import io
import json
from pathlib import Path
import shutil
import tarfile

ROOT=Path(__file__).resolve().parents[1]
DESKTOP=('app.py','backend.py','profile_config.py','updates.py','update.pub','install-linux.sh')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--release-files',action='store_true')
    args=parser.parse_args();version=(ROOT/'VERSION').read_text().strip()
    if not all(part.isdigit() for part in version.split('.')) or len(version.split('.'))!=3:
        raise ValueError('invalid release version')
    if not args.release_files:
        output=ROOT/'artifacts/clients';output.mkdir(parents=True,exist_ok=True)
        target=output/f'FamilyConnect-Linux-{version}.tar.gz'
        with target.open('wb') as stream, gzip.GzipFile(fileobj=stream,mode='wb',filename='',mtime=0) as compressed, tarfile.open(fileobj=compressed,mode='w') as archive:
            for name in DESKTOP:
                source=ROOT/'clients/desktop'/name
                if source.is_symlink() or not source.is_file():
                    raise ValueError('missing or unsafe public source: '+name)
                data=source.read_bytes()
                entry=tarfile.TarInfo(f'FamilyConnect-Linux-{version}/{name}')
                entry.size,entry.mode,entry.mtime=len(data),0o600,0
                archive.addfile(entry,io.BytesIO(data))
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
