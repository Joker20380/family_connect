import hashlib
import json
from pathlib import Path
import shutil


root = Path(__file__).resolve().parent
state = root.parent
result = json.loads((state / 'reliable-full-stack-1/results.json').read_text())
assert result['result'] == 'PASS_LOCAL_FULL_STACK' and result['scenarios'] == 36
gateway = json.loads((state / 'reliable-full-stack-1/gateway-results.json').read_text())
assert gateway['result'] == 'PASS_EXACT_PEER_SOURCES' and gateway['scenarios'] == 24
recovery = state / 'cutover-recovery-1'
inventory = json.loads((recovery / 'build/cumulative-source.json').read_text())
assert inventory['source_delta_sha256'] == 'ea9312d013aac02a190a06b8ad9091e1245ef63a994db6618054dde27739c0d4'
for name, checksum in inventory['files'].items():
    assert hashlib.sha256((recovery / 'source' / name).read_bytes()).hexdigest() == checksum
shutil.copytree(recovery / 'source', root / 'source')
for name in ('engine.go', 'fast_recovery_test.go', 'throughput_comparison_test.go'):
    shutil.copyfile(state / 'reliable-fast-recovery-1/candidate/carrier/reliablestream' / name,
                    root / 'source/carrier/reliablestream' / name)
shutil.copytree(state/'gateway-transport-progress-burst-candidate-1/source', root/'gateway-source')
shutil.copyfile(root/'source/carrier/reliablestream/engine.go', root/'gateway-source/carrier/reliablestream/engine.go')
