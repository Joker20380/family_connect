"""Reconstruct only the nineteen public support baseline sources for native CI."""
import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
BASELINE_COMMIT = '61b00409e24b92651678b817d2a6f5d4796948f9'
CANDIDATE_SHA256 = '621009b8df9baffb81e0d9069cfa52b3781e7dd7bf4e435dd89740e38cae5739'


def prepare(output):
    sys.path.insert(0, str(ROOT))
    from scripts import package_support_capture as package
    output = Path(output).absolute()
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    baseline = output / 'baseline'
    for name, expected in package.contract(ROOT)['baseline'].items():
        raw = subprocess.check_output(['git', 'show', BASELINE_COMMIT + ':' + name], cwd=ROOT)
        package.require(package.digest(raw) == expected, 'CI_BASELINE_PIN')
        target = baseline / name
        target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        target.write_bytes(raw)
    package.build(baseline, output / 'archive', ROOT)
    candidate = output / 'archive/candidate.pyz'
    package.require(package.digest(candidate.read_bytes()) == CANDIDATE_SHA256, 'CI_CANDIDATE_PIN')
    return dict(FC_TEST_SUPPORT_BASELINE=str(baseline), FC_TEST_SUPPORT_ARCHIVE=str(candidate))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    for name, value in prepare(args.output).items():
        if '\n' in value or '\r' in value:
            raise ValueError('CI_PATH')
        print(name + '=' + value)
