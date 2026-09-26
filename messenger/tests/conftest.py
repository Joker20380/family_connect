import pytest
import RNS


@pytest.fixture(scope='session')
def chat_runtime(tmp_path_factory):
    """One RNS singleton for in-process tests; wire tests use child processes."""
    config = tmp_path_factory.mktemp('chat-rns')
    (config / 'config').write_text('[reticulum]\nshare_instance = No\nenable_transport = No\n'
                                  '[logging]\nloglevel = -1\n[interfaces]\n')
    return RNS.Reticulum(configdir=str(config), loglevel=-1)
