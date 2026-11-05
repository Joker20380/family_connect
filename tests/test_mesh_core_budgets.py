import datetime

import pytest

from mesh_core_budget import delivery_observed, require_delivery_window, require_seed_span


@pytest.mark.parametrize('duration,lifetime,rotation', [(3600, 3600, 0), (18000, 14400, 3600)])
def test_supported_single_overlap_span(duration, lifetime, rotation):
    require_seed_span(duration, lifetime, rotation)


@pytest.mark.parametrize('duration', [25200, 28800])
def test_long_harness_cannot_outlive_both_real_seeds(duration):
    with pytest.raises(AssertionError, match='SEED_MANAGER_SINGLE_ROTATION_LIMIT'):
        require_seed_span(duration, 14400, 3600)


def observations(deadline):
    security = datetime.datetime.fromtimestamp(deadline, datetime.timezone.utc).isoformat()
    return {slot: dict(last=dict(security=security)) for slot in ('NL', 'NL2')}


def test_actual_first_renewal_bound_cannot_reach_next_eligibility():
    with pytest.raises(AssertionError, match='SEED_CAPPED_DELIVERY_WINDOW_TOO_SHORT'):
        require_delivery_window(observations(1793929259), 1793929320)


def test_delivery_window_preserves_ssh120_and_scheduling_lateness():
    require_delivery_window(observations(5000), 3605)
    with pytest.raises(AssertionError, match='SEED_CAPPED_DELIVERY_WINDOW_TOO_SHORT'):
        require_delivery_window(observations(5000), 3605, lateness=1)


def test_both_participants_need_the_window():
    nodes = observations(5000)
    nodes['NL2'] = observations(4900)['NL2']
    with pytest.raises(AssertionError, match='NL2: SEED_CAPPED_DELIVERY_WINDOW_TOO_SHORT'):
        require_delivery_window(nodes, 3605)


def test_continuous_rotation_requires_bounded_overlap_and_explicit_opt_in():
    require_seed_span(28800, 14400, 7200, continuous=True)
    with pytest.raises(AssertionError, match='SEED_ROTATION_OVERLAP_NOT_BOUNDED'):
        require_seed_span(28800, 14400, 3600, continuous=True)
    with pytest.raises(AssertionError, match='SEED_MANAGER_SINGLE_ROTATION_LIMIT'):
        require_seed_span(28800, 14400, 7200)


def test_commit_callback_does_not_replace_sampled_runtime_generation():
    nodes = {slot: dict(committed=1, first=dict(generation=0), last=dict(generation=0)) for slot in ('NL', 'NL2')}
    assert not delivery_observed(nodes, 1)
    nodes['NL']['last']['generation'] = 1
    assert not delivery_observed(nodes, 1)
    nodes['NL2']['last']['generation'] = 1
    assert delivery_observed(nodes, 1)
    assert not delivery_observed(nodes, 2)
