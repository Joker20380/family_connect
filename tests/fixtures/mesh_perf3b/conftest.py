import json
from pathlib import Path

import pytest


collect_ignore = list(json.loads(Path(__file__).with_name('historical-suite.json').read_text())['tests'])


def pytest_pycollect_makemodule(module_path, parent):
    if module_path.name in collect_ignore:
        raise pytest.UsageError('BLOCKED: use tests/fixtures/mesh_perf3b/run_history.py with verified historical inputs')
