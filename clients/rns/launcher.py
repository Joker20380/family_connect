"""Run unmodified filesystem-discovered RNS modules from a private bounded extraction."""
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
import runpy
import stat
import sys
import tempfile
import zipfile


@contextmanager
def unpack(archive):
    with zipfile.ZipFile(archive) as source, tempfile.TemporaryDirectory(prefix='fc-rns-runtime-') as temporary:
        entries = source.infolist()
        if not 0 < len(entries) <= 512 or len({entry.filename for entry in entries}) != len(entries):
            raise ValueError('RNS_ARCHIVE_INVENTORY')
        if sum(entry.file_size for entry in entries) > 16 * 1024 * 1024:
            raise ValueError('RNS_ARCHIVE_LIMIT')
        root = Path(temporary)
        for entry in entries:
            path = PurePosixPath(entry.filename)
            if (not path.parts or path.is_absolute() or '..' in path.parts or str(path) != entry.filename or
                    '\\' in entry.filename or ':' in entry.filename or entry.is_dir() or
                    not stat.S_ISREG(entry.external_attr >> 16) or entry.file_size > 2 * 1024 * 1024):
                raise ValueError('RNS_ARCHIVE_MEMBER')
            destination = root.joinpath(*path.parts)
            destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            with destination.open('xb') as output:
                output.write(source.read(entry))
            destination.chmod(0o600)
        yield root


def main():
    if sys.argv[1:] not in (['--stdio'], ['--version']):
        return 64
    with unpack(sys.argv[0]) as root:
        sys.path.insert(0, str(root))
        try:
            runpy.run_path(str(root / 'fc_rns_worker.py'), run_name='__main__')
        finally:
            sys.path.remove(str(root))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, zipfile.BadZipFile):
        raise SystemExit(65)
