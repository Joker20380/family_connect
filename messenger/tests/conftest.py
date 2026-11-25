import pytest
import RNS


@pytest.fixture(scope='session')
def chat_runtime(tmp_path_factory):
    """One RNS singleton for in-process tests; wire tests use child processes."""
    existing = getattr(tmp_path_factory, '_family_connect_chat_runtime', None)
    if existing is not None:
        return existing
    config = tmp_path_factory.mktemp('chat-rns')
    (config / 'config').write_text('[reticulum]\nshare_instance = No\nenable_transport = No\n'
                                  '[logging]\nloglevel = -1\n[interfaces]\n')
    runtime = RNS.Reticulum(configdir=str(config), loglevel=-1)
    tmp_path_factory._family_connect_chat_runtime = runtime
    return runtime
