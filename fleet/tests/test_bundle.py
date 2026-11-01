import base64
import copy
import io
import tarfile

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from fleet.bundle import build, codec, safe_path, verify
from fleet.contracts import FleetError, canonical, digest, load


@pytest.fixture
def bundle(tmp_path):
    root = tmp_path / 'source'
    root.mkdir()
    (root / 'runtime').write_bytes(b'synthetic runtime fixture, not a production gateway\n')
    key = Ed25519PrivateKey.from_private_bytes(bytes([1]) * 32)
    spec = dict(source_commit='a'*40, scope='synthetic', roles=['awg'], secret_slots=['awg-material'],
        members=[dict(path='bin/runtime', source='runtime', sha256=digest((root/'runtime').read_bytes()),
        mode=0o555, restart_group='awg', secret_slots=['awg-material'])])
    directory = tmp_path/'bundle'
    manifest = build(root,spec,key,directory)
    return root,spec,key,directory,manifest


def test_reproducible(bundle,tmp_path):
    root,spec,key,directory,manifest = bundle
    second = tmp_path/'second'
    build(root,spec,key,second)
    assert {path.name:path.read_bytes() for path in directory.iterdir()} == {path.name:path.read_bytes() for path in second.iterdir()}
    assert verify(directory,key.public_key(),manifest['bundle_id'])[0] == manifest
    assert [item['path'] for item in manifest['members']] == sorted(item['path'] for item in manifest['members'])


@pytest.mark.parametrize('path',['/etc/passwd','../x','a/../x','a//b','a/./b','a\\b'])
def test_path_rejection(path):
    with pytest.raises(FleetError):safe_path(path)


@pytest.mark.parametrize('kind',['archive','manifest','signature','wrong_key','bundle_id'])
def test_tamper(bundle,kind):
    root,spec,key,directory,manifest = bundle
    if kind in ('archive','manifest','signature'):
        name={'archive':'fc-gateway-'+manifest['bundle_id']+'.tar.zst','manifest':'manifest.json','signature':'manifest.sig'}[kind]
        (directory/name).write_bytes((directory/name).read_bytes()+b'bad')
    with pytest.raises(FleetError):
        verify(directory,Ed25519PrivateKey.generate().public_key() if kind=='wrong_key' else key.public_key(),
               'wrong' if kind=='bundle_id' else manifest['bundle_id'])


@pytest.mark.parametrize('kind',['missing','extra','duplicate','symlink','hardlink','mode','absolute','traversal','target'])
def test_signed_malicious_archive(bundle,kind):
    root,spec,key,directory,manifest = bundle
    archive_name='fc-gateway-'+manifest['bundle_id']+'.tar.zst'
    raw=codec((directory/archive_name).read_bytes(),True)
    output=io.BytesIO()
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r:') as original, tarfile.open(fileobj=output,mode='w',format=tarfile.USTAR_FORMAT) as changed:
        for info in original:
            content=original.extractfile(info).read()
            if kind=='missing':continue
            if kind=='mode':info.mode=0o777
            if kind=='absolute':info.name='/bad'
            if kind=='traversal':info.name='../bad'
            if kind in ('symlink','hardlink'):
                info.type=tarfile.SYMTYPE if kind=='symlink' else tarfile.LNKTYPE
                info.linkname='elsewhere';info.size=0
            changed.addfile(info,io.BytesIO(content))
            if kind in ('extra','duplicate'):
                if kind=='extra':info.name='extra'
                changed.addfile(info,io.BytesIO(content))
    archive=codec(output.getvalue())
    manifest=copy.deepcopy(manifest)
    manifest['archive_sha256']=digest(archive)
    if kind=='target':manifest['members'][0]['target']='ETC/escape'
    payload=canonical(manifest);signature=base64.b64encode(key.sign(payload))
    (directory/archive_name).write_bytes(archive)
    (directory/'manifest.json').write_bytes(payload)
    (directory/'manifest.sig').write_bytes(signature)
    (directory/'sha256.json').write_bytes(canonical({archive_name:digest(archive),'manifest.json':digest(payload),'manifest.sig':digest(signature)}))
    with pytest.raises(FleetError):verify(directory,key.public_key())


def test_secret_and_source_symlink(bundle,tmp_path):
    root,spec,key,directory,manifest=bundle
    (root/'runtime').write_bytes(b'-----BEGIN ' + b'PRIVATE KEY-----')
    spec['members'][0]['sha256']=digest((root/'runtime').read_bytes())
    with pytest.raises(FleetError):build(root,spec,key,tmp_path/'bad')
    (root/'runtime').unlink();(root/'runtime').symlink_to('/etc/hosts')
    with pytest.raises(FleetError):build(root,spec,key,tmp_path/'bad')
