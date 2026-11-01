# FLEET-BOOTSTRAP-2 — second-NL activation check and measured timing

## Activation result

The owner explicitly requested enabling the retained VPS after the successful rehearsal.
That request is recorded; this is no longer a claim that activation was not requested.
**Production activation is NOT_RUN: SINGLE_GATEWAY_PER_COUNTRY_CONTRACT.**
No new top-level PLAN ID is introduced. Source/package and physical A/B/reboot/retirement
acceptance remain PASS; the new finding concerns simultaneous production admission, not
another failed VPS installation or a reason to repeat the completed reboot test.

The current signed catalog has exactly two entries, one RU and one NL. A third entry or a
second NL entry cannot be added as a configuration-only publication without rejection:

- [Published Android catalog parser](../../clients/android/app/src/main/java/com/familyconnect/app/ControlFriendsCatalog.java)
  requires exactly two gateways and rejects duplicate countries. Its current bytes equal
  accepted Android109 source `600ae52bfac673ca0323bd7c96d6cdd369593624`; this is source
  verification, not a new Android runtime/CI acceptance claim.
- [Shared verifier](../../provisioning/friends_catalog.py) enforces the same constraints.
- [Offline catalog signer](../../scripts/sign_friends_catalog.py) admits exactly RU and NL.
- [Access backend](../../deploy/friends/access-api.py) requires exactly one gateway for the
  selected country and otherwise rejects an ambiguous gateway; it selects registration host
  from that single entry.
- [Production maintenance controller](../../deploy/friends/restricted/maintenance/production_controller.py)
  binds exactly the RU/NL node set. Permanent third-node renewal is not implemented merely by
  keeping a rehearsal process running. No live production readback was performed in this check.

Replacing the NL entry would move the existing slot, not provide two simultaneous Amsterdam
nodes. Disabling these validators, cloning the current node's identity or extending a rehearsal
permit is not an acceptable activation path. A compatible physical-node assignment/catalog and
renewal design is required, including a migration/rollback contract. Whether existing clients
can be preserved through authenticated per-device assignment must be established before any
claim that an Android release is either mandatory or unnecessary. No new APK or client sequence
is authorized or published by this source-only diagnosis.

## Bounded reproduction

An isolated pinned operator container with network disabled ran the existing shared catalog
vectors: **36 PASS, 5 unrelated HTTP tests deselected**. Three fresh, synthetic, correctly signed
catalog cases exercised the shared verifier and the exact backend country-selection functions:

| Catalog | Shared client contract | Backend NL selection |
| --- | --- | --- |
| One RU + one NL | ACCEPTED | ACCEPTED |
| One RU + two NL | REJECTED | REJECTED |
| Two NL | REJECTED | REJECTED |

The backend functions were extracted unchanged from the source AST and evaluated against a
temporary synthetic catalog, without importing the server's startup/database/SSH paths.
No real credentials, publisher input, SSH key, production signer or private identity was mounted.
[Sanitized evidence](2026-11-02-fleet-bootstrap-2-activation-check.receipt.json) records the source
binding, observed results and timestamp calculations. Runtime and tests are unmodified.

## How long the preparation took

Use wall-clock records rather than treating debugging and credential waits as installation time:

| Measured interval | Time | Meaning |
| --- | --- | --- |
| First recorded host preflight,1 Nov17:46:56UTC → final retirement,23:25:24UTC | 5h38m28s | Recorded preparation/rehearsal span, including OS transition, source fixes, packaging, tests and input waits |
| Last trial preflight completion,23:08:51UTC → first ACTIVE,23:15:19UTC | 6m28s | Enrollment/material delivery/install plus initial external acceptance on the prepared VPS |
| Last trial preflight completion → final retirement | 16m33s | Includes acceptance before/after reboot and final drain/retirement |

The last preflight itself took3.933s, so from its start the latter two intervals are approximately
6m32s and16m37s. These are one observed qualified run, not an SLA or a prediction for every VPS.
The overall span excludes unrecorded setup before the first host preflight and includes idle
waits; it is not an active-engineering-time measurement. Permanent production activation has
not completed, so none of these times is represented as time-to-production for a second NL.

## Preserved state

The retained VPS is still at the previous terminal rehearsal state: no new host operation was
performed for this assessment. Production RU/NL writes0; catalog publications0; user invitations0;
paid events0; phone actions0. Android109/sequence4, gateway catalog4, paid baseline108, existing
entitlement, ledger1/4, cohort1/10 and revenue0 remain unchanged by this work. The first NL is not
replaced. The independent SSH-fingerprint verification limitation is retained, not silently waived.
