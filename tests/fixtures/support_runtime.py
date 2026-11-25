"""Private standalone Reticulum lifecycle with synthetic queued and asynchronous writes."""
import json
import os
from pathlib import Path
import signal
import sys
import threading
import time

archive = os.environ.get('FC_TEST_SUPPORT_ARCHIVE')
sys.path.insert(0, archive or str(Path(__file__).resolve().parents[2]))

import RNS
from control.capture_gate import initialize
from provisioning import support_runtime
from provisioning.support_lifecycle import stop_requested

if archive:
    assert support_runtime.__file__.startswith(archive + '/')


root, mode = Path(sys.argv[1]), sys.argv[2]
os.umask(0o077)
gate = initialize(root / 'gate')
originals = (RNS.log, RNS.Transport.inbound_job, RNS.Transport.jobloop, threading.excepthook)


def wait(name):
    (root / name).touch()
    deadline = time.monotonic() + 60
    while not (root / 'release').exists():
        assert time.monotonic() < deadline
        time.sleep(.01)


if mode == 'source-drift':
    support_runtime.PINS['RNS.Identity'] = '0' * 64
elif mode == 'loaded-drift':
    RNS.Transport.inbound_job = lambda: None
elif mode == 'outbound-enabled':
    RNS.Transport.USE_OUTBOUND_QUEUE = True

try:
    with stop_requested() as stopped, support_runtime.ManagedRuntime(gate) as owner:
        if mode == 'periodic':
            original_clean = RNS.Reticulum._Reticulum__clean_caches

            def clean(instance, background=False):
                wait('writer-entered')
                original_clean(instance, background=background)
                (root / 'writer-finished').touch()

            RNS.Reticulum._Reticulum__clean_caches = clean
            RNS.Reticulum.JOB_INTERVAL = .02
            RNS.Reticulum.CLEAN_INTERVAL = .01
        runtime = owner.initialize(root / 'runtime')
        deadline = time.monotonic() + 5
        while len(owner.loops) != 4:
            assert time.monotonic() < deadline
            time.sleep(.01)
        (root / 'loops.json').write_text(json.dumps(sorted(owner.loops.values())))
        destination = b'd' * 16
        identity = RNS.Identity()
        RNS.Identity.remember(b'p' * 32, destination, identity.get_public_key(), b'synthetic-lifecycle')
        (root / 'public').write_bytes(identity.get_public_key())
        if mode == 'startup-failure':
            raise RuntimeError('synthetic startup failure')
        if mode in ('queue', 'queue-descendant'):
            def inbound(packet):
                if packet == 'first':
                    wait('writer-entered')
                    RNS.Identity._remember_ratchet(destination, b'r' * 32)
                    if mode == 'queue-descendant':
                        def later():
                            time.sleep(.2)
                            RNS.Transport.inbound_queues.put(0, 'second')
                            (root / 'descendant-finished').touch()
                        threading.Thread(target=later, daemon=True).start()
                (root / ('packet-' + packet)).touch()
            RNS.Transport._inbound = inbound
            RNS.Transport.inbound_queues.put(0, 'first')
        elif mode in ('async', 'thread-failure'):
            original_replace = os.replace

            def replace(source, target, *args, **kwargs):
                if str(source).endswith(destination.hex() + '.out'):
                    wait('writer-entered')
                    if mode == 'thread-failure':
                        raise OSError('synthetic ratchet write failure')
                    (root / 'writer-finished').touch()
                return original_replace(source, target, *args, **kwargs)

            os.replace = replace
            RNS.Identity._remember_ratchet(destination, b'r' * 32)
        elif mode in ('exit-failure', 'exit-wait'):
            original_replace = os.replace

            def replace(source, target, *args, **kwargs):
                if str(target).endswith('/known_destinations'):
                    if mode == 'exit-failure':
                        raise OSError('synthetic final persistence failure')
                    wait('exit-entered')
                return original_replace(source, target, *args, **kwargs)

            os.replace = replace
        elif mode == 'fsync-failure':
            support_runtime.sync_tree = lambda root: (_ for _ in ()).throw(OSError('synthetic fsync failure'))
        elif mode == 'caught-close-failure':
            original_sync = support_runtime.sync_tree
            support_runtime.sync_tree = lambda root: (_ for _ in ()).throw(OSError('synthetic fsync failure'))
            try:
                owner.close()
            except OSError:
                (root / 'caught').touch()
            support_runtime.sync_tree = original_sync
        elif mode == 'replaced-state':
            (root / 'runtime').rename(root / 'preserved-runtime')
            (root / 'runtime').mkdir(mode=0o700)
        elif mode == 'unsafe-state':
            (root / 'runtime/unsafe-link').symlink_to(root / 'public')
        elif mode == 'application-failure':
            raise RuntimeError('synthetic application failure')
        (root / 'ready').touch()
        while not stopped.is_set():
            time.sleep(.01)
        (root / 'closing').touch()
    result = {'result': 'PASS'}
except (ValueError, RuntimeError, OSError) as error:
    result = {'result': 'REFUSED', 'reason': str(error)}
result['threads'] = len(threading.enumerate())
result['native_threads'] = len(list(Path('/proc/self/task').iterdir()))
result['hooks_restored'] = originals == (RNS.log, RNS.Transport.inbound_job, RNS.Transport.jobloop, threading.excepthook)
(root / 'result.json').write_text(json.dumps(result))
