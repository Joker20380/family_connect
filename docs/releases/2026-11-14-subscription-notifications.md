# SUBSCRIPTION-NOTIFICATIONS-1

## Entry and collection prerequisite

Remote main verified `1b186e15cc88302807a7927776b9a5ad1f428149`.
The original checkout and its uncommitted work are preserved; work continues in the
clean existing paid125 worktree fast-forwarded to main, on its existing upstream.
PR23/24/25, public beta125/catalog8, tablet109→125 and paid125/support acceptance
are retained. No APK, deployment, subscription or real message changed here.

Reproduction: collecting `tests/test_chat_service.py` alongside
`clients/desktop/tests/test_chat_service.py` exits2 with `import file mismatch`.
Rename only the server file to `tests/test_chat_service_sender.py`, update its
workflow reference, keep all three pytest testpaths and all tests. The inventory
subprocess inherits stdout/stderr; a subprocess regression verifies the original
failure detail is emitted before the nonzero launcher result.

Local locked support environment: pip check PASS. With system GI appended after
the virtualenv packages, full collection6149 PASS; targeted sender/desktop/context
checks24 PASS. Initial collection without GI failed on desktop support-service;
prepending system packages instead caused five typing_extensions import failures.
These were environment ordering failures, not removed or skipped tests. Full hosted
CI and backend notification gates are NOT claimed from collection success.

## Remaining gates

Durable read-only producer, canonical event/deadline deduplication, service-source
authorization, exact recipient, panel observations, isolated full route, review/merge
and server installation are pending. No new real automatic receipt observed.
Rollback must preserve queue/checkpoints/deduplication; never restore an old registry
over new events. No payment-provider integration, client-card polling or RU repair.
