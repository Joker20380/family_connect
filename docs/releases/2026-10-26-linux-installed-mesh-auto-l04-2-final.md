# L04.2 — final review checkpoint

26.10.2026. **BLOCKED at protected non-VPN chat preflight; VPN scenarios NOT_RUN.**
Cause is **not localized**; no client product defect or gateway outage is established.
This is the same L04.2, not a new task/candidate and **not CHECKPOINT PASS**.
**L04.1 DONE; parent L04 IN_PROGRESS. STOP. NEXT — final review L04.2.**

## Review correction, not a product patch

Entry `main`/remote SHA: `64e76b3726fce1aa194674c72cff12851410a5c9`.
The [RESUME checkpoint](2026-10-26-linux-installed-mesh-auto-l04-2-resume.md)
is accepted. Its literal “one ChatClient” criterion was **corrected by review**:
one messenger proxy and one support proxy are permitted. The two objects were
**not merged**, and no product source was changed.

The corrected contract requires one Chat1 D-Bus owner, ChatService, ChatOwner and
encrypted-store lock; exactly one proxy per messenger/support role, no third proxy.
Support is only the existing support_status/support_consent projection, with no
chat open/queue/edit/heartbeat, visible peer or independent native transport.
During VPN, one native context/transport owner and one TUN are required; chat must
borrow the verified existing context as EXISTING_EXIT, not match merely by country.
DIRECT or SERVICE_ONLY is acceptable before VPN and after Disconnect.

Previously accepted **PASS remains PASS**, without repeating these acceptance gates:
exact .9/system READY, derived chat state, create=False reopen, restricted native
readiness/durable readback/ACK and the earlier DIRECT registration. This continuation
only performs current-state resume preflight and records a new availability obstacle.
The historical [initial BLOCKED report](2026-10-26-linux-installed-mesh-auto-l04-2.md)
is not rewritten.

## Exact input and retained-state resume

Internal **0.2.12~l03.2.9** remains immutable, using the existing
[CHAT-UX-2 manifest](2026-10-26-chat-ux-2/candidate-delivery.json):

- Source `cb81cd50e0afaee0b25d78bb3bd7176c9999d250`.
- Candidate `6f312d1e7c783ea42a39ca164d93d74b0ec4faf5bac53e24c12551cedd052a5b`.
- System `43266d97c6a9f8d4e7026727cbb4b5cb6aeea49db799f93bd798b67a8135198c`.
- DEB SHA256 `e79bca1bb70a1b8d6db1ba44436cb9216c8fa7bf769fb3d919a1f2c8c96eaf62`.
- AppImage SHA256 `dc790701321da9e63325bc097bf6eab81032ed7f46236e0ed2de39cc673d45d4`.

Created a clean encrypted copy of the retained, powered-off derived base for the
planned P0 run. Original encrypted base remains untouched/read-only; no new state
tree, Friends identity, invite, activation or local chat creation. Environment is
the retained **Ubuntu26.04.1 / Python3.14.4 / systemd259.9** KVM fixture with its own
Secret Service, D-Bus, display and network namespace. No owner home/bus is mounted.

Started only the already-installed test chat boundary units and fixture session
services after boot. **No DEB install, system setup or prepare-chat acceptance
replay.** Read-only `--candidate-status` again reports the exact candidate/system
READY. GUI opened once; normal automatic resume reopened the existing encrypted
store. Same device/chat-identity digest and exclusive store lock were observed.
The original protected **seven files**, and their copied Friends identity/cache/
floor files, remain byte-identical. No manual certificate/cache/floor/journal edits.

## Corrected role observations

At the current GUI preflight, one main window and the following live counts were
observed using read-only, allowlisted in-process inspection; no bus unique names,
message bodies, credentials or profile material were recorded:

```json
{
  "messenger_proxy_count": 1,
  "support_proxy_count": 1,
  "unexpected_proxy_count": 0,
  "distinct_roles": true,
  "support_visible_peer": false,
  "dbus_owner_count": 1,
  "chat_service_count": 1,
  "chat_owner_count": 1,
  "store_owner_lock_exclusive": true,
  "vpn_owner_count": 0,
  "vpn_tun_count": 0
}
```

Passive function-call tracing **after attachment** observed52 support RPC calls,
all **support_status**. No support_consent change was requested. No support
open/queue/edit/heartbeat, visible peer or unexpected-role call was observed.
Messenger had26 heartbeats and one detach during closing; no queue/edit action.
The trace records only role/operation names and local timing, never arguments.
Calls before attachment are not claimed to be traced; constructor/operation routing
was also checked in the unchanged installed-source implementation.

This removes the old literal-proxy-count objection. It is **not** a substitute for
the still-unrun VPN-time context ownership/lifecycle gates. Native context count1
while VPN active cannot be claimed: no VPN was connected. The chat MESH owner was
observed with no context/worker/lease after its idle cleanup, and final runtime
cleanup leaves native transport owners0.

## New preflight obstacle and bounded diagnosis

At **14:47:49 UTC**, the existing ChatOwner's normal startup work reported:

```json
{
  "stage": "ChatOwner.tick / registration preflight",
  "registration_error": "delivery_unavailable",
  "registration_route": null,
  "node_present": false,
  "state": {
    "attached": false,
    "registration_error": "delivery_unavailable",
    "route": null,
    "events_unavailable": false
  }
}
```

A healthy current protected non-VPN route was therefore **not established before
P0**. No Connect, refresh/selected-next exercise or later scenario was started.
No manual registration/fetch replay and no source/fixture repair followed this
observation. Closed the GUI and stopped its test chat daemon to bound further
activity. Automatic product work before shutdown is distinguished from a manual
retry; its individual request/attempt count was not instrumented.

Read-only diagnosis found:

- Existing certificate expiry was16:01:11 UTC. The product's normal fallback/
  readiness path issued **one additional certificate** at14:46:54 UTC, revision1,
  expiry **18:31:47 UTC**. No explicit renewal/fetch command was sent. The precise
  product refresh trigger was not captured; do not call the original certificate
  expired merely because the product refreshed materials.
- Actual material-owner result: **VERIFIED_READBACK / READY / durable / FRESH**;
  receipt **ACK_RECEIVED / READY / import / durable**. No owner failure flag.
- CRL floor **27197 → 27198**; issuer sequence18 unchanged; same exact device,
  family and gateway reference hashes. Directory SHA256 after renewal:
  `fe204817294cd3a865d0d27597c9f43098fecf97240f7e05ba0ee4b28cb9b417`.
  Directory format has no sequence field; issuer sequence is not substituted for it.
- Registry read-only accounting: certificate records **1 → 2**, two unexpired at
  accounting time; chat binding remains **1**, same test chat identity. Active test
  device and all_activated policy unchanged; explicit grant rows remain0.
- Later root DIRECT authority retained an **active** registration response,
  sequence172467, expiry14:51:07 UTC. This shows a later successful root response,
  not a healthy ChatOwner route readback at the first failing observation, and does
  not retrospectively turn that preflight into PASS.
- The bounded API-journal read for14:46–14:51 UTC timed out after20s. No attributed
  lower-level client/gateway failure code was recovered. The journal timeout itself
  is **not evidence of an outage**. Read-only debugger observations introduce pauses;
  their contribution to timing has not been excluded.

**Classification: availability/preflight BLOCKED, causal attribution unresolved.**
No proven client defect, DENIED, certificate-expiry failure or gateway outage is
asserted. In particular, successful native material validation/ACK is not the
blocked gate; the missing evidence is the healthy current protected chat route.
Earlier accepted registration/readiness PASS is retained for its own run only.
Neither a second product action nor a product patch was used to obtain a better result.

## Cleanup and teardown accounting

Normal GUI close, test daemon SIGTERM, stop of the two already-prepared test chat
units, then normal guest shutdown. QEMU/container exited0. No credential revoke,
identity deletion, server restart/deployment or production policy change.

- GUI gone, Chat1 D-Bus owner absent, no running Family Connect unit.
- VPN Connect/Disconnect **0/0**; normal VPN owner/TUN **0/0**.
- No operation/journal was created: journal **ABSENT**, pending absent; default
  generation0 readback is **not** represented as an exercised IDLE transition.
- Routes4/6, rules4/6, DNS/domains/default-route and firewall digests equal this
  snapshot's preflight baseline. Address count remains2 but its aggregate digest
  changed; full address equality **NOT_PROVEN**, cause not diagnosed or repaired.
- Original seven protected/copied files preserved; settings remained unchanged.
  Existing store reopened via GUI, with same identity and exclusive lock; no new
  history/delivery acceptance or contacts/messages/voice operation.
- Original encrypted base and powered-off encrypted P0-preflight copy retained;
  no P1/Auto snapshot or AppImage launch was performed. No second setup/state tree.

Private teardown receipt extended atomically, retaining old fields and accounting
for the extra product-issued certificate, expiry/floor/directory, unchanged chat
binding and retained snapshot. **L04.1-AUTH-TEARDOWN stays QUEUED / NOT_RUN**.
No actual teardown/revoke. Future review must re-read expiry and current state;
this report does not authorize retry, repair or fresh credential issuance.

Sanitized receipts/probes remain outside Git; receipt-manifest SHA256:
`dff2ecbfca5118a7755389d7aee3345c70746b05991afcf848c8b0ef3f99113a`.
No raw certificates, keys, room URLs, profiles, unique bus names or messages enter
the report/commit. Owner workstation/personal identity were not used.

## Completion matrix

| Gate | Result |
|---|---|
| Earlier exact .9/system, derived state/reopen, readiness/ACK, DIRECT registration | **Accepted PASS retained**, not repeated as acceptance gates |
| Corrected messenger/support proxy and Chat1/ChatOwner/store-owner counts | **PASS in observed non-VPN preflight scope**; no product patch |
| Current protected DIRECT/SERVICE_ONLY baseline | **BLOCKED**, registration_error=delivery_unavailable at first failed readback |
| Manual P0 | **NOT_RUN**; snapshot booted, Connect not invoked |
| Manual P1 / Auto | **NOT_RUN** |
| VPN-time EXISTING_EXIT borrowing / one native context/TUN | **NOT_RUN** |
| Active-session GUI reopen / stale callbacks / single Disconnect | **NOT_RUN** |
| DEB/AppImage live installed system/state sharing | **NOT_RUN** |
| No-VPN runtime cleanup / protected seven-file preservation | **PASS**; address equality NOT_PROVEN |
| L05 / publication / signing | **NOT_RUN** |

STATUS/PLAN updated under existing L04.2; no new ID/candidate. Documentation checks
**PASS**: staged secret scan, manifest/13 private receipts/2 report JSON blocks,
416 local links, four-file staged scope and `git diff --check`. Immutable artifact
hashes and original seven-file preservation rechecked as consistency checks, not
another installed acceptance run. Ordinary commit/push and remote-SHA verification;
pre-existing VPN-health reports and STATUS/PLAN preambles remain unstaged.
No source suite/build or rollout. No owner upgrade/rollback is required; the
powered-off snapshots retain evidence.

**L04.2 and parent L04 are not DONE. STOP. NEXT — final review L04.2.**
