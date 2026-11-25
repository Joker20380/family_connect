"""Finish owned support work before releasing its encrypted store on termination."""
from contextlib import contextmanager
import signal
import time

from control.capture_gate import Busy


class StopRequest:
    def __init__(self):
        self.stopped = False

    def is_set(self):
        return self.stopped

    def request(self, *_):
        self.stopped = True


@contextmanager
def stop_requested():
    stopped = StopRequest()
    previous = {}
    try:
        for signum in (signal.SIGTERM, signal.SIGINT):
            previous[signum] = signal.signal(signum, stopped.request)
        yield stopped
    finally:
        for signum, handler in previous.items():
            signal.signal(signum, handler)


def drain_delivery(delivery):
    while not delivery.close(timeout=1):
        pass


def close_store(store):
    while True:
        try:
            store.close()
            return
        except Busy:
            time.sleep(.1)


def unlink_socket(path, identity):
    try:
        info = path.lstat()
    except FileNotFoundError:
        return
    if (info.st_dev, info.st_ino) == identity:
        path.unlink()
