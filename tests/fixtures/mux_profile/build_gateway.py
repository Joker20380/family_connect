"""Build the compatible b9-descended gateway, preserving seed1011 sources."""

import json
import subprocess

from prepare import WORK, BASE, TOOLS, environment, digest


def main():
    source=WORK/'gateway-source/carrier'
    for name in ('main.go','seed_recovery.go','seed_recovery_test.go'):
        assert digest(source/'cmd/bootstrap-broker'/name)==digest(BASE/'gateway-source/carrier/cmd/bootstrap-broker'/name)
    binary=WORK/'gateway-negotiated';assert not binary.exists()
    with (WORK/'gateway-build.log').open('x') as output:
        subprocess.run([TOOLS/'go/bin/go','build','-p=1','-trimpath','-buildvcs=false','-tags=fc_perf_diagnostic','-o',binary,'./cmd/bootstrap-broker'],
                       cwd=source,env=environment(),stdout=output,stderr=subprocess.STDOUT,check=True)
    files={str(path.relative_to(source)):digest(path) for path in source.rglob('*') if path.is_file()}
    result=dict(sha256=digest(binary),files=files,bootstrap1011_preserved=True,full_packet_export=False,
                default_profile='LEGACY64',profiles=['LEGACY64','CREDIT128'],counters_default_off=True)
    (WORK/'negotiated-build.json').write_text(json.dumps(result,indent=2))
    print('COMPATIBLE_GATEWAY',result['sha256'])


if __name__=='__main__':main()
