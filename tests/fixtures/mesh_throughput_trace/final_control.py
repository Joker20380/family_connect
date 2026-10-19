"""Verify original gateway plus in-place beta89 identity and one ordinary HTTPS probe."""

import hashlib

from rollout import PREVIOUS, ROOT, WORK


if __name__ == '__main__':
    path = PREVIOUS / 'final_control.py'
    assert hashlib.sha256(path.read_bytes()).hexdigest() == 'a90702377d08d4be05b06aca182e7121e2a3055efe2a0ab076964b0a6ba80508'
    probe = ROOT / 'state-client-build/beta87-product-fix-20261019/physical_probe88.py'
    assert hashlib.sha256(probe.read_bytes()).hexdigest() == 'd06aa28bbe8365ab3f3c6df244d1a935b3bf340c64407e0c1e3813388154da9d'
    source = path.read_text().replace("response=subprocess.run", "remote=remote.replace(\"version_code')=88\", \"version_code')=89\").replace('beta88_readiness','beta89_readiness')\nresponse=subprocess.run", 1)
    source = source.replace("identity['beta88_readiness']", "identity['beta89_readiness']")
    source = source.replace("[1]=='88'", "[1]=='89'")
    source = source.replace('968a61724f4e71ac0335e330960eb9b54e5ede59bae81df0b6e8499e4ce6c2ce',
                            'b6ab744740726676dca8f51a73460db82b435c719828af14e6564c764ed11856')
    source = source.replace('beta88-throughput-return', 'mesh-throughput-trace-final')
    exec(compile(source, str(WORK / 'final_control.py'), 'exec'), dict(__name__='__main__', __file__=str(WORK / 'final_control.py')))
