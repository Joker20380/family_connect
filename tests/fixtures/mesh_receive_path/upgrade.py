"""Guarded same-signer90->91 update; requires ordinary disconnected state."""

from preserve import ROOT, digest


if __name__=='__main__':
    original=ROOT/'tests/fixtures/mesh_throughput_trace/upgrade.py'
    assert digest(original)=='cde4965c08308c14bf23175ad3af87cdcbdc72d5e3cfd03de1f4d2ffeb623301'
    source=original.read_text()
    replacements={
        'mesh-throughput-trace-20261019':'mesh-receive-path-20261020',
        "current['code'] == 88":"current['code'] == 90",
        "after['code'] == 89":"after['code'] == 91",
        "version_code')=89":"version_code')=91",
        'beta89_readiness':'beta91_readiness',
        'FamilyConnect-0.1.18-beta89-mesh-trace.apk':'FamilyConnect-0.1.18-beta91-receive-trace.apk',
    }
    for old,new in replacements.items():
        assert old in source,old
        source=source.replace(old,new)
    exec(compile(source,str(original),'exec'),dict(__name__='__main__',__file__=str(original)))
