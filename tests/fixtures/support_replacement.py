"""Unmodified legacy main/delivery around a persistent synthetic store and standalone RNS."""
import ctypes
import os
from pathlib import Path
import sys
import time

if os.environ.get('FC_TEST_PTRACER_ANY') == '1':
    assert ctypes.CDLL(None, use_errno=True).prctl(0x59616d61, ctypes.c_ulong(-1), 0, 0, 0) == 0
source, arguments = sys.argv[1], sys.argv[2:]
sys.path.insert(0, source)
from provisioning import support_worker as worker
from messenger.mailbox import ExchangeResult, SyncResult
import RNS

RNS.Reticulum.JOB_INTERVAL = .2
root = Path(arguments[arguments.index('--store') + 1]).parent
mode = os.environ.get('FC_TEST_SUPPORT_MODE', 'idle')


def exchange(mailbox, **kwargs):
    if mode == 'blocked':
        (root / 'writer-entered').touch()
        while not (root / 'release').exists():
            time.sleep(.01)
        assert not kwargs['cancel'].is_set()
        with mailbox.owner.store._lock, mailbox.owner.store._db:
            mailbox.owner.store._put('retained', {'after_drain': True})
    return ExchangeResult(SyncResult(0, 0, 0, 0), 0, 0, False)


worker.SupportMailbox.exchange = exchange
sys.argv = ['support', *arguments]
worker.main()
