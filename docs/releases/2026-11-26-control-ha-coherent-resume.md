# HA-02 continuation — current census, OWNER restart refusal, capture not accepted

Observation window: **26 November 2026, 14:38–14:49 UTC**. This is an incomplete
source/evidence checkpoint, not a release, coherent backup or successful recovery.
The interrupted attempt's private `20261126-coherent-01` census at10:45–10:47UTC
is retained unchanged; it is not current after the OWNER reboot.

## Baseline and current incident

Both worktrees were clean at entry. Local and remote heads matched exactly:
feature `ede03b9f4f27a38747fad42ef412515850b22575`, main
`4307401c70932ae3cabc65e30f1b50a905786d16`. Accepted installed/CI source remains
`57c19b1ccc5f97b650ed1e2382c40286bec7c950`; main remains documentation-only.
The [accepted support handoff](2026-11-26-control-ha-joint-support.md) remains
accepted at its recorded time. Historical WORKERS_REMAIN remains **UNPROVEN**;
neither old failures nor seven historical UNKNOWN outcomes are cleared.

**New observed failure:** OWNER boot time is12:04:08UTC. At14:42 and14:47UTC,
`family-connect-support.service` is failed, MainPID0, ExecMainStatus78, NRestarts0;
subscription notifications are also failed. The handoff supervisor is inactive.
This is not a claim that PID3790078 still runs. The archive on disk still hashes to
`621009b8df9baffb81e0d9069cfa52b3781e7dd7bf4e435dd89740e38cae5739`.
All three OWNER panel containers are healthy, with new PIDs5923/5939/5903 and the
same pinned console/PostgreSQL/publisher images as the earlier census.

The entrypoint deliberately requires one process/boot-bound startup authority;
it is not a restart lease. This explains a possible refusal mechanism, **not the
observed unique cause**: the installed service has StandardOutput=null and
StandardError=null, and accessible journal records contain no application reason.
The root plan/authority/terminal records cannot currently be read. `sudo -n true`
returns `sudo: interactive authentication is required`. Authorization is present;
technical privileged execution is not. No alternate privilege path, stale ticket,
reservation deletion, forced start, key substitution or old-data rollback was used.

## Fresh census and coverage comparison

Strict pinned SSH read-only collectors succeeded once on all three authorized
hosts. No retired/excluded or neighbouring service was contacted. Raw records are
private; no DB row or private key was copied into this source checkpoint.

| Participant | Observed now | What remains unproved |
| --- | --- | --- |
| RU |32 Family Connect unit names; four default SQLite schemas,34 tables total; exact v1 plus five-table handoff-v2 schema match | Row capture, configured-store completeness, external/manual writers, common barrier and current floors |
| NL1 |9 unit names; mailbox PID3705/0 restarts; authenticated endpoint readback14:46UTC: OPEN_LOCAL_ONLY, accepted work0, consumed witness present, capture=false | Local-store barrier, generation renewal and shared closed/drained interval; empty default Friends stores do not mean no node state |
| NL2 |5 unit names; no failed sampled units; explicit default Friends stores absent | Node-local receiver/allocator/publication/journals and all writers are not a coherent capture |
| OWNER |11 unit names; three healthy pinned containers; current API process/UID/mount and on-disk source observations; support/notification failures | Root-only stores/plan/queues, loaded-byte attestation, direct ORM/manual writers and installed common gate |

RU before/after unit observations agree within the census. Failed friends-AWG,
paid-reconcile and two historical pressure units remain recorded, not normalized.
NL1/NL2 sampled units have no failed state. A unit census is not transport E2E.
Cron, explicit account crontabs/forced-command summaries and unit cgroups were
observed, not closed; arbitrary manual CLI/SSH/Docker execution is not excluded.

OWNER source binding independently observes only2/10 candidate source matches
in each console/publisher container. Admission preflight reports no configured
common gate, no verified writable gate mount, different host identities, and no
loaded-byte/manual/external-completion attestation. Source qualification and old
prepared overlays must not be described as current installation coverage.

NL1 resource preflight14:38UTC: CPUQuotaPerSecUSec=1s (100%), MemoryMax805306368
(768MiB), MemoryCurrent610484224 bytes, MemAvailable732524KiB, SwapFree1431592KiB;
load1.48/1.13/0.96, filesystem27% used. Accepted limits are unchanged. This is a
point observation, not permission to start a later operation without fresh preflight.

Support's installed lifetime gate includes local persistence; remote handoff
`--pause` is not its substitute. Pause invalidates opening authority. There is no
qualified normal new-generation resume for this working post-reboot case. Recovery
must first inspect retained root records, preserve current data/UNKNOWN/queues,
reclose/drain as required, and establish a newly valid linked generation. It must
not rerun an old reservation or reinterpret an old successful handoff as permission.

## Completed source change and validation

The local [capture guard](../../scripts/control_ha_capture_guard.py) formerly
returned only REFUSED. It now distinguishes pending controller, drain timeout,
unsettled operation, gate identity/permissions and I/O failure, with an exact-hash
bounded diagnostic. At most256 pending-entry metadata records are returned; names
are hashed, contents never read, symlinks/FIFOs never followed, and truncation is
explicit. Diagnostics are **after-refusal, non-atomic**, never proof of settlement,
current authority or capture. A diagnostic read failure preserves the original
refusal. No marker is removed and no admission, timeout or enforcement gate changes.

Python3.14.4; all26 combined control/identity lockfile pins match. Final
**55 PASS,0 skips**,4.37s:

```sh
python -m pytest -q tests/test_control_ha_capture_refusal.py \
  tests/test_capture_gate.py tests/test_capture_gate_integration.py
```

The tests cover live busy/uncertain/unknown writers, exact evidence hash, private
message suppression, missing/replaced gates, bounded inventories, competing
controllers, controller death/EOF/deadline and release of only owned locks. These
are local guard tests, not combined fleet interruption/capture/resume qualification.
Earlier42-pass run is superseded, not added to the final total. Installed support,
its archive, startup rules and accepted handoff invariants are unchanged; this
source diagnostic is not installed. Exact pushed-SHA CI is separate, not claimed
from local results. No client/public/invitation/catalog/signing version changes.

## Exact preparation, trust and custody

Private directory: `~/.local/share/family-connect/control-ha/20261126-coherent-resume-01/`.
`preparation-manifest.json` binds24 exact evidence files, baselines, required
RU/NL1/NL2/OWNER component families, blocking observations and the custody decision
request. SHA256:
`5791fe8855f51f8ca2b8aefecca9b8f6c87d350f16080eb6d65f3b7beef49777`.
A separate `python -I` reader verifies that digest, exact file set, sizes and every
file hash. Result: **PREPARATION_EVIDENCE_BYTES_VERIFIED_ONLY**, not independent
trust, encrypted-bundle completeness or recovery acceptance. The manifest explicitly
has coherent_bundle=null and forward_signing_request=null.

Accessible prior private custody/key-checkpoint directories and preparation records
were checked. The retained offline-runner receipt proves source retention, not
off-origin custody. Prior proposals have independent approval unset. No dedicated
real HA signer, independently approved pins/floors or off-origin destination is
confirmed by those records; root-only records still require inspection before
concluding they do not exist. No signing/decryption key was printed, generated,
selected or copied; the release signer was not reused.

Concrete proposed arrangement, **not yet selected or transferred**: encrypted full
recovery kit on an owner-designated independent offline workstation/removable medium;
decryption key and separately approved signer fingerprint/request hash/monotonic
floors on a second medium held by the designated custodian, outside originating OWNER.
The remaining owner choice, if not already in root records, is the dedicated HA
signer/pin-floor custodian and the exact off-origin storage destination. A real
forward-signing request cannot be constructed honestly until actual coherent
ciphertext/checkpoint bytes exist. This preparation request cannot authorize it.

## One NEXT, rollback and exact remainder

**NEXT: one current coherent encrypted RU/NL1/NL2/OWNER capture, exact independent
verification and normal participant resume**, with guarded OWNER post-reboot recovery
in a new valid generation as its immediate prerequisite. Restore technical root
access, inspect original records, close implementation/installation gaps and obtain
independent trust/custody choices; do not stop at a readiness inventory.

No operation imposed working restrictions, paused/stopped/restarted participants,
installed a candidate or restored working data. Therefore no own working restriction
needs removal; **all-participant normal resume is NOT confirmed**, because support
and notifications were already failed. Source rollback is an ordinary revert of the
diagnostic/tests only; it neither undoes UNKNOWN nor restores any old DB/profile.

No real common closed/drained interval, encrypted coherent kit, full independent
reader acceptance or off-origin machine-loss restore was obtained. The full isolated
current/post-ACK restore remains NOT_RUN pending that accepted kit; no new confirmed
operation was issued on production. Isolated replication retains its prior PASS.
The same three HA-02 criteria remain partial: current inputs plus independent
trust/authorization/journals; installed schemas/all writers/coherent capture;
independent machine-loss custody/full current-state post-ACK recovery. No HA-03.
FLEET-PRODUCTION-ONBOARDING-1 remains the mandatory OPEN modernization result:
VPS → IP/access/roles → normal enrollment → verified active node.
