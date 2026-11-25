import copy
import gzip
import io
import json
import os
from pathlib import PurePosixPath
import sys
import tarfile

import pytest

from scripts import control_ha_owner_overlay as overlay


def encoded(value):
    return json.dumps(value, sort_keys=True).encode()


def source_files():
    return {name: b'private source fixture\n' + name.encode() for name in overlay.plan.upgrade.source.SOURCES}


def expectation():
    return dict(source_commit='a' * 40, files={name: dict(size=len(raw), sha256=overlay.digest(raw))
                                            for name, raw in source_files().items()})


def source_layer(change=None):
    files = {'app/' + name: raw for name, raw in source_files().items()}
    directories = {str(parent) for name in files for parent in PurePosixPath(name).parents if str(parent) != '.'}
    entries = []
    for name in sorted(set(files) | directories):
        member = tarfile.TarInfo(name)
        member.type = tarfile.DIRTYPE if name in directories else tarfile.REGTYPE
        member.mode = 0o755 if name in directories else 0o644
        raw = files.get(name, b'')
        member.size = len(raw)
        entries.append((member, raw))
    if change:
        change(entries)
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode='w', format=tarfile.PAX_FORMAT) as archive:
        for member, raw in entries:
            archive.addfile(member, io.BytesIO(raw))
    return output.getvalue()


def image_archive(monkeypatch, *, layer=None, config_change=None, manifest_change=None, archive_change=None):
    files = {'oci-layout': encoded({'imageLayoutVersion': '1.0.0'})}
    def blob(raw, media):
        identifier = 'sha256:' + overlay.digest(raw)
        files['blobs/sha256/' + identifier[7:]] = raw
        return dict(mediaType=media, size=len(raw), digest=identifier)
    original_layer = blob(b'original layer is outside this overlay audit', 'application/vnd.oci.image.layer.v1.tar')
    original = dict(os='linux', architecture='amd64', config={'Env': ['PASSWORD=private-value'], 'User': 'console'},
                    rootfs={'type': 'layers', 'diff_ids': [original_layer['digest']]})
    original_manifest = dict(schemaVersion=2, mediaType=overlay.MANIFEST,
                            config=blob(encoded(original), overlay.CONFIG), layers=[original_layer])
    baseline = blob(encoded(original_manifest), overlay.MANIFEST)
    raw = source_layer() if layer is None else layer
    updated = copy.deepcopy(original)
    updated['rootfs']['diff_ids'].append('sha256:' + overlay.digest(raw))
    if config_change:
        config_change(updated)
    selected = dict(schemaVersion=2, mediaType=overlay.MANIFEST, config=blob(encoded(updated), overlay.CONFIG),
                    layers=[original_layer, blob(gzip.compress(raw, mtime=0), 'application/vnd.oci.image.layer.v1.tar+gzip')])
    if manifest_change:
        manifest_change(selected)
    candidate = blob(encoded(selected), overlay.MANIFEST)
    files['index.json'] = encoded(dict(schemaVersion=2, manifests=[baseline, candidate]))
    if archive_change:
        archive_change(files, baseline, candidate, selected)
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode='w', format=tarfile.USTAR_FORMAT) as archive:
        for name, body in files.items():
            member = tarfile.TarInfo(name)
            member.size, member.mode = len(body), 0o600
            archive.addfile(member, io.BytesIO(body))
    monkeypatch.setitem(overlay.plan.upgrade.ROLES, 'console', baseline['digest'])
    return output.getvalue(), candidate['digest']


def test_exact_source_delta_never_dispatches_or_authorizes(monkeypatch):
    raw, candidate = image_archive(monkeypatch)
    monkeypatch.setattr(overlay.plan.upgrade, 'docker', lambda *args: pytest.fail('Docker dispatch'))
    receipt = overlay.inspect(io.BytesIO(raw), 'console', candidate, expectation())
    assert receipt['source_matches'] and receipt['layer_content_closed'] and receipt['changed_sources'] == []
    assert all(receipt[field] is False for field in ('independent_approval', 'runtime_qualified', 'capture_permitted', 'deployed'))
    assert 'private-value' not in json.dumps(receipt) and 'private source fixture' not in json.dumps(receipt)


def test_closed_but_stale_source_is_not_accepted(monkeypatch):
    raw, candidate = image_archive(monkeypatch)
    expected = expectation()
    selected = next(iter(expected['files']))
    expected['files'][selected]['sha256'] = 'f' * 64
    receipt = overlay.inspect(io.BytesIO(raw), 'console', candidate, expected)
    assert receipt['status'] == 'OWNER_OVERLAY_SOURCE_MISMATCH'
    assert receipt['changed_sources'] == [selected] and not receipt['source_matches']


@pytest.mark.parametrize('mutation', ['extra', 'whiteout', 'absolute', 'traversal', 'duplicate', 'missing', 'uid', 'gid',
                                     'executable', 'setuid', 'symlink', 'hardlink', 'fifo', 'device', 'pax', 'directory',
                                     'directory-mode', 'empty', 'alias', 'trailer'])
def test_non_source_overlay_refuses(mutation):
    def change(entries):
        member, body = next(entry for entry in entries if entry[0].isreg())
        if mutation in ('extra', 'whiteout'):
            extra = tarfile.TarInfo('app/.wh.control' if mutation == 'whiteout' else 'etc/cron.d/extra')
            extra.mode, extra.size = 0o644, 4
            entries.append((extra, b'bad\n'))
        elif mutation in ('absolute', 'traversal', 'alias'):
            member.name = {'absolute': '/' + member.name, 'traversal': 'app/../' + member.name,
                           'alias': './' + member.name}[mutation]
        elif mutation == 'duplicate':
            entries.append((copy.copy(member), body))
        elif mutation == 'missing':
            entries.remove((member, body))
        elif mutation in ('uid', 'gid'):
            setattr(member, mutation, 1000)
        elif mutation in ('executable', 'setuid'):
            member.mode = 0o755 if mutation == 'executable' else 0o4644
        elif mutation in ('symlink', 'hardlink', 'fifo', 'device'):
            member.type = {'symlink': tarfile.SYMTYPE, 'hardlink': tarfile.LNKTYPE,
                           'fifo': tarfile.FIFOTYPE, 'device': tarfile.CHRTYPE}[mutation]
            member.size = 0
            if mutation in ('symlink', 'hardlink'):
                member.linkname = '/unexpected'
        elif mutation == 'pax':
            member.pax_headers = {'SCHILY.xattr.security.capability': 'unexpected'}
        elif mutation.startswith('directory'):
            directory = next(entry[0] for entry in entries if entry[0].isdir())
            if mutation == 'directory':
                directory.type = tarfile.REGTYPE
            else:
                directory.mode = 0o777
        elif mutation == 'empty':
            member.size = 0
    raw = source_layer(change)
    if mutation == 'trailer':
        raw += b'x' * 512
    with pytest.raises((ValueError, tarfile.TarError)):
        overlay.layer_contents(raw, expectation()['files'])


@pytest.mark.parametrize('mutation', ['config', 'os', 'architecture', 'prefix', 'diff', 'count', 'descriptor', 'base',
                                     'urls', 'layer-type', 'layer-hash', 'config-hash', 'index', 'layout', 'json', 'extra'])
def test_oci_reference_or_runtime_drift_refuses(monkeypatch, mutation):
    def config_change(config):
        if mutation == 'config':
            config['config']['User'] = 'root'
        elif mutation in ('os', 'architecture'):
            config[mutation] = 'changed'
        elif mutation in ('prefix', 'diff'):
            config['rootfs']['diff_ids'][0 if mutation == 'prefix' else -1] = 'sha256:' + 'f' * 64
        elif mutation == 'count':
            config['rootfs']['diff_ids'].append('sha256:' + 'f' * 64)
    def manifest_change(manifest):
        if mutation == 'descriptor':
            manifest['layers'][-1]['size'] += 1
        elif mutation == 'base':
            manifest['layers'][0] = copy.deepcopy(manifest['layers'][0])
            manifest['layers'][0]['size'] += 1
        elif mutation == 'urls':
            manifest['layers'][-1]['urls'] = ['https://example.invalid']
        elif mutation == 'layer-type':
            manifest['layers'][-1]['mediaType'] = 'unexpected'
    def archive_change(files, baseline, candidate, selected):
        if mutation in ('layer-hash', 'config-hash'):
            descriptor = selected['layers'][-1] if mutation == 'layer-hash' else selected['config']
            files['blobs/sha256/' + descriptor['digest'][7:]] += b'changed'
        elif mutation == 'index':
            files['index.json'] = encoded(dict(schemaVersion=2, manifests=[candidate, candidate]))
        elif mutation == 'layout':
            files['oci-layout'] = encoded({'imageLayoutVersion': '2.0.0'})
        elif mutation == 'json':
            files['index.json'] = b'{"schemaVersion":2,"schemaVersion":2,"manifests":[]}'
        elif mutation == 'extra':
            files['unexpected.py'] = b'no execution'
    raw, candidate = image_archive(monkeypatch, config_change=config_change,
                                   manifest_change=manifest_change, archive_change=archive_change)
    with pytest.raises(ValueError):
        overlay.inspect(io.BytesIO(raw), 'console', candidate, expectation())


def test_compressed_expansion_is_bounded(monkeypatch):
    raw, candidate = image_archive(monkeypatch, layer=b'\0' * (overlay.LIMIT + 1))
    with pytest.raises(ValueError, match='OCI_DIFF_PIN'):
        overlay.inspect(io.BytesIO(raw), 'console', candidate, expectation())


@pytest.mark.parametrize('mutation', ['commit', 'scope', 'sha', 'size', 'boolean'])
def test_unpinned_expected_sources_refuse(mutation):
    expected = expectation()
    selected = next(iter(expected['files']))
    if mutation == 'commit':
        expected['source_commit'] = 'HEAD'
    elif mutation == 'scope':
        expected['files']['unexpected'] = expected['files'][selected]
    elif mutation == 'sha':
        expected['files'][selected]['sha256'] = 'not-a-digest'
    else:
        expected['files'][selected]['size'] = True if mutation == 'boolean' else overlay.LIMIT
    with pytest.raises(ValueError):
        overlay.expected_sources(expected)


@pytest.fixture
def private_archive(tmp_path, monkeypatch):
    tmp_path.chmod(0o700)
    raw, candidate = image_archive(monkeypatch)
    path = tmp_path / 'images.tar'
    path.write_bytes(raw)
    path.chmod(0o600)
    return path, overlay.digest(raw), candidate


@pytest.mark.parametrize('mutation', ['mode', 'parent', 'symlink', 'hardlink', 'fifo', 'pin', 'oversize'])
def test_unsafe_private_archive_refuses(private_archive, mutation):
    path, pinned, candidate = private_archive
    if mutation == 'mode':
        path.chmod(0o644)
    elif mutation == 'parent':
        path.parent.chmod(0o755)
    elif mutation == 'symlink':
        alias = path.parent / 'alias'
        alias.symlink_to(path)
        path = alias
    elif mutation == 'hardlink':
        os.link(path, path.parent / 'alias')
    elif mutation == 'fifo':
        path.unlink()
        os.mkfifo(path, 0o600)
    elif mutation == 'pin':
        pinned = '0' * 64
    else:
        with path.open('r+b') as source:
            source.truncate(overlay.ARCHIVE_LIMIT + 1)
    with pytest.raises((ValueError, OSError)):
        overlay.inspect_private(path, pinned, 'console', candidate, expectation())


def test_changed_archive_refuses_before_receipt(private_archive, monkeypatch):
    path, pinned, candidate = private_archive
    original = overlay.inspect
    def changed(*args):
        result = original(*args)
        os.utime(path, ns=(1, 1))
        return result
    monkeypatch.setattr(overlay, 'inspect', changed)
    with pytest.raises(ValueError, match='ARCHIVE_CHANGED'):
        overlay.inspect_private(path, pinned, 'console', candidate, expectation())


@pytest.mark.parametrize('mode,code', [('match', 0), ('mismatch', 2), ('refuse', 1), ('decode', 1)])
def test_read_only_cli_and_sanitized_failure(private_archive, monkeypatch, capsys, mode, code):
    path, pinned, candidate = private_archive
    value = expectation()
    if mode == 'mismatch':
        value['files'][next(iter(value['files']))]['sha256'] = 'f' * 64
    sources = path.parent / 'sources.json'
    raw = encoded(value)
    sources.write_bytes(raw)
    sources.chmod(0o600)
    before = {entry.name: (entry.stat().st_mtime_ns, entry.read_bytes()) for entry in path.parent.iterdir()}
    if mode == 'decode':
        def failed_decoder(*args, **kwargs):
            raise overlay.zlib.error('private-value')
        monkeypatch.setattr(overlay.gzip, 'GzipFile', failed_decoder)
    monkeypatch.setattr(sys, 'argv', ['overlay', '--archive', str(path), '--archive-sha256',
        '0' * 64 if mode == 'refuse' else pinned, '--sources', str(sources), '--sources-sha256',
        overlay.digest(raw), '--role', 'console', '--candidate', candidate])
    assert overlay.main() == code
    output = capsys.readouterr()
    assert 'private-value' not in output.out + output.err
    if code == 1:
        assert output.out == '' and output.err == 'OWNER_OVERLAY_REFUSED\n'
    else:
        assert json.loads(output.out)['source_matches'] is (code == 0) and output.err == ''
    assert before == {entry.name: (entry.stat().st_mtime_ns, entry.read_bytes()) for entry in path.parent.iterdir()}
