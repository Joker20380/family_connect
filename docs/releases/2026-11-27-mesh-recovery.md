# Amsterdam MESH recovery — 27 November 2026

## Observed failure and retained evidence

The owner reports both MESH services stopped while the coherent mandatory-collector
transition is being prepared. Installation is not started. At01:05–01:06UTC both
`family-connect-restricted-bootstrap.service` units are failed/exit1, PID0,
NRestarts5. NL1 Reticulum/mailbox remain active with their original PIDs3769/3705;
NL2 has neither unit by design. These are not substitutes for the actual MESH unit.

NL1's immutable fatal receipts distinguish the00:39:02 scheduled renewal SIGTERM
from the00:43:13 SIGNAL_READ failure, then provider_timeout at SEED_CREATE and
seed_join_failed at SEED_CONNECT. The last failure is00:46:20; restart-limit refusal
is00:46:51. Credentials still have13963 seconds of headroom in that last receipt.
NL2 logs successful seed readiness after renewal, TURN refresh failures and exit1
at00:44:05, then repeated short failed starts through00:47:01 and restart-limit
refusal at00:47:31. NL2 has no corresponding captured first-cause application
receipt: do not infer its initiating cause solely from exit1 or NL1's diagnostics.
Neither provider blocking nor a common underlying network cause is established.

Raw journals/effective units/private screenshots stay outside Git under
`/mnt/data/fc-mesh-incident-20261127`, with root operation records at
`/root/fc-mesh-recover-20261127` on RU/NL1/NL2. No provider credentials, profiles,
room URLs, customer records or private keys are included here.

## Guarded unchanged-runtime recovery

- Read-only provider checks from each NL reach the conference endpoint with expected
  unauthenticated GET405 and Telemost HEAD200; no synthetic room is created.
- Installed three-node renewal evaluate returns NOOP, alerts/due empty, files_changed0,
  remote_writes0/restarts0. Last receipt is COMMITTED for
  `scheduled-1795739918-37dd1d85eed311b0`; current authority/CRL/leaves are valid.
- First attempt to establish timer holds detects the normal renewal controller's
  temporary directory-timer hold and exits before changing either timer. After
  normal completion, a fresh read confirms both timers active, both services empty,
  and no RU ownership. Only then are our own short timer holds recorded/applied.
- Each NL's exact installed maintenance manifest/locator, root operation lock,
  absent renewal owner, profile/key/issuer/CRL/leaf and headroom are checked. Existing
  gateway executable SHA256 is
  `70e6c0fc1b920ad308e24667be94f674c34979dab6aa518e1a8194fff7c131b6`
  at `/usr/local/lib/fc-profile-tools/unified-a597d2a/gateway` on both nodes.
- Exactly one actual `systemctl start` per node. NL1 READY01:15:58UTC, PID1990396;
  NL2 READY01:16:55UTC, PID2732173. The initial NL2 dispatch selected an absent
  interpreter and exited127 before executing code; the corrected dispatch uses its
  observed installed `friends-restricted-runtime/venv` and `mesh2-eb0b5e68e49d`
  capsule, not NL1's paths. That dispatch failure remains retained separately.
- New directory bytes pass the installed directory validator. Loaded binary hashes
  and protected profile bytes are unchanged. Unit boot enablement stays disabled
  as before; no enable/unmask/reset-failed, runtime upgrade, credential rotation,
  database restore, enforcement change or unrelated-service restart occurs.
- RU normal directory-sync invocation `682110f44a204462954683edb5b4c6fe` completes
  01:17:27UTC, success/0. Own holds are removed; both RU timers enabled/active/waiting.

## Independent result and limits

Follow-up01:51:46UTC: both units remain active, but NL1 is no longer the original
recovery invocation. Its01:32:57 fatal receipt is SIGNAL_READ/SEED_READ with11166s
credential headroom and completed cleanup; systemd performs one normal automatic
restart01:33:27. NewPID2011396, invocationb50a80b0768b44939d46483267bd594b,
NRestarts1; no second manual start or credential/runtime change. NL2 remains
PID2732173/NRestarts0. The earlier bounded recovery observation remains history;
sustained stability and initiating provider/network cause are NOT established.

At01:18:30/31UTC the same NL PIDs/invocations remain active/running, NRestarts0,
success. RU at01:18:32UTC has the exact newly validated directory hashes:

| Node | Directory SHA256 |
| --- | --- |
| NL1 | `a64f4af75a272b1d39a7a0205dceef6a2debf79554969966a93400b9e98cd52b` |
| NL2 | `99d9757333ec546ff9328f2ccfd69d4817401a3cb233acb2028f926c6d3030aa` |

The local normal inventory invocation completes01:18:30UTC successfully. A real
authenticated browser visits overview, servers and both Amsterdam cards: all200,
both MESH bootstrap rows say “Процесс работает”, normal logout succeeds. No messages
or manual business-data mutations are issued. This verifies process/readiness,
publication and panel visibility, not phone traffic, long-duration stability or
proof of the provider incident's underlying cause.

No new rollback payload is needed: existing binaries/configuration remain installed.
If the bounded first invocation had failed, the recovery controller would stop that
failed retry cycle rather than loop; evidence remains and a fresh cause/readiness
check is required. Do not restore stale directory/profile/database bytes.

The accepted PANEL_AND_DEPENDENCIES_NORMAL_BASELINE_PASS remains intact. The
mandatory collector maintenance-compatibility changes are unfinished source only;
old panel01 plan/authority/receipts/capsule and installed192343eb are unchanged.
Console/publisher12-file candidates and common capture are not activated here.
Inventory3+12, probe14 and support33 historical markers are not settled or deleted.
