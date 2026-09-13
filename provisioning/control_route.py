"""Lease the root-pinned relay route for one control exchange, never a VPN profile.

The pipe is a liveness lease: EOF (including a killed client) releases the route.
The broker independently bounds its lifetime and recovers its own durable intent.
"""
import base64
from contextlib import contextmanager
import hashlib
import selectors
import subprocess
import time
import threading

HELPER = '/usr/local/lib/family-connect-control-route/helper'


@contextmanager
def managed_route(provider_public, cancel):
    raw = base64.b64decode(provider_public, validate=True)
    if len(raw) != 64:
        raise ValueError('invalid provider identity')
    provider = hashlib.sha256(raw).hexdigest()
    process = subprocess.Popen(['pkexec', HELPER, provider], stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    stopping = threading.Event()
    watcher = None
    try:
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ)
            deadline = time.monotonic() + 120
            while True:
                if cancel.is_set() or time.monotonic() >= deadline:
                    raise RuntimeError('control route authorization cancelled or timed out')
                if selector.select(.1):
                    if process.stdout.readline(64) != b'READY\n':
                        raise RuntimeError('control route unavailable')
                    break
        def watch():
            while not stopping.wait(.1):
                if process.poll() is not None:
                    cancel.set()
                    return
        watcher = threading.Thread(target=watch, daemon=True)
        watcher.start()
        yield
    finally:
        stopping.set()
        if watcher is not None:
            watcher.join(timeout=1)
        process.stdin.close()
        try:
            result = process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            # Do not pretend success or kill a root broker that is cleaning up.
            raise RuntimeError('control route cleanup incomplete') from None
        finally:
            process.stdout.close()
        if result != 0:
            raise RuntimeError('control route broker failed')
