"""Guarded forward updates using current receipts; no UI or provisioning bypass."""

import json
import sys

from deadline import WORK
from late_arrival import ROOT, digest


def main():
    original = ROOT / 'tests/fixtures/mesh_throughput_trace/upgrade.py'
    assert digest(original) == 'cde4965c08308c14bf23175ad3af87cdcbdc72d5e3cfd03de1f4d2ffeb623301'
    baseline = '--baseline' in sys.argv
    destination = WORK / 'normal94' if baseline else WORK
    previous, version = (93, 94) if baseline else (92, 93)
    source = original.read_text()
    replacements = {
        "ROOT = Path(__file__).resolve().parents[3]": 'ROOT = Path('+repr(str(ROOT))+')',
        "WORK = ROOT / 'state-client-build/mesh-throughput-trace-20261019'": 'WORK = Path('+repr(str(destination))+')',
        "current['code'] == 88": "current['code'] == "+str(previous),
        "after['code'] == 89": "after['code'] == "+str(version),
        "version_code')=89": "version_code')="+str(version),
        'beta89_readiness': 'beta'+str(version)+'_readiness',
        'FamilyConnect-0.1.18-beta89-mesh-trace.apk': 'FamilyConnect-0.1.18-beta94-stability.apk' if baseline else 'FamilyConnect-0.1.18-beta93-rtp-deadline.apk',
    }
    if baseline:
        candidate = json.loads((WORK / 'delivery/signing-receipt.json').read_text())
        replacements["current['apk_sha256'] == signing['baseline']['sha256']"] = "current['apk_sha256'] == "+repr(candidate['signed']['sha256'])
        replacements["current['native_sha256'] == 'dd722eada0da7c890a8d71a72099cba5d0bbac1ce73377bbdbc8e7b85d820c23'"] = "current['native_sha256'] == "+repr(candidate['native_sha256'])
    for old, new in replacements.items():
        assert old in source, old
        source = source.replace(old, new)
    exec(compile(source, str(original), 'exec'), dict(__name__='__main__', __file__=str(original)))


if __name__ == '__main__':
    main()
