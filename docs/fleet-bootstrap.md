# Deterministic physical gateway bootstrap

FLEET-BOOTSTRAP-1 is source/synthetic only. No production transport issuance,
catalog publication, paid operation or SSH mutation is authorized by this foundation.
See the [checkpoint](releases/2026-11-01-fleet-bootstrap-1.md).

Logical gateways own country/routing intent. Physical instances own deployment identity,
bundle version, health and operation history. Replacements never inherit physical keys,
renewal/rollback journals, pending operations or short-lived transport material.

State graph: DISCOVERED → PREFLIGHTED → STAGED → VERIFIED → ACTIVE, with DRAINING,
QUARANTINED, FAILED and RETIRED. STAGED cannot become ACTIVE directly. Local synthetic
ACTIVE is not client-visible publication. The [strict contract](../fleet/schemas/README.md)
is independent of existing client leases, subscription and payment state machines.
