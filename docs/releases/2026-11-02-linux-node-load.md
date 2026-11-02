# Linux two-node load — 2 November 2026

## Scope and source checkpoint

Owner requests two Amsterdam choices instead of the duplicate legacy assigned-NL
entry, working load for each node, and provisional5Gbps capacity for both.
Existing FLEET-BOOTSTRAP-2 only; public Linux0.2.11, installed internal.12,
Android110/sequence5 and Windows0.2.16/sequence12 remain unchanged at this checkpoint.
Internal Linux0.2.12~l03.2.13 is reserved for a new full-package delivery, not a
replacement of already-qualified .12 bytes. No Windows/Android release is claimed.

Linux AWG/TCP has Amsterdam1, Russia, Amsterdam2; Auto/MESH retain country-based
routing without offering second-node MESH. Switching back restores the chosen
manual node. Existing backend assignments are not changed by UI initialization.
Country legacy telemetry remains compatible; new node samples must match the exact
gateway ID and country and pass the same freshness/finite-number bounds. Missing
node metrics never fall back to another node or the country sample. The RU legacy
NL alias remains first-Amsterdam-only, even when that node is temporarily absent.

Capacity5000Mbps is operator-assumed, not a measured speed or provider guarantee.
The planned duplex-channel percentage uses max(RX,TX)/5000; displayed utilization
is max(CPU,channel percentage), not RX+TX. Both live throughput directions remain
measured independently. The UI marks the capacity-dependent value as an estimate.
The earlier missing NL combined load came from capacity=null; per-node samples were
also absent and the old Linux explicit-node load path deliberately returned none.

## Source checks

- New regression tests reproduced missing node parsing/collection before the fix:
  5 failed/18 passed. Focused parser/collector tests now26 PASS, including wrong-ID,
  stale/absent samples, independent values and no cross-node legacy substitution.
- Full desktop plus monitor and candidate-CI contracts:1251 PASS/183 environment
  skips. Locked package venv with system GI appended; umask022.
- Earlier full attempts are retained: GI unavailable inside the isolated venv, then
  8 safe-file fixture failures under inherited umask002. No guard/test suppression.
- Real-display GTK RU/EN2 PASS: three total manual rows, exact node passed to
  connection callback, distinct percentages/capacity tooltip and Auto/MESH boundary.
  A first test fixture lacked the parser's country field; corrected without relaxing
  product validation. Rendering/package acceptance remains separate.
- Backend telemetry-only source pin updated; native transport source unchanged.

## Delivery and rollback gates

NOT_RUN: live monitor configuration, verified public per-node samples, full .13
DEB/AppImage/system qualification and guarded owner installation. Do not label the
source checkpoint delivered or ask the legacy six-file updater to install it.

Only the monitoring services may be installed/restarted for this request. Preserve
existing forced-command SSH restrictions and accepted pins; back up monitor source,
configuration and any changed monitoring key authorization privately. Revert only
those files/service changes if acceptance fails; never restart the VPN/backend to
repair telemetry. The accepted NL2 pin is RSA from the retained owner-approved
known-hosts file; an unrecognized ED25519 key scan was not accepted or used.

Owner package update requires disconnect/closed GUI, idle services/ownership and
fresh protected-state fingerprints. Keep .12 full DEB and matching embedded system
for a guarded rollback; no data deletion, marker removal or automatic connection.
