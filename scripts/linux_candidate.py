"""Bind the full user bundle to the reviewed internal system component."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SYSTEM = dict(build_id='8708ba6d5e218f86b42d862dd5a66237e974a03d5434e8f1c30524b16720e2da',
              sha256='bdd7e04b8ca78a232acccd881004cfb3b6c96b13dc3c608d0b919f53f40f02d9', size=49247776,
              source_digest='cfcb7bae874765cfe6a66742fbeed55cb03399b7e32c13d5a5edcd212299df61')


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'packaging/linux' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def embed(bundle, archive, *, standard_rebuild=False):
    raw = archive.read_bytes()
    if not standard_rebuild and (len(raw) != SYSTEM['size'] or hashlib.sha256(raw).hexdigest() != SYSTEM['sha256']):
        raise ValueError('Expected accepted L03.1/build-9, not a same-version replacement')
    import io
    import tarfile
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:gz') as source:
        installer_raw = source.extractfile('FamilyConnect-MESH-system-amd64/install.py').read()
        manifest = json.load(source.extractfile('FamilyConnect-MESH-system-amd64/manifest.json'))
    reference = json.loads((ROOT / 'packaging/linux/system-reference.json').read_text())
    if any(manifest['sha256'].get(name) != checksum for name, checksum in reference['source_files'].items()):
        raise ValueError('System sources differ from accepted L03.1')
    if manifest['source_digest'] != reference['native_source_digest']:
        raise ValueError('Native source reference mismatch')
    expected = dict(build_id=manifest['build_id'], source_digest=manifest['source_digest'], size=len(raw),
                    sha256=hashlib.sha256(raw).hexdigest(), installer_sha256=hashlib.sha256(installer_raw).hexdigest())
    with tempfile.TemporaryDirectory(prefix='fc-candidate-verify-') as temporary:
        component = load('candidate_setup').extract_verified(raw, expected, Path(temporary))
        runtime = json.loads((component / 'python-runtime.json').read_text())
        if json.loads((component / 'rns/build.json').read_text())['source_digest'] != reference['rns_source_digest']:
            raise ValueError('RNS source reference mismatch')
        if runtime['python'] != [3, 12]:
            raise ValueError('The accepted runtime requires Python3.12')
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


def seal(bundle, version, system, python):
    if not re.fullmatch(r'0\.2\.12~l03\.2\.[1-9][0-9]*', version):
        raise ValueError('Explicit reserved internal Linux candidate version required')
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
    record = dict(schema=1, runtime_contract=2, internal_version=version,
                  source_version=(ROOT / 'VERSION').read_text().strip(), python=python, system=system,
                  system_source_commit='f826dbdfb562541bde95d2fcbecc1d944d15da3d',
                  system_kind='accepted-build-9' if system['sha256'] == SYSTEM['sha256'] else 'standard-source-rebuild',
                  source_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                  source_dirty=dirty, files=files, signing='unsigned-internal-candidate')
    record['build_id'] = hashlib.sha256(json.dumps(record, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    (bundle / 'candidate.json').write_text(json.dumps(record, sort_keys=True, indent=2) + '\n')
    (bundle / 'candidate.json').chmod(0o644)
    return record
