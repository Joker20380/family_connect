from dataclasses import replace
from datetime import datetime
import importlib.util
from pathlib import Path
import sys

import pytest


spec = importlib.util.spec_from_file_location('timing_preflight', Path(__file__).with_name('timing_preflight.py'))
timing = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = timing
spec.loader.exec_module(timing)


def instant(value):
    return int(datetime.fromisoformat('2026-10-18T' + value + '+00:00').timestamp())


def fixture():
    return timing.Inputs(now=instant('17:40:00'), start=instant('17:45:00'),
        publication_not_before=instant('18:29:27'), target_cycle=instant('18:30:08'),
        loaded_material_expiry=instant('19:59:27'), scope_expiry=instant('23:00:00'),
        operation='synthetic-attempt-03', used_operations=('synthetic-attempt-01', 'synthetic-attempt-02'),
        baseline_generation='synthetic-baseline', observed_generation='synthetic-baseline')


def actual(plan_value):
    return dict(now=instant('18:46:00'), canary_issued=instant('17:46:00'),
        canary_expiry=plan_value['assumed_canary_expiry'], return_issued=instant('18:31:00'),
        return_expiry=instant('22:30:00'), owner_floor_issued=instant('15:59:45'),
        actual_chain_expiry=instant('19:59:27'), production_matches_return=True,
        canary_credentials_compatible=True, fence_captured_before_return=True, native_validated=True)


def test_previous_failed_combination_rejected_before_launch():
    inputs = replace(fixture(), now=instant('17:02:37'), start=instant('17:02:37'))
    with pytest.raises(timing.Rejected, match='START_OUTSIDE_WINDOW'):
        timing.plan(inputs)


def test_next_generation_tick_before_eligibility_is_not_publication():
    inputs = replace(fixture(),now=instant('20:10:00'),start=instant('20:10:00'),
        loaded_material_expiry=instant('22:29:32'),publication_not_before=instant('20:59:32'),
        target_cycle=instant('21:14:28'))
    with pytest.raises(timing.Rejected,match='NO_TIMING_INTERSECTION'):
        timing.plan(inputs)


def test_next_generation_window_requires_actual_timer_alignment():
    inputs = replace(fixture(),now=instant('20:10:00'),start=instant('20:10:00'),
        loaded_material_expiry=instant('22:29:32'),publication_not_before=instant('20:59:32'),
        target_cycle=instant('20:59:38'))
    result=timing.plan(inputs)
    assert result['earliest_start']==instant('20:05:38')
    assert result['latest_start']==instant('20:19:31')


def test_feasible_time_intersection_is_not_live_acceptance():
    plan_value = timing.plan(fixture())
    assert plan_value['earliest_start'] == instant('17:36:08')
    assert plan_value['latest_start'] == instant('17:49:26')
    assert plan_value['validation_cutoff'] == instant('18:59:00')
    assert plan_value['latest_activation'] == instant('19:04:00')
    assert plan_value['return_cleanup_deadline'] == instant('19:34:00')
    assert timing.activation(plan_value, **actual(plan_value)).startswith('ACTUAL_TIMING_GATE_PASS')


@pytest.mark.parametrize('change,reason', [
    ({'now': instant('18:59:01')}, 'RETURN_VALIDATION_TOO_LATE'),
    ({'canary_expiry': instant('19:33:00')}, 'MATERIAL_HEADROOM_LOST'),
    ({'actual_chain_expiry': instant('19:20:00')}, 'MATERIAL_HEADROOM_LOST'),
    ({'owner_floor_issued': instant('18:31:00')}, 'DIRECTORY_FLOOR_CONFLICT'),
    ({'return_issued': instant('17:45:00')}, 'EARLY_ROTATION_REPLAN'),
    ({'return_issued': instant('17:47:00')}, 'EARLY_ROTATION_REPLAN'),
    ({'production_matches_return': False}, 'RETURN_NOT_CURRENT_PRODUCTION'),
    ({'canary_credentials_compatible': False}, 'POST_ROTATION_CREDENTIALS_NOT_VERIFIED'),
    ({'fence_captured_before_return': False}, 'OWNER_FENCE_NOT_VERIFIED'),
    ({'native_validated': False}, 'ACTUAL_NATIVE_TRANSITION_NOT_VERIFIED'),
])
def test_actual_events_close_gate_safely(change, reason):
    plan_value = timing.plan(fixture())
    values = dict(actual(plan_value), **change)
    with pytest.raises(timing.Rejected, match=reason):
        timing.activation(plan_value, **values)


def test_early_rotation_invalidates_prelaunch_plan():
    with pytest.raises(timing.Rejected, match='BASELINE_ROTATED_REPLAN'):
        timing.plan(replace(fixture(), observed_generation='new-rotation'))


@pytest.mark.parametrize('operation', fixture().used_operations)
def test_cleaned_ids_never_reused(operation):
    with pytest.raises(timing.Rejected, match='OPERATION_ID_ALREADY_USED'):
        timing.plan(replace(fixture(), operation=operation))


def test_no_window_if_material_headroom_is_insufficient():
    with pytest.raises(timing.Rejected, match='NO_TIMING_INTERSECTION'):
        timing.plan(replace(fixture(), loaded_material_expiry=instant('19:10:00')))


def test_timer_before_policy_eligibility_is_not_a_publication():
    with pytest.raises(timing.Rejected, match='CYCLE_NOT_ELIGIBLE'):
        timing.plan(replace(fixture(), target_cycle=instant('17:44:27')))


def test_clock_is_input_only_and_prior_start_cannot_be_extended():
    with pytest.raises(timing.Rejected, match='START_IN_PAST'):
        timing.plan(replace(fixture(), now=instant('17:46:00')))


def test_fixed_closed_operator_cannot_launch_new_operation():
    with pytest.raises(timing.Rejected, match='PREPARER_BOUND_TO_DIFFERENT_OPERATION'):
        timing.launch_gate(requested_operation='new-03', preparer_operation='cleaned-01', existing_handoff_rows=1)


def test_changing_only_operation_constant_does_not_make_slot_reusable():
    with pytest.raises(timing.Rejected, match='PREPARE_REQUIRES_EMPTY_SLOT'):
        timing.launch_gate(requested_operation='new-03', preparer_operation='new-03', existing_handoff_rows=1)


def test_empty_first_operation_preflight_is_not_return_gate():
    assert timing.launch_gate(requested_operation='new-03', preparer_operation='new-03',
                              existing_handoff_rows=0).endswith('NOT_ACTUAL_RETURN_GATE')
