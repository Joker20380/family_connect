"""Partition the full collected suite by its explicit UID/interpreter contract."""
import json
import os
from pathlib import Path
import sys

import pytest

ROOT_FILES = frozenset(('tests/test_profile_store.py', 'tests/test_profile_snapshot.py',
                        'tests/test_restricted_maintenance.py'))
ROOT_CLASS = 'tests/test_gateway_credential_publication.py::IsolatedRootTests::'
SNAPSHOT_FILE = 'tests/test_profile_snapshot_launcher.py'
NATIVE314_FILES = frozenset((
    'messenger/tests/test_control_ha_mailbox_fence.py',
    'messenger/tests/test_control_ha_mailbox_links.py',
    'messenger/tests/test_control_ha_mailbox_startup.py',
    'tests/test_control_ha_legacy_http.py', 'tests/test_control_ha_legacy_support.py',
    'tests/test_control_ha_support_quiesce.py', 'tests/test_control_ha_support_exit.py',
    'tests/test_control_ha_support_replace.py', 'tests/test_control_ha_support_witness.py',
    'tests/test_control_ha_support_terminal.py', 'tests/test_control_ha_support_terminal_native.py'))
CONTEXTS = ('standard', 'root', 'snapshot314', 'native314')


def context(nodeid):
    path = nodeid.split('::')[0]
    if path in ROOT_FILES or nodeid.startswith(ROOT_CLASS):
        return 'root'
    if path in NATIVE314_FILES:
        return 'native314'
    return 'snapshot314' if path == SNAPSHOT_FILE else 'standard'


def pytest_addoption(parser):
    parser.addoption('--fixture-context', choices=(*CONTEXTS, 'inventory'))
    parser.addoption('--fixture-collection', type=Path)


def pytest_collection_modifyitems(config, items):
    selected = config.getoption('--fixture-context')
    if not selected:
        return
    if selected == 'root' and os.geteuid() != 0:
        raise pytest.UsageError('Ownership fixtures require isolated UID 0')
    if selected in ('standard', 'snapshot314', 'native314') and os.geteuid() == 0:
        raise pytest.UsageError('Non-ownership fixtures must run unprivileged')
    if selected in ('snapshot314', 'native314') and (sys.version_info[:2] != (3, 14) or
                                                   not sys._is_gil_enabled()):
        raise pytest.UsageError('Native fixtures require Python 3.14 with GIL')
    groups = {name: [] for name in CONTEXTS}
    for item in items:
        groups[context(item.nodeid)].append(item.nodeid.split('[')[0])
    groups = {name: sorted(values) for name, values in groups.items()}
    output = config.getoption('--fixture-collection')
    if output:
        output.write_text(json.dumps(groups, sort_keys=True))
    if selected != 'inventory':
        rejected = [item for item in items if context(item.nodeid) != selected]
        items[:] = [item for item in items if context(item.nodeid) == selected]
        config.hook.pytest_deselected(items=rejected)
        if not items:
            raise pytest.UsageError('Empty required fixture context: ' + selected)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_protocol(item, nextitem):
    if item.config.getoption('--fixture-context'):
        print('\nFIXTURE TEST: ' + item.nodeid.split('[')[0], flush=True)
    previous = os.umask(0o022)
    os.umask(previous)
    try:
        yield
    finally:
        os.umask(previous)
