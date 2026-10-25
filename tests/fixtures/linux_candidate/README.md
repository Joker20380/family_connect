# L03.2 disposable exact-artifact gate

R1 extends the same offline gate with `prestart-awg` and `prestart-tcp` modes.
Each uses a fresh container, real polkit/session-v2 and the fixed installed helper,
one synthetic verified configuration, and an actual root transport flock.
`prestart.py` requires one import/up/discard, zero network starts, IDLE and
generation0→1→2/pending null, unchanged cache and successful subsequent poll/recover.
This is source/package evidence, not a live B1 retest. No protected test state is used.
CI builds current committed system sources against the pinned native/RNS/normal
builders; it does not silently reuse the earlier accepted build-9 protocol.
Optional `deb-old-system` requires the retained exact build-9 archive mounted
read-only at `/evidence/build-9.tar.gz`; its fixed hash is verified before actual
installation. New client refusal then explicit matching setup are checked separately
from the manifest-tamper fixture. No old artifact is downloaded or invented by CI.

Only run `smoke.py` inside a new Ubuntu24.04/systemd255 Docker container, once
per format. Never install on the workstation. Use `--network none`, private
cgroup/PID/mount namespaces, `--privileged`, and tmpfs `/run`, `/run/lock`,
`/tmp:exec`. The executable tmpfs is required for actual AppImage extract/run;
no host bus, resolver, network or cgroup mounts are permitted. Bind only the
public artifacts and this fixture read-only. No checkout/venv is mounted into
the system-smoke container. The image installs host GTK/GI/voice dependencies,
not application Python distributions.

Build the image with `docker build -t fc-l032-system:check
-f tests/fixtures/linux_candidate/Dockerfile tests/fixtures/linux_candidate`.
Start PID1 `/sbin/init`; the fixture waits for the real D-Bus/resolved services.
Invoke `/usr/bin/python3 -I -S /evidence/smoke.py deb <artifact>` or
`... appimage <artifact>` through `docker exec`, passing
`FC_L032_HOST_NETNS=$(stat -Lc %i /proc/self/ns/net)` from the host.
Stop/remove only those owned disposable containers after preserving stdout.

The fixture admits only synthetic UID1000 and the exact fixed bootstrap command
through a private temporary polkit rule. It is not shipped. Wrong UID and path
are rejected. No fake systemctl, import, readback or trust-success switch is used.
Root setup snapshots the hash-verified archive from stdin into a root-owned0700
directory; it does not execute an installer from a user-writable path. Extracted
and installed imports, exact capabilities, negative payload/build/schema checks,
real system setup/reinstall, no-VPN chat preparation, user D-Bus ownership after
GUI exit and preservation of synthetic encrypted state are exercised separately.
No activation/registration, Telemost, external VPN traffic or P1 grant is supplied.

`python -B -m scripts.verify_linux_candidate <artifact-directory>` separately
checks both extracted inventories, shared candidate identity, integration scripts,
artifact hashes and unchanged six-file legacy shape. It requires Python3.12 to
validate this candidate's ABI. Source/mocked tests remain separately reported.

`scripts/ci_linux_candidate.sh` rebuilds only accepted L03.1 source `f826dbd` with
the standard native/RNS/AWG/Xray builders and pinned Go1.26.1. New archive bytes
receive a new system build identity and repeat the real L03.1 system smoke before
candidate integration. `--standard-system-rebuild` checks the accepted source
inventory; it never renames new bytes to build-9. Local reviewed candidates may
instead embed the exact retained build-9. CI candidates are unsigned internal
artifacts, not public releases. Existing full desktop/native/root→UID/Auto/DIRECT
and control/phase0/Docker gates remain independent and enabled.
