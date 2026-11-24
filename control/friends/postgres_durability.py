"""Refuse a successful application acknowledgement after a warning during COMMIT."""
import psycopg


class ReplicationAcknowledgementUncertain(RuntimeError):
    """The local commit may exist; reconcile its original operation before retrying."""


class DurableConnection(psycopg.Connection):
    def __init__(self, *arguments, **options):
        super().__init__(*arguments, **options)
        self._committing = False
        self._commit_warning = False
        self.add_notice_handler(self._observe_commit)

    def _observe_commit(self, diagnostic):
        if self._committing and diagnostic.severity_nonlocalized == 'WARNING':
            self._commit_warning = True

    def commit(self):
        self._commit_warning = False
        self._committing = True
        try:
            super().commit()
        finally:
            self._committing = False
        if self._commit_warning:
            self.close()
            raise ReplicationAcknowledgementUncertain(
                'Commit acknowledgement is uncertain; reconcile the original operation, do not replay it')
