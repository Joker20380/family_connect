"""Reuse bounded performance export on current1011, without Android rollout."""

import json
import os
import shutil
import subprocess

from prepare import ROOT, WORK, digest


def main():
    os.umask(0o077)
    target=WORK/'observation-source'
    shutil.copytree(WORK/'baseline-source',target)
    overlays=[(ROOT/'tests/fixtures/mesh_perf3/accepted-overlay.patch','4a32c5e04ffa903791ff30abe80eca6103238f1d2365e9c64d7afc6076f2911c'),
              (ROOT/'tests/fixtures/mesh_throughput_trace/receiver-trace.patch','4f6d02072d57ce4b6d92d85ccd6665caa6f4ac940d97c10d4d0185171cb5f875')]
    pins=json.loads((ROOT/'tests/fixtures/mesh_throughput_trace/source-inputs.json').read_text())['gateway']
    for number,(patch,expected) in enumerate(overlays):
        assert digest(patch)==expected
        if number:
            assert all((digest(target/'carrier'/name) if (target/'carrier'/name).exists() else None)==value for name,value in pins['inputs'].items())
        for dry in (True,False):
            subprocess.run(['patch','-p1','--fuzz=0',*(['--dry-run'] if dry else []),'-i',str(patch)],cwd=target/'carrier',check=True,stdout=subprocess.DEVNULL)
    assert all(digest(target/'carrier'/name)==value for name,value in pins['outputs'].items())
    for name in ('main.go','seed_recovery.go','seed_recovery_test.go'):
        relative='carrier/cmd/bootstrap-broker/'+name
        assert digest(target/relative)==digest(WORK/'baseline-source'/relative)
    print('BOUNDED_SERVER_OBSERVATION_ON_CURRENT1011_SOURCE')


if __name__=='__main__':main()
