"""Advisory only. No imports of fleet admission, operations or transport clients."""
from datetime import timedelta

from .network_probe import ENDPOINTS

LABELS = {
    'no_data': 'Нет независимых сетевых наблюдений',
    'hold': 'Недостаточно свежих согласованных данных · никаких действий',
    'stabilizing': 'Ожидание трёх последовательных проб за ≥90 секунд',
    'observe': 'TCP доступен, службы active · VPN ещё не проверен',
    'investigate_service': 'Проверить службы · TCP доступен, но службы не active',
    'investigate_path': 'Проверить сетевой путь с рабочего места · не доказательство отказа узла',
    'investigate_node': 'Проверить узел и путь · повторный отказ TCP и служб',
}


def assess(source, samples, service_state, now):
    result = dict(state='hold', label=LABELS['hold'], automatic_action=False,
        vpn_readiness='not_checked', latest=None)

    def finish(state):
        return dict(result, state=state, label=LABELS[state])

    if source not in ENDPOINTS:
        return finish('hold')
    if not samples:
        return finish('no_data')
    recent = samples[:3]
    for sample in recent:
        if (sample.source != source or sample.scope != 'production'
                or sample.probe != 'tcp_connect' or sample.vantage != 'operator-workstation'
                or (sample.address, sample.port) != ENDPOINTS[source]
                or sample.observed_at > now or now - sample.observed_at > timedelta(minutes=5)
                or sample.outcome not in ('reachable', 'refused', 'timeout', 'network_error')):
            return finish('hold')
    result['latest'] = recent[0]
    if now - recent[0].observed_at > timedelta(seconds=150):
        return finish('hold')
    if service_state not in ('observed_active', 'degraded'):
        return finish('hold')
    if len(recent) < 3:
        return finish('stabilizing')
    gaps = [(newer.observed_at - older.observed_at).total_seconds()
        for newer, older in zip(recent, recent[1:])]
    if any(gap <= 0 or gap > 150 for gap in gaps):
        return finish('hold')
    if sum(gaps) < 90:
        return finish('stabilizing')
    successes = [sample.outcome == 'reachable' for sample in recent]
    if all(successes):
        return finish('observe' if service_state == 'observed_active' else 'investigate_service')
    if not any(successes):
        return finish('investigate_path' if service_state == 'observed_active' else 'investigate_node')
    return finish('stabilizing')
