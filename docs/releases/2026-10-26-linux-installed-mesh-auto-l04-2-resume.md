# L04.2-RESUME — installed Linux MESH/Auto checkpoint

26.10.2026. **PARTIAL / prerequisite singleton gate FAIL; VPN scenarios NOT_RUN.**
Continuation of the existing **L04.2**, not a new PLAN ID or CHECKPOINT PASS.
**L04.1 DONE; parent L04 IN_PROGRESS. STOP. NEXT — review L04.2.**

## Scope and immutable inputs

Entry `main`: `1d81091df6dedc46704750174363d71cf8810b8f`, also verified upstream.
The [previous BLOCKED checkpoint](2026-10-26-linux-installed-mesh-auto-l04-2.md)
remains valid historical evidence: no product defect was established there.
This resume expressly permits test-only chat creation/binding, Secret Service,
normal restricted challenge/fetch/ACK and chat registration for the existing
activated Friends device **FC-3YSQ-BE2D**. No new Friends identity, invite,
activation, manual grant or registry SQL mutation was performed.

Exact internal **0.2.12~l03.2.9**, source
`cb81cd50e0afaee0b25d78bb3bd7176c9999d250`:

- Candidate `6f312d1e7c783ea42a39ca164d93d74b0ec4faf5bac53e24c12551cedd052a5b`.
- Matching system `43266d97c6a9f8d4e7026727cbb4b5cb6aeea49db799f93bd798b67a8135198c`.
- DEB SHA256 `e79bca1bb70a1b8d6db1ba44436cb9216c8fa7bf769fb3d919a1f2c8c96eaf62`.
- AppImage SHA256 `dc790701321da9e63325bc097bf6eab81032ed7f46236e0ed2de39cc673d45d4`.
- Legacy archive SHA256 `348f5e9609987a9c1751e3cca47e321b2622cb142ecbebedbe70f874fc17b215`.
- System archive SHA256 `402affe5628da4ecd1df3e274f3c67848d5e59023a63374765c91419490b9a55`.

The [CHAT-UX-2 delivery manifest](2026-10-26-chat-ux-2/candidate-delivery.json),
all artifact sizes/hashes and retained matching system archive were rechecked.
Candidate/package/system bytes and manifest were **not rebuilt or edited**.
Installed candidate integrity/import check and final `--candidate-status`:
**PASS / system READY**. Existing architecture, L02.2/L03.2/L04.1 and CHAT-UX-2
dependencies are linked in the original report; they are not re-run acceptance.

Owner workstation and personal identity were **not used** for this run.
OWNER-CHAT-UX-2-INSTALL remains **PARTIAL / owner-use accepted**, unknown queue
events excluded; no owner messages, smiley/composer/visual checks were performed.
No server restart/deployment, policy/issuer changes, new gateways/VPS, Android106,
Windows/iOS, signing or publication. No source fix was attempted at this checkpoint.

## Disposable installed environment and derived state

Fresh KVM guest: **Ubuntu26.04.1 / Python3.14.4 / systemd259.9**, 2 CPUs/4 GiB.
Official cloud image SHA256 was checked against its HTTPS checksum inventory.
Separate 24 GiB virtual qcow2 base uses **LUKS encryption**; original image is a
read-only backing image. The guest has its own user, bus, Secret Service, Xvfb,
window manager, NetworkManager and network namespace. No owner home/session bus
is mounted. The private fixture directory is mode700; retained disk/key are now
mode400, owned by the operator. Private test data stays outside the checkout.

Only the authorized protected test home was copied by the previously accepted
tar-stream method into the guest. All **seven original files** were hashed before
and after: original protected home and those seven files in the derived copy
remain byte-identical, including Friends identity, cache and floors. The original
operator directory was not copied into the guest. New product files exist only
in the encrypted derived state; certificate/cache/floor files were not hand-edited.

Installed exact DEB, then explicit packaged `--setup-system`, then
`--prepare-chat`. The matching system installer reported no automatic service
start or user-state change. Both chat root boundaries subsequently became ready.
No normal VPN Connect was invoked, and no AWG/TCP/MESH/Auto VPN owner or TUN arose.

Infrastructure corrections, not hidden product-action retries:

- Cloud-init completed with a password-configuration warning; the fixture user
  password was already set by its separate chpasswd configuration. NetworkManager
  renderer configuration was finalized before readiness/baseline collection.
- The first setup CLI had no polkit agent in its SSH session and did not enter
  the privileged installer. A same-session agent supplied normal authentication.
  The initial accessibility submission did not dismiss that dialog; keyboard
  authentication completed the **same pending prompt**, not another installer.
  The timed-out collector was reconciled using the installer result and READY.
- A read-only observer initially used a path hidden by the root unit's ProtectHome;
  moving only the observer into its allowed runtime path fixed observation.
  No readiness or user Connect operation was repeated for this instrumentation.

The packaged `ChatOwner.open(create=True)` product path was invoked once in a
separate guest process, using the real FriendsOwner, runtime, encrypted store and
Secret Service keyring, without mocks or key injection. It created a device-bound
account and chat store. After closing that owner, a separate process reopened
with **create=False**: same device and chat public-identity digest, readable store,
zero contacts/inbox entries, exclusive owner lock. Final cleanup-time create=False
reopen also passed. The chat directory is700, account file600, owned by guest UID1000;
no symlinks or wrong-owner descendants were found. No chat key left Secret Service.

## One normal restricted readiness operation

At **14:05:21 UTC**, the exact packaged `ChatBridge` service-only preparation path
returned **PREPARED / SERVICE_ONLY** after **0.818 s**. It used real product
materials acquisition and the installed native/root service, not fixture-supplied
credentials. Exactly one explicit prepare request was made; an exclusive fixture
intent prevented manual replay. VPN Connect count remained zero.

Read-only runtime observation of the material owner confirmed:

```json
{
  "readiness": {"stage": "VERIFIED_READBACK", "code": "READY", "durable": true, "source": "FRESH"},
  "receipt": {"ack_state": "ACK_RECEIVED", "durable": true, "result": "READY", "phase": "import"},
  "owner_failed": false
}
```

This is actual native/product validation, durable readback and ACK evidence, not
mere certificate-file presence. Only sanitized metadata was extracted afterward:

| Field | Observed value |
|---|---|
| Issued/reused | **Fresh issued**, existing activated test device; exact device binding matches |
| Revision | **1** |
| Issued / expires UTC | **14:05:16 / 16:01:11**,26.10.2026; unexpired at validation/accounting |
| Issuer sequence | **18** |
| Family reference SHA256 | `1437a927202f9afa3035a2fc94be89b818c2619c8be7ab31d85a23b4dd2b1ec3` |
| Gateway reference SHA256 | `62d3d57c9d2ddda1bf33f58ebaa78c442f8eb8bb127a468ed6ecf831b43dbfc4` |
| Directory SHA256 | `c7416afe181b6220e2de395b1a01653ceaa283478d45016aac3d520b5e32fe70` |
| Directory sequence | **Not a field in this directory format**; issuer sequence18 is reported separately, not relabeled |
| CRL floor | **27197** |
| Test-device certificate records | **0 → 1**, one unexpired record at final read-only accounting |
| Policy / explicit grant rows | `all_activated` unchanged / **0 → 0** |

The normal service-only native worker/context has a45-second idle lifetime. By
the14:07:58 read-only observation it had already released context, worker and lease;
`owner_failed:false` and VERIFIED_READBACK/ACK remained recorded. No second manual
prepare was made to obtain a convenient live-context capture. Thus this operation
does **not** prove a continuously retained native context through the later GUI
baseline, nor any existing-VPN context borrowing. No DENIED/gateway failure occurred.

## Chat registration and first failing gate

Opened the installed GUI **once** with the already-created store. Normal automatic
resume/registration reached, at14:16:54 UTC:

- One main window, existing messenger store open, same device/chat identity.
- Authenticated registration/node present, `registration_error:null`.
- Healthy idle delivery state: attached, no error, no pending/running operation,
  service-events fetch not unavailable. Actual route **DIRECT**, VPN off.
- Exactly one ChatService/ChatOwner and one owner of `com.familyconnect.Chat1`.
- Registry chat bindings **0 → 1**, matching the newly created test-only chat
  public-identity digest. No contacts were added and no messages sent.

DIRECT is not relabeled SERVICE_ONLY: the protected DIRECT boundary was the
actual registration route; the preceding service-only readiness operation is
separate evidence. There was one explicit registration-producing GUI launch;
automatic short-lived node renewal/request totals were not instrumented and are
not claimed to be exactly one wire request. No manual registration retry occurred.

**First failed acceptance invariant: the requested “one ChatClient” was not met.**
Read-only GC/reference inspection in the exact installed GUI found:

```json
{
  "chat_clients": 2,
  "messenger_client_count": 1,
  "support_client_count": 1,
  "same_client": false,
  "clients": [
    {"messenger": false, "support": true, "closed": false, "connected": true},
    {"messenger": true, "support": false, "closed": false, "connected": true}
  ],
  "main_windows": 1,
  "messenger_opened": true,
  "vpn_active": false
}
```

These are two distinct live connected RPC proxies, not duplicate references to
one object. One belongs to the embedded messenger; the other belongs to
`App.support_upload.client`. The read-only probe constructs **no ChatClient**.
Source inspection explains the second proxy: `App.initialize()` constructs
`SupportClient()`, whose default constructor constructs another `ChatClient()`.
No source change, method replacement, artificial callback or repeated GUI launch
was used to establish this observation.

**Classification: PARTIAL, installed singleton acceptance mismatch**, not external
assignment BLOCKED. This is **not evidence of a second chat daemon, transport
owner, native worker or TUN**, and does not establish a message-delivery defect.
The intended acceptability of the separate support RPC proxy needs review; this
run does not silently narrow the requested invariant to “one messenger proxy”.
No P0/P1/Auto action followed discovery; no repair or retry was attempted.

## Cleanup, preservation and retained accounting

Closed the GUI normally, stopped only its test user chat daemon with SIGTERM and
the two prepared test chat units with systemctl, then shut down the disposable
guest normally. Container/QEMU exited **0**. This is runtime cleanup, **not**
credential teardown, registry revoke or deletion of retained test state.

- GUI process gone; Chat1 D-Bus owner absent; no running Family Connect unit.
- Normal VPN owners **0**, normal VPN TUNs **0** throughout; Connect/Disconnect **0/0**.
- No operation/journal files were created: readback defaults generation0/pending
  absent; journal **ABSENT**, not a falsely claimed verified `IDLE` transition.
- Routes4/6, rules4/6, DNS/domains/default-route, nft and iptables digests equal the
  pre-readiness baseline. Address count remains2, but its aggregate digest changed;
  the cause was not resolved and full address-baseline equality is **NOT_PROVEN**.
  No VPN cleanup/network-migration gate is inferred from these no-VPN observations.
- Original protected home and its seven copied files remain byte-identical.
  Final create=False store reopen/exclusive-lock check passes; no user settings
  change was requested. No manual journal/cache/floor repair.
- Encrypted derived base is retained, powered off/read-only; no clean P0/P1/Auto
  scenario snapshots were started after the failing prerequisite.

Private test teardown receipt was atomically extended, preserving all previous
fields: test-only chat identity/store/binding, product keyring, certificate revision,
issuance/expiry, record counts, directory/CRL references and retained encrypted base
are accounted for. **L04.1-AUTH-TEARDOWN remains QUEUED / NOT_RUN.** No revoke,
unregister or server cleanup was executed. Re-read actual expiry/bindings before
any future authorized continuation/teardown; do not assume this context stays valid.

Sanitized receipts and probes are retained privately outside Git. Receipt-manifest
SHA256: `4d9f5a2fdbc60939d2502afb39cff505453fcb2936c8296150df210f0503b901`.
No raw certificate, key, profile, credential, room URL, store/database or VM image
is included in this report or commit.

## Completion matrix and handoff

| Gate | Result |
|---|---|
| Exact installed candidate / matching explicit system setup | **PASS**, READY; bytes unchanged |
| Derived chat state, device binding, Secret Service, create=False reopen | **PASS** |
| Product MESH readiness validation / durable readback / ACK | **PASS** for the bounded prepare; native context later idle-released |
| Pre-VPN chat prerequisites as a whole | **PARTIAL / FAIL** on literal singleton; DIRECT registration healthy, continuous SERVICE_ONLY context not proven |
| Manual MESH P0 | **NOT_RUN** |
| Manual MESH P1, separate clean snapshot | **NOT_RUN** |
| Auto, separate clean snapshot | **NOT_RUN** |
| Chat/VPN native-context ownership boundary | **NOT_RUN**; no active VPN |
| Active-session GUI close/reopen, stale callback, one Disconnect | **NOT_RUN** |
| AppImage/DEB installed system/state sharing | Artifact integrity **PASS**; live sharing **NOT_RUN** |
| No-VPN runtime cleanup / original-state preservation | **PASS** for the scope above; full address equality NOT_PROVEN |
| L05 delivery / L06–L08 / signing / publication | **NOT_RUN in this resume**; prior queue statuses retained |

Documentation-only validation **PASS**: staged secret/private-data scan; candidate
manifest,18 retained receipt files and2 report JSON blocks;417 local documentation
links; four-file staged scope and `git diff --check`. Exact artifacts and original
seven-file preservation rechecked. No unrelated source suite or build was rerun.
Pre-existing VPN-health documents and STATUS/PLAN preambles stay unstaged.
Ordinary commit/push with remote SHA verification; no tag/public rollout.

No installed upgrade/rollback is needed on the owner workstation: it was not
touched. Exact retained .9 artifacts and powered-off encrypted test base remain
available; no policy rollback is applicable. **L04.2 is not DONE, parent L04 is not
DONE, L05 remains NOT_RUN. STOP. NEXT — review L04.2.**
