"""Guarded same-signer94->95 owner update through the existing workflow."""

from prepare import ROOT, digest

original=ROOT/'tests/fixtures/mesh_throughput_trace/upgrade.py'
assert digest(original)=='cde4965c08308c14bf23175ad3af87cdcbdc72d5e3cfd03de1f4d2ffeb623301'
source=original.read_text()
for old,new in {
    'mesh-throughput-trace-20261019':'mux-profile-20261020',
    "current['code'] == 88":"current['code'] == 94",
    "after['code'] == 89":"after['code'] == 95",
    "version_code')=89":"version_code')=95",
    'beta89_readiness':'beta95_readiness',
    'FamilyConnect-0.1.18-beta89-mesh-trace.apk':'FamilyConnect-0.1.18-beta95-mux-profile.apk',
}.items():
    assert old in source,old
    source=source.replace(old,new)
exec(compile(source,str(original),'exec'),dict(__name__='__main__',__file__=str(original)))
