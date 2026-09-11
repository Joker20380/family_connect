import importlib.util,json,struct,tarfile
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('tcp_package',ROOT/'scripts/package_tcp.py');package=importlib.util.module_from_spec(spec);spec.loader.exec_module(package)

def elf(path):
 data=bytearray(64);data[:6]=b'\x7fELF\x02\x01';struct.pack_into('<H',data,18,62);path.write_bytes(data);return path

def test_archive_is_deterministic_and_contains_only_component_payload(tmp_path):
 binary=elf(tmp_path/'xray');a=tmp_path/'a.tar.gz';b=tmp_path/'b.tar.gz'
 assert package.build(binary,a)==package.build(binary,b) and a.read_bytes()==b.read_bytes()
 with tarfile.open(a) as archive:
  names={x.name.removeprefix('FamilyConnect-TCP-amd64/') for x in archive.getmembers()}
  assert names=={'bin/xray','lib/helper','lib/backend.py','lib/profile_config.py','lib/LICENSE','systemd/family-connect-tcp@.service','install.py','README.txt','manifest.json'}
  manifest=json.load(archive.extractfile('FamilyConnect-TCP-amd64/manifest.json'))
  assert set(manifest['sha256'])==names-{'manifest.json'}
  assert all(x.uid==x.gid==x.mtime==0 for x in archive.getmembers())

def test_packager_refuses_overwrite(tmp_path):
 output=tmp_path/'existing';output.write_bytes(b'keep')
 with pytest.raises(FileExistsError):package.build(elf(tmp_path/'xray'),output)
 assert output.read_bytes()==b'keep'

def test_packager_rejects_wrong_architecture(tmp_path):
 binary=elf(tmp_path/'xray');raw=bytearray(binary.read_bytes());struct.pack_into('<H',raw,18,183);binary.write_bytes(raw)
 with pytest.raises(ValueError):package.build(binary,tmp_path/'result')
 assert not (tmp_path/'result').exists()
