"""Deterministic private A/B qualification from one exact, committed source."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from .bundle import build, safe_path, source_bytes, verify
from .contracts import canonical, digest, fail, load, typed
from .materials import SLOTS, public_hex
from .private_files import checked, read_private, write_private
from .provenance import check_inputs, validate
from .remote import build_agent
from .role_config import DISABLED, ROLES

GO_IMAGE='sha256:ab3d6955bbc813a0f3fdf220c1d817dd89c0b3f283777db8ece4a32fe7858edd'


def git_bytes(commit, path):
    if not typed(commit,'commit'):
        fail('package_frozen_commit')
    safe_path(path)
    return subprocess.check_output(['git','show',commit+':'+path],stderr=subprocess.DEVNULL)


def frozen_files(commit):
    names=subprocess.check_output(['git','ls-tree','-r','--name-only',commit,'fleet','LICENSE','THIRD_PARTY_NOTICES.md']).decode().splitlines()
    selected={name:git_bytes(commit,name) for name in names if name in ('LICENSE','THIRD_PARTY_NOTICES.md')
              or name.startswith('fleet/') and '/tests/' not in name and '__pycache__' not in name}
    for name,content in selected.items():
        if Path(name).read_bytes()!=content:
            fail('package_worktree_not_frozen')
    if set(Path('fleet').glob('*.py'))!={Path(name) for name in selected if name.startswith('fleet/') and name.endswith('.py') and name.count('/')==1}:
        fail('package_untracked_agent_source')
    return selected


def capsule(artifact_root, maps):
    records=load((artifact_root/'mesh-source-roots.private.json').read_bytes())
    files=maps['mesh-gateway']['files']
    if len(files)!=282:
        fail('canonical_capsule_file_count')
    for location in records['roots']:
        root=Path(location).absolute()
        try:
            contents={name:source_bytes(root,name) for name in files}
            if all(digest(contents[name])==expected for name,expected in files.items()):
                return contents
        except (OSError,ValueError):
            continue
    fail('EXACT_CANONICAL_MESH_CAPSULE_MISSING_OR_CORRUPT')


def operator_probe(source, patch, output, *, expected, cache=None):
    if (expected['source_inventory_sha256']!=digest(canonical({name:digest(content) for name,content in source.items()}))
            or expected['patch_sha256']!=digest(patch) or expected['compiler_image']!=GO_IMAGE):
        fail('operator_probe_source_binding')
    source_root=output/'operator-source'
    source_root.mkdir(mode=0o700)
    for name,content in source.items():
        path=source_root/safe_path(name)
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(content)
    applied=subprocess.run(['git','apply','--check','-'],cwd=source_root,input=patch,capture_output=True)
    if applied.returncode:
        fail('operator_probe_patch_binding')
    subprocess.run(['git','apply','-'],cwd=source_root,input=patch,capture_output=True,check=True)
    if cache is not None and cache.exists():
        if load(source_bytes(cache,'receipt.json'))!=expected:
            fail('operator_probe_cache_receipt')
        for revision in ('first','second'):
            name='operator-probe-'+revision
            content=source_bytes(cache,name,64*1024*1024)
            if digest(content)!=expected['sha256'] or len(content)!=expected['size']:
                fail('operator_probe_cache_binding')
            write_private(output/name,content,mode=0o500)
        return expected
    log=output/'operator-build.log'
    binaries=[]
    with log.open('wb') as stream:
        for revision in ('first','second'):
            result=subprocess.run(['docker','run','--rm','-v',str(source_root)+':/src:ro',
                '-v',str(output)+':/out','-w','/src','-e','GOTOOLCHAIN=local','-e','CGO_ENABLED=0',GO_IMAGE,
                'go','build','-trimpath','-buildvcs=false','-ldflags=-buildid=','-o','/out/operator-probe-'+revision,
                './cmd/telemost-binary'],stdout=stream,stderr=subprocess.STDOUT,timeout=600)
            if result.returncode:
                fail('operator_probe_build')
            binaries.append((output/('operator-probe-'+revision)).read_bytes())
    if binaries[0]!=binaries[1]:
        fail('operator_probe_nondeterministic')
    metadata=dict(sha256=digest(binaries[0]),size=len(binaries[0]),compiler_image=GO_IMAGE,
        source_inventory_sha256=digest(canonical({name:digest(content) for name,content in source.items()})),
        patch_sha256=digest(patch),purpose='OPERATOR_ONLY_DISPOSABLE_TARGET_EGRESS')
    if metadata!=expected:
        fail('operator_probe_rebuild_binding')
    return metadata


def prepare(commit, artifact_root, key_path, output):
    os.umask(0o077)
    artifact_root=checked(artifact_root.absolute(),directory=True)
    output=output.absolute()
    if output.exists() or output.is_symlink():
        fail('package_output_exists')
    checked(output.parent,directory=True,owner=os.geteuid())
    sources=frozen_files(commit)
    native=validate(load(sources['fleet/inventory/deployable-gateway-v1.json']))
    inventory=validate(load(sources['fleet/inventory/deployable-gateway-v2.json']))
    maps=load((artifact_root/'bound-inputs/source-inventories.json').read_bytes())
    check_inputs(native,artifact_root/'bound-inputs',maps)
    canonical_source=capsule(artifact_root,maps)
    monitor=next(artifact for artifact in inventory['artifacts'] if artifact['id']=='rehearsal-monitoring')
    maps['rehearsal-monitoring']=dict(source_commit=monitor['source_commit'],files={'fleet/monitoring.py':digest(sources['fleet/monitoring.py'])})
    if digest(canonical(maps['rehearsal-monitoring']))!=monitor['source_inventory_sha256']:
        fail('monitor_source_inventory_binding')
    key_path=key_path.absolute()
    repository=Path(subprocess.check_output(['git','rev-parse','--show-toplevel']).decode().strip())
    if key_path.is_relative_to(repository) and subprocess.run(['git','check-ignore','-q',str(key_path)],capture_output=True).returncode:
        fail('private_signer_must_be_outside_git')
    if not key_path.exists():
        key=Ed25519PrivateKey.generate()
        write_private(key_path,key.private_bytes(serialization.Encoding.Raw,serialization.PrivateFormat.Raw,serialization.NoEncryption()))
    else:
        key=Ed25519PrivateKey.from_private_bytes(read_private(key_path,owner=os.geteuid(),limit=32))
    raw_private=key.private_bytes(serialization.Encoding.Raw,serialization.PrivateFormat.Raw,serialization.NoEncryption())
    if raw_private in tuple(bytes([value])*32 for value in range(256)):
        fail('synthetic_signing_key_forbidden')
    output.mkdir(mode=0o700)
    probe=operator_probe(canonical_source,sources['fleet/operator_probe.patch'],output,
        expected=load(sources['fleet/inventory/operator-probe.json']),cache=artifact_root/'operator-qualification')
    agent=build_agent({name:content for name,content in sources.items()
                       if name.startswith('fleet/') and name.count('/')==1 and name.endswith('.py')})
    write_private(output/'agent.pyz',agent,mode=0o500)
    write_private(output/'bundle.pub',bytes.fromhex(public_hex(key.public_key())),mode=0o444)
    contents={artifact['path']:source_bytes(artifact_root/'bound-inputs',artifact['path'],64*1024*1024) for artifact in native['artifacts']}
    for name,content in sources.items():
        if name.startswith('fleet/') and name.endswith('.py') and '/' not in name[len('fleet/'):]:
            contents['runtime/'+name]=content
        elif name.startswith('fleet/runtime/'):
            contents[name.removeprefix('fleet/')]=content
        elif name.startswith('fleet/templates/'):
            contents[name.removeprefix('fleet/')]=content
    contents['runtime/monitoring.py']=sources['fleet/monitoring.py']
    contents['metadata/deployable.json']=canonical(inventory)
    contents['metadata/agent.json']=canonical(dict(sha256=digest(agent)))
    contents['metadata/operator-probe.json']=canonical(probe)
    contents['metadata/source-inventories.json']=canonical(maps)
    dependencies=load(sources['fleet/inventory/python-rehearsal.json'])
    for record in dependencies['wheels']:
        content=source_bytes(artifact_root/'python-wheels',Path(record['path']).name)
        if digest(content)!=record['sha256'] or len(content)!=record['size']:
            fail('python_dependency_binding')
        contents[record['path']]=content
    contents['metadata/python-dependencies.json']=canonical(dependencies)
    contents['metadata/runtime-source.json']=canonical(dict(source_commit=commit,files={name:digest(content) for name,content in sources.items()}))
    contents['licenses/family-connect.txt']=sources['LICENSE']
    contents['licenses/third-party-notices.txt']=sources['THIRD_PARTY_NOTICES.md']
    contents['licenses/mesh-dependencies.txt']=canonical_source['licenses/dependencies.txt']
    for name,filename in (('awg-engine','LICENSE'),('awg-tools','COPYING')):
        artifact=next(item for item in native['artifacts'] if item['id']==name)
        contents['licenses/'+name+'.txt']=subprocess.check_output(['git','-C',str(artifact_root/(name+'-source.git')),
            'show',artifact['source_commit']+':'+filename],stderr=subprocess.DEVNULL)
    locations=load((artifact_root/'upstream-source-locations.private.json').read_bytes())
    xray=next(item for item in native['artifacts'] if item['id']=='tcp-xray')
    contents['licenses/xray.txt']=subprocess.check_output(['git','-C',locations['xray_source'][0],
        'show',xray['source_commit']+':LICENSE'],stderr=subprocess.DEVNULL)
    for artifact in inventory['artifacts']:
        if digest(contents[artifact['path']])!=artifact['sha256'] or len(contents[artifact['path']])!=artifact['size']:
            fail('deployable_source_binding')
    results={}
    for revision in ('A','B'):
        members=dict(contents)
        members['metadata/revision.json']=canonical(dict(revision=revision,monitoring_marker='rehearsal-'+revision))
        stage=output/('source-'+revision)
        stage.mkdir(mode=0o700)
        for name,content in members.items():
            path=stage/safe_path(name)
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(content)
        specification=dict(source_commit=commit,scope='rehearsal',roles=list(ROLES),secret_slots=list(SLOTS),members=[
            dict(path=name,source=name,sha256=digest(content),mode=0o555 if name.startswith('bin/') else 0o444,
                 restart_group='monitoring' if 'monitor' in name else 'mesh',secret_slots=[])
            for name,content in sorted(members.items())])
        outputs=[]
        for attempt in ('first','second'):
            destination=output/(revision+'-'+attempt)
            manifest=build(stage,specification,key,destination)
            verified,loaded=verify(destination,key.public_key(),manifest['bundle_id'])
            if loaded!=members:
                fail('package_reverification')
            outputs.append({path.name:path.read_bytes() for path in destination.iterdir()})
        if outputs[0]!=outputs[1]:
            fail('package_nondeterministic')
        results[revision]=dict(bundle_id=manifest['bundle_id'],archive_sha256=manifest['archive_sha256'],
            manifest_sha256=digest(outputs[0]['manifest.json']),signature_sha256=digest(outputs[0]['manifest.sig']),
            sha256_inventory_sha256=digest(outputs[0]['sha256.json']))
    receipt=dict(schema=1,scope='SOURCE_PACKAGE_ONLY',source_commit=commit,bundles=results,
        bundle_signer_sha256=digest(bytes.fromhex(public_hex(key.public_key()))),agent_sha256=digest(agent),
        permit_source_sha256=digest(sources['fleet/permit.py']),remote_agent_source_sha256=digest(sources['fleet/remote_agent.py']),
        roles=list(ROLES),disabled_roles=list(DISABLED),
        operator_probe=probe,reproducibility='PASS',target_reverification='PASS',production_writes=0,
        catalog_publications=0,user_invitations=0,paid_events=0,phone_actions=0)
    write_private(output/'receipt.json',canonical(receipt))
    return receipt
