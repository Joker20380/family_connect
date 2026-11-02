from datetime import timedelta

from .collector import ACTIVE_SOURCES, SOURCES


STATE_LABELS = {
    'no_data': 'Нет наблюдений в выбранном периоде',
    'retired': 'Архивный узел · больше не опрашивается',
    'clock_skew': 'Время снимка в будущем · состояние неизвестно',
    'stale': 'Устарело: старше 5 минут',
    'unknown': 'Состояние обязательных служб неизвестно',
    'degraded': 'Не все обязательные службы active',
    'observed_active': 'Наблюдаемые службы active · не проверка VPN',
}


def observation_state(source, snapshot, now):
    if source not in ACTIVE_SOURCES:
        return 'retired'
    if snapshot is None:
        return 'no_data'
    if snapshot.source != source or snapshot.scope != 'production':
        return 'unknown'
    if snapshot.observed_at > now + timedelta(seconds=15):
        return 'clock_skew'
    if snapshot.observed_at < now - timedelta(minutes=5):
        return 'stale'
    services = snapshot.server.services
    states = [services.get(service, 'unknown') for service in SOURCES[source]['required_services']]
    if any(state in ('failed', 'inactive', 'not_found', 'deactivating') for state in states):
        return 'degraded'
    if any(state not in ('active', 'activating') for state in states):
        return 'unknown'
    return 'observed_active' if all(state == 'active' for state in states) else 'degraded'


def server_cards(snapshots, now, selected_source=''):
    by_source = {snapshot.source: snapshot for snapshot in snapshots}
    sources = [selected_source] if selected_source else list(ACTIVE_SOURCES) + [
        source for source in by_source if source not in ACTIVE_SOURCES]
    cards = []
    for source in sources:
        if source not in SOURCES:
            continue
        snapshot = by_source.get(source)
        state = observation_state(source, snapshot, now)
        cards.append(dict(source=source, label=SOURCES[source]['label'], snapshot=snapshot,
            state=state, state_label=STATE_LABELS[state]))
    return cards
