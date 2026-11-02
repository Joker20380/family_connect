"""Public synthetic vectors; the deterministic signing seed is never a release key."""
import base64
import copy
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


def build():
    legacy = json.loads((Path(__file__).parent / 'vectors/friends-multinode-v2.json').read_text())
    signing = Ed25519PrivateKey.from_private_bytes(bytes(range(32)))

    def sign(payload):
        raw = json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()
        return dict(payload=base64.b64encode(raw).decode(),
                    signature=base64.b64encode(signing.sign(b'family-connect/invited-test/v1\0' + raw)).decode())

    old = [json.loads(base64.b64decode(case['reply']['catalog']['payload'])) for case in legacy['cases']]
    gateways = [dict(next(item for item in payload['gateways'] if item['country'] == 'nl'), gateway_id=target)
                for payload, target in zip(old, ('nl-amsterdam-1', 'nl-amsterdam-2'))]
    payload = dict(schema=3, sequence=1, access='invite-test', gateways=gateways)
    reply = copy.deepcopy(legacy['cases'][0]['reply'])
    reply['catalog'] = sign(payload)
    cases = []
    for gateway in gateways:
        cases.append(dict(name=gateway['gateway_id'], target=gateway['gateway_id'], valid=True,
                          floor=0, reply=dict(reply, gateway_id=gateway['gateway_id'])))
    cases.append(dict(cases[0], name='wrong-selection', target='nl-amsterdam-2', valid=False))
    cases.append(dict(cases[0], name='stale', floor=2, valid=False))
    cases.append(dict(cases[0], name='same-sequence-conflict', floor=1, previous_hash='0' * 64, valid=False))
    for damage in ('same-host', 'duplicate-id', 'wrong-country', 'unknown-id', 'endpoint-mismatch', 'unknown-schema'):
        changed = copy.deepcopy(payload)
        if damage == 'same-host':
            changed['gateways'][1] = dict(changed['gateways'][0], gateway_id='nl-amsterdam-2')
        elif damage == 'duplicate-id':
            changed['gateways'][1]['gateway_id'] = 'nl-amsterdam-1'
        elif damage == 'wrong-country':
            changed['gateways'][0]['country'] = 'ru'
        elif damage == 'unknown-id':
            changed['gateways'][0]['gateway_id'] = 'nl-untrusted'
        elif damage == 'endpoint-mismatch':
            changed['gateways'][0]['tcp']['server'] = '192.0.2.99'
        else:
            changed['schema'] = 4
        cases.append(dict(cases[0], name=damage, valid=False,
                          reply=dict(cases[0]['reply'], catalog=sign(changed))))
    return dict(schema=1, anchor=base64.b64encode(signing.public_key().public_bytes_raw()).decode(),
                device=legacy['device'], wireguard_key=legacy['wireguard_key'], cases=cases,
                legacy_catalogs=[sign(value) for value in old])
