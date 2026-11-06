"""Run only the declared ownership fixtures with a private /run temporary tree."""
import argparse
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.ci_pytest_context import ROOT_CLASS, ROOT_FILES


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--collection', type=Path, required=True)
    args = parser.parse_args()
    if os.geteuid() != 0:
        parser.error('Ownership fixtures require isolated UID 0')
    os.umask(0o022)
    with tempfile.TemporaryDirectory(prefix='fc-root-fixtures-', dir='/run') as temporary:
        os.environ['TMPDIR'] = temporary
        tempfile.tempdir = temporary
        import pytest
        result = pytest.main(['-p', 'scripts.ci_pytest_context', '--fixture-context=root',
            '--fixture-collection=' + str(args.collection), '--basetemp=' + temporary + '/pytest',
            '-o', 'faulthandler_timeout=180', '-q', '--tb=short',
            *sorted(ROOT_FILES), ROOT_CLASS.removesuffix('::')])
    raise SystemExit(result)


if __name__ == '__main__':
    main()
