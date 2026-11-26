"""Opt-in OWNER admission; the directory must be pre-created and shared by all participants."""
from contextlib import contextmanager
from functools import lru_cache
import os
from pathlib import Path
import sys
import threading

from control.capture_gate import CURRENT, Gate, GateError, external_operation, require


MOUNTED_GATE = Path('/run/family-connect-capture')


class Admission:
    def __init__(self, admitted):
        self.operation = admitted
        self.process = os.getpid()
        self.thread = threading.get_ident()
        self.active = True


@lru_cache(maxsize=8)
def gate_for(directory):
    try:
        return Gate(directory)
    except OSError:
        raise GateError('CAPTURE_UNAVAILABLE') from None


def configured_gate():
    directory = os.environ.get('FC_CONTROL_CAPTURE_GATE') or None
    if os.path.lexists(MOUNTED_GATE):
        require(directory in (None, str(MOUNTED_GATE)), 'CAPTURE_GATE_CONFIGURATION_CHANGED')
        directory = str(MOUNTED_GATE)
    return gate_for(directory)


def database_admission():
    gate = configured_gate()
    if gate.directory is None:
        return None
    scope = getattr(CURRENT.get(), 'owner_database_scope', None)
    require(scope is not None and scope.active and scope.process == os.getpid() and
            scope.thread == threading.get_ident() and CURRENT.get() is scope.operation and
            scope.operation.gate.pins == gate.pins, 'CAPTURE_DATABASE_ADMISSION_REQUIRED')
    with gate.opened():
        return scope


def close_databases(admitted):
    configuration = sys.modules.get('django.conf')
    if configuration is None or not configuration.settings.configured:
        return
    from django.db import connections
    unsettled = False
    for database in connections.all(initialized_only=True):
        if database.connection is None:
            continue
        try:
            from psycopg.pq import TransactionStatus
            status = database.connection.info.transaction_status
            if database.in_atomic_block or not database.autocommit or status != TransactionStatus.IDLE:
                admitted.uncertain()
                unsettled = True
        except BaseException:
            admitted.uncertain()
            raise
        finally:
            try:
                database.close()
            except BaseException:
                admitted.uncertain()
                raise
    require(not unsettled, 'CAPTURE_DATABASE_TRANSACTION_UNSETTLED')


@contextmanager
def operation():
    with configured_gate().operation() as admitted, external_operation():
        if admitted.gate.directory is None:
            yield admitted
            return
        previous = getattr(admitted, 'owner_database_scope', None)
        if previous is not None:
            database_admission()
            yield admitted
            return
        scope = Admission(admitted)
        admitted.owner_database_scope = scope
        try:
            yield admitted
        finally:
            try:
                close_databases(admitted)
            finally:
                scope.active = False
