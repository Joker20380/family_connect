"""Bounded, payload-free classification for the disposable normal fixture."""
import re
import time


class Trace:
    def __init__(self, addresses):
        self.addresses = set(addresses)
        self.started = time.monotonic()
        self.flows = set()
        self.events = []
        self.reasons = {}

    def accept(self, line):
        if time.monotonic() - self.started > 180 or len(self.events) >= 512:
            return
        matched = re.search(r'\[(\d+)\]', line)
        if not matched:
            return
        flow = matched.group(1)
        target = re.search(r'(?:tcp|udp):(?:\[([^]]+)\]|([0-9.]+)):(\d+)', line)
        if target and (target.group(1) or target.group(2)) in self.addresses and target.group(3) == '443':
            self.flows.add(flow)
        labels = (
            'received request for', 'connection opened to', 'connection ends',
            'connection closed', 'connection reset by peer', 'broken pipe',
            'context canceled', 'i/o timeout', 'EOF', 'no route to host',
            'network is unreachable', 'failed to transfer request payload',
            'failed to transfer response payload', 'failed to decode response header',
            'XTLS rejected UDP/443 traffic', 'XtlsFilterTls found tls client hello!',
            'XtlsFilterTls found tls 1.3!', 'XtlsFilterTls found tls 1.2!',
            'Xtls Unpadding new block', 'XtlsRead', 'XtlsWrite',
        )
        found = [label for label in labels if label in line]
        for label in found:
            self.reasons[label] = self.reasons.get(label, 0) + 1
        if flow in self.flows and found:
            self.events.append({'flow': flow, 'elapsed_ms': int((time.monotonic() - self.started) * 1000),
                                'labels': found, 'ipv6': bool(target and target.group(1))})

    def snapshot(self):
        return {'events': self.events, 'reason_counts': self.reasons, 'controlled_flows': len(self.flows)}
