import ast
import subprocess
import sys

from scripts.package_linux import assemble_bundle, audit, LEGACY_TAR


def test_new_chat_runtime_closure_and_legacy_shape(tmp_path):
    bundle = tmp_path / 'bundle'
    assemble_bundle(bundle)
    audit(bundle)
    assert len(LEGACY_TAR) == 6
    assert (bundle / 'messenger/admission.py').is_file()
    assert (bundle / 'provisioning/chat_audio.py').is_file()
    assert (bundle / 'clients/desktop/chat_voice.py').is_file()
    assert (bundle / 'clients/desktop/chat_notifications.py').is_file()
    assert (bundle / 'clients/desktop/chat_daemon.py').is_file()
    assert (bundle / 'clients/desktop/messenger_window.py').is_file()
    assert (bundle / 'clients/desktop/messenger_widgets.py').is_file()
    assert (bundle / 'clients/desktop/chat_announcements.py').is_file()
    assert (bundle / 'provisioning/chat_client.py').is_file()
    assert (bundle / 'provisioning/chat_rpc.py').is_file()
    assert (bundle / 'provisioning/chat_admin.py').is_file()
    assert (bundle / 'provisioning/chat_events.py').is_file()
    assert (bundle / 'provisioning/chat_bridge.py').is_file()
    assert (bundle / 'provisioning/chat_bridge_protocol.py').is_file()
    assert (bundle / 'provisioning/chat_direct.py').is_file()
    assert (bundle / 'provisioning/support.py').is_file()
    assert (bundle / 'provisioning/support_client.py').is_file()
    assert (bundle / 'clients/desktop/support_daemon.py').is_file()
    assert (bundle / 'VERSION').read_text().strip() == '0.2.11'
    assert 'LGPL-2.1' in (bundle / 'licenses/audio-runtime-notices.txt').read_text()
    assert (bundle / 'licenses/LXMF.txt').read_text().startswith('Reticulum License')
    for path in bundle.rglob('*.py'):
        ast.parse(path.read_text())
    script = ('import sys;from pathlib import Path;sys.path.insert(0,sys.argv[1]);'
              'sys.path.insert(0,str(Path(sys.argv[1])/"clients/desktop"));'
              'from provisioning.chat_owner import ChatOwner;'
              'from provisioning.chat_bridge import ChatBridge;'
              'from provisioning.chat_direct import DirectBridge;'
              'from provisioning.chat_transport import ExistingExitMailbox;'
              'from provisioning.support_client import SupportClient;'
              'import support_daemon;from support_daemon import SupportSession;'
              'from chat_daemon import ChatService;'
              'from messenger.admission import message;'
              'assert ChatOwner.__module__=="provisioning.chat_owner";'
              'assert Path(sys.modules[ChatBridge.__module__].__file__).is_relative_to(sys.argv[1]);'
              'assert ExistingExitMailbox.ROUTES==("SYSTEM","EXISTING_EXIT");'
              'assert DirectBridge.ROUTE=="DIRECT";'
              'assert Path(sys.modules[DirectBridge.__module__].__file__).is_relative_to(sys.argv[1]);'
              'assert support_daemon.version_info(sys.argv[1])==("0.2.11",2011);'
              'assert Path(support_daemon.__file__).is_relative_to(sys.argv[1]);'
              'assert Path(sys.modules[SupportClient.__module__].__file__).is_relative_to(sys.argv[1]);'
              'assert Path(sys.modules[ChatService.__module__].__file__).is_relative_to(sys.argv[1]);'
              'assert SupportSession(None,lambda: {},2011).status()["enabled"] is False;'
              'assert sys.argv[1] in __import__("provisioning").__file__;'
              'assert sys.argv[1] in __import__("messenger").__file__')
    result = subprocess.run([sys.executable, '-c', script, str(bundle)], cwd=tmp_path,
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
