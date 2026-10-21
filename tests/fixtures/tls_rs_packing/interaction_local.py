"""Bounded local tests, unique attempt directories, immutable per-attempt inputs."""
import json
import os
import shutil
import subprocess
import sys
from interaction_prepare import FIX, SOURCE, TOOLS, WORK, environment, inventory, save, write


def main():
    label = sys.argv[1]
    assert label.isalnum()
    target = WORK/('local-'+label)
    target.mkdir(mode=0o700, exist_ok=False)
    write(SOURCE/'tcpforward/lab_interaction_test.go',(FIX/'interaction/matrix_test.go').read_text())
    subprocess.run([TOOLS/'go/bin/gofmt','-w',SOURCE/'tcpforward/lab_interaction_test.go'],check=True)
    env = environment()
    env.update(FC_INTERACTION_LOCAL='1',FC_INTERACTION_OUTPUT=str(target))
    save(target/'inputs.json',dict(inventory=inventory(SOURCE),model='mux-credit measured delay156345875ns each way,8KiB/2ms original proxy; byte-domain faults first transmission overlaps [64KiB+128KiB*k,80KiB+128KiB*k); reorder crossing32KiB with next; ciphertext includes framing, not exact application-loss equivalence',local_source_bulk=6*1024**2,network_source_reserved=0))
    with (target/'tests.log').open('x') as output:
        result=subprocess.run([TOOLS/'go/bin/go','test','-p=1','-race','-tags=fc_perf_diagnostic','-run','TestInteractionMatrix','-v','-count=1','-timeout=360s','./tcpforward'],cwd=SOURCE,env=env,stdout=output,stderr=subprocess.STDOUT,timeout=400)
    save(target/'result.json',dict(exit=result.returncode))
    print(json.dumps(dict(label=label,exit=result.returncode)),flush=True)
    raise SystemExit(result.returncode)


if __name__ == '__main__':
    main()
