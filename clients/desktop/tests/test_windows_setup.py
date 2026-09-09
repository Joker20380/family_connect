import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import backend

@pytest.mark.parametrize('code,message',[(20,'WireGuard not installed'),(21,'WireGuard signature verification failed'),(1,'WireGuard verification failed; exit=1')])
def test_setup_reports_safe_specific_error(code,message):
    shell=SimpleNamespace(shell32=SimpleNamespace(IsUserAnAdmin=lambda:True))
    result=SimpleNamespace(returncode=code,stdout='',stderr='private data must never be displayed')
    with patch.object(backend.ctypes,'windll',shell,create=True),patch.object(backend.subprocess,'run',return_value=result):
        with pytest.raises(backend.BackendError) as exc: backend.Windows()
    assert str(exc.value)==message


def test_setup_requires_admin_before_running_commands():
    shell=SimpleNamespace(shell32=SimpleNamespace(IsUserAnAdmin=lambda:False))
    with patch.object(backend.ctypes,'windll',shell,create=True),patch.object(backend.subprocess,'run') as run:
        with pytest.raises(backend.BackendError,match='Administrator rights required'):backend.Windows()
        run.assert_not_called()
