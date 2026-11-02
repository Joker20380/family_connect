# Linux two-node load — 2 November 2026

## Current delivery result

**INSTALLED_GTK_AND_LIVE_METRICS_PASS.** Both Amsterdam
nodes now supply independent fresh samples bound to their exact IDs, with provisional
5000Mbps duplex capacity and operator-assumed provenance. Verified public HTTPS
acceptance observed first-node CPU/load12.3% and second-node0.6%; these are one
snapshot, not constants. The legacy country NL sample aliases the first node only.
RU capacity remains200Mbps/egress/provider estimate. No device assignment or
paid-state mutation and no VPN/backend restart; only monitor services changed.
Non-monitor service identities/PIDs/restart state were unchanged at all three
activation boundaries (first NL6, second NL2, RU4 observed services).

The new second-node monitor initially could not traverse its own0700 directory
created under private umask. Bounded node acceptance failed before RU activation;
automatic monitor restarts and diagnostic records are retained. The monitor was
stopped; only its dedicated root directory became0755, with its private state
remaining0700. Fixed installer now establishes the public traversal mode explicitly
and rejects a symlink root. Regression2 plus monitor11 PASS. The original NL
activation intents were not replayed: a new RU-only operation first rechecked
both node samples, then activated aggregation and verified actual HTTPS.
Forced-command/from-host restrictions remain; the existing monitoring public key
was added only to NL2, and the retained approved RSA host pin was added to the RU
monitor's known-hosts file. Private backups and diagnostic details remain local.

Source64182449b7370ac429b942a64ebca5563f91b32a produced full internal
0.2.12~l03.2.13; source_dirty=false. Exact artifact integrity, real isolated system
install/rollback, DEB, AppImage and both AWG/TCP pre-start guards PASS. No transport
source rebuild was needed; accepted native/RNS/normal bytes were reverified, and
the system bundle was rebuilt for the telemetry backend delta. Exact packaged
GTK RU/EN interaction/render at scale1/2 PASS (four cases); the node label, distinct
synthetic23%/7% and5000Mbps tooltip are verified. Screenshots inspected. The first
capture encountered an unmapped render node; a bounded frame wait fixes the test
harness, not product code. The initial scale2 virtual display provided only512
logical pixels vertically; the final2560x2160 physical display verifies full layout.
Earlier diagnostics/captures are retained. Owner installation and final readback
are now complete as recorded below.

| Artifact | Bytes | SHA256 |
| --- | ---: | --- |
| `FamilyConnect_0.2.12~l03.2.13_amd64.deb` | 56157812 | `2e8381104cf6f05bbb638954e6e39342d3328b2397d37b6b6a7c6a9b68ae1dfc` |
| `FamilyConnect-0.2.12~l03.2.13-x86_64.AppImage` | 58128888 | `452d595d932078a50724e9691f4c137d110e387d7db46bb06c6921a93cceea9d` |

Candidate `0d23476c3cd10ad4605534da4e9de5ffef97736f897be2237dfba633a28fcfa4`;
paired system `1428321b7743b6b624675552545b33fb32f04518b3ea05889acd385bd6dd157d`.
These are internal owner artifacts, not public downloads or signed update entries.

## Owner installation and final readback

Fresh .12→.13 full-package operation: reviewed DEB hash and retained .12 rollback
bytes verified, GUI/transport idle, user/root background owners stopped normally.
Ordinary system authorization installed the user package and matching embedded
system. Candidate imports PASS; `--candidate-status` READY. All3171 protected
entries were unchanged through installation and GTK smoke: user config/data/state/
cache plus root AWG/TCP configuration, modes/owners and hashed symlink targets
without following them. This is a fresh snapshot, not a count-delta claim against
the earlier .12 operation. No marker deletion, ownership bypass or automatic VPN.

Installed GTK startup on the owner display with isolated D-Bus PASS; no renderer
overrides. The installed backend independently fetched verified public HTTPS and
accepted both exact node samples: AMS1 load16.3%, AMS2 load4.7%, each5000Mbps with
operator-assumed provenance. These are observed samples, not fixed percentages.
Private operation records/fingerprints remain local. Physical owner AWG/TCP
connections and Disconnect acceptance remain pending; no such connection was made.
The build-time manifest's installed=false/acceptance=NOT_RUN is immutable build
metadata, superseded for delivery by this report and the sanitized receipt.

Rollback if needed: disconnect, close GUI, stop idle background owners normally,
verify fresh protected fingerprints and restore the retained full .12 DEB SHA256
`cde8416c07ef87ec2ef5441e17a33b93f72be8aad2e1675c7203d542ea975972`
and its embedded system `d5fc9df50a66292b7cd1b10c81a2521352d7648c0bd2b5037af2c457b1617eb7`
through normal guarded setup. Require imports/READY and unchanged protected state;
never replay a completed install intent or use only the six-file archive.

[Sanitized delivery receipt](2026-11-02-linux-node-load.receipt.json).

## Scope and source checkpoint

Owner requests two Amsterdam choices instead of the duplicate legacy assigned-NL
entry, working load for each node, and provisional5Gbps capacity for both.
Existing FLEET-BOOTSTRAP-2 only; public Linux0.2.11, Android110/sequence5 and
Windows0.2.16/sequence12 remain unchanged. Installed Linux is now0.2.12~l03.2.13,
a new full-package delivery, not a replacement of already-qualified .12 bytes.
No public Linux or new Windows/Android release is claimed. Invitation versions,
public download links and signed catalogs are unchanged.

Linux AWG/TCP has Amsterdam1, Russia, Amsterdam2; Auto/MESH retain country-based
routing without offering second-node MESH. Switching back restores the chosen
manual node. Existing backend assignments are not changed by UI initialization.
Country legacy telemetry remains compatible; new node samples must match the exact
gateway ID and country and pass the same freshness/finite-number bounds. Missing
node metrics never fall back to another node or the country sample. The RU legacy
NL alias remains first-Amsterdam-only, even when that node is temporarily absent.

Capacity5000Mbps is operator-assumed, not a measured speed or provider guarantee.
The duplex-channel percentage uses max(RX,TX)/5000; displayed utilization
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
  product validation. Exact package/render acceptance is recorded separately above.
- Backend telemetry-only source pin updated; native transport source unchanged.
- Final artifact/installed-receipt consistency, new documentation links and
  whitespace PASS. The broader nine-document/700-link scan retains one existing
  historical STATUS anchor failure: `2026-10-27-vpn-health.md#evening-readback--1736utc`.
  The pre-edit STATUS/PLAN snapshot reproduces the same failure; unrelated owner
  documentation/untracked history is preserved, not silently repaired or called PASS.

## Delivery and rollback gates

PASS: live monitor configuration, verified public per-node samples, full .13
DEB/AppImage/system qualification, packaged GTK interaction/rendering, guarded
owner installation, installed startup and live node metrics.
PENDING: owner-initiated physical connections and Disconnect acceptance.
Do not ask the legacy six-file updater to install this internal full candidate.

Only the monitoring services may be installed/restarted for this request. Preserve
existing forced-command SSH restrictions and accepted pins; back up monitor source,
configuration and any changed monitoring key authorization privately. Revert only
those files/service changes if acceptance fails; never restart the VPN/backend to
repair telemetry. The accepted NL2 pin is RSA from the retained owner-approved
known-hosts file; an unrecognized ED25519 key scan was not accepted or used.

Any later owner package update requires disconnect/closed GUI, idle services/
ownership and fresh protected-state fingerprints. Keep .12 full DEB and matching
embedded system for guarded rollback; no data deletion, marker removal or automatic connection.
