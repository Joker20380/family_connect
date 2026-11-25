import io
from pathlib import Path
import tarfile

import pytest

from scripts import ci_maintenance_fixture as provision
from scripts import control_ha_maintenance_fixture as capture


def test_build_context_contains_only_explicit_public_recipe_and_lockfiles():
    with tarfile.open(fileobj=io.BytesIO(provision.context())) as archive:
        assert tuple(archive.getnames()) == provision.INPUTS
        for entry in archive:
            assert entry.isfile() and entry.mode == 0o644
            assert archive.extractfile(entry).read() == (provision.ROOT / entry.name).read_bytes()
    recipe = (provision.ROOT / provision.INPUTS[0]).read_text()
    assert 'python:3.13.15-slim-bookworm' in recipe
    assert '46.0.7' in recipe and '--require-hashes' in recipe


@pytest.mark.parametrize('image', ['latest', 'python:3.13', 'sha256:short', 'sha256:' + 'g' * 64])
def test_mutable_or_malformed_ci_image_refuses_before_docker(tmp_path, monkeypatch, image):
    monkeypatch.setenv('FC_TEST_MAINTENANCE_IMAGE', image)
    monkeypatch.setattr(capture.subprocess, 'run', lambda *args, **kwargs: pytest.fail('must not start Docker'))
    with pytest.raises(ValueError, match='IMMUTABLE_FIXTURE_IMAGE_REQUIRED'):
        capture.capture_container({}, tmp_path)


def test_root_helper_refuses_outside_networkless_build_container(monkeypatch):
    monkeypatch.setattr(provision.os, 'geteuid', lambda: 0)
    with pytest.raises(ValueError, match='NETWORKLESS_BUILD_CONTAINER_REQUIRED'):
        provision.root_fixture()


def test_native_build_path_keeps_full_gate_and_explicit_root_scope():
    root = Path(__file__).resolve().parents[1]
    docker = (root / 'Dockerfile.control').read_text()
    assert 'RUN --network=none python scripts/ci_release_fixtures.py run' in docker
    assert '--unprivileged-user runner && touch /tmp/tests-passed' in docker
    assert 'NOPASSWD: /opt/fc-python313-env/bin/python -I -B ' + str(provision.HELPER) + ' --root' in docker
    assert 'chmod -R go-w /opt/fc-ci-maintenance-source' in docker
    for workflow in ('test.yml', 'control.yml'):
        assert 'python scripts/ci_maintenance_fixture.py >> "$GITHUB_ENV"' in (root / '.github/workflows' / workflow).read_text()


def test_privileged_runtime_probes_use_the_root_owned_gil_interpreter():
    from scripts.ci_pytest_context import context
    for name in ('tests/test_capture_launch.py', 'tests/test_capture_renewal_state.py'):
        assert context(name + '::test_native') == 'native314'
