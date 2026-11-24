# P1 four-member gateway expansion —2026-10-26

Result: requested SERVER PROFILE expansion completed and verified. User explicitly
authorized four total identities and a shared gateway restart. Not a new Android
release, not proof of the target's installation or negotiated live P1 session.

## Exact scope

Preserved the owner and two existing testers; added the requested third tester.
Authoritative RU checks before and under renewal locks found exactly one active,
non-revoked canonical identity per expected public signing-key hash. No DB updates,
invites, key replacement, re-enrollment, global entitlement or P2 grant. Target
canonical reference is retained privately; policy uses SHA256 of the certificate Ed25519
public-key half, truncated to16 bytes, not Support ID or canonical device ID.
Support IDs occur only in administrative evidence, never in client code.

## Source and artifact

Frozen accepted23.10 source, not unrelated current desktop changes, rebuilt
byte-identically to loaded baseline:
`a515539af72844cb5af4f918a229c85e23cff874f0f6ac369649df3839273c85`.
Only production delta: speed-targets bound99→132 bytes, member cap3→4.
Tests extended for four accepted/fifth denied, old three preserved, newline
boundary, owner-only diagnostics, invalid/duplicate/wildcard/P2/pacing rejection
and protected file permissions. No protocol/native/mux/window/crypto change.
Reproducible delta: `deploy/friends/restricted/p1-four-members.patch`, applicable
to the frozen baseline carrier module, NOT an instruction to replace current main.
Private source snapshot/inventory/builds/operator receipts:
`state-client-build/p1-four-20261026/`.

Candidate/installed SHA256:
`96754942e7518233bc702277d860b0c9b740fb7553c9742b2ae642a0746fe367`.
Go1.26.1, linux/amd64, CGO1, fc_perf_diagnostic, trimpath, buildvcs=false;
same build settings as baseline. No Git commit/branch created by this task.
Existing shared Android0.1.18-beta106-recovery/code106 remains unchanged,
SHA256242855c43e889e708234ce2f687fa02d37bccb1eee408904f09216b6abd8f020,
signer67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a.
No new signing, public download/catalog update or remote client installation.

## Tests and rollout

Initial sandbox tests failed on forbidden sockets and missing shared vector;
failure log retained. Copied unchanged timestamp vector, reran outside sandbox:
race tests PASS for roombroker, familysession, reliablestream, tcpforward, bootstrap.
Baseline reproduction PASS; Python operator syntax PASS. Pre/post-deployment
TLS served certificate, chain/CRL, validity and RU/NL directory publication PASS.

Under existing RU coordinator/node and NL node locks, saved exact old binary,
group file, unit/argv/config hashes and durable intent. Stopped only NL
family-connect-restricted-bootstrap.service, atomically replaced policy and binary,
started once at17:43:11UTC. Existing AWG/TCP services untouched.
Final PID1244097, invocation68b76cc72c8044d7900be5c736a77d14, active/running,
NRestarts0. Actual /proc executable matches candidate; unit/argv/config unchanged.
Four-member policy SHA256:
`dd3718efdd99c11582306ecf435e9e393377acf6c5e9c5cbc73f0bb72aa9e81f`.
All original members preserved, target present exactly once, service-owned0600
under0700; P1 enabled, pacingOFF, diagnostic target remains owner-only.
Repeating set addition yields unchanged policy (NO_OP readback); no repeated write.

Operator error retained: after all start/identity/policy assertions passed, a local
variable name reused for an fsync descriptor broke final receipt formatting.
Control-channel closure released RU locks. Readback proved successful transition
from deploy-intent/stopped/replaced/started receipts; fixed operator variable only,
did NOT replay deployment. Independent17:44:06UTC reconciliation wrote
`/opt/apps/family_connect/friends-restricted/bin/.p1-four-20261026-stage/deploy-reconciled.json`.
Post-TLS receipt17:43:44UTC PASS; credentials limiting expiry21:02:03UTC under
unchanged scheduled maintenance, not a client entitlement expiry.

## Rollback and remaining checks

Exact NL backup directory:
`/opt/apps/family_connect/friends-restricted/bin/.p1-four-20261026-stage/`.
Contains baseline executable and policy-baseline (original3), no copied client
private keys. Operator:
`python3 state-client-build/p1-four-20261026/transitions/operate.py rollback --shared-restart-approved`.
Use only after fresh guards/coordinated restart; restores binary AND original3
members, not DB/config/credentials. Never restore old binary with four-member file.
No rollback performed. Unknown outcomes require durable readback, not blind retry.

Target's actual84→106 install, selection/negotiation and live traffic unobserved.
Server permission is enabled; no claim that an offline device already uses P1.
No new security bypass, expanded diagnostics or modifications to other identities.
