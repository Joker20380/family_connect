from copy import deepcopy

import pytest

from scripts.paid_postgres_rehearsal import require_current_restore


@pytest.fixture
def current():
    return dict(paid_beta_events=[dict(event_id='synthetic-payment'), dict(event_id='synthetic-revoke')],
        paid_beta_subscriptions=[dict(version=2, state='revoked')], challenges=[dict(used=1)],
        device_support=[dict(support_id='synthetic-only')], extra_future_table=[dict(revision=1)])


def test_exact_restore_is_accepted(current):
    require_current_restore(current, deepcopy(current))


@pytest.mark.parametrize('mutation', ['old-ledger', 'unrevoke', 'proof-replay', 'binding', 'omitted-table', 'added-row'])
def test_partial_or_stale_restore_is_refused(current, mutation):
    candidate = deepcopy(current)
    if mutation == 'old-ledger':
        candidate['paid_beta_events'].pop()
    elif mutation == 'unrevoke':
        candidate['paid_beta_subscriptions'][0]['state'] = 'active'
    elif mutation == 'proof-replay':
        candidate['challenges'][0]['used'] = 0
    elif mutation == 'binding':
        candidate['device_support'][0]['support_id'] = 'other-synthetic'
    elif mutation == 'omitted-table':
        del candidate['extra_future_table']
    else:
        candidate['extra_future_table'].append(dict(revision=2))
    with pytest.raises(ValueError, match='RESTORE_WOULD_LOSE_OR_CHANGE_ACKNOWLEDGED_STATE'):
        require_current_restore(current, candidate)
