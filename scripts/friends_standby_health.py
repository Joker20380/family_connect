"""Strict local observations and preconditions for ordinary-node admission."""

import re


def require(condition):
    if not condition:
        raise ValueError('ordinary admission evidence rejected')


def listener_owners(raw, transport, port, owners, addresses):
    matches = []
    for line in raw.splitlines():
        fields = line.split()
        if len(fields) < 7 or fields[0] != transport:
            continue
        host, observed_port = fields[4].rsplit(':', 1)
        if observed_port != str(port):
            continue
        processes = set(re.findall(r'pid=(\d+)', line))
        require(host in addresses and processes and processes <= set(owners))
        matches.append(host)
    require(matches)
    return sorted(matches)


def require_ready(health, external, registration, *, target, now):
    require(health['result'] == 'LOCAL_ORDINARY_HEALTH_PASS' and health['target'] == target)
    require(type(health['observed_at']) is int and now - 120 <= health['observed_at'] <= now)
    require(all(health[name] == 'PASS' for name in ('native_hashes', 'forwarding_nat', 'awg_address', 'listener_ownership')))
    require(all(value['ActiveState'] == 'active' and value['NRestarts'] == '0'
                and value['UnitFileState'] == 'enabled' for value in health['units'].values()))
    require(set(health['units']) == {'family-connect-friends-awg.service', 'family-connect-friends-tcp.service'})
    require(external['target'] == target and external['exit'] == 0)
    require(external['external']['awg'] == 'HANDSHAKE_DNS_HTTPS_EGRESS_PASS'
            and external['external']['tcp'] == 'AUTH_DNS_HTTPS_EGRESS_PASS'
            and external['external']['operator_cleanup'] == 'PASS')
    require(external['cleanup']['receipt']['result'] == 'TARGET_CLEANUP_PASS')
    require(registration['probe']['result'] == 'PINNED_RU_TO_NEW_NL_REGISTRATION_PASS'
            and registration['cleanup']['result'] == 'REGISTRATION_PROBE_CLEANUP_PASS')
