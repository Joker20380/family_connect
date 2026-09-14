"""Keep operation-coordination tests off the user's actual client state."""
import sys
from pathlib import Path

import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import backend


@pytest.fixture(autouse=True)
def isolated_operations(tmp_path,monkeypatch):
    monkeypatch.setattr(backend,'operation_directory',lambda:tmp_path/'operations')
