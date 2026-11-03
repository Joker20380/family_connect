# Isolated native data-plane canary qualification — 3 November 2026

## Selected task and authorization boundary

Continuation of FLEET-BOOTSTRAP-2 after the
[independent TCP observation/advisory step](2026-11-03-fleet-network-probes.md).
The owner requests the next step without interactive personal testing. The old
admission probes were cleaned up; no permanent production canary credentials exist
in that evidence. Retired rehearsal keys and user/owner profiles are not a substitute.

This bounded task qualifies the canary implementation using real native AWG3.1 and
VLESS REALITY traffic inside disposable Docker networks. It does not register a
production identity, change an assignment, open an invitation, restart a production
service, change a policy or catalog, or import synthetic evidence as node readiness.
Production AMS1/AMS2 per-transport acceptance remains NOT_RUN by this task.

## Topology and proof

[Runbook](../../pilot/fleet-canary/README.md). Host runner
`scripts/test_fleet_canary.py` builds an allowlisted two-file context and creates
exactly two internal networks plus client, gateway and controlled origin containers.
The gateway alone connects both networks. No host network/PID/private bind mount,
public port, privileged container or broad device access. Read-only root filesystems,
tmpfs secret custody, no-new-privileges and exact capabilities are checked after creation.
NET_ADMIN is namespace-local on client/gateway, TUN is the only passed host device.

All keys and identity UUIDs are newly generated and discarded. Native binaries retain
the accepted hashes; source hash must match the executed image. No release-signing,
Friends identity, source capsule, database, server private key or SSH credential is used.
The host sees private fixture material only in process memory/stdin, never argv/report/Git.

- REALITY: running native client must reject wrong UUID and wrong server public key.
  Only the valid identity reaches domain-based, certificate-verified HTTPS through
  the gateway's remote DNS resolver. No direct/freedom client fallback exists.
- AWG3.1: wrong server key cannot reach the origin. Correct key must give a new
  handshake, nonzero transfer counters, interface-bound DNS and verified HTTPS/NAT.
- The TLS1.3 origin echoes a fresh nonce and exact gateway egress address. The client
  has no direct origin route before/after the tunnel; cached or generic200 cannot pass.
- Origin counts must show two HTTPS application requests, exactly the two positive
  controls, and DNS traffic. Negative controls must not obtain an application response.
- Commands are bounded; the host removes only exact run-labelled resources in finally.
  A cleanup failure makes the entire run FAIL. No periodic canary timer is installed.

This is genuine native packet/authentication/forwarding proof, but a controlled
single-workstation test. Public PKI/DNS, Internet/provider firewall, real Amsterdam
nodes, desktop/mobile lifecycle, MESH and independent failure domains are not tested.

## Checkpoint and retained failures

Unit guards initially33 PASS; capability canonicalization/device-budget and JSON/nft
fixture regressions bring the final count to37. Native qualification PASS below.

1. Attempt01 failed before native traffic; resources cleaned up. Attempt02 identifies
   verify-isolation: Docker returns `CAP_NET_ADMIN`/`CAP_NET_BIND_SERVICE`, while the
   initial comparator expected unprefixed aliases. Normalize only the standard prefix;
   the exact capability set remains enforced, with an added extra-capability rejection.
2. Attempt03 failed gateway setup; attempt04 identifies the Xray configuration gate.
   Fixture filenames used `.tcp`, which is not Xray's JSON config extension. Changed
   only fixture files to `.json`; no native parser/identity check or product code relaxed.
3. Attempt05 reached nft configuration but rejected the one-line nested-chain syntax.
   A separate isolated `nft -c` reproduced the missing line separator; use normal
   multiline syntax and add a regression for the exact source/destination-scoped rule.
   No permission, forwarding restriction, NAT source match or production firewall changed.
4. All failed receipts are retained privately, with cleanup PASS, production writes0
   and production node acceptance NOT_RUN. None is a transport acceptance PASS.

Raw local receipts are ignored under `state-client-build/fleet-canary-20261103/`.
Final qualified image/source hashes, test counts and sanitized receipt follow below;
no source push or fixture build alone is a runtime PASS.

Versions unchanged: installed Linux `0.2.12~l03.2.13`, public Linux `0.2.11`, Android110/
catalog5 and Windows `0.2.16`/catalog12. Owner physical acceptance DEFERRED_TO_FIELD.
Existing local inventory/network timers and console deployment remain unchanged.

## Qualified native run

Attempt06 at07:45:05–07:45:19UTC: ISOLATED_NATIVE_DATA_PLANE_PASS.
Image `sha256:541e3a7f23782b8f07a47f8bae95350fe8d1cac2dfe1bc9bd5d7bd3b564e35b1`.
Independent repeat attempt07 at07:46:40–07:46:54UTC on the same exact image/source
also PASS with newly generated keys, fresh nonce, identical gates and cleanup PASS.
Runtime source equals the measured `pilot/fleet_canary.py` hash; both transport keys
are fresh disposable fixture material, not copied profile data.

| Check | Result |
| --- | --- |
| Direct origin bypass before tunnel | REJECTED |
| REALITY wrong UUID / wrong server public key | REJECTED / REJECTED |
| REALITY valid identity, remote DNS, verified TLS HTTPS, exact egress | PASS |
| TCP child/SOCKS cleanup | PASS |
| AWG wrong server public key | REJECTED |
| AWG fresh handshake + received/sent counters + interface DNS + verified HTTPS/NAT | PASS |
| Direct bypass after cleanup | REJECTED |
| Client interface/process cleanup | PASS |
| All owned containers and both internal networks removed | PASS |

Origin observed exactly2 DNS queries and2 application HTTPS requests, one positive
request per transport with the same current-run nonce and expected gateway egress.
No HTTP request passed the negative authentication controls. The nonce is not an
independent authority; topology/authentication/CA/egress checks jointly bind the proof.

Accepted native SHA256 values, verified during build and on every inner invocation:

| Native component | SHA256 |
| --- | --- |
| AWG3.1 CLI | `906d6795af1dd4adee7b11bf1e7fa133d4795c8a8d6e2099b34a026f810a3278` |
| AWG3.1 userspace engine | `e7f00e47d6df853ade5dcd2fe79240f01ff897d75088c768316a444c27c87e0f` |
| Xray | `4f7a4436f86798bbb5c875014e352021a1673710a45e170ccc507c5f59341940` |

No client package was rebuilt; installed/public/invitation versions remain as above.
The source adds an opt-in qualification harness only. Product observation/admission
code is unchanged and receives no synthetic ready marker from this run.
[Sanitized qualification receipt](2026-11-03-fleet-data-plane-canary.receipt.json).

Final37 unit guards PASS; source hashes and both successful receipts match. Docker
label readback confirms no remaining run containers/networks; both pre-existing
inventory/network timers remain active and the console stays on its prior image
`sha256:55119faec980ca2ce58bf3f1846c01f649a2e8a31ca6fccdfb84ffd1b0474285`.
New documentation links and whitespace PASS. The broader5-file/524-link check retains
only the pre-existing STATUS27 October historical anchor error; not a full docs PASS.

## Rollback and next boundary

There is nothing deployed to production or installed in a client to roll back.
For a failed/interrupted run, use the exact receipt run label to inspect and remove
only its temporary containers/networks; retain all evidence and do not run prune.
SIGKILL/host shutdown may require this bounded cleanup; ordinary failure/TERM cleans
up in the runner. Fixture images remain local; no user configuration should be restored.

A later production canary requires dedicated test-only credentials, strictly scoped
temporary registration/revocation, an exact target/expiry journal and before/after
conservation of existing peers/users/services. No borrowing customer identity or
re-enabling retired credentials. These are next-task gates, not automatic permission
to mutate the production gateway or enable recovery/failover from this queue.
