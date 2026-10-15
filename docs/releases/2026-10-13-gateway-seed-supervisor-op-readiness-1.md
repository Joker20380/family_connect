# GATEWAY-SEED-SUPERVISOR-OP-READINESS-1

**Result: PARTIAL. READY_FOR_CONTROLLED_DEPLOYMENT = NO.**

First blocker: `SYNTHETIC_TEST_ONLY_ISSUANCE_PATH_UNSUPPORTED` by the existing accepted
issuer/admission path. This is an operational policy gate, not a failure of the
accepted supervisor. No production grant, renewal, deployment, restart, canary room,
trigger or owner action was performed. The frozen candidate was neither changed nor
rebuilt. Historical functional warm-start/local supervisor acceptance remains intact.

## Exact candidate and baseline

All **6186** entries in the four retained input capsules were verified against their
SHA256SUMS: trigger611, supervisor1239, predeploy290 and real-provider proof4046.
The frozen source checkout is clean at the declared commit. Accepted local race,
security, media, reproducible-build and rollback artifacts remain input evidence;
they are not relabelled as live canary results.

| Identity | Exact value |
|---|---|
| Candidate source | `134083d87773dacc038c9593afdaff0c57ea951d` |
| Candidate binary | `53beb661cab014c32494fa8d7384f9565300311ef467e62ae9f8c20201e5138f` |
| Accepted manifest SHA256 | `90e7210bb002a9b685aa1490dbefd3b823a635f14ac24f456375d563a4568866` |
| Current loaded/next and rollback gateway | `21f0a0fdc27b50c00ea922f0b716516e2422aedf1b3797369718f7d00070509a` |
| Current API archive | `12ca0c72a89ff20c1b3c70a1182a2d5d98d4d78d25e7a079bb4d75bdf34060ed` |
| Current combined unit hash | `85583b50844ba7518e44cea75c311e7622384b36f1d4783069353eaa0ff61997` |

`CANDIDATE_BASELINE_MATCH=PASS` at the observed artifact boundary. The loaded Go
executable matches the candidate's declared deployed baseline; the separate current
API argv archive matches the preserved AKI/skew/ACK/publisher implementation. Its
Python in-memory self-attestation is unavailable; this is explicitly a current
argv/on-disk archive observation. API PID/invocation is unchanged from the prior
snapshot. The candidate does not replace API modules. No stale API checkout is used
as the authority. Lease, admission/revocation/floors, directory format, fatal observer
and classifier are preserved by the sealed feature inventory. Source-only structured
collector compatibility is not a claim that those collectors have been deployed.

## Fresh bounded production observations

NL entry07:35:21UTC and final07:48:24UTC; RU entry07:36:01UTC and final07:48:40UTC13.10.
Four bounded read-only SSH calls; no journal query, DB mutation or owner connection.
These values are snapshots, not a guarantee about a later deployment window.

| Field | Observed value |
|---|---|
| Service | active/running |
| MainPID | `1864957` |
| InvocationID | `41b2f937d7c64a488a65ac3475e3b850` |
| NRestarts | `5` |
| Process start | 05:57:27UTC |
| Process uptime at final | 6657.22s |
| `--duration` / seed rotation | 4h / 3h |
| RuntimeMax / watchdog | infinity / 0 |
| Conservative planned process deadline | approximately09:57:27UTC |
| Current process lifetime remaining | 7742.78s, approximately2h09m |
| Served leaf expiry | 00:09:41UTC13.10; expired |
| Current served credential headroom | −27523.67s |
| Issuer/delegation/CRL upper expiry | 09:33:59UTC13.10 |
| Fatal observer | environment present, ExecStopPost configured; bounded receipts retained |
| Receipt directories | application0700/UID979, systemd0700/UID0 |
| Receipt files | 0600; application15, systemd16; each directory bounded at32 |
| Listener | 127.0.0.1:18444 present |
| Resources at final | FD77, RSS33260KiB, threads7; not a canary resource test |
| Current live seed media | NOT_PROBED; a publication is not media readiness |

Runtime PID/invocation/NRestarts, unit/drop-in hashes, argv and directory remained
unchanged between these observations. No new fatal receipt appeared during this
task. This is not the future candidate's15-minute prelive acceptance.

Directory SHA256:
`3cd6ccb16dbecce640fe382b8d236ba8fac199469b5d1dd5a4272b06358552f6`.
RU/NL final directory, authority and CRL agree; final CRL number24875 and hash
`646cd943e9fee3233282d57a4b1a23587b0337e3b6edc2b00a758f5f4f124727`.
Entry CRL observations differed by one scheduled publication; no sync was initiated
by this task. Final equality is explicitly point-in-time, not a transaction across
hosts. Signature/binding checks pass; expiry remains enforced.

Strict Python/OpenSSL Family chain verification fails with `CERTIFICATE_EXPIRED`,
verify_code10. A separate non-authenticating certificate-only diagnostic observes
served DER SHA256 `78f2b6bcdba298ab0c2633b976d7d755bb7a64e1bc6ebf639591fac5afe01fb3`,
matching the profile. It sends no application bytes/client certificate and is NOT
strict validation or permission to use the expired certificate.

### Newly preserved historical fatal evidence

Compared with the05:25UTC predeploy snapshot, there are **two additional historical
fatal episodes**, both before this task's entry, with matching application/systemd
receipts. They are not the earlier planned4h exit0 events:

| UTC | Invocation | Immutable first boundary | Outcome |
|---|---|---|---|
| 05:56:12.087 | `00d21e8d81a549f0aa9df8a2714f9ea6` | `SEED_READ / PUBLISHER_DISCONNECTED` | fatal=true, exit1 |
| 05:56:57.323 | `a47c12e2fd8d4f3b9643bd3525e5b2fa` | `SEED_CREATE / provider_timeout` | fatal=true, exit1 |

The service automatically reached the current invocation at05:57:27UTC, NRestarts5.
No manual restart was performed. Original bytes/hashes are retained. Neither event
is reattributed to WS1011, credential expiry or an owner action. Provider internals
are not established. These categories are outside the accepted narrow1011 recovery
scope; this task does not broaden it. Earlier UNKNOWN and natural1011 evidence stays
separate. `RUN/DEADLINE`, fatal=false, exit0 remains `PLANNED_DEADLINE` where supported
by its own receipts.

## Synthetic identity policy — first blocker

The user authorized one identity only if the existing authority/runbook supports the
requested minimal test-only scope. Review of the exact current API archive and the
operator/runbook establishes:

- `control/friends/restricted.py:238`, `_enroll`, requires an admitted, activated
  ordinary device and non-revoked invite. `_grant` at265 retains these conditions.
- `restricted_grants` stores device/family/revision/expiry/revocation, not a separate
  restricted-test-only role or mailbox-denial scope.
- `control/friends/chat.py:27`, `ChatAccess.active`, accepts the same ordinary active
  device/invite. A finite restricted grant does not remove that chat eligibility.
- `_issue` at368 accepts certificate roles `device` or `gateway`; the frozen Family
  authorizer also requires those roles. Merely inventing a new certificate role or
  adding a label to a manifest is not an enforced privilege boundary.
- The existing operator grant helper requires an already activated device; it is not
  a separate test-principal creation path. Direct private `_issue` invocation to
  bypass enrollment/admission/CRL tracking would be a new authority policy, not an
  authorized shortcut.

An **11-check disposable local policy probe**, importing the exact deployed archive,
confirms these predicates, including missing activation/invite rejection, ordinary
activation enabling both restricted grant and chat eligibility, finite grant still
chat-eligible, revocation rejection and unsupported certificate role rejection.
No real keys/certificates, production DB, identities or grants were used/created.
This is evidence of a missing accepted isolation path, **not** a claim that an actual
mailbox/admin account was created or that every possible future policy is impossible.
An operator label is not substituted for enforcement. No publisher/admin privilege
was asserted merely from ordinary chat eligibility.

Per the user's stop condition, synthetic grant creation and canary preparation stop
here rather than creating a normal user or changing policy silently.
`SYNTHETIC_IDENTITY_READY=NO`; private/sealed identity custody is NOT_CREATED.

## Next credentials and active sessions

`NEXT_CREDENTIALS_READY=NO / NOT_ISSUED`. One issuance was permitted, not mandatory
regardless of the policy gate. With no executable canary/deployment window, no
short-lived next set was issued only to expire while that gate remains unresolved.
The issuance allowance is unspent. No keys/root, grants, floors, live gateway.json,
issuer/delegation, CRL policy, publication or sync timer was changed by this task.
The separate staging/validation plan is in the capsule; it never treats running
served bytes and next credentials as the same state. A future expired issuer also
requires its established same-key/delegation path, not arbitrary leaf TTL extension.

`ACTIVE_REAL_RESTRICTED_SESSIONS=UNKNOWN`. Current argv enables neither accepted
admission ownership nor peer evidence output. There is no retained live holder
census in this snapshot. Socket counts, the expired served control certificate,
AWG audit numbers and absent evidence do not prove zero established dedicated
sessions. Owner/tester/synthetic/holder/pending-bootstrap counts remain UNKNOWN.
DIRECT ChatDeliveryService is not counted as restricted full-VPN. No session was
terminated and no maintenance window was inferred.

## Collector, rollback and window readiness

Trigger/recovery schemas and local acceptance receipts are checksum-verified against
the exact candidate. The current fatal observer is armed and its bounded immutable
receipts were preserved. Full live trigger→reader→recovery→Pion/data→same TCP→old-cache
correlation has NOT_RUN. `COLLECTORS_READY=NO` for this operational acceptance; a
historical local fixture does not satisfy the exact-binary real-provider criterion.

The exact observation rollback binary matches current loaded/next. Unit/drop-in and
argv hashes match the previous preserved snapshot. The older historical-unit file
must not overwrite the current combined unit; capture the current private config
before a future write. Healthy next credentials/rollback compatibility is unverified,
so complete `ROLLBACK_READY=NO`, despite `ROLLBACK_BINARY_IDENTITY=PASS`.
Maximum one safe evidence-preserving rollback; it changes invocation/seed/directory.

Future runbook arithmetic is validated locally:2710s acceptance, including bounded
startup and one rollback reserve, plus180s separate safety margin = **2890s /48m10s**.
Conservative trigger/recovery completion cap is new process start+1380s (23min),
cleanup+2580s; root control's25min absolute TTL is not extended if setup is late.
Start with the single future controlled invocation, not halfway through an old one.
The fresh4h process and3h seed-rotation budgets fit; credential validity is independent.
Latest mathematical start is planned deadline−2890s and also before seed rotation−2890s.
Existing issuer alone implies hypothetical08:45:49UTC latest start; **not authorization**
because the served leaf is expired and identity/canary gates remain open.

No production binary/argument/unit change, restart, renewal or live canary is performed
by the plan. The frozen binary remains the only candidate for a later canary; no
special canary rebuild or substitute local provider is introduced.

## Requested result fields

| Field | Result |
|---|---|
| FROZEN_CANDIDATE_IDENTITY | PASS |
| CURRENT_PRODUCTION_BASELINE | PASS at recorded loaded/argv artifact boundary |
| ACTIVE_SESSION_INVENTORY | UNKNOWN; no zero-session inference |
| SYNTHETIC_IDENTITY_CREATION | NOT_RUN; policy gate |
| SYNTHETIC_IDENTITY_SECURITY | NOT_SATISFIED by accepted issuance path |
| CURRENT_SERVED_CREDENTIALS | FAIL: expired leaf |
| NEXT_CREDENTIALS | NOT_RUN / NO |
| EXACT_BINARY_CANARY | NOT_RUN |
| CANARY_REAL_TELEMOST | NOT_RUN |
| CANARY_TRIGGER | NOT_RUN; local accepted contract preserved |
| CANARY_WS1011_CLASSIFICATION | NOT_RUN |
| CANARY_SUPERVISOR_RECOVERY | NOT_RUN |
| CANARY_PROCESS_CONTINUITY | NOT_RUN |
| CANARY_SAME_ROOM_CONTINUITY | NOT_RUN |
| CANARY_DIRECTORY_CONTINUITY | NOT_RUN |
| CANARY_DEDICATED_CONTINUITY | NOT_RUN |
| CANARY_OLD_CACHE_BOOTSTRAP | NOT_RUN |
| CANARY_STALE_CALLBACK_ISOLATION | NOT_RUN |
| CANARY_RESOURCE_BOUNDS | NOT_RUN |
| COLLECTORS_READY | NO: full exact-binary live correlation untested |
| ROLLBACK_READY | NO: valid next credentials/config capture still required |
| DEPLOYMENT_WINDOW | Arithmetic PASS; operational window not ready |
| CANARY_CLEANUP | NOT_APPLICABLE: no canary created; local policy fixture removed |
| READY_FOR_CONTROLLED_DEPLOYMENT | **NO** |

## Tests, privacy and artifacts

New local work only:11 policy predicates PASS and6 readiness evaluator tests PASS
(including each missing gate, UNKNOWN/NOT_RUN/string values, expired credentials
versus independent process budget and exact window arithmetic). Initial probe harness
setup issues were corrected locally: system Python lacked RNS; the existing accepted
venv was used, class name and fixture column count corrected. No candidate change.
No new Go race run or full product suite is claimed; sealed prior acceptance and its
known baseline failures are preserved. Privacy/artifact sealing receipts accompany
the output capsule. Private keys, raw profiles, room URLs, SDP, tokens and user
identities are absent. Public/owner APK and production state are untouched by this task.

Capsule: `state-client-build/field65-export16/gateway-seed-supervisor-op-readiness-1/`:

- `manifest.json`, `RESULT.json`, `SHA256SUMS`;
- `receipts/input-verification.json`, four bounded snapshots and request-source provenance;
- `preserved-receipts/`, `receipts/fatal-chronology.json`;
- `receipts/policy-probe.json`, `policy_probe.py`, `evaluate.py`, `test_evaluate.py`;
- `receipts/baseline-compatibility.json`, `collector-readiness.json`, `rollback-readiness.json`, `window.json`;
- `OPERATION_PLAN.md`, local test/privacy receipts and source hashes.

## Counters and next operation

| Counter | This task |
|---|---:|
| Production deployment | 0 |
| Production restart | 0 |
| Production owner CONNECT | 0 |
| Renewal applied to running service | 0 |
| Same-key next credential issuance/staging | 0 |
| Synthetic identities/grants created | 0 |
| Canary seed rooms | 0 |
| Canary dedicated rooms | 0 |
| Canary signaling disconnects | 0 |
| Canary supervisor recoveries | 0 |
| Canary process restarts | 0 |
| Canary TCP stream reopens | 0 |
| Owner install/instrumentation/refresh | 0 |
| Provisioning gate arm | 0 |
| Natural fatal exits during this task's snapshot interval | 0 |

Two historical automatic restarts/fatal episodes were newly discovered, not caused
or counted as task restarts. No owner/canary attempt was consumed.

**Exactly next operation:** separately authorize and locally accept a test-only
issuance/admission policy that excludes ordinary activation/chat privileges, without
changing or deploying the frozen gateway. Do not automatically proceed to issuance,
canary or deployment. Expired credentials, unknown sessions and full canary/collector/
rollback readiness remain explicit downstream gates, not additional automatic tasks.

`ATTEMPT_CONSUMED=NO`; historical `FUNCTIONAL_WARM_START=PASS_IN_TESTED_SCENARIO` retained.
`PUBLIC_RELEASE=NOT_RUN`; `REAL_RESTRICTED_NETWORK_FIELD=NOT_RUN`.
