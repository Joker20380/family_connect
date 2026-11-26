from django.db.backends.postgresql.base import DatabaseWrapper as PostgreSQLWrapper

from control.capture_gate import external_operation, require
from fc_control_plane.capture import database_admission


class GuardedCursor:
    def __init__(self, cursor):
        self.cursor = cursor

    def __getattr__(self, name):
        attribute = getattr(self.cursor, name)
        if not callable(attribute) or name == 'close':
            return attribute

        def guarded(*arguments, **keywords):
            with external_operation():
                scope = database_admission()
                require(scope is None or name not in ('copy', 'stream'), 'CAPTURE_LAZY_DRIVER_UNSUPPORTED')
                return attribute(*arguments, **keywords)

        return guarded

    def __iter__(self):
        return self

    def __next__(self):
        scope = database_admission()
        try:
            return next(self.cursor)
        except StopIteration:
            raise
        except BaseException:
            if scope is not None:
                scope.operation.uncertain()
            raise

    def __enter__(self):
        database_admission()
        return self

    def __exit__(self, *arguments):
        self.cursor.close()


class DatabaseWrapper(PostgreSQLWrapper):
    def get_new_connection(self, parameters):
        with external_operation():
            database_admission()
            return super().get_new_connection(parameters)

    def create_cursor(self, name=None):
        database_admission()
        return GuardedCursor(super().create_cursor(name))

    def _commit(self):
        with external_operation():
            database_admission()
            return super()._commit()

    def _set_autocommit(self, autocommit):
        with external_operation():
            database_admission()
            return super()._set_autocommit(autocommit)
