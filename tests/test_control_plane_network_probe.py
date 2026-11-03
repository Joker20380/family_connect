from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest

from control_plane import probe_network
from control_plane.apps.console import network_probe, recovery_policy

NOW = datetime(2026, 11, 3, 10, tzinfo=timezone.utc)


@pytest.mark.parametrize('source', network_probe.ENDPOINTS)
@pytest.mark.parametrize('error,outcome', [(None, 'reachable'), (TimeoutError, 'timeout'),
    (ConnectionRefusedError, 'refused'), (OSError, 'network_error')])
def test_fixed_credential_free_probe(source, error, outcome):
    calls = []

    class Connection:
        def __enter__(self):
            return self

        def __exit__(self, *arguments):
            calls.append('closed')

    def connect(endpoint, timeout):
        calls.append(endpoint)
        assert endpoint == network_probe.ENDPOINTS[source] and timeout == 5
        if error:
            raise error('private network details')
        return Connection()

    times = iter([0.0, 0.125])
    result = network_probe.collect(source, connect, lambda: next(times), lambda: NOW)
    assert result['outcome'] == outcome and result['duration_ms'] == 125
    assert result['source'] == source and result['observed_at'] == NOW.isoformat()
    assert 'private' not in json.dumps(result)
    assert (calls[-1] == 'closed') is (error is None)


def test_exact_admitted_sockets_and_no_legacy_or_arbitrary_probe():
    assert network_probe.ENDPOINTS == {'gateway-ru': ('185.251.89.19', 8443),
        'nl-amsterdam-1': ('185.10.158.212', 443), 'nl-amsterdam-2': ('185.10.158.196', 443)}
    for source in ('gateway-nl', '127.0.0.1', 'unapproved'):
        with pytest.raises(KeyError):
            network_probe.collect(source, connect=lambda *args, **kwargs: pytest.fail('network forbidden'))


def samples(outcomes=('reachable',) * 3, source='nl-amsterdam-1'):
    return [SimpleNamespace(source=source, scope='production', probe='tcp_connect',
        vantage='operator-workstation', address=network_probe.ENDPOINTS[source][0], port=443,
        observed_at=NOW - timedelta(seconds=60 * index), outcome=outcome)
        for index, outcome in enumerate(outcomes)]


@pytest.mark.parametrize('outcomes,service,state', [
    (('reachable',) * 3, 'observed_active', 'observe'),
    (('reachable',) * 3, 'degraded', 'investigate_service'),
    (('timeout', 'refused', 'network_error'), 'observed_active', 'investigate_path'),
    (('timeout',) * 3, 'degraded', 'investigate_node'),
    (('reachable', 'refused', 'refused'), 'observed_active', 'stabilizing'),
    (('reachable', 'reachable', 'refused'), 'observed_active', 'stabilizing'),
    (('refused', 'reachable', 'refused'), 'observed_active', 'stabilizing'),
    (('reachable',), 'observed_active', 'stabilizing'),
    ((), 'observed_active', 'no_data'),
    (('reachable',) * 3, 'stale', 'hold'),
    (('timeout',) * 3, 'unknown', 'hold'),
    (('reachable',) * 3, 'no_data', 'hold'),
])
def test_advisory_hysteresis_never_becomes_vpn_acceptance_or_mutation(outcomes, service, state):
    result = recovery_policy.assess('nl-amsterdam-1', samples(outcomes), service, NOW)
    assert result['state'] == state
    assert result['automatic_action'] is False and result['vpn_readiness'] == 'not_checked'


@pytest.mark.parametrize('field,value', [
    ('source', 'nl-amsterdam-2'), ('scope', 'synthetic'), ('probe', 'awg_handshake'),
    ('vantage', 'another-location'), ('address', '185.10.158.196'), ('port', 22),
    ('observed_at', NOW + timedelta(seconds=1)), ('outcome', 'unknown'),
    ('observed_at', NOW - timedelta(seconds=301)),
])
def test_wrong_or_stale_evidence_cannot_authorize_recovery(field, value):
    rows = samples()
    setattr(rows[0], field, value)
    assert recovery_policy.assess('nl-amsterdam-1', rows, 'observed_active', NOW)['state'] == 'hold'


@pytest.mark.parametrize('ages,state', [((151, 211, 271), 'hold'), ((0, 151, 211), 'hold'),
    ((0, 0, 60), 'hold'), ((60, 0, 120), 'hold'), ((0, 1, 2), 'stabilizing'),
    ((0, 45, 90), 'observe')])
def test_replay_fast_retries_and_monitor_gaps_are_not_stable_health(ages, state):
    rows = samples()
    for row, age in zip(rows, ages):
        row.observed_at = NOW - timedelta(seconds=age)
    assert recovery_policy.assess('nl-amsterdam-1', rows, 'observed_active', NOW)['state'] == state
    assert recovery_policy.assess('gateway-nl', rows, 'observed_active', NOW)['state'] == 'hold'


def test_probe_cycle_is_independent_of_ssh_and_continues_after_import_timeout(tmp_path):
    probed, imported = [], []

    def probe(source):
        probed.append(source)
        return dict(source=source, observed_at=NOW.isoformat(), outcome='timeout')

    def run(command, **options):
        assert command[0] == 'docker' and command[-1] == 'import_network_probe'
        assert options['timeout'] == 20 and options['capture_output'] and options['check']
        source = json.loads(options['input'])['source']
        imported.append(source)
        if source == 'nl-amsterdam-1':
            raise subprocess.TimeoutExpired(command, 20, stderr=b'private details')
        return subprocess.CompletedProcess(command, 0)

    result = probe_network.cycle(tmp_path, probe, run)
    assert probed == imported == list(network_probe.ENDPOINTS)
    assert [row['status'] for row in result['sources']] == ['IMPORTED', 'IMPORT_FAILED', 'IMPORTED']
    assert result['automatic_actions'] == 0 and 'private' not in json.dumps(result)
    assert sorted(path.name for path in (tmp_path / '.local').iterdir()) == ['network-probe.lock']
    assert (tmp_path / '.local/network-probe.lock').stat().st_mode & 0o777 == 0o600


def test_probe_rejects_symlinks_and_concurrent_cycles(tmp_path):
    target = tmp_path / 'target'
    target.mkdir()
    (tmp_path / '.local').symlink_to(target)
    with pytest.raises(ValueError):
        probe_network.cycle(tmp_path)
    (tmp_path / '.local').unlink()

    def probe(source):
        with pytest.raises(BlockingIOError):
            probe_network.cycle(tmp_path)
        return dict(source=source, observed_at=NOW.isoformat(), outcome='reachable')

    probe_network.cycle(tmp_path, probe, lambda *args, **kwargs: None)


def test_unit_timeout_covers_fixed_endpoints_and_imports():
    root = Path(probe_network.__file__).parent
    unit = (root / 'network-probe.service.in').read_text()
    timeout = int(next(line.split('=')[1] for line in unit.splitlines() if line.startswith('TimeoutStartSec=')))
    assert timeout >= len(network_probe.ENDPOINTS) * (network_probe.TIMEOUT_SECONDS + 20) + 10
    timer = (root / 'network-probe.timer.in').read_text()
    assert 'OnUnitInactiveSec=60' in timer and 'family-connect-network-probe.service' in timer
