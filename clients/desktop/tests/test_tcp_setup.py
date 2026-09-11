import importlib.util,json,tarfile,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
import package_tcp_setup as package
spec=importlib.util.spec_from_file_location('setup_installer',ROOT/'clients/linux/install-tcp-setup.py');setup=importlib.util.module_from_spec(spec);spec.loader.exec_module(setup)

def unpack(archive,root):
 root.mkdir()
 with tarfile.open(archive) as a:
  members=a.getmembers()
  for m in members:
   target=root/Path(m.name).relative_to('FamilyConnect-TCP-Setup-0.1.0');target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(a.extractfile(m).read())
 return root

def test_setup_is_reproducible_and_self_contained(tmp_path):
 a=tmp_path/'a';b=tmp_path/'b';assert package.build(a)==package.build(b)
 with tarfile.open(a) as archive:
  members=archive.getmembers();assert len(members)==8
  assert all(m.isfile() and m.uid==m.gid==m.mtime==0 for m in members)
 root=unpack(a,tmp_path/'setup');payload=setup.verified(root)
 assert set(payload)==setup.FILES
 assert payload['clients/desktop/update.pub']==(ROOT/'clients/desktop/update.pub').read_bytes()
 assert not any('backend.py' in n or '.git' in n or n.endswith('.key') for n in payload)

@pytest.mark.parametrize('attack',['tamper','symlink','manifest','missing','parent_link'])
def test_setup_refuses_changed_payload(tmp_path,attack):
 archive=tmp_path/'a';package.build(archive);root=unpack(archive,tmp_path/'setup');p=root/'scripts/tcp_delivery.py'
 if attack=='tamper':p.write_text('changed')
 elif attack=='symlink':p.unlink();p.symlink_to(ROOT/'scripts/tcp_delivery.py')
 elif attack=='missing':p.unlink()
 elif attack=='parent_link':
  (root/'scripts').rename(root/'other');(root/'scripts').symlink_to(root/'other',target_is_directory=True)
 else:
  data=json.loads((root/'manifest.json').read_text());data['sha256']['../evil']='a'*64;(root/'manifest.json').write_text(json.dumps(data))
 with pytest.raises(ValueError):setup.verified(root)

def test_setup_refuses_existing_output_and_invalid_version(tmp_path):
 p=tmp_path/'a';p.write_bytes(b'keep')
 with pytest.raises(FileExistsError):package.build(p)
 assert p.read_bytes()==b'keep'
 with pytest.raises(ValueError):package.build(tmp_path/'b','../bad')

def test_bootstrap_preflight_missing_dependency_before_lock(monkeypatch):
 spec=importlib.util.spec_from_file_location('bootstrap',ROOT/'clients/linux/install-tcp-updater.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 monkeypatch.setattr(module.os,'geteuid',lambda:0);monkeypatch.setattr(module.sys,'argv',['bootstrap'])
 monkeypatch.setattr(module.shutil,'which',lambda name:None)
 monkeypatch.setattr(module.os,'open',lambda *a,**k:pytest.fail('opened lock before dependency check'))
 with pytest.raises(ValueError,match='Missing setup dependency'):module.main()


def test_setup_executes_verified_private_snapshot(tmp_path,monkeypatch):
 archive=tmp_path/'a';package.build(archive);root=unpack(archive,tmp_path/'setup')
 monkeypatch.setattr(setup.os,'geteuid',lambda:0);monkeypatch.setattr(setup.sys,'argv',['install.py'])
 monkeypatch.setattr(setup,'__file__',str(root/'install.py'))
 original=setup.tempfile.TemporaryDirectory
 def temporary(**kwargs):
  assert kwargs['dir']=='/run'
  return original(prefix=kwargs['prefix'],dir=tmp_path)
 monkeypatch.setattr(setup.tempfile,'TemporaryDirectory',temporary)
 def execute(path,**kwargs):
  snapshot=Path(path).parents[2]
  assert snapshot.stat().st_mode&0o777==0o700
  expected=(root/'clients/linux/install-tcp-updater.py').read_bytes()
  (root/'clients/linux/install-tcp-updater.py').write_bytes(b'changed after verification')
  assert Path(path).read_bytes()==expected and Path(path).stat().st_mode&0o777==0o600
  assert kwargs['run_name']=='__main__'
 monkeypatch.setattr(setup.runpy,'run_path',execute)
 setup.main()
 assert not list(tmp_path.glob('family-connect-setup-*'))
