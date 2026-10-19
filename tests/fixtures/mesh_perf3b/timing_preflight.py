"""Offline timing gate for the existing two-hour owner diagnostic operation."""

from dataclasses import dataclass


LIFETIME = 7200
INITIAL_HEADROOM = 7800
DIRECTORY_MARGIN = 600
ACTIVATION_HEADROOM = 1800
STARTUP_EXPIRY_RESERVE = 60
READY_AND_FENCE_BUDGET = 600
PUBLICATION_BUDGET = 900
VALIDATION_BUDGET = 300
ACTIVATION_RESERVE = 300
HANDOFF_BUDGET = 300
MEASUREMENT_BUDGET = 900
RETURN_AND_CLEANUP_BUDGET = 600


class Rejected(ValueError):
    pass


def require(condition, reason):
    if not condition:
        raise Rejected(reason)


@dataclass(frozen=True)
class Inputs:
    now: int
    start: int
    publication_not_before: int
    target_cycle: int
    loaded_material_expiry: int
    scope_expiry: int
    operation: str
    used_operations: tuple
    baseline_generation: str
    observed_generation: str


def plan(inputs):
    require(inputs.operation not in inputs.used_operations, 'OPERATION_ID_ALREADY_USED')
    require(inputs.baseline_generation == inputs.observed_generation, 'BASELINE_ROTATED_REPLAN')
    require(inputs.target_cycle >= inputs.publication_not_before, 'CYCLE_NOT_ELIGIBLE')
    require(inputs.now <= inputs.start, 'START_IN_PAST')
    latest_publication = inputs.target_cycle + PUBLICATION_BUDGET
    planned_validation = latest_publication + VALIDATION_BUDGET
    earliest_start = (planned_validation + ACTIVATION_RESERVE + ACTIVATION_HEADROOM
                      + DIRECTORY_MARGIN + STARTUP_EXPIRY_RESERVE - LIFETIME)
    latest_start = min(inputs.publication_not_before - READY_AND_FENCE_BUDGET,
                       inputs.loaded_material_expiry - INITIAL_HEADROOM - 1,
                       inputs.scope_expiry - INITIAL_HEADROOM - 1)
    require(earliest_start <= latest_start, 'NO_TIMING_INTERSECTION')
    require(earliest_start <= inputs.start <= latest_start, 'START_OUTSIDE_WINDOW')
    guard_end = inputs.start + LIFETIME
    assumed_expiry = guard_end - STARTUP_EXPIRY_RESERVE
    operation_deadline = assumed_expiry - DIRECTORY_MARGIN
    latest_activation = operation_deadline - ACTIVATION_HEADROOM
    validation_cutoff = latest_activation - ACTIVATION_RESERVE
    require(planned_validation <= validation_cutoff, 'PUBLICATION_MISSES_VALIDATION_CUTOFF')
    require(HANDOFF_BUDGET + MEASUREMENT_BUDGET + RETURN_AND_CLEANUP_BUDGET
            <= ACTIVATION_HEADROOM, 'EXECUTION_BUDGET_TOO_LONG')
    return dict(earliest_start=earliest_start, latest_start=latest_start,
                start=inputs.start, target_cycle=inputs.target_cycle,
                publication_not_before=inputs.publication_not_before,
                latest_publication=validation_cutoff - VALIDATION_BUDGET,
                validation_cutoff=validation_cutoff, latest_activation=latest_activation,
                measurement_finish=latest_activation + HANDOFF_BUDGET + MEASUREMENT_BUDGET,
                return_cleanup_deadline=operation_deadline, guard_end=guard_end,
                assumed_canary_expiry=assumed_expiry,
                loaded_material_expiry=inputs.loaded_material_expiry,
                scope_expiry=inputs.scope_expiry,
                baseline_generation=inputs.baseline_generation,
                result='TIMING_ONLY_PASS_NOT_LAUNCH_AUTHORIZATION')


def activation(plan_value, *, now, canary_issued, canary_expiry, return_issued,
               return_expiry, owner_floor_issued, actual_chain_expiry,
               production_matches_return, canary_credentials_compatible,
               fence_captured_before_return, native_validated):
    require(now <= plan_value['validation_cutoff'], 'RETURN_VALIDATION_TOO_LATE')
    require(canary_issued < plan_value['publication_not_before'] <= return_issued, 'EARLY_ROTATION_REPLAN')
    require(owner_floor_issued <= canary_issued < return_issued, 'DIRECTORY_FLOOR_CONFLICT')
    require(min(canary_expiry, return_expiry, actual_chain_expiry, plan_value['guard_end'])
            >= plan_value['return_cleanup_deadline'] + DIRECTORY_MARGIN, 'MATERIAL_HEADROOM_LOST')
    require(production_matches_return, 'RETURN_NOT_CURRENT_PRODUCTION')
    require(canary_credentials_compatible, 'POST_ROTATION_CREDENTIALS_NOT_VERIFIED')
    require(fence_captured_before_return, 'OWNER_FENCE_NOT_VERIFIED')
    require(native_validated, 'ACTUAL_NATIVE_TRANSITION_NOT_VERIFIED')
    return 'ACTUAL_TIMING_GATE_PASS_REQUIRES_EXISTING_ARM_VALIDATOR'


def launch_gate(*, requested_operation, preparer_operation, existing_handoff_rows):
    require(requested_operation == preparer_operation, 'PREPARER_BOUND_TO_DIFFERENT_OPERATION')
    require(existing_handoff_rows == 0, 'PREPARE_REQUIRES_EMPTY_SLOT_NO_RETIRED_ROW_ALLOCATION')
    return 'OPERATOR_ALLOCATION_PREFLIGHT_PASS_NOT_ACTUAL_RETURN_GATE'
