"""Minimal same-recovery95 build, both Mux ALPNs, ordinary diagnostics."""

from prepare import ROOT, WORK, digest


def main():
    original=ROOT/'tests/fixtures/mesh_throughput_trace/build.py'
    assert digest(original)=='4ed782e6d77748d1cc0e7342c9d15d4486b5a9459b19018d623da929022e9a58'
    source=original.read_text()
    replacements={
        'ROOT = Path(__file__).resolve().parents[3]':'ROOT = Path('+repr(str(ROOT))+')',
        "WORK = Path(os.environ.get('MESH_TRACE_OUT', STATE / 'mesh-throughput-trace-20261019'))":'WORK = Path('+repr(str(WORK))+')',
        "version_code=89, version='0.1.18-beta89-mesh-trace'":"version_code=95, version='0.1.18-beta95-mux-profile'",
        "'-tags=fc_perf_diagnostic', ":'',
        "build_tags=['fc_perf_diagnostic']":'build_tags=[]',
        "actual_build_receipt='mesh-throughput-trace-20261019/build/receipt.json'":"actual_build_receipt='mux-profile-20261020/build/receipt.json'",
    }
    for old,new in replacements.items():
        assert source.count(old)==1,old
        source=source.replace(old,new)
    runner=WORK/'executed-build.py'
    with runner.open('x') as output:output.write(source)
    exec(compile(source,str(runner),'exec'),dict(__name__='__main__',__file__=str(runner)))


if __name__=='__main__':main()
