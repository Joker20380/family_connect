import hashlib
import json
from pathlib import Path
import shutil


root = Path(__file__).resolve().parent
retained = root.parent/'gateway-transport-progress-burst-candidate-1'
receipt = json.loads((retained/'build/receipt.json').read_text())
assert receipt['binary_sha256'] == 'a537257162348afc35b1ebc08755d8c5dc1cd90e74c49e3987fb3eb81885e61f'
origin = retained/'source/carrier'
inventory = {str(filename.relative_to(origin)): hashlib.sha256(filename.read_bytes()).hexdigest()
             for filename in sorted(origin.rglob('*')) if filename.is_file()}
manifest = json.loads((root.parent/'owner-cumulative-client-acceptance-1-resume/review-publication/research/gateway-transport-progress-20261016/source-manifest.json').read_text())
assert inventory == manifest['candidate_files']
assert manifest['candidate_inventory_sha256'] == receipt['source_inventory']
for variant in ('baseline', 'candidate'):
    destination = root/('gateway-'+variant)/'carrier'
    shutil.copytree(origin, destination)
    shutil.copyfile(root/'gateway_stack_test.go', destination/'telemost/full_stack_test.go')
    shutil.copyfile(root/'baseline/carrier/telemost/full_stack_credentials_test.go', destination/'telemost/full_stack_credentials_test.go')
    shutil.copyfile(root/'fixture_dns.go', destination/'tcpforward/fixture_dns.go')
    if variant == 'candidate':
        shutil.copyfile(root/'candidate/carrier/reliablestream/engine.go', destination/'reliablestream/engine.go')
(root/'gateway-input-files.json').write_text(json.dumps(inventory,sort_keys=True,indent=2)+'\n')
