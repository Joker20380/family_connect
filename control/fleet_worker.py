"""One bounded reconciliation pass over durable fleet intents.

Adapters are operator-configured/authenticated per gateway. execute() must use the
gateway-side fence, not raw SSH wg commands. No signing or payment side effects.
"""
from control.fleet_gateway import PeerCommand, receipt
from control.fleet_store import LeaseRejected


class FleetWorker:
    def __init__(self, store, adapters):
        self.store, self.adapters = store, dict(adapters)

    def once(self, *, limit=100):
        self.store.expire()
        results = []
        for lease in self.store.pending(limit=limit):
            result = self.process(lease)
            results.append((lease.lease_id, result))
        return results

    def process(self, lease):
        try:
            work = self.store.work_item(lease.lease_id, generation=lease.generation)
            command = PeerCommand(lease_id=lease.lease_id, gateway_id=lease.gateway_id,
                device=lease.device, wg=work.wg, address=lease.address, transport=lease.transport,
                version=lease.version, expires_at=lease.expires_at, generation=lease.generation,
                operation='present' if lease.state == 'reserved' else 'absent')
            answer = self.adapters[lease.gateway_id].execute(command)
            # Receipt is meaningful only through the authenticated adapter.
            if (type(answer) is not dict or type(answer.get('generation')) is not int
                    or answer != receipt(command)):
                raise ValueError('receipt-mismatch')
            if command.operation == 'present':
                self.store.mark_ready(lease.lease_id, generation=lease.generation)
            else:
                self.store.confirm_removed(lease.lease_id, generation=lease.generation)
            result = 'ready' if command.operation == 'present' else 'released'
        except LeaseRejected:
            result = 'state-changed'
        except Exception:
            # Retain pending work; no exception text/credentials in diagnostics.
            result = 'retry'
        return result
