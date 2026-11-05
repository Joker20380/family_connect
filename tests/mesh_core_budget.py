import datetime


def require_seed_span(duration_seconds, lifetime_seconds, rotation_seconds):
    assert duration_seconds > 0 and lifetime_seconds > 0 and 0 <= rotation_seconds < lifetime_seconds
    supported = lifetime_seconds+rotation_seconds
    assert duration_seconds <= supported, 'SEED_MANAGER_SINGLE_ROTATION_LIMIT: requested runtime exceeds both real seed lifetimes'


def require_delivery_window(observations, next_eligible, lateness=0):
    assert lateness >= 0
    for slot, observation in observations.items():
        deadline = datetime.datetime.fromisoformat(observation['last']['security'].replace('Z', '+00:00')).timestamp()
        assert deadline-next_eligible >= 1395+lateness, f'{slot}: SEED_CAPPED_DELIVERY_WINDOW_TOO_SHORT'
