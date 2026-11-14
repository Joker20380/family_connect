# DEVICE-TECHNICAL-METADATA-1 — 15 November 2026

## State

IN_PROGRESS / NOT_DEPLOYED / NOT_USER_READY. This is the selected product work,
not recorder architecture or production failure-writer work. RU CAUSE_OPEN and
PR36 NO_GO_PREFLIGHT remain. PR37 sourcea5067ae2 and merge53a780d9 are the entry
baseline, not qualification of this change. No delegated agents.

Remote main53a780d9ccfcdb2c3ec6141a197917190f9be7a5 verified by fetch. Primary
checkout8937e71e has unrelated modified/untracked files and diverged history;
all preserved. Worktree branch: feature/device-technical-metadata-20261115.

## Observed ingress and deployment boundary

Read-only authorized RU inspection: TLS nginx listens8443; Friends routes proxy
to loopback18086, NOT the inactive legacy18084 unit. Current Friends locations
do not overwrite a client-address header. Therefore neither self.client_address
nor arbitrary X-Forwarded-For is suitable for city attribution. No header, route,
service, policy or production data has been changed. RU filesystem available7514MiB
at entry; recheck before any GeoIP staging (including rollback space).

Latest prior verified paid rollout uses exact108/119/123/125 descriptors and
separate HTTP/operator/reconciler archives; reuse their actual runtime baseline,
not arbitrary main. Fresh baseline and consistent private backups/restoration
checks are required immediately before deployment; historical64/118 counts are
not today's acceptance expectations. No production payment/period changes.

## Contract and retention design

New versioned endpoint; old support and seven-day diagnostics contracts unchanged.
New consent is off by default and lasts until explicitly disabled. Latest hardware,
application, network, mobile, session and diagnostic observations each expire in
seven days, independently of readiness/support updates. Revocation deletes payloads;
minimal identity-bound consent/sequence tombstones prevent delayed resurrection.
No raw IP persistence, coordinates, SIM IDs, traffic, messages or identity secrets.
Collector projections must replace current data, not append it to inventory history.

## Pending delivery gates

Implementation/security/lifecycle tests, Android API27/API35 and NVIDIA/KVM runtime
qualification; installed125→new identity/settings/support preservation; local MMDB
positive/provenance/negative checks; latest-only panel projection and UI; exact APK
CI/signing/source archive/hash; isolated paid compatibility; consistent production
backup/restore; minimal runtime/panel/policy delivery; public discovery/invitations/
full HTTPS byte verification; PR/own review/ordinary merge and remote SHA readback.
Physical5G/carrier cases may be NOT_OBSERVED with fallback tests, not fabricated PASS.

Rollback must restore code/config only, preserving later user events and metadata
revocation tombstones. Never restore old databases over live data. No transport
restart, kill-switch bypass, new dangerous permission or RU persistence changes.
