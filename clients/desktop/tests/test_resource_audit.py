import os
import socket
import threading

import pytest

from resource_audit import ResourceAudit, descriptor_snapshot


def test_foreign_finalizer_does_not_own_test_invariant():
    previous = socket.socket()
    before = descriptor_snapshot()
    with ResourceAudit() as audit:
        with socket.socket() as current:
            with audit.keep_alive(current, 'current participant'):
                previous.close()
    after = descriptor_snapshot()
    assert len(after) == len(before) - 1
    assert any(event['action'] == 'close' and not event['resources'] for event in audit.events)


def test_fd_reuse_cannot_hide_owned_leak_behind_foreign_cleanup():
    previous = socket.socket()
    descriptor = previous.fileno()
    before = descriptor_snapshot()
    with pytest.raises(AssertionError, match='owned socket'):
        with ResourceAudit():
            previous.close()
            leaked = socket.socket()
            assert leaked.fileno() == descriptor
            assert descriptor_snapshot()[descriptor] != before[descriptor]
            assert len(descriptor_snapshot()) == len(before)
    leaked.close()


def test_detached_descriptor_and_alias_are_still_owned():
    with pytest.raises(AssertionError, match='owned socket'):
        with ResourceAudit():
            channel = socket.socket()
            descriptor = channel.detach()
            alias = os.dup(descriptor)
            os.close(descriptor)
    os.close(alias)


@pytest.mark.parametrize('release', ['close', 'detach', 'raw-close'])
def test_protected_foreign_resource_cannot_be_closed_early(release):
    borrowed = socket.socket()
    detached = None
    try:
        with pytest.raises(AssertionError, match='premature'):
            with ResourceAudit() as audit, audit.keep_alive(borrowed, 'borrowed live resource'):
                if release == 'close':
                    borrowed.close()
                elif release == 'detach':
                    detached = borrowed.detach()
                else:
                    os.close(borrowed.fileno())
    finally:
        if detached is not None:
            os.close(detached)
        try:
            borrowed.close()
        except OSError:
            pass


def test_worker_resources_are_tracked_and_join_required():
    release = threading.Event()
    entered = threading.Event()
    def worker():
        with socket.socket():
            entered.set()
            assert release.wait(3)
    with ResourceAudit() as audit:
        thread = threading.Thread(target=worker)
        thread.start()
        try:
            assert entered.wait(3)
            with pytest.raises(AssertionError, match='owned threads remain'):
                audit.verify()
        finally:
            release.set()
            thread.join(3)
    assert len(audit.records) == 1


def test_snapshot_does_not_include_its_own_directory_descriptor():
    first = descriptor_snapshot()
    assert first == descriptor_snapshot()
    for descriptor, identity in first.items():
        assert os.fstat(descriptor).st_ino == identity[1]
