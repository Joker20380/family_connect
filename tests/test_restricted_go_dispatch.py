import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NATIVE = ROOT/'pilot/android-restricted/native'


def test_go_callbacks_never_inherit_another_runtime_thread(tmp_path):
    binary = tmp_path/'dispatch-test'
    subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror', '-pthread',
                    '-I'+str(NATIVE), str(NATIVE/'go_dispatch.c'),
                    str(ROOT/'tests/fixtures/mobile_bootstrap/go_dispatch_test.c'),
                    '-Wl,--wrap=pthread_create', '-o', str(binary)], check=True)
    subprocess.run([str(binary)], check=True, timeout=10)


def test_every_jni_go_export_is_dispatched():
    header = (NATIVE/'go_dispatch.h').read_text()
    exports = set()
    for source in NATIVE.glob('*.go'):
        exports.update(re.findall(r'^//export (fc(?:Restricted|Provision|Chat)\w+)$', source.read_text(), re.M))
    for name in exports:
        assert f'#define {name} isolated{name[2:]}' in header
    for name in ('bridge.c', 'provision_bridge.c', 'chat_bridge.c'):
        assert '#include "go_dispatch.h"' in (NATIVE/name).read_text()
