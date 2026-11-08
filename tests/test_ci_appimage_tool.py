import hashlib
import os
from pathlib import Path
import subprocess
import textwrap

import pytest


ROOT = Path(__file__).resolve().parents[1]
TOOL_PIN = 'e8c1169c4af66c3184d7ee110713d4be04befe671fa358e2c1591ee840553b03'
RUNTIME_PIN = '617aa77314d57c8b8e4fae9c3f0b35af7b30d5529cb69e98f64f92510ed98a46'


@pytest.mark.parametrize('tamper', ['', 'appimage-tool', 'appimage-runtime'])
def test_ci_appimage_fetch_checks_both_inputs_before_execution(tmp_path, tamper):
    workflow = (ROOT / '.github/workflows/clients.yml').read_text()
    step = workflow.split('      - name: Install appimagetool\n        run: |\n', 1)[1].split('      - name:', 1)[0]
    script = textwrap.dedent(step)
    assert TOOL_PIN in script and RUNTIME_PIN in script
    assert 'https://api.github.com/repos/AppImage/appimagetool/releases/assets/715388534' in script
    assert 'https://api.github.com/repos/AppImage/type2-runtime/releases/assets/657374641' in script
    assert '--runtime-file' in script
    assert 'Verify DEB metadata, desktop integration and content audit' in workflow
    assert 'AppImage extract smoke' in workflow
    tool = b'#!/bin/sh\nprintf "%s\\n" "$@"\n'
    runtime = b'synthetic-runtime'
    script = script.replace(TOOL_PIN, hashlib.sha256(tool).hexdigest()).replace(RUNTIME_PIN, hashlib.sha256(runtime).hexdigest())
    binaries = tmp_path / 'bin'
    binaries.mkdir()
    (tmp_path / 'tool.fixture').write_bytes(tool)
    (tmp_path / 'runtime.fixture').write_bytes(runtime)
    curl = binaries / 'curl'
    curl.write_text('#!/bin/bash\nset -e\noutput="${@: -1}"\n'
                    'if [[ "$output" == */appimage-tool ]]; then fixture=tool; else fixture=runtime; fi\n'
                    'cp "$RUNNER_TEMP/$fixture.fixture" "$output"\n'
                    'if [[ -n "$TAMPER" && "$output" == */"$TAMPER" ]]; then printf corrupted >> "$output"; fi\n')
    curl.chmod(0o755)
    environment = os.environ | {'RUNNER_TEMP': str(tmp_path), 'TAMPER': tamper,
                                'PATH': str(binaries) + ':' + os.environ['PATH']}
    result = subprocess.run(['bash', '-e', '-o', 'pipefail', '-c', script], env=environment, capture_output=True, text=True)
    wrapper = tmp_path / 'appimagetool'
    if tamper:
        assert result.returncode != 0
        assert not wrapper.exists()
    else:
        assert result.returncode == 0, result.stderr
        invoked = subprocess.check_output([wrapper, 'input path', 'output path'], text=True)
        assert invoked.splitlines() == ['--runtime-file', str(tmp_path / 'appimage-runtime'), 'input path', 'output path']
