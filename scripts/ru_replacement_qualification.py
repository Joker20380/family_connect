"""One bounded, synthetic replacement profile for the existing systemd fixture."""
import json
import time


WINDOW_SECONDS = 600
WATCH = 'family-connect-paid-watch.service'


def registration_sets(identities):
    if len(identities) != 63 or len(set(identities)) != 63:
        raise ValueError('EXPECTED_63_DISTINCT_SYNTHETIC_IDENTITIES')
    return identities[:20], identities[:6] + identities[20:], identities[1:6]


def call_summary(journal):
    summary = {}
    for line in journal.decode().splitlines():
        try:
            progress = json.loads(line).get('transport_progress', {})
        except (ValueError, AttributeError):
            continue
        for entry in progress.get('calls', []):
            key = entry['kind']+':'+str(entry.get('role'))
            row = summary.setdefault(key, dict(count=0, maximum_seconds=0, minimum_remaining_seconds=8,
                incomplete=0, process_maxima={}))
            row['count'] += 1
            row['incomplete'] += not entry['completed']
            row['maximum_seconds'] = max(row['maximum_seconds'], entry.get('duration') or 0)
            row['minimum_remaining_seconds'] = min(row['minimum_remaining_seconds'], entry['remaining'])
            for name, stage in entry.get('process', {}).items():
                if isinstance(stage, dict) and stage.get('duration') is not None:
                    row['process_maxima'][name] = max(row['process_maxima'].get(name, 0), stage['duration'])
    assert summary, 'MISSING_PER_CALL_DATA'
    return summary


def qualify(receipt, inner, operator, cycle, nodes, paid_device, *, clock=time):
    expected = dict.fromkeys(nodes, 'applied')
    checks = receipt['checks']
    checks['context'] = {node: inner(node, 'replacement-context') for node in nodes}

    def refresh():
        result = cycle()
        assert result == expected, 'RECONCILIATION_FAILED_STOP_NO_RETRY'
        return result

    def readback():
        return {node: inner(node, 'live-readback') for node in nodes}

    def allow(event, duration):
        now = int(clock.time())
        operator('activate', event, start=now, end=now+duration)
        refresh()
        return inner('client', 'dns-probe', dict(allowed=True))

    checks['active_dns_https'] = allow('replacement-initial', WINDOW_SECONDS+90)
    initial = {node: inner(node, 'info') for node in nodes}
    first_lease = initial[nodes[0]]['state']['records'][paid_device]['decision']['valid_until']
    started = clock.monotonic()
    samples = []
    while clock.monotonic()-started < WINDOW_SECONDS:
        refresh()
        live = readback()
        for node in nodes:
            assert inner(node, 'info')['services'] == initial[node]['services'], 'UNEXPECTED_RESTART'
        samples.append(dict(elapsed=clock.monotonic()-started, live=live))
        clock.sleep(min(20, max(0, WINDOW_SECONDS-(clock.monotonic()-started))))
    renewed = inner(nodes[0], 'info')['state']['records'][paid_device]['decision']['valid_until']
    assert renewed > first_lease+120 and clock.time() > first_lease
    checks['ordinary_window'] = dict(seconds=clock.monotonic()-started,
        required_seconds=WINDOW_SECONDS, first_lease=first_lease, renewed_lease=renewed, samples=samples)

    deadline = inner(nodes[0], 'info')['state']['records'][paid_device]['decision']['valid_until']
    assert deadline == inner(nodes[0], 'info')['state']['records'][paid_device]['decision']['paid_until']
    while clock.time() < deadline:
        refresh()
        clock.sleep(min(10, max(0, deadline-clock.time())))
    clock.sleep(3)
    checks['natural_expiry_denied_noncohort_survives'] = inner('client', 'probe', dict(allowed=False))
    checks['expiry_live_sets'] = readback()

    checks['renewal_dns_https'] = allow('replacement-renewal', 600)
    lease = inner(nodes[0], 'info')['state']['records'][paid_device]['decision']['valid_until']
    clock.sleep(max(0, lease-clock.time())+4)
    checks['center_loss_denied_noncohort_survives'] = inner('client', 'probe', dict(allowed=False))
    checks['lease_expiry_live_sets'] = readback()
    refresh()
    checks['fresh_lease_dns_https'] = inner('client', 'dns-probe', dict(allowed=True))

    operator('revoke', 'replacement-terminal')
    refresh()
    checks['revoked_live_sets'] = readback()
    before = inner(nodes[0], 'info')['state']['records'][paid_device]
    inner(nodes[0], 'restart')
    after = inner(nodes[0], 'info')['state']['records'][paid_device]
    for field in ('decision', 'prepared', 'boot', 'deadline'):
        assert before.get(field) == after.get(field), 'RETAINED_STATE_CHANGED'
    checks['controlled_restart_terminal_deny'] = inner('client', 'probe', dict(allowed=False))
    refresh()
    checks['final_live_sets'] = readback()
    checks['scope'] = 'synthetic private IPv4 DNS/TLS/egress; no public endpoint or owner-client acceptance'
