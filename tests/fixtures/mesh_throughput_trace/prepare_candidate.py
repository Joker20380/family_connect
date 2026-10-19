"""Reproduce the one-line candidate only from the verified observation tree."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(directory):
    files = {str(path.relative_to(directory)): digest(path) for path in directory.rglob('*') if path.is_file()}
    return hashlib.sha256(json.dumps(files, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


if __name__ == '__main__':
    os.umask(0o077)
    fixture = Path(__file__).resolve().parent
    root = fixture.parents[2]
    work = Path(os.environ.get('MESH_TRACE_OUT', root / 'state-client-build/mesh-throughput-trace-20261019'))
    pins = json.loads((fixture / 'candidate-source.json').read_text())
    source = work / 'source/carrier'
    assert inventory(source) == pins['baseline_inventory']
    assert digest(fixture / 'sack-holes.patch') == pins['patch_sha256']
    assert digest(fixture / 'sack_holes_test.go') == pins['test_sha256']
    destination = work / 'candidate/source/carrier'
    assert not destination.exists()
    shutil.copytree(source, destination)
    subprocess.run(['git', 'apply', '--check', str(fixture / 'sack-holes.patch')], cwd=destination, check=True)
    subprocess.run(['git', 'apply', str(fixture / 'sack-holes.patch')], cwd=destination, check=True)
    shutil.copy2(fixture / 'sack_holes_test.go', destination / 'reliablestream/sack_holes_test.go')
    assert digest(destination / 'reliablestream/engine.go') == pins['output_engine_sha256']
    assert inventory(destination) == pins['source_inventory']
    print(json.dumps(dict(candidate_source_inventory=inventory(destination), applied=True, built=False)))
