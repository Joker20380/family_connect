import os,subprocess,json,re
from pathlib import Path
base=Path('/work');root=base/'rootfs';root.mkdir()
subprocess.run(['tar','-xf',str(base/'rootfs.tar'),'-C',str(root)],check=True)
(root/'.dockerenv').unlink(missing_ok=True)
p=root/'etc/resolv.conf';p.unlink(missing_ok=True);p.symlink_to('/run/systemd/resolve/stub-resolv.conf')
(root/'etc/fstab').write_text('/dev/vda / ext4 defaults 0 1\n')
(root/'etc/hostname').write_text('fc-setup-test\n')
image=base/'root.img'
with image.open('wb') as f:f.truncate(2*1024**3)
subprocess.run(['mkfs.ext4','-q','-F','-d',str(root),str(image)],check=True)
kernel=next((root/'boot').glob('vmlinuz-*'));initrd=next((root/'boot').glob('initrd.img-*'))
args=['qemu-system-x86_64','-machine','accel=tcg','-m','1024','-smp','2','-nographic','-no-reboot','-kernel',str(kernel),'-initrd',str(initrd),'-append','root=/dev/vda rw console=ttyS0','-drive','file='+str(image)+',format=raw,if=virtio','-netdev','user,id=n0','-device','virtio-net-pci,netdev=n0']
with (base/'serial.log').open('w') as log:
 subprocess.run(args,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=900)
raw=(base/'serial.log').read_text(errors='replace');matches=re.findall(r'FC_VM_RESULT (\{[^\r\n]*\})',raw)
assert matches,'No VM acceptance result; inspect serial.log'
result=json.loads(matches[-1]);(base/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
assert result.get('passed'),result
