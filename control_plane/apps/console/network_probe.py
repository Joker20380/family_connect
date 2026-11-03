"""Credential-free, fixed-endpoint TCP observations; never VPN readiness."""
from datetime import datetime, timezone
import socket
import time

from .collector import ACTIVE_SOURCES, SOURCES

ENDPOINTS = {source: (SOURCES[source]['host'], 8443 if source == 'gateway-ru' else 443)
    for source in ACTIVE_SOURCES}
TIMEOUT_SECONDS = 5


def collect(source, connect=socket.create_connection, clock=time.monotonic, now=None):
    address, port = ENDPOINTS[source]
    started = clock()
    outcome = 'reachable'
    try:
        with connect((address, port), timeout=TIMEOUT_SECONDS):
            pass
    except TimeoutError:
        outcome = 'timeout'
    except ConnectionRefusedError:
        outcome = 'refused'
    except OSError:
        outcome = 'network_error'
    elapsed = round(min(60000, max(0, (clock() - started) * 1000)), 3)
    observed = now() if now is not None else datetime.now(timezone.utc)
    return dict(schema=1, scope='production', source=source, probe='tcp_connect',
        vantage='operator-workstation', address=address, port=port,
        observed_at=observed.isoformat(), outcome=outcome, duration_ms=elapsed)
