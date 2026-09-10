# Client updates

0.2.1 introduces opt-in Check for updates in Linux and Windows. The client downloads
`updates/pilot.json` over HTTPS, verifies its Ed25519 signature against embedded
`update.pub`, lease and monotonic sequence, then offers only a newer version. After
user confirmation it downloads the platform artifact and checks signed size/SHA-256.
The unsigned release.json on GitHub is informational, never install authorization.

Linux stores code under `~/.local/share/family-connect/releases`, smoke-checks it and
atomically switches `current`, retaining `previous`. The desktop shortcut uses
current/app.py. Floors/cache are in `~/.local/state/family-connect-updates`; NetworkManager
profiles remain untouched. Python Tk and python3-cryptography are required. Old clients
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
