import re
import base64
import json

from credential_renewal import canonical, digest, require
import gateway_set


CONTRACT = 'MESH_SAME_HOLDER_ONLINE_V1'
DELIVERY_SECONDS = 300 + 30 + 30 + 55 + 15 + 5
RPC_COUNT = 8


def window(rpc_seconds, schedule_seconds):
    require(type(rpc_seconds) is int and 1 <= rpc_seconds <= 120
            and type(schedule_seconds) is int and 0 <= schedule_seconds <= 900, 'ONLINE_TIMING_CONTRACT')
    return dict(rpc_seconds=rpc_seconds, schedule_seconds=schedule_seconds,
                delivery_seconds=DELIVERY_SECONDS,
                required_seconds=RPC_COUNT * rpc_seconds + schedule_seconds + DELIVERY_SECONDS)


def projection(snapshot):
    return {name: value for name, value in snapshot.items() if name != 'restricted_certificates'}


def eligible(validator, previous, now, timing, *, candidate=None, full_window=True):
    require(timing == window(timing['rpc_seconds'], timing['schedule_seconds']), 'ONLINE_TIMING_CONTRACT')
    old, trust, issuer, crl, leaf = validator.validate(canonical(previous), now)
    bound = min(trust['expires_at'], int(issuer.not_valid_after_utc.timestamp()),
                int(crl.next_update_utc.timestamp()), int(leaf.not_valid_after_utc.timestamp()))
    require(bound > now + (timing['required_seconds'] if full_window else 0), 'ONLINE_WINDOW_INSUFFICIENT')
    if candidate is not None:
        validator.transition(canonical(previous), canonical(candidate), now)
        require(candidate['authority'] == old['authority'] and candidate['grants'] == old['grants'],
                'ONLINE_BINDING_CHANGED')
        new = validator.validate(canonical(candidate), now)
        new_bound = min(new[1]['expires_at'], int(new[2].not_valid_after_utc.timestamp()),
                        int(new[3].next_update_utc.timestamp()), int(new[4].not_valid_after_utc.timestamp()))
        require(new_bound > bound and new_bound > now + timing['required_seconds'], 'ONLINE_SUCCESSOR_WINDOW')
    return bound


def validate_plan(node, plan, *, full_window=False, committed=False):
    require(set(plan['online']) == {'contract', 'timing'} and plan['online']['contract'] == CONTRACT,
            'ONLINE_CONTRACT')
    require(node.gateway_ids is not None and node.validator.all_activated, 'ONLINE_MEMBERSHIP_REQUIRED')
    node.validate(plan, recovery=True)
    for slot in ('NL', 'NL2'):
        selected = gateway_set.selected(plan, slot)
        now = plan['grant_plan']['issued_at'] if committed else int(node.clock())
        eligible(node.validator, selected['previous'], now, plan['online']['timing'],
                 candidate=selected['candidate'], full_window=full_window)
    require(not plan['grant_plan']['predecessors'], 'ONLINE_REVOCATION_FORBIDDEN')


def ready_receipt(slot, operation, plan, runtime):
    selected = gateway_set.selected(plan, slot)
    require(type(runtime) is dict and set(runtime) == {'contract', 'gateway', 'profile_sha256', 'instance'},
            'ONLINE_RUNTIME_RECEIPT')
    require(runtime['contract'] == CONTRACT and runtime['gateway'] == plan['gateway_ids'][slot]
            and all(type(runtime[name]) is str and re.fullmatch('[0-9a-f]{64}', runtime[name])
                    for name in ('instance', 'profile_sha256')),
            'ONLINE_RUNTIME_RECEIPT')
    return dict(slot=slot, operation_id=operation, plan_sha256=digest(canonical(plan)), runtime=runtime,
                crl_sha256=digest(selected['candidate']['crl'].encode()))


def directory_material(receipt, family, gateway, now):
    from control.friends.restricted import directory, timestamp_ns
    require(type(receipt) is dict and set(receipt) == {'payload', 'sha256'}, 'ONLINE_DIRECTORY_RECEIPT')
    raw = base64.b64decode(receipt['payload'], validate=True)
    require(digest(raw) == receipt['sha256'], 'ONLINE_DIRECTORY_RECEIPT')
    value = directory(raw, family, gateway, now_ns=now*1_000_000_000)
    return raw, timestamp_ns(value['issued_at']), timestamp_ns(value['expires_at'])


def publication_receipt(slot, operation, plan, receipt, now):
    require(type(receipt) is dict and set(receipt) ==
            {'slot','operation_id','plan_sha256','runtime','crl_sha256','directory'}, 'ONLINE_RUNTIME_RECEIPT')
    require({key:value for key,value in receipt.items() if key != 'directory'} ==
            ready_receipt(slot, operation, plan, receipt['runtime']), 'ONLINE_RUNTIME_RECEIPT')
    selected = gateway_set.selected(plan, slot)
    trust = json.loads(base64.b64decode(selected['candidate']['authority']['payload']))
    directory_material(receipt['directory'], trust['family'], plan['gateway_ids'][slot], now)
    return receipt
