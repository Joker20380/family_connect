# Client updates

Windows0.2.13+ uses a separate signed [Windows catalog](../updates/windows.json): schema2, platform=windows, sequence9 for0.2.13. Windows0.2.12 and earlier still read the legacy shared catalog0.2.9/sequence8 and can incorrectly report the newest manual preview as current. Install0.2.13 manually once, preserving identity and data. Later Windows versions are offered by Check for updates. Linux continues to use the legacy shared channel described below.

Every Windows release must publish the accepted installer at `windows-v{version}/FamilyConnect-Setup-{version}-pilot-unsigned.exe`, then sign `updates/windows.json` offline using `scripts/sign_update.py --platform windows`, an increasing sequence and the accepted artifact directory. Never send the signing key to CI. Validate the public catalog with the client verifier and verify the full public installer hash. Keep the90-day lease renewed with a higher sequence.

0.2.1 introduces opt-in Check for updates in Linux and Windows. The client downloads
`updates/pilot.json` over HTTPS, verifies its Ed25519 signature against embedded
`update.pub`, lease and monotonic sequence, then offers only a newer version. After
user confirmation it downloads the platform artifact and checks signed size/SHA-256.
The unsigned release.json on GitHub is informational, never install authorization.

Linux stores code under `~/.local/share/family-connect/releases`, smoke-checks it and
atomically switches `current`, retaining `previous`. The desktop shortcut uses
current/app.py. Floors/cache are in `~/.local/state/family-connect-updates`; NetworkManager
profiles remain untouched. From 0.2.7, Python GI, GTK 4, libadwaita and python3-cryptography are required.
Ubuntu/Debian: `sudo apt install python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 python3-cryptography`.
These dependencies are already present on the current laptop. Other Linux hosts must
install them before upgrading; smoke failure preserves the previous application. Old clients
without an updater need one manual install-linux.sh transition.

Windows uses `%LOCALAPPDATA%/FamilyConnect/updates`, verifies downloaded bytes again
before launching the installer with standard UAC. In-place installation preserves
ProgramData/DPAPI keys and restarts the service, briefly interrupting its VPN. Catalog
signing is separate from Authenticode: this pilot installer still lacks publisher
code signing; the official WireGuard driver keeps its original signature.

The signed catalog is transport-independent. Linux Updater.accept and Windows
Updates.Verify can consume identical bytes delivered by Reticulum. An RNS notification/
catalog listener is a planned next step, not running in 0.2.1. Large files remain on
HTTPS; notifications or transport identity alone never authorize installing code.

The real private signing key remains local at
`state-client-build/update-signing/ed25519.key`, mode 0600 in a private directory,
excluded from Git. Back it up offline. Never send it to CI/server or regenerate it
silently. Public anchors and separate reproducible test fixtures may be committed.

Release process: increase VERSION/client/installer versions; never move published tags
or replace assets for an existing version. A `Release ` commit on main (or a new vX.Y.Z
tag) publishes a pilot release only after Windows and Linux jobs pass. Download those
exact artifacts and verify CI/checksums. Run scripts/sign_update.py with the local key,
version, increasing sequence, artifacts directory and --output updates/pilot.json;
verify and commit only that signed catalog. Catalog leases last 90 days; renewing one
also requires a higher sequence. Existing updaters discover it on demand.

Failed verification/download/smoke preserves the existing application. Linux retains
previous code for manual rollback; do not reset floors to accept old catalogs. Owner/root
backup rollback is not hardware-prevented. Unattended installation, stable channel,
signed root rotation/recovery and Android update integration remain future work.


### Updating versus activation

Use Check for updates → Install update → confirmation. Manual installer transfer is
optional. GitHub may briefly cache an older catalog; check again later. Updates retain
the device key and activation. A separate `.fcactivation` file is needed only when
activation must be restored after reinstalling; ordinary updates do not need a new
grant. The operator verifies the current device code before issuing a restoration grant.
