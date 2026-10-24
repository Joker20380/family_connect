"""Real user-systemd FD-store fixture with synthetic material and no networking."""
import base64
import json
import os
from pathlib import Path
import subprocess
import sys
import time

root, unit = Path(sys.argv[1]), sys.argv[2]
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'clients/linux'))
from mesh_intent import Intent, Notifier
if sys.argv[3:] == ['auto']:
    from auto_intent import AutoIntent
    Intent = AutoIntent
elif sys.argv[3:]:
    raise ValueError('Unknown fixture contract')

count_path = root / 'starts'
count = int(count_path.read_text()) + 1 if count_path.exists() else 1
count_path.write_text(str(count))
deadline_path = root / 'deadline'
if not deadline_path.exists():
    deadline_path.write_text(str(time.time() + 60))
deadline = float(deadline_path.read_text())


def descriptor_count():
    return int(subprocess.check_output(['systemctl', '--user', 'show', unit,
        '--property=NFileDescriptorStore', '--value'], timeout=3).strip())


notifier = Notifier(unit, counter=descriptor_count, name=Intent.name)
owner = Intent(root / 'intent.json', os.getuid(), notifier, expected_owner=os.getuid())
material = dict(identity=base64.b64encode(b'x' * 64).decode(), anchor=base64.b64encode(b'a' * 32).decode(),
                wireguard_public=base64.b64encode(b'w' * 32).decode(), profile='P1')
if sys.argv[3:] == ['auto']:
    material.update(wireguard_private=base64.b64encode(b's' * 32).decode(), country='nl', normal_floors=[
        dict(payload=base64.b64encode(b'x' * 8192).decode(), signature=base64.b64encode(b's' * 64).decode())] * 2)
    material = dict(materials=material, preferred='tcp')
try:
    recovered = owner.recover()
    if count == 1:
        assert recovered is None
        owner.begin(material)
    elif count == 2:
        assert recovered == material
    elif count == 3:
        assert recovered is None and not owner.desired()
    else:
        raise RuntimeError('Unexpected service restart')
    record = dict(run=count, recovered=recovered is not None, desired=owner.desired(),
                  descriptors=descriptor_count(), recoveries=owner.read()['recoveries'])
    (root / ('stage' + str(count) + '.json')).write_text(json.dumps(record))
    notifier.ready()
    while count < 3 and time.time() < deadline:
        if count == 2 and (root / 'revoke').exists():
            owner.revoke()
            (root / 'revoked').write_text('committed')
        time.sleep(0.1)
finally:
    owner.close()
