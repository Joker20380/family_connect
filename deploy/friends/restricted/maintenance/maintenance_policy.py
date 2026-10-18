import dataclasses

from credential_renewal import canonical, digest, require


@dataclasses.dataclass(frozen=True)
class MaintenanceAuthorization:
    operation_id: str
    expected_state_sha256: str
    approved_at: int
    expires_at: int
    approval: str = 'OPERATOR_APPROVED_OUTAGE'

    def validate(self, operation_id, current, now):
        require(self.approval == 'OPERATOR_APPROVED_OUTAGE', 'MAINTENANCE_APPROVAL_INVALID')
        require(self.operation_id == operation_id and self.expected_state_sha256 == digest(canonical(current)),
                'MAINTENANCE_APPROVAL_BINDING')
        require(self.approved_at <= now < self.expires_at <= self.approved_at + 900,
                'MAINTENANCE_APPROVAL_EXPIRED')


def maintenance_gate(operation_id, current, now, *, inventory=None, approval=None, scheduled=False):
    if approval is not None:
        require(not scheduled, 'SCHEDULED_OUTAGE_FORBIDDEN')
        approval.validate(operation_id, current, now)
        return dict(result='RENEWAL_READY',authorization='OPERATOR_APPROVED_OUTAGE',
                    pre_stop_sessions='UNKNOWN' if inventory is None else inventory.get('count', 'UNKNOWN'),
                    zero_downtime=False)
    if inventory is not None:
        require(set(inventory) == {'count', 'observed_at', 'state_sha256', 'source'}, 'INVENTORY_SCHEMA')
        require(type(inventory['count']) is int and inventory['count'] >= 0, 'INVENTORY_SCHEMA')
        if (inventory['count'] == 0 and inventory['source'] == 'AUTHENTICATED_GATEWAY_INVENTORY'
                and 0 <= now - inventory['observed_at'] <= 5
                and inventory['state_sha256'] == digest(canonical(current))):
            return dict(result='RENEWAL_READY',authorization='FRESH_ZERO_SESSION_INVENTORY',
                        pre_stop_sessions=0,zero_downtime=False)
    return dict(result='MAINTENANCE_REQUIRED',mutations=0,
                alerts=['MAINTENANCE_REQUIRED', 'MAINTENANCE_BLOCKED_BY_SESSION_UNCERTAINTY'])
