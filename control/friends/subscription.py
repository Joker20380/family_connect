"""Personal read-only paid projection, authenticated by the existing Friends proof."""
import hashlib

from device_identity.device import verify_transport_key_proof
from .access import Rejected
from . import paid_beta


class Unsupported(Exception):
    pass


class Unavailable(Exception):
    pass


def snapshot(database, device, now):
    database = paid_beta.transaction(database)
    if not paid_beta.schema_present(database):
        raise Unsupported()
    row = database.subscription(device)
    event = database.event(row['last_event_id'] if row else '')
    effective = paid_beta.effective_subscription_state(database, device, now)
    result = dict(schema=1, device=device, observed_at=now, cohort=row is not None,
                  subscription=None, event=None)
    if row is None:
        return result
    if effective is None:
        raise Unavailable()
    result['subscription'] = {name: row[name] for name in (
        'state', 'period_start', 'paid_until', 'grace_until', 'updated_at', 'version', 'last_event_id')}
    result['subscription'].update(effective_state=effective.state, paid_allow=effective.allowed,
                                  entitlement_until=effective.expires_at)
    if event is not None and event['device'] == device and event['result'] == 'APPLIED' and all(event[source] == row[target] for source, target in (
            ('event_id', 'last_event_id'), ('new_state', 'state'), ('period_start', 'period_start'),
            ('paid_until', 'paid_until'), ('grace_until', 'grace_until'),
            ('occurred_at', 'updated_at'), ('applied_at', 'updated_at'))):
        result['event'] = {name: event[name] for name in (
            'event_id', 'event_type', 'occurred_at', 'previous_state', 'new_state', 'result')}
    return result


def request(access, proof):
    try:
        device = verify_transport_key_proof(proof, expected_challenge=proof['challenge'])
    except (ValueError, KeyError, TypeError):
        raise Rejected() from None
    nonce = hashlib.sha256(proof['challenge'].encode()).hexdigest()
    failure = None
    with access.enrollment() as transaction:
        now = int(access.clock())
        challenge = transaction.challenge(nonce)
        row = transaction.device(device)
        invitation = transaction.device_invitation(device)
        if (challenge is None or challenge['used'] or challenge['expires'] <= now
                or challenge['purpose'] != 'subscription' or challenge['device'] != device
                or challenge['public'] != proof['public_identity'] or challenge['wg'] != proof['wireguard_public_key']
                or row is None or row['revoked'] or invitation is None or invitation['revoked']
                or row['public'] != proof['public_identity'] or row['wg'] != proof['wireguard_public_key']):
            raise Rejected()
        transaction.consume_challenge(nonce)
        try:
            with transaction.paid().projection() as database:
                result = snapshot(database, device, now)
        except Unsupported:
            failure = Unsupported()
        except Exception:
            failure = Unavailable()
    if failure is not None:
        raise failure
    return result
