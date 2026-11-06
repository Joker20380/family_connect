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
    if not paid_beta.schema_present(database):
        raise Unsupported()
    row = database.execute('SELECT state,period_start,paid_until,grace_until,updated_at,version,last_event_id '
                           'FROM paid_beta_subscriptions WHERE device=?', (device,)).fetchone()
    event = database.execute('SELECT event_id,event_type,occurred_at,previous_state,new_state,result,'
                             'period_start,paid_until,grace_until,applied_at FROM paid_beta_events '
                             'WHERE device=? AND event_id=? AND result=?',
                             (device, row['last_event_id'] if row else '', 'APPLIED')).fetchone()
    effective = paid_beta.effective_subscription_state(database, device, now)
    result = dict(schema=1, device=device, observed_at=now, cohort=row is not None,
                  subscription=None, event=None)
    if row is None:
        return result
    if effective is None:
        raise Unavailable()
    result['subscription'] = dict(row)
    result['subscription'].update(effective_state=effective.state, paid_allow=effective.allowed,
                                  entitlement_until=effective.expires_at)
    if event is not None and all(event[source] == row[target] for source, target in (
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
    with access.db() as database:
        now = int(access.clock())
        challenge = database.execute('SELECT device,public,wg,purpose,expires,used FROM challenges WHERE nonce=?', (nonce,)).fetchone()
        row = database.execute('SELECT d.public,d.wg,d.revoked,i.revoked AS invite_revoked FROM devices d '
                               'JOIN invites i ON i.device=d.device WHERE d.device=?', (device,)).fetchone()
        if (challenge is None or challenge['used'] or challenge['expires'] <= now
                or challenge['purpose'] != 'subscription' or challenge['device'] != device
                or challenge['public'] != proof['public_identity'] or challenge['wg'] != proof['wireguard_public_key']
                or row is None or row['revoked'] or row['invite_revoked']
                or row['public'] != proof['public_identity'] or row['wg'] != proof['wireguard_public_key']):
            raise Rejected()
        database.execute('UPDATE challenges SET used=1 WHERE nonce=?', (nonce,))
        try:
            result = snapshot(database, device, now)
        except Unsupported:
            failure = Unsupported()
        except Exception:
            failure = Unavailable()
    if failure is not None:
        raise failure
    return result
