import json
import os
from pathlib import Path
import shutil
import time

import pytest

from mesh_legacy_peer import EXCHANGE_HANDLER, describe, legacy_source
from mesh_core_stand import CoreStand
from mesh_core_directory import publish_seed_directories
from online_package_stand import private_file
from scripts import package_online_renewal as package
from test_mesh_core_soak import generations
from test_online_runtime_package import online_package


def test_legacy_overlay_only_omits_optional_exchange_handler():
    original = b'prefix\n\tconfig.LeaseRenewal = binding.dynamicHandler(access)\n'+EXCHANGE_HANDLER+b'suffix\n'
    altered = legacy_source(original)
    assert altered == original.replace(EXCHANGE_HANDLER, b'')
    receipt = describe(original, altered, b'synthetic-binary', 'synthetic-source', b'normal')
    assert receipt['lease_renewal'] and not receipt['credential_exchange']
    assert receipt['original_sha256'] != receipt['overlay_sha256']
    with pytest.raises(AssertionError, match='unchanged driver refused'):
        describe(original, altered, b'normal', 'synthetic-source', b'normal')


@pytest.mark.parametrize('original', [b'', EXCHANGE_HANDLER, EXCHANGE_HANDLER*2])
def test_unknown_peer_source_never_silently_qualifies(original):
    with pytest.raises(AssertionError):
        legacy_source(original)


def test_actual_legacy_peer_cannot_extend_original_authorization(online_package, tmp_path):
    if not os.environ.get('FC_LEGACY_PEER_ROOT'):
        pytest.skip('explicit frozen legacy compatibility fixture required')
    root = Path(os.environ['FC_LEGACY_PEER_ROOT'])
    driver = root/'mesh-runtime-legacy2'
    manifest = json.loads((root/'manifest2.json').read_bytes())
    assert manifest['driver_sha256'] == package.digest(driver.read_bytes())
    assert manifest['driver_sha256'] != manifest['normal_driver_sha256']
    assert manifest['source_commit'] == online_package[4]['source_commit']
    owned_driver = tmp_path/'mesh-runtime-legacy'
    shutil.copyfile(driver, owned_driver)
    owned_driver.chmod(0o755)
    stand = CoreStand(tmp_path, online_package[3], owned_driver)
    clients = {}
    receipt = dict(legacy_peer=manifest, package=online_package[4], scope='legacy-core-preflight-not-Android')
    try:
        stand.start()
        receipt['directory_publication'] = publish_seed_directories(stand, Path(os.environ['FC_TEST_SNAPSHOT']))
        clients = {slot: stand.client(slot, 60) for slot in ('NL', 'NL2')}
        deadline = time.monotonic()+30
        while not all((tmp_path/(slot+'-client.log')).exists() and
                      '"event":"traffic"' in (tmp_path/(slot+'-client.log')).read_text() for slot in clients):
            assert all(client.poll() is None for client in clients.values())
            assert time.monotonic() < deadline
            time.sleep(.1)
        code, result = stand.run('online')
        assert code == 0 and result['result'] == 'COMMITTED', result
        assert all(client.wait(timeout=90) == 0 for client in clients.values())
        receipt['traffic'] = {}
        for slot in clients:
            path = tmp_path/(slot+'-client.log')
            observed = generations(path)
            assert observed['committed'] == 0
            assert observed['last']['generation'] == observed['first']['generation'] == 0
            assert observed['last']['security'] == observed['first']['security']
            events = [json.loads(line)['event'] for line in path.read_text().splitlines()]
            assert events.count('credentials_offered') == 1
            receipt['traffic'][slot] = observed
        fresh = {slot: stand.client(slot, 3, name=slot+'-fresh') for slot in clients}
        assert all(client.wait(timeout=40) == 0 for client in fresh.values())
        receipt.update(result='PASS_LEGACY_UNCHANGED_BOUND', fresh='new-sessions-not-renewal')
    finally:
        for client in clients.values():
            if client.poll() is None:
                client.terminate()
                client.wait(timeout=15)
        stand.close()
        receipt['cleanup'] = 'processes-waited'
        destination = Path(os.environ['FC_CORE_EVIDENCE'])/'legacy-peer'
        destination.mkdir(mode=0o700, parents=True)
        private_file(destination/'receipt.json', package.encode(receipt))
        for path in tmp_path.glob('*.log'):
            private_file(destination/path.name, path.read_bytes())
