# Operator-only standalone setup acceptance in a VM

These recipes build a Debian 12 guest with its own Linux kernel and run it under
QEMU TCG in a separate unprivileged Docker runner. No host networking, KVM, host
root filesystem, profiles or private keys are mounted into the guest.

Use a new scratch directory for each run. Copy these recipes there, plus the
independently checked setup archive as `setup.tar.gz`. `accept.py` pins the tested
setup SHA256 deliberately: update that pin only after validating a new artifact.
Build `Dockerfile.guest` as `family-connect-setup-vm:local` and `Dockerfile.runner`
as `family-connect-qemu-check:local`. Create a stopped container from the guest
image and `docker export --output SCRATCH/rootfs.tar CONTAINER`; remove that
container after export. Run the QEMU image with SCRATCH mounted at `/work`, command
`python3 /work/run.py`. Do not mount the repository into this runner or guest.

The runner makes a 2 GiB ext4 virtual disk, supplies the guest's kernel/initramfs,
and boots systemd. Normal networking uses QEMU user-mode NAT and guest
systemd-networkd/resolved. The guest verifies the setup hash, installs bootstrap,
fetches the public signed TCP catalog/component, executes Xray's version check,
checks no VPN was started, reinstalls bootstrap and rejects arbitrary broker args.
The service prints `FC_VM_RESULT` then powers off. `result.json` and `serial.log`
are the acceptance evidence. Success requires `passed: true`, not just QEMU exit 0.

This checks headless root installation, not GTK, interactive polkit, profiles,
VPN data traffic or recovery. It depends on a live unexpired public TCP catalog;
no production signing key is used. The base image/APT package revisions are not
pinned snapshots. Treat the VM image/logs as local test artifacts, not releases.
