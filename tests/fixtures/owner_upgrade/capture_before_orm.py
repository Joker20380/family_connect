"""Opt-in OWNER admission; the directory must be pre-created and shared by all participants."""
from contextlib import contextmanager
from functools import lru_cache
import os

from control.capture_gate import Gate, GateError, external_operation


@lru_cache(maxsize=8)
def gate_for(directory):
    try:
        return Gate(directory)
    except OSError:
        raise GateError('CAPTURE_UNAVAILABLE') from None


def configured_gate():
    return gate_for(os.environ.get('FC_CONTROL_CAPTURE_GATE') or None)


@contextmanager
def operation():
    with configured_gate().operation() as admitted, external_operation():
        yield admitted
