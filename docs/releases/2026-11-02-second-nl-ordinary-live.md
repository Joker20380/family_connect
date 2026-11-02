# Second Amsterdam: ordinary AWG3.1/TCP admission

**SECOND_NL_ORDINARY_LIVE — AWG3.1 and TCP REALITY only.**
Continuation of FLEET-BOOTSTRAP-2 under the owner's later production authorization.
This is not a claim that a second production MESH/renewal stack has been admitted.

## Actual result

- New node185.10.158.196, Ubuntu24.04/x86_64, owner-reported Amsterdam, now runs enabled
  `family-connect-friends-awg.service` and `family-connect-friends-tcp.service`.
  Both remain active with NRestarts0; startup was00:43:32/00:43:31UTC respectively.
- Independent operator-container AWG3.1 handshake/DNS/HTTPS/egress and REALITY auth/
  DNS/HTTPS/egress PASS. Both operator and target probe cleanup PASS; zero disposable
  peers/users remain. These are real external tests, not node self-assertion.
- The existing RU registration private key stays on RU. Only its public key was admitted
  on the new node, restricted by source IPv4 and a fixed forced registration command.
  RU→new-NL registration with strict host-key checking and credential-free argv PASS;
  its temporary persistent peer and TCP entry were removed and config restored exactly.
- Routing generation2 admits new device assignments to the second NL. All57 existing
  device assignments remain on the first NL185.10.158.212. No existing device was moved.
- The unchanged schema2 contract works with Android109, public Linux0.2.11 and
  Windows0.2.15. This changes backend assignment, not the country selector or installers.
  It does not add a manual two-NL selector or migrate every existing client automatically.
- MESH/readiness, directory distribution and production renewal remain on the existing
  first-NL path. No Telemost credential or FLEET_MESH_PROBE_1 identity was read/copied here.

The owner's existing TOFU pin was explicitly accepted without another VNC comparison.
StrictHostKeyChecking and the dedicated single-host pin remain enabled. This is not
independent provider verification. No insecure SSH flag, password in chat or reinstall.

## Bound source and publication

Installed native/helper capsule source: `02181e366afeccda00511c8ee29215b029c535de`.
Capsule manifest SHA256 `6974fd804193cef21bac5276d5fc607e208066ec2d0a40406cfcaaf9d4a920bc`;
archive SHA256 `3b29bde7951f8c1a3dd829809a7845fda1d24d5b886e1f06e8c51f9848255c44`.
The exact three native hashes retain their accepted inventory/provenance; no observed or
unbound binary was substituted. New server keys/material were generated locally on this node.
Operator external probe source: `a2df2a1b09de0a30f22ea045df91717ae98a2e9f`.

The closed HTTP archive from corrected routing source
`88bc7e54c9e1ac362948aec562c939d7bdebbee3` is now serving on the existing RU candidate unit:
`f33dee20e5069353914def7ae3a338631fbc4a5af7bf48af1d6fddbe5662b669`.
Comparison with the actual served paid108 predecessor8e74997c… proves only
`friends_http.py` changed and `control/friends/gateway_routing.py` was added; every other
member, including paid/ordinary/restricted/chat/publisher code, is byte-identical.
The archive was already built twice byte-identically and its locked-source tests passed.

Original `catalog.json` remains byte-identical at sequence4, SHA256
`214cb6a3611b5c05117dd2ddfbfbb2f8add0603c680368a9299b34cd28214922`.
Offline-signed per-device variants are stored privately, not in Git:

| Purpose | Sequence | Signed envelope SHA256 |
| --- | --- | --- |
| Second NL, new assignments | 5 | `f543fb9c0d3b54a4436a7468376bf22980214422720c4103c11f8fcaf7e038a6` |
| First-NL forward rollback, reserved | 6 | `e89ff6da3edc85008a397d8aa75e1e00f0d8923d0368ed7d15faa455ca57b37e` |

Signing public-key SHA256: `6a09fb42468acdb4cfcb4f0888e27c13705ac437a45a6624fc21dddbe83fed83`.
The existing offline signing key never left local custody. Both variants retain the exact
RU template and existing client root. No Android/desktop update catalog, installer or tag
was published. Sequence5 is now eligible for authenticated configuration delivery to new
assignments; this is a real routing publication, not a zero-publication source checkpoint.

Policy1 seeded existing devices with no move. Policy2 SHA256:
`c7d9b6399c45f14e8ef12f94b9fa6a7fe57f4b0a3724088cf7b17c78fd8381e9`.
Two append-only operation events are present. The node admission marker fences the
first-install helper's start/stop actions; that helper is not the production status API.

## Failures and reconciliation

1. First preparation stopped before creating units: private umask made newly created
   application ancestors0700. Readback proved no service start/forwarding. Private failed
   state was retained; exact empty owned directories were reconciled before operation02.
   Source correction and a real service-user/native-config/container check passed.
2. The first HTTP override sorted before existing `zzzzzz-paid-baseline108.conf` and did
   not become effective. Readback rejected the unchanged running argv; bounded rollback
   restored the retained predecessor and resumed both maintenance timers. No database was
   restored. A new operation used the correctly ordered override and checked effective
   D-Bus ExecStart **before** restart and running argv after startup. Final HTTP is f33dee20…,
   NRestarts0. There were3 controlled HTTP restarts total, including1 bounded rollback.
3. A final health harness expected literal `0.0.0.0:443`; `ss` reported the valid wildcard
   `*:443`. Its assertion failed despite the previously successful external test. The shell
   command sequence incorrectly continued to policy2 publication after that assertion.
   This ordering defect is recorded, not relabeled as a pre-publication gate PASS. Immediate
   readback found both original processes active/NRestarts0 and the exact listener owners.
   The corrected checker validates endpoint scope/port/PID, not presentation spelling;
   admission now has an in-process freshness/health/external/registration precondition, so
   a missing/failed observation cannot be bypassed by shell sequencing. Regression tests
   cover all wildcard spellings, wrong owner/scope/port, missing/stale/failed evidence.
   Fresh corrected local health and final policy/registry readback PASS; all57 existing
   assignments remained on the first NL and no new device appeared in that interval.

## Validation and preserved state

- New installer/probe/health source:52 tests PASS, no skips.
- Final selected ordinary/routing/catalog/HTTP/client contour:339 PASS,25 existing
  environment-dependent skips; zero failures/errors.
- Network-disabled Ubuntu24.04 root simulation: exact Xray validation under `fc-friends`,
  `systemd-analyze verify`, positive TCP config access and negative AWG-secret access PASS.
  This simulation did not start real systemd or claim network/physical reboot acceptance.
- Real new-node local native/config/service/listener/forwarding/NAT checks PASS.
- Retained prior qualification: Android JVM174 PASS; native Windows conformance/DPAPI,
  ordinary-user access, desktop visual and Client builds PASS. Public tagged Linux parser
  accepts the three routing vectors; Windows public parsers are byte-identical.
- Retained paid/package regression327 PASS/22 isolated-root skips and unchanged fleet/
  console480 PASS. These are retained results, not newly rerun whole-suite counts.
- Broader phase0 was still running at observation. Superseded Linux preview runs were
  cancelled by workflow concurrency. No blanket latest full-CI PASS is claimed.

SQLite backup plus isolated restore/integrity/FK checks PASS before rollout. Protected
row hashes before/after match: devices57, invites111, restricted grants2, paid subscriptions1,
paid events4. Owner entitlement/paid108/ledger1/4/cohort1/10/revenue0 are unchanged.
Both credential-renewal and directory-sync timers are active again. No first-NL service was
changed. RU backend/registration pin and new-node deployment were authorized mutations;
production writes and routing publications are therefore **not zero** for this admission.
User invitations0; paid-event mutations0; phone actions0. Probe client files were removed
only after target cleanup and final receipts; permanent node keys remain solely on the node.

## Rollback and remaining boundary

Keep the routing-aware HTTP package once assignments are enabled. Returning to the old
pre-routing HTTP after sequence5 delivery would cause downgrade refusals and is not a valid
routine rollback. To stop new second-NL assignments, install a higher-generation policy using
the already signed first-NL sequence6 catalog; move only affected second-NL devices through
explicit forward-only assignment operations, preserving the append-only journal. Never restore
the product database or revoke the first NL. No rollback is currently required.

Second-node MESH/renewal and a manual two-NL client selector are not delivered by this ordinary
admission. No new production-layout reboot test or real end-user activation is claimed; real
transport and registration probes used disposable material without issuing an invitation.

[Sanitized receipt](2026-11-02-second-nl-ordinary-live.receipt.json) ·
[Source preparation](2026-11-02-second-nl-ordinary.md) ·
[Compatible routing design](2026-11-02-fleet-multinode-source.md).
