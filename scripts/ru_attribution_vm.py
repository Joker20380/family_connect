"""Build a disposable initramfs from explicit local packages; never install packages."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess


def build(kernel, output, legacy=False):
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    root = output / 'root'
    root.mkdir()
    copied = set()

    def copy_binary(source):
        source = Path(source)
        if str(source) in copied:
            return
        copied.add(str(source))
        target = root / str(source).lstrip('/')
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        target.chmod(source.stat().st_mode & 0o777)
        reply = subprocess.run(['ldd', str(source)], capture_output=True, text=True)
        for dependency in re.findall(r'(/[^\s()]+)', reply.stdout):
            if Path(dependency).is_file():
                copy_binary(dependency)

    for name in ('busybox', 'python3', 'bpftrace', 'modprobe', 'mkfs.ext4', 'dmsetup'):
        copy_binary(shutil.which(name))
    library = Path('/usr/lib/python3.14')
    shutil.copytree(library, root / library.relative_to('/'),
                    ignore=shutil.ignore_patterns('__pycache__', 'test', 'tests'))
    for module in (root / 'usr/lib/python3.14/lib-dynload').glob('*.so'):
        reply = subprocess.run(['ldd', str(module)], capture_output=True, text=True)
        for dependency in re.findall(r'(/[^\s()]+)', reply.stdout):
            if Path(dependency).is_file():
                copy_binary(dependency)
    shutil.copytree(kernel / 'usr/lib/modules', root / 'lib/modules')
    shutil.copytree('/usr/include', root / 'usr/include')
    subprocess.run(['depmod', '-b', str(root), '7.0.0-30-generic'], check=True)
    for directory in ('proc', 'sys', 'dev', 'run', 'tmp', 'test', 'bin', 'etc'):
        (root / directory).mkdir(exist_ok=True)
    for name in ('sh', 'mount', 'mkdir', 'cat', 'echo', 'poweroff', 'sleep', 'hostname', 'ln'):
        (root / 'bin' / name).symlink_to('/usr/bin/busybox')
    (root / 'etc/passwd').write_text('root:x:0:0:root:/root:/bin/sh\n')
    (root / 'etc/group').write_text('root:x:0:\n')
    (root / 'init').write_text('''#!/bin/sh
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
mount -t proc proc /proc
mount -t sysfs sysfs /sys
mount -t devtmpfs devtmpfs /dev
ln -s /proc/self/fd /dev/fd
mount -t tmpfs -o size=32m tmpfs /run
mount -t tmpfs -o size=32m tmpfs /tmp
mkdir -p /sys/fs/cgroup /sys/kernel/tracing
mount -t cgroup2 none /sys/fs/cgroup
mount -t tracefs none /sys/kernel/tracing
hostname fc-attribution-disposable
echo yes > /run/fc-attribution-disposable-vm
modprobe virtio_pci
modprobe virtio_blk
modprobe ext4
modprobe dm-mod
modprobe dm-delay
mkfs.ext4 -q -F /dev/vda
mount /dev/vda /test
python3 -u /ru_attribution_lab.py
echo FC_LAB_EXIT=$?
poweroff -f
''')
    (root / 'init').chmod(0o755)
    for name in ('ru_attribution_recorder.py', 'ru_attribution_trace.bt', 'ru_attribution_lab.py',
                 'ru_attribution_program.py', 'ru_attribution_contract.py', 'ru_attribution_lab_v2.py'):
        shutil.copyfile(Path(__file__).with_name(name), root / name)
    if not legacy:
        init = root / 'init'
        init.write_text(init.read_text().replace('/ru_attribution_lab.py', '/ru_attribution_lab_v2.py'))
    archive = output / 'initramfs.cpio.gz'
    with archive.open('wb') as stream:
        subprocess.run(['bash', '-o', 'pipefail', '-c',
                        'find . -print0 | cpio --null -o --format=newc 2>/dev/null | gzip -1'],
                       cwd=root, stdout=stream, check=True)
    image = next((kernel / 'boot').glob('vmlinuz-*'))
    shutil.copyfile(image, output / 'vmlinuz')
    manifest = {name: hashlib.sha256((output / name).read_bytes()).hexdigest()
                for name in ('vmlinuz', 'initramfs.cpio.gz')}
    (output / 'manifest.json').write_text(json.dumps(manifest))
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kernel', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--legacy', action='store_true')
    args = parser.parse_args()
    print(json.dumps(build(args.kernel, args.output, args.legacy)))
