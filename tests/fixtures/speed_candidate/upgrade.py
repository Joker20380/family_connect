"""Existing in-place update guard; no uninstall, reset, touch injection or activation."""

import json
from prepare import ROOT, WORK, digest


def main():
    original = ROOT/'tests/fixtures/mesh_throughput_trace/upgrade.py'
    assert digest(original)=='cde4965c08308c14bf23175ad3af87cdcbdc72d5e3cfd03de1f4d2ffeb623301'
    text=original.read_text()
    changes={
        'mesh-throughput-trace-20261019':'speed-candidate-20261021',
        "current['code'] == 88":"current['code'] == 96",
        "after['code'] == 89":"after['code'] == 97",
        "version_code')=89":"version_code')=97",
        'beta89_readiness':'beta97_readiness',
        'FamilyConnect-0.1.18-beta89-mesh-trace.apk':'FamilyConnect-0.1.18-beta97-speed.apk',
        'dd722eada0da7c890a8d71a72099cba5d0bbac1ce73377bbdbc8e7b85d820c23':'66a9d18d04ff71100df0144228db05decb970aea71b6d277ec321b1c6c240c63',
        "reference = json.loads((previous.parent / 'identity-before88.json').read_text())":"reference = json.loads((WORK / 'identity-before.json').read_text()) if label == 'after' else record\n    assert record['owner_record_count'] == 1 and record['support_id_sha256']",
    }
    for old,new in changes.items():
        assert old in text,old
        text=text.replace(old,new)
    exec(compile(text,str(original),'exec'),dict(__name__='__main__',__file__=str(original)))


if __name__=='__main__':main()
