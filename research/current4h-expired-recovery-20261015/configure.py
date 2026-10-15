import argparse
import hashlib
import json
import os
from pathlib import Path


BASE_SOURCE_MAP = '107d1c4219e13fdb91283b9e34f01951f95436a30c9b155f57ea427041221a5b'


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def project(node, controller=None):
    manifest = json.loads((Path(__file__).resolve().parent/'source-manifest.json').read_bytes())
    successor = manifest['management_source_sha256']
    assert set(node) == {'schema', 'role', 'live', 'state', 'database', 'anchor', 'anchor_sha256',
        'api_archive', 'api_sha256', 'source_files', 'source_sha256'}
    assert node['schema'] == 1 and node['role'] in ('RU', 'NL')
    assert node['source_sha256'] in (BASE_SOURCE_MAP, successor)
    assert hashlib.sha256(canonical(node['source_files'])).hexdigest() == node['source_sha256']
    new_node = dict(node, source_files=manifest['management_sources'], source_sha256=successor)
    new_controller = None
    if controller is not None:
        assert node['role'] == 'RU'
        assert set(controller) == {'schema', 'node_config', 'coordinator_state', 'nl_source_sha256',
                                   'ssh', 'approved_leaf_crl_schedule'}
        assert controller['schema'] == 1 and controller['nl_source_sha256'] in (BASE_SOURCE_MAP, successor)
        new_controller = dict(controller, nl_source_sha256=successor)
    return new_node, new_controller


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description='Produce private management config copies; no live apply or credentials')
    parser.add_argument('--node', type=Path, required=True)
    parser.add_argument('--controller', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    node, controller = project(json.loads(args.node.read_bytes()),
        None if args.controller is None else json.loads(args.controller.read_bytes()))
    args.out.mkdir(mode=0o700, parents=True, exist_ok=False)
    (args.out/'node.json').write_bytes(canonical(node))
    if controller is not None:
        (args.out/'controller.json').write_bytes(canonical(controller))
    print('MANAGEMENT_CONFIG_COPIES_PREPARED_NO_LIVE_APPLY')


if __name__ == '__main__':
    main()
