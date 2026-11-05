import importlib.util
from pathlib import Path

import pytest


spec = importlib.util.spec_from_file_location('core_emulators', Path(__file__).with_name('android_core_emulators.py'))
emulators = importlib.util.module_from_spec(spec)
spec.loader.exec_module(emulators)


def test_real_nvidia_renderer():
    renderer = 'GLES: Google (NVIDIA Corporation), Android Emulator OpenGL ES Translator (NVIDIA GeForce GTX 1650 Ti)'
    assert emulators.require_nvidia_renderer('header\n'+renderer+'\nfooter') == renderer


@pytest.mark.parametrize('surface', [
    '', 'GLES: Google SwiftShader', 'GLES: Mesa llvmpipe', 'GLES: lavapipe',
    'GPU: NVIDIA\nGLES: Google SwiftShader', 'GLES: NVIDIA software rasterizer',
    'GLES: NVIDIA SwiftShader', 'GLES: Intel UHD Graphics',
])
def test_missing_or_software_renderer_refused(surface):
    with pytest.raises(RuntimeError, match='hardware renderer required'):
        emulators.require_nvidia_renderer(surface)


def test_only_one_emulator_per_shared_directory(tmp_path):
    with emulators.emulator_slot(tmp_path):
        with pytest.raises(RuntimeError, match='already running'):
            with emulators.emulator_slot(tmp_path):
                pytest.fail('Concurrent emulator acquired the slot')
    with emulators.emulator_slot(tmp_path):
        pass


def test_slot_released_after_failure(tmp_path):
    with pytest.raises(ValueError):
        with emulators.emulator_slot(tmp_path):
            raise ValueError('fixture interruption')
    with emulators.emulator_slot(tmp_path):
        pass
