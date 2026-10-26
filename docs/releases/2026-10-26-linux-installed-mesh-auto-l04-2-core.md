# L04.2 core — installed MESH/Auto continuation

Date: 2026-10-26. Input main: `4a4b102e69a9cc5d663ca7f0c91cade08fa5ba30`.
**Result: PARTIAL / STOP at the first manual P0 Connect failure.**
This continues **L04.2**, not a new PLAN ID or candidate. Parent L04 remains
IN_PROGRESS; L04.1 stays DONE. **STOP. NEXT — final review L04.2 core.**

## Review boundary

The [previous checkpoint](2026-10-26-linux-installed-mesh-auto-l04-2-final.md)
is accepted as a correct BLOCKED observation. Its
`registration_error=delivery_unavailable` now belongs to the **L05 backlog**,
with cause unresolved: neither a client defect nor a gateway outage is established.
It is not a prerequisite, STOP reason or PASS for this core VPN checkpoint.
No chat registration diagnosis or repair was performed. DIRECT, SERVICE_ONLY and
EXISTING_EXIT are not acceptance criteria here; mandatory borrowing is not required.

The earlier literal one-ChatClient criterion was **corrected by review**, not by a
product patch: messenger1 + support1 are permitted RPC projections, with no third
proxy or second privileged VPN owner. Earlier exact package/system, derived chat
state, create=False reopen, readiness/readback/ACK and DIRECT registration PASS
remain accepted; they were not replayed as acceptance gates.

Historical L04.2 reports remain unchanged. No L05, messages, contacts, voice,
benchmark, soak, sleep/resume, network migration, owner-workstation operation,
Android106, Windows/iOS, signing, publication or server changes.

## Immutable input and clean snapshot

Exact internal **0.2.12~l03.2.9**, from the unchanged
[candidate manifest](2026-10-26-chat-ux-2/candidate-delivery.json):

- Source `cb81cd50e0afaee0b25d78bb3bd7176c9999d250`.
- Candidate `6f312d1e7c783ea42a39ca164d93d74b0ec4faf5bac53e24c12551cedd052a5b`.
- System `43266d97c6a9f8d4e7026727cbb4b5cb6aeea49db799f93bd798b67a8135198c`.
- DEB SHA256 `e79bca1bb70a1b8d6db1ba44436cb9216c8fa7bf769fb3d919a1f2c8c96eaf62`.
- AppImage SHA256 `dc790701321da9e63325bc097bf6eab81032ed7f46236e0ed2de39cc673d45d4`.
- System archive SHA256 `402affe5628da4ecd1df3e274f3c67848d5e59023a63374765c91419490b9a55`.

Created one clean encrypted P0 copy of the latest retained, powered-off derived
snapshot from the previous checkpoint. The prepared base was not booted or modified.
The disposable Ubuntu26.04.1 / Python3.14.4 / systemd259.9 KVM guest has its own
home, Secret Service, D-Bus, display and network. No owner home/bus was mounted.
Only the existing test device/state was used; no Friends identity, invite,
activation, grant, policy change or new local chat identity/store.

Started the already-installed chat boundary units and fixture desktop; no package
installation, setup or prepare-chat replay. Installed `--candidate-status` returned
the exact candidate and system READY. Initial VPN owner/TUN counts were0;
MESH and Auto were DISCONNECTED, coordination generation0/pending null, with no
Friends application journal. Existing test identity/cache/floor files were intact.

## One P0 Connect and observed failure

Selected manual MESH/P0 in the installed GUI and emitted its actual Connect button
once. Normal polkit authentication was completed. No direct helper start, synthetic
successful result, repeated Connect or fallback action was used.

The privileged service recorded one attempt:

```json
{
  "selected_transport": "mesh",
  "selected_profile": "P0",
  "connect_count": 1,
  "service_attempts": 1,
  "events": [
    {"state": "CONNECTING", "reason": "NONE", "attempt": 1, "elapsed_ms": 146},
    {"state": "FAILED", "reason": "NETWORK_SETUP_FAILED", "attempt": 1, "elapsed_ms": 60835}
  ],
  "first_reason": "NETWORK_SETUP_FAILED",
  "desired_connected_at_failure": true,
  "applied_profile": null,
  "negotiated_profile": null,
  "vpn_owner_count_at_failure": 1,
  "tun_count_at_failure": 0
}
```

GUI readback was FAILED / “Unable to connect”, selected P0 with negotiated value
absent; Auto stayed DISCONNECTED. No CONNECTED session or applied/effective P0
is claimed. AWG/TCP/Auto owner markers were absent. The MESH guard routes/rules
were still present while the failed session retained desired intent.

SSH fixture control became unavailable after Connect. Read-only status and the
single cleanup action were obtained through the guest's existing serial console,
using fixture-only QEMU input. No guest network bypass, product patch, VM restart,
second Connect or new identity was introduced. The service event sequence, not the
SSH timeout, establishes the VPN failure. Delayed observation is disclosed; no
claim of continuous external polling or of SSH timeout as a separate product defect.

The typed stopping stage is **manual P0 Connect / supervisor NETWORK_SETUP_FAILED**.
This is a failed installed VPN action, hence PARTIAL rather than CHECKPOINT PASS.
The underlying exception/root cause was not localized. This generic code alone
does not prove a particular client defect or gateway outage; no external
certificate/assignment/gateway cause was established to reclassify it as BLOCKED.
No source repair or further VPN scenario was attempted.

### Readiness observation, not a repeated gate

The same valid cached certificate metadata remained: revision1, expiry
**18:31:47 UTC**, issuer sequence18, CRL floor27198; device binding and hashed
directory/family/gateway references matched the previous retained snapshot.
The current service reported `VERIFIED_READBACK / READY / VALIDATED_CACHE`, durable
and relay available. Its separate receipt was `ACK_PENDING / FETCH_FAILED / import`.
This receipt is not relabelled ACK PASS, nor substituted for the prior accepted ACK.
No manual fetch/replay/renewal was requested. No expired-certificate or DENIED
result was observed. The receipt does not by itself localize NETWORK_SETUP_FAILED.

## Non-interference and safe cleanup

The current GUI's passive trace was separated from the inherited snapshot log.
Only role/operation names and local timings were retained, not RPC arguments.
Counts while the GUI remained open: messenger proxy1, support proxy1, unexpected0;
support visible peer false. This run observed154 `support_status` calls, no other
support operation; messenger77 heartbeats and one detach, no queue/edit action.
No support consent change, message or manual registration was requested.

Read-only post-Disconnect inspection found one ChatService, one ChatOwner and one
exclusive encrypted-store lock under the single Chat1 D-Bus owner. The device and
chat public-identity digest matched the retained state. A supplementary DIRECT
readback is not used as a gate or as evidence that the L05 availability observation
is resolved. There was no successful VPN-time borrowing/context acceptance.

One actual GUI Disconnect was used for cleanup, with normal polkit authentication:

```json
{
  "disconnect_count": 1,
  "gui_state": "DISCONNECTED",
  "active": false,
  "busy": false,
  "vpn_owner_count": 0,
  "tun_count": 0,
  "coordination_generation": 2,
  "pending": null,
  "mesh_intent_desired": false,
  "mesh_intent_recoveries": 0,
  "friends_application_journal": "ABSENT",
  "mesh_service_active": false,
  "mesh_service_main_pid": 0,
  "mesh_fd_store_count": 0,
  "immediate_network_baseline_equal": true
}
```

Immediate post-Disconnect readback matched the original network snapshot for
addresses, IPv4/IPv6 routes and rules, DNS/domains/default-route, nft and iptables.
Late GUI readback stayed DISCONNECTED with no late CONNECTED. The manual MESH
intent is inactive; the absent Friends application journal is **not** falsely
reported as an observed IDLE journal. Coordination pending is actually null.

The final, later address digest differs only by an underlay IPv6 `mngtmpaddr`
flag becoming absent (lease lifetimes also advance). Addresses, prefixes,
interfaces and other network digests remain unchanged. The cause of that flag
change was not investigated; full late address-metadata equality is NOT_PROVEN,
not silently normalized into PASS. No VPN route, guard rule, owner or TUN remained.

The application's newly saved next preference is nl/MESH/P0 and remains unchanged
through cleanup; this is an expected product settings write, not a manual edit.
Original protected seven files and the copied Friends identity/cache/floors are
byte-identical. Existing chat identity/store reopened normally and remained owned
by the same singleton; no store replacement or new state tree occurred.

Closed the GUI normally, then terminated only the verified test ChatService with
its normal SIGTERM handler and stopped the two existing test chat boundary units.
Chat1 owner became absent, GUI/service processes exited, no Family Connect runtime
unit remained running. The guest was shut down normally; encrypted evidence/state
were retained, not revoked or destroyed.

## Gate accounting

| Gate | Result |
| --- | --- |
| Exact .9/system and earlier state/readiness gates | Retained PASS; current candidate READY |
| Corrected proxy/singleton non-interference observations | PASS in observed pre-/failed-/post-VPN scope; no duplicate VPN resources |
| Manual P0 | **FAIL — Connect / NETWORK_SETUP_FAILED**; actual applied profile not reached |
| P0 DNS/HTTPS, refresh, selected-next/active separation | NOT_RUN after first failure |
| Manual P1 | NOT_RUN |
| Auto, stale callback fencing | NOT_RUN |
| Active system-owned GUI close/reopen | NOT_RUN |
| Original AppImage over shared installed system/state | NOT_RUN |
| Failure-path Disconnect/network cleanup | Observed as above; late address-metadata caveat retained |
| Original protected state preservation | PASS, seven files byte-identical |
| L05 / signing / publication | NOT_RUN |

## Evidence, checks and next review

Private receipt accounting is extended for this same test device: reused retained
certificate metadata, existing chat identity/store, one failed P0 Connect and one
Disconnect, cleanup and retained encrypted snapshot. Previous server record count2
is retained as historical; no fresh registry/chat diagnostic query or server write.
L04.1-AUTH-TEARDOWN remains separate, with revoke/teardown NOT_RUN.

Sanitized local receipts include candidate status, service event/typed-stage summary,
role trace, failed/post-disconnect/final network readbacks, material metadata,
inactive intent/pending state and original-file digests. Raw private state, keys,
certificates, profiles, bus unique names and messages are not committed.

Validation: exact artifact/manifest hashes and system archive, JSON receipt/report
syntax, documentation links, staged-scope/secret scan and `git diff --check`.
Only this report and STATUS/PLAN/README routing change; unrelated VPN-health edits
remain unstaged. Historical L04.2 reports, source, candidate bytes and manifest are
unchanged. No deployment/rollout/rollback: cleanup returns the disposable guest to
its network baseline; retained encrypted snapshots remain available for review.

**L04.2 PARTIAL; parent L04 IN_PROGRESS. STOP. NEXT — final review L04.2 core.**
