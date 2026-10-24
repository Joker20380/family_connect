# L03.1 exact system/runtime smoke

This fixture requires an explicitly disposable Docker system with real systemd
255 (Ubuntu24.04), private PID/mount/cgroup/network namespaces, private D-Bus and
systemd-resolved. Never run `smoke.py` on a workstation. No host bus, resolver,
network or cgroup directories may be bind-mounted. `--network none` is mandatory;
the fixture checks PID1, the distinct network namespace and a loopback-only network.

Build context is only this Dockerfile and the four existing Python lockfiles:

```sh
tar -c tests/fixtures/linux_system_runtime/Dockerfile control/requirements.lock \
  device_identity/requirements.lock provisioning/requirements.lock messenger/requirements.lock |
  docker build --target builder -t fc-l031-builder:check -f tests/fixtures/linux_system_runtime/Dockerfile -
```

Use the same bounded context with `--target system` for the isolated installation
image and `--target desktop_tests` for the mandatory GTK-aware desktop suite.
The system image has **no venv, checkout or pip runtime dependencies**. The builder
is separate; its locked distributions are copied only via verified wheel RECORDs.

Build the native worker with `scripts/build_desktop_mesh.py --test`, or verify an
existing standard artifact's complete source inventory against the current tree.
Do not supply the lifetime/combined test-overlay worker. Build RNS with
`python -m scripts.build_desktop_rns --out <fresh-dir>`. Obtain normal binaries
from the existing pinned `pilot/awg31/Dockerfile` (`/opt/awg31`) and
`pilot/tcp/Dockerfile` (`/usr/local/bin/xray`), not a workstation's installation.
Then run in the builder with read-only sources and explicit input mounts:

```sh
/opt/build-venv/bin/python -m scripts.package_mesh_component \
  --native /native --rns /evidence/rns --awg /evidence/awg \
  --tcp /evidence/xray --out /evidence/fresh-build
```

These are **builder inputs**, not requirements for an installed user. The resulting
system/runtime archive contains all those bytes, modules, notices and manifests.
L03.2 must consume this reviewed component alongside the user/GUI bundle, declare
the OS dependencies and matching Python ABI, and verify its own final artifacts.
It must not require users to find Go binaries, a source checkout or a dev venv.

Run the system image as PID1 `/sbin/init`, with `--network none --cgroupns private
--privileged --tmpfs /run --tmpfs /run/lock --tmpfs /tmp`. Privileged is confined
to that disposable system for actual service hardening and namespace operations;
never add host namespace options or host service mounts. Mount only the public
archive, this fixture and an evidence directory. Invoke:

```sh
docker exec -e FC_L031_HOST_NETNS="$(stat -Lc %i /proc/self/ns/net)" <own-container> \
  /usr/bin/python3 -I -S /evidence/smoke.py /evidence/fresh-build/FamilyConnect-MESH-system-amd64.tar.gz
```

The fixture uses actual `systemctl`, native/RNS binaries, Python imports, Unix
credentials and polkit. Its temporary polkit rule authorizes only UID1000's fixed
installed helper; it is **not shipped**. The positive payload has no test trust
switches. No enrollment, external request, native packet/VPN session or real
message is attempted. Service-only probe is expected to be unavailable without
materials; this is not a fabricated successful MESH connection.

Negatives include a separate intentionally invalid Python module (fresh hash
manifest) whose **real** installed import fails, triggering own-file rollback;
the profiler pauses after actual rollback re-masking so real unit starts can be
checked before old source restoration (no replaced systemctl/readback results);
live owner, held lock, sticky marker, concurrent unit and executable start;
missing/modified files, old capability schema with unchanged native, and an
unlisted vendor symlink. Synthetic marker cleanup occurs only in the fixture
after the installer has refused and preserved it. Product code never clears it.

After recording the result, stop/remove only this fixture's container. Archive
its stdout, image/version information and delivery checksums. Distinguish this
gate from mocked unit tests, source/native fixture acceptance and future L04/L05.
