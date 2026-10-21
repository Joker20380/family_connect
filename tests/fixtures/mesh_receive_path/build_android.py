"""Reuse the pinned offline observation builder on exact beta90 ancestry."""

import os

from preserve import ROOT, WORK, digest


def main():
    os.umask(0o077)
    original = ROOT / 'tests/fixtures/mesh_throughput_trace/build.py'
    assert digest(original) == '4ed782e6d77748d1cc0e7342c9d15d4486b5a9459b19018d623da929022e9a58'
    source = original.read_text()
    replacements = {
        "ROOT = Path(__file__).resolve().parents[3]": 'ROOT = Path(' + repr(str(ROOT)) + ')',
        "WORK = Path(os.environ.get('MESH_TRACE_OUT', STATE / 'mesh-throughput-trace-20261019'))": 'WORK = Path(' + repr(str(WORK)) + ')',
        "version_code=89, version='0.1.18-beta89-mesh-trace'": "version_code=91, version='0.1.18-beta91-receive-trace'",
        "actual_build_receipt='mesh-throughput-trace-20261019/build/receipt.json'": "actual_build_receipt='mesh-receive-path-20261020/build/receipt.json'",
    }
    for old, new in replacements.items():
        assert source.count(old) == 1, old
        source = source.replace(old, new)
    output = WORK / 'build'
    output.mkdir(mode=0o700, exist_ok=True)
    runner = output / 'executed-build-runner.py'
    with runner.open('x') as handle:
        handle.write(source)
    exec(compile(source, str(runner), 'exec'), dict(__name__='__main__', __file__=str(runner)))


if __name__ == '__main__':
    main()
