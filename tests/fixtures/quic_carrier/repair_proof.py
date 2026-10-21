import runpy
from lab import *
from proof_snapshot import remote_drain

def local_read(host,source,timeout):
    return subprocess.check_output([sys.executable,'-c',source],timeout=timeout)
for phase in ['AN','QS','QN1']:
    observed=remote_drain(local_read,'unused',str(WORK/phase))
    expected=json.loads((WORK/phase/'two-end-proof.json').read_text())['client']
    assert observed==[expected]
shutil.copy2(WORK/'build.json',WORK/'build-v2-startgate.json')
shutil.copy2(WORK/'run_phase.py',WORK/'run_phase.v3.py')
runpy.run_path(str(FIX/'operator_prepare.py'))
manifest=json.loads((WORK/'build.json').read_text())
manifest['operator_sha256']=digest(WORK/'run_phase.py')
manifest['proof_snapshot_sha256']=digest(WORK/'proof_snapshot.py')
write(WORK/'build.json',json.dumps(manifest,indent=2)+'\n')
assert inventory(SOURCE)==manifest['source_inventory']
save(WORK/'controller-proof-repair.json',dict(cause='QN1 all17 bodies and receiver receipts verified; blocking whole remote snapshot14MiB delayed finish past25s QUIC idle and180s phase deadline',outcome='post-delivery completion failure, not download failure; not clean speed acceptance',operator_sha256=manifest['operator_sha256'],before=digest(WORK/'run_phase.v3.py'),bounded_proof=manifest['proof_snapshot_sha256'],local_tests=['AN','QS','QN1'],change='select only complete p_drained record remotely, max32MiB input/4MiB selected line/12s command; applies to all modes; full evidence fetched after shutdown',data_path_unchanged=True,next='only remaining QN2/A2; no QN1 rerun or expansion'))
