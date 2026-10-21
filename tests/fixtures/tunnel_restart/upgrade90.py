"""Reuse the accepted data-preserving upgrade checks with explicit 89->90 pins."""

import sys

from preserve import ROOT, WORK, digest


if __name__ == '__main__':
    path = ROOT / 'tests/fixtures/mesh_throughput_trace/upgrade.py'
    assert digest(path) == 'cde4965c08308c14bf23175ad3af87cdcbdc72d5e3cfd03de1f4d2ffeb623301'
    source = path.read_text().replace('mesh-throughput-trace-20261019', 'tunnel-restart-20261019')
    source = source.replace("current['code'] == 88", "current['code'] == 89")
    source = source.replace("after['code'] == 89", "after['code'] == 90")
    source = source.replace("version_code')=89", "version_code')=90").replace('beta89_readiness', 'beta90_readiness')
    source = source.replace('FamilyConnect-0.1.18-beta89-mesh-trace.apk', 'FamilyConnect-0.1.18-beta90-stability.apk')
    source = source.replace("current['native_sha256'] == 'dd722eada0da7c890a8d71a72099cba5d0bbac1ce73377bbdbc8e7b85d820c23'",
                            "current['native_sha256'] == '3ca3119ac12c9a3a61b5ebb1ee0244650db39dc36743e355d35bf523b53ef992'")
    exec(compile(source, str(path), 'exec'), dict(__name__='__main__', __file__=str(path)))
