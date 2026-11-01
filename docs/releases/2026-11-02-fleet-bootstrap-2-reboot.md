# FLEET-BOOTSTRAP-2 — physical role reboot verified

## Result and scope

Physical reboot of the reserved disposable Ubuntu24.04/x86_64 VPS: **PASS**.
This continues the existing FLEET-BOOTSTRAP-2; it creates no new PLAN ID and does not
start production admission, FLEET-ACTIVATION-1, catalog publication or user onboarding.
Run date is 2 November 2026 in Europe/Brussels; receipt timestamps use UTC Unix seconds.
The VPS is retained, not deleted or reinstalled. Final rehearsal instance state is **RETIRED**.

Frozen source `d3416ea4abacfafc843411f765fb8037722b55d0` and the qualified A/B pair are unchanged.
This run uses bundle A `gw-e215192b1e491de45ae1fa103fd9ba94` and agent SHA256
`837f885b278b52b1808fbc3178b7b9e21d1f41eed9428da5f715fc36a411c23a`. No native/config/protocol/slot contract was patched.
[Package hashes and source qualification](2026-11-01-fleet-bootstrap-2-ready.receipt.json)
and [prior physical A→B→A evidence](2026-11-01-fleet-bootstrap-2-host-ab.receipt.json)
remain accepted and immutable. B was not rebooted in this run.

## Physical evidence

Instance `fleet-rehearsal-nl-disposable-07` used a fresh signed four-hour permit,
new enrollment and disposable material after verified predecessor retirement. Every remote
action retained the exact target/SSH pin, bundle/agent/signer binding and target-side reverification.

| Phase | AWG | TCP REALITY | MESH | Services / restarts | Signed external receipt SHA256 |
| --- | --- | --- | --- | --- | --- |
| Before reboot | PASS | PASS | PASS | 6 active /0 | `5e3dc511c99da08fa4e1587a5b65d588cb97ec2ad92f2951b0ef172b4645437c` |
| After reboot | PASS | PASS | PASS | 6 active /0 | `c583ec1ccfb6b0f494876584830ca64f0ec8e482187786e61757178f4921db12` |

AWG handshake/DNS/HTTPS/expected egress, TCP authentication/HTTPS/expected egress and MESH
room/join/READY/registration/Family TLS/DNS/four HTTPS streams/expected egress all passed.
Operator cleanup passed on both runs. The node did not self-assert external success.
The operator signed fresh 300-second receipts against different unpredictable challenges;
the node rechecked local health before each VERIFIED→ACTIVE transition.

One `reboot-verify --request-reboot` from fresh ACTIVE scheduled the fixed delayed reboot.
After SSH returned with the same pinned key, status reconciled the exact completed request
from the durable journal. All six units were already active with zero restarts: no manual
service start, config rewrite, firewall repair or second reboot was used. Bound `reboot_check`
verified a changed boot and unchanged node identity/current bundle before the new challenge.
Monitoring uptime at accepted health observations changed from 17376.18s
to 323.81s. These are observations, not a downtime measurement.
The safe pre-reboot boot digest is `bc049ae703a5a223725727a5fd73d031ef1db27d7fbae2847c5c3fd572e36e18`.

[Sanitized reboot evidence](2026-11-02-fleet-bootstrap-2-reboot.receipt.json) records all 14
operation IDs/durations/hashes, both external receipts' safe results and local-health digests.
Operator intent/completion signatures, raw receipt hashes and external challenge signatures
were verified before export. Archival validation as of issue time does not extend receipt expiry.
No credentials, room URLs, client IPs, raw packets or private identity bytes are published.

## Retirement and recovery boundary

Final drain and retirement: **PASS**. Retirement operation `host472-v7-retire-a-d61d92449259436d8c659527c33ddfd6`,
receipt SHA256 `4ec98e338cc3d3ac2c2aeafcdf64ec06459cf95cb2ced17870e3cfd3bd30d611`. Only owned rehearsal resources and node secrets
were removed. After signed retirement verification, three disposable operator client files were
removed; the original approved probe and separate private publisher credential remain in custody.
Immutable releases and journals remain for audit; no temporary role remains active.
A retired instance cannot be reused: later authorized host work needs a new permit/enrollment.

The owner reported successful VNC access and explicitly authorized proceeding, offering manual
recovery if needed. No manual recovery was requested. This is owner-confirmed console availability,
not an independently observed recovery exercise. SSH trust remains **owner-accepted TOFU**;
no independent provider-console fingerprint comparison was supplied. Strict pin checking was
not disabled, and this limitation must not become an independent-verification or production-ready
trust claim. The normal handoff requirement remains unchanged for future admission.

## Validation and preserved state

Runtime source is byte-unchanged from the qualified frozen source. Its retained gates are
fleet324 + console156 =480 PASS; paid/backend/package170 PASS; Django check PASS;
migration drift NONE. No claim is made that those full suites were rerun for this docs-only
continuation. This run adds actual before/after-reboot external acceptance, automatic service
recovery, journal reconciliation and physical retirement evidence.

Publication checks: strict JSON PASS; 526 Markdown links across six documents PASS;
secret/privacy guard PASS (3353 index entries, zero blocked); staged scope PASS;
`git diff --check` PASS. Unrelated local work is preserved in ten paths. Public Android109/sequence4/catalog4,
paid baseline108, owner entitlement, ledger1/4, cohort1/10 and revenue0 remain unchanged by this
work. Production RU/NL writes0; catalog publications0; user invitations0; paid events0;
phone actions0. No queued production activation starts automatically.
