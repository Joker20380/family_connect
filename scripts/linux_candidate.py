"""Bind the full user bundle to the reviewed internal system component."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SYSTEM = dict(build_id='8d7d78ec06fc897fa7e94d21f208b08b31d6c6c3e33eaad19a262705117c8f9d',
              sha256='ddd74c2132a76ac833b587d9df6409d779ce6afcdaa45fafd23faa86d7817726', size=49250848,
              source_digest='cfcb7bae874765cfe6a66742fbeed55cb03399b7e32c13d5a5edcd212299df61')
TARGETS = {'ubuntu24.04': [3, 12], 'ubuntu26.04': [3, 14]}


def compatibility(target, python):
    if target not in TARGETS or python != TARGETS[target]:
        raise ValueError('Candidate target/Python ABI mismatch')
    return dict(distribution='ubuntu', version=target.removeprefix('ubuntu'),
                python=python, interpreter='/usr/bin/python3')


def python_dependency(python):
    if python not in TARGETS.values():
        raise ValueError('Unsupported candidate Python ABI')
    return f'python3 (>= {python[0]}.{python[1]}), python3 (<< {python[0]}.{python[1] + 1})'


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'packaging/linux' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def embed(bundle, archive, *, standard_rebuild=False, target='ubuntu24.04'):
    if target not in TARGETS or (target != 'ubuntu24.04' and not standard_rebuild):
        raise ValueError('New platform requires an explicit standard system rebuild')
    raw = archive.read_bytes()
    if not standard_rebuild and (len(raw) != SYSTEM['size'] or hashlib.sha256(raw).hexdigest() != SYSTEM['sha256']):
        raise ValueError('Expected pinned internal system build, not a same-version replacement')
    import io
    import tarfile
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:gz') as source:
        installer_raw = source.extractfile('FamilyConnect-MESH-system-amd64/install.py').read()
        manifest = json.load(source.extractfile('FamilyConnect-MESH-system-amd64/manifest.json'))
    reference = json.loads((ROOT / 'packaging/linux/system-reference.json').read_text())
    if any(manifest['sha256'].get(name) != checksum for name, checksum in reference['source_files'].items()):
        raise ValueError('System sources differ from the pinned candidate contract')
    if manifest['source_digest'] != reference['native_source_digest']:
        raise ValueError('Native source reference mismatch')
    expected = dict(build_id=manifest['build_id'], source_digest=manifest['source_digest'], size=len(raw),
                    sha256=hashlib.sha256(raw).hexdigest(), installer_sha256=hashlib.sha256(installer_raw).hexdigest())
    with tempfile.TemporaryDirectory(prefix='fc-candidate-verify-') as temporary:
        component = load('candidate_setup').extract_verified(raw, expected, Path(temporary))
        runtime = json.loads((component / 'python-runtime.json').read_text())
        if json.loads((component / 'rns/build.json').read_text())['source_digest'] != reference['rns_source_digest']:
            raise ValueError('RNS source reference mismatch')
        compatibility(target, runtime['python'])
        for lock in ('provisioning/requirements.lock', 'messenger/requirements.lock'):
            for line in (ROOT / lock).read_text().splitlines():
                match = re.match(r'^([A-Za-z0-9_-]+)==([^ ]+)', line)
                if match and runtime['distributions'].get(match[1]) != match[2]:
                    raise ValueError('User/system dependency lock mismatch')
        for name in (*runtime['files'], 'python-runtime.json'):
            target = bundle / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((component / name).read_bytes())
    (bundle / 'embedded').mkdir()
    (bundle / 'embedded/system.tar.gz').write_bytes(raw)
    for name in ('candidate_setup.py', 'candidate_runtime.py', 'remove_user_service.py'):
        (bundle / name).write_bytes((ROOT / 'packaging/linux' / name).read_bytes())
    return expected, runtime['python']


def seal(bundle, version, system, python, *, target='ubuntu24.04'):
    if not re.fullmatch(r'0\.2\.12~(?:l03\.2|ci\.preview)\.[1-9][0-9]*', version):
        raise ValueError('Explicit reserved internal Linux candidate version required')
    platform = compatibility(target, python)
    if target == 'ubuntu26.04' and int(version.rsplit('.', 1)[1]) <= 5:
        raise ValueError('Ubuntu26.04 requires a new candidate version after the frozen .5')
    paths = ['clients/desktop', 'provisioning', 'messenger', 'device_identity', 'packaging',
             'scripts/package_linux.py', 'scripts/linux_candidate.py']
    dirty = bool(subprocess.check_output(['git', 'diff', 'HEAD', '--', *paths], cwd=ROOT))
    files = {}
    for path in sorted(bundle.rglob('*')):
        if path.is_file():
            path.chmod(0o644)
            raw = path.read_bytes()
            files[str(path.relative_to(bundle))] = dict(sha256=hashlib.sha256(raw).hexdigest(), size=len(raw))
        elif path.is_dir():
            path.chmod(0o755)
    system_source = subprocess.check_output(['git', 'log', '-1', '--format=%H', '--',
        'clients/linux', 'clients/desktop/backend.py', 'clients/desktop/profile_config.py',
        'provisioning', 'device_identity', 'messenger', 'scripts/package_mesh_component.py',
        'scripts/package_system_python.py'], cwd=ROOT, text=True).strip()
    record = dict(schema=1, runtime_contract=2, authorization_protocol=2, internal_version=version,
                  source_version=(ROOT / 'VERSION').read_text().strip(), python=python, system=system,
                  system_source_commit=system_source,
                  system_kind='pinned-internal-system' if system['sha256'] == SYSTEM['sha256'] else 'standard-source-rebuild',
                  source_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                  source_dirty=dirty, files=files, signing='unsigned-internal-candidate')
    record['compatibility'] = platform
    record['build_id'] = hashlib.sha256(json.dumps(record, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    (bundle / 'candidate.json').write_text(json.dumps(record, sort_keys=True, indent=2) + '\n')
    (bundle / 'candidate.json').chmod(0o644)
    return record
