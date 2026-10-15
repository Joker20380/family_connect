# OWNER-CUMULATIVE-CLIENT-ACCEPTANCE-1

**RESULT: ENVIRONMENT_BLOCKED — stopped before installation and CONNECT.**
The checked cumulative APK was signed with the existing Android signer, with no
rebuild. Fresh owner metadata and a compatible original-APK backup were obtained.
Fresh NL preflight found the restricted gateway **failed, MainPID=0, no listener**,
and expired authority, leaf, CRL and directory material. The task's environment gate
therefore prohibits proceeding. No server repair or candidate substitution occurred.

`CLIENT_DEVICE_SMOKE=NOT_RUN`; `HANDOFF_ON_DEVICE=NOT_PROVEN`;
`DEVICE_ACCEPTANCE=NOT_RUN`; `PRODUCTION_ACCEPTANCE=FAIL`;
`HISTORICAL_CAUSAL_BINDING=NOT_PROVEN`. This is neither a client startup failure
nor a new explanation of historical C1/I1.

## Input and signed artifact

Input review: `ace063f8bcdf22ae92d55223f069339706fbe897`.
The [diagnostic delta report](2026-10-15-startup-diagnostic-cause-fidelity-1.md),
[cumulative reproduction](../../research/startup-cause-fidelity-20261015/README.md)
and [handoff contract](2026-10-15-restricted-chat-vpn-handoff-1.md) remain unchanged.
No host/race/JVM suites or product build were repeated.

| Identity | SHA256 / value |
|---|---|
| Cumulative source inventory digest | `a4d489079e3da0df7fdd01b7977962b20ddbbf8605fbf682a349703a88b916d5` |
| Existing checked unsigned APK | `a2578412f8a3850e5f06aae838ddff0d1f4b04364b01885ffe3ea3b7dbe8ce3d` |
| **New signed, not installed APK** | `3c733d2fc3a0ec377143b668244a4c7d6619ff24abe024da4ee9bfe31d140513` |
| Cumulative native, in unsigned and signed APK | `2a974350c168913ca8a217d3fc73f452fdd709c3619d0c690abd5d884c54b88c` |
| Existing and cumulative signer certificate | `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a` |
| Package | `com.familyconnect.app.friends` |
| Version, unchanged | versionCode 84; `0.1.18-research84-provisioning-seam` |

Used retained `sign_android_vault.credentials/sign` and the existing signing-only
vault selection workflow. Secrets remained in memory/memfd; no key generation,
plaintext key/password export, helper signing or production signing-policy change.
APK signature verification and 16 KiB alignment checks pass. Every DEX and native
entry has the same hash before/after signing. Package/version are unchanged; the
embedded provisioning source-delta asset matches the cumulative digest. The APK
remains non-debuggable. A publication SHA is not an APK source SHA.

## Owner readback and return path

At **13:09:17 UTC**, one already authorized device matched the saved owner selector
(selector kept private). Scoped package metadata and APK pull established:

| Installed original, before and final | Value |
|---|---|
| APK SHA256 | `fd3106170ceeb1e24dad6c8eacda4107b1ab09a6ee120ccf495d92d96841aa48` |
| Embedded original native SHA256 | `cb3af31f62fdc1339df5f03374652ef6c62c4382ed10ef2d314bd6b610c989e2` |
| UID | 10283 |
| Package / version / signer | Same package, versionCode 84 and certificate pin shown above |
| APK layout | One base APK; no splits reported by package manager |
| VPN | No VPN transport observed before or at final readback |
| Existing app state | App process and ChatDeliveryService present before; not started by this task |

The actual installed original APK was pulled to the private capsule; its local hash
matches the device-side hash and its signature is verified. The cumulative diff
changes in-process ownership and optional schema-1 diagnostics, not identity/database
migrations or persisted identity formats. Equal versionCode and identical signer
provide the normal replace-install return preconditions; no downgrade flag or
uninstall is planned. **Neither forward install nor rollback was exercised**, so
successful Android replacement is not claimed merely because a backup exists.

At **13:16:11 UTC**, final readback again found the same UID and original installed
APK hash, with VPN OFF by system observation. Signer/native equality follows from
that exact hash and the pulled, verified APK. There was no re-enrollment, app-data
read/clear, launch, force-stop or install-induced process replacement. Private
identity/database contents were not copied or hashed; background app writes are
not claimed to have stopped.

The already supplied historical support export was copied without modification:
66,200 bytes, SHA256
`85722f4a9fe2a1089f7b7e20cbafec5b5546cc545dbf3160a8f57e9f10e16a1a`.
It is not a new export or evidence from this acceptance attempt. No new Share UI
or export-cache rotation was needed because no connection/install was attempted.

## Fresh gateway gate

Reused the existing read-only NL collector, with narrowly scoped unit/config and
acceptance-flag observations. No provider/TLS live probe was made. A first local
summary wrapper incorrectly subtracted an ISO directory date from an epoch integer;
that read-only failure was retained, the date conversion corrected, and the
collector read again. It made no server mutation and was not a VPN attempt.

At **13:12:51 UTC**:

| Boundary | Observation |
|---|---|
| Restricted systemd unit | `failed / failed`, MainPID `0` |
| Retained unit invocation | `c332f43e5ced4aa58258e4d3877434fe` — not a live owner session |
| Last start | `2026-10-15 11:08:07 UTC` (systemd reported 14:08:07 MSK) |
| Currently loaded executable/hash | **NO_RUNNING_EXECUTABLE**; `/proc/<pid>/exe` cannot be asserted |
| Configured baseline binary on disk | `21f0a0fdc27b50c00ea922f0b716516e2422aedf1b3797369718f7d00070509a` |
| Ordinary restricted listener | Absent on the configured loopback port |
| Acceptance startup flag | Not configured; loaded-argv check not applicable with PID 0 |
| Known prior research policy/staging paths | Absent; no active acceptance process |
| Authority validity end | `2026-10-15 11:01:34 UTC` (already expired) |
| Gateway leaf validity end | `2026-10-15 08:47:36 UTC` (already expired) |
| CRL next update | `2026-10-15 08:32:34 UTC` (already expired) |
| Directory expiry | `2026-10-15 11:05:36.386432969 UTC` (already expired) |

All measured security/directory headrooms were negative. No guessed long credential
window or repeated full audit was used. The planned bounded two-attempt sequence
would allow at most 2 × 300 seconds existing overall CONNECT budget, 240 seconds
first-READY stability, 2 × 60 seconds traffic/chat observations and 2 × 60 seconds
cleanup: **18 minutes from the first CONNECT**, not a requested credential extension.
The preflight already fails at time zero; no owner attempt or fresh activation is
appropriate. Owner cached-material suitability was not bypassed or privately read.

At **13:16:12 UTC**, final read-only verification still found the same failed unit
invocation, PID 0, `Result=exit-code`, `ExecMainStatus=1`, no listener and no acceptance
flag. The failure's causal mechanism was not investigated or repaired in this task.
Disk binary, unit/drop-in configuration, gateway profile and directory hashes match
the preflight exactly. No claim that the old baseline is currently active is made.

Safe continuity digests:

- Canonical sorted unit/drop-in hash-map digest, before = after:
  `d3b0671613d40b7aee7b4c2a046a64ba6f4fd9e4a78edb9b1af792d5bb6cc3a6`.
- Gateway profile byte digest, before = after:
  `4d8828983449bb1d7d8c4cb050edf10645b8ef66ab45412a0ce1a033c6ca619e`.
- Directory byte digest, before = after:
  `0cf9bef7a5a429ba8beb1694a45ee938a8a973fd469cc358928d0e6ef68df1d3`.

## Attempt matrix and limits

| Field | Result |
|---|---|
| CONNECT 1 | NOT_RUN — pre-install environment gate |
| CONNECT 2 | NOT_RUN — first attempt never started |
| CHAT_FIRST_PRECONDITION | NOT_PROVEN; existing service alone is not a live independent holder |
| Dedicated READY / native attach / app CONNECTED | NOT_RUN for cumulative client |
| Owner HTTPS egress / owner DNS path | NOT_MEASURED |
| Stability 240 seconds after READY | NOT_RUN |
| Chat recovery / borrowing | NOT_TESTED / NOT_PROVEN |
| HANDOFF_ON_DEVICE | NOT_PROVEN |
| First unexpected failure | PRE_INSTALL_GATEWAY_PREFLIGHT; no client startup failure record exists |
| New support export | NOT_OBTAINED_NOT_NEEDED; historical copy preserved |
| Final device / client rollback | Original research84 installed, VPN OFF observed; rollback NOT_NEEDED |

No connection/incident/session identifiers for a new attempt exist. No counters
from the historical export, host tests or pre-existing background chat are assigned
to a nonexistent new attempt. No cached page, host request or shell traffic is
presented as owner TUN traffic. Device/supervisor acceptance remains open.

## Action counts and retained material

| Action | Count / scope |
|---|---|
| Checked APK signing / original installed APK backup pull | 1 / 1 |
| Owner installs / client rollbacks | 0 / 0 |
| Intentional CONNECT / reconnect / DISCONNECT | 0 / 0 / 0 |
| Task app launches / install-induced process changes | 0 / 0 — no installation occurred |
| Instrumentation / extra native stats poll / helper APK | 0 / 0 / 0 |
| New support exports / export cache rotations / data clears | 0 / 0 / 0 |
| Administrative credential mutation / re-enrollment | 0 / 0 |
| Gateway deployment / restart / configuration change | 0 / 0 / 0 |
| Fault injection / WS1011 / intentional network disruption | 0 / 0 / 0 |
| Read-only SSH executions | 3: summary-format failure, corrected preflight, final continuity readback |
| Product rebuild / patch / APK publication / main merge | 0 / 0 / 0 / 0 |
| App provider sessions initiated by this task | 0; no launch or connection action |
| Pre-existing background app protocol activity | **NOT_MEASURED**, not asserted to be zero |

Private capsule: `/tmp/fc-owner-cumulative-client-acceptance-1/`, with provenance,
receipts and SHA256SUMS. Signed cumulative APK and original rollback APK remain
there, not in Git/GitHub/download catalogs. Raw metadata, device selector and
historical export remain private. No key/password is stored in the capsule.
Public output is this safe report and STATUS/PLAN/index updates only. Original
dirty checkout, frozen snapshots, product source, main and workflows are preserved.

Next decision is separate handling of the blocked gateway/security environment,
not an automatic restart, renewal, install or CONNECT from this task. The signed
client is retained; any later acceptance needs fresh environment and owner checks.
