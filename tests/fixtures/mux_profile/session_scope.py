"""Local measurement attribution; raw gateway capture retains other peers."""

import re


def select_session(records, scope, now=None):
    assert re.fullmatch('[0-9a-f]{64}', scope['session_tag'])
    assert (scope['profile'], scope['window']) in (('LEGACY64', 65536), ('CREDIT128', 131072))
    selected = [record for record in records if record['session_tag'] == scope['session_tag']]
    assert selected, 'OWNER_SESSION_MISSING_NO_BULK'
    assert all(record['performance']['Mux']['Profile'] == scope['profile'] and
               record['performance']['Mux']['Window'] == scope['window'] for record in selected), 'OWNER_PROFILE_CHANGED_STOP'
    if now is not None:
        assert -2 <= now - selected[-1]['observed_epoch'] <= 8, 'OWNER_SESSION_STALE_STOP'
    return selected
