"""Retain terminal coordinator bytes before a new online operation can replace them."""
import base64
import os
import re

from credential_renewal import atomic, canonical, digest, private_directory, read_private, require

FILES = ('transaction.json', 'plan.json', 'last-receipt.json')


def check_operation(root, operation):
    history = root / 'history'
    if history.exists() or history.is_symlink():
        private_directory(history)
        requested = history / (operation + '.json')
        require(not requested.exists() and not requested.is_symlink(), 'ONLINE_HISTORY_OPERATION_REUSED')


def retain(controller, record, operation):
    check_operation(controller.root, operation)
    if record is None:
        return
    history = controller.root / 'history'
    predecessor = record['operation_id']
    require(type(predecessor) is str and re.fullmatch('[a-z0-9-]{16,96}', predecessor), 'OPERATION_ID')
    require(record['state'] in ('COMMITTED', 'ABORTED'), 'OTHER_OPERATION_RECOVERY_REQUIRED')
    history.mkdir(mode=0o700, exist_ok=True)
    private_directory(history)
    files = {name: read_private(controller.root / name) for name in FILES
             if (controller.root / name).exists() or (controller.root / name).is_symlink()}
    raw = canonical(dict(schema=1, operation_id=predecessor,
        files={name: base64.b64encode(value).decode() for name, value in files.items()},
        sha256={name: digest(value) for name, value in files.items()}))
    destination = history / (predecessor + '.json')
    if destination.exists() or destination.is_symlink():
        require(read_private(destination) == raw, 'ONLINE_HISTORY_CONFLICT')
    else:
        require(len(list(history.iterdir())) < 4096, 'OPERATION_HISTORY_CAPACITY')
        atomic(destination, raw)
    descriptor = os.open(controller.root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    controller.fault('ONLINE_PREDECESSOR_RETAINED')
