"""Per-role acceptance contract. Synthetic observations are never live VPN proof."""

import time

from .contracts import ROLES, exact, fail

HOST = ('time_sync', 'disk', 'inodes', 'memory', 'swap', 'no_oom', 'critical_units', 'listeners')
CHECKS = {
    'awg': ('interface', 'peer_inventory', 'forwarding', 'nat', 'handshake_hook', 'dns_https_hook'),
    'tcp': ('listener', 'auth_hook', 'https_hook'),
    'mesh': ('profile', 'certificate', 'crl_floor', 'directory', 'listener', 'snapshot', 'fleet_mesh_probe_1_hook'),
    'profile-reader': ('freshness', 'signature'), 'publisher': ('state', 'freshness'),
    'renewal': ('state', 'expiry'), 'snapshot': ('freshness', 'digest'),
    'restricted-sync': ('state', 'freshness'), 'mailbox': ('listener', 'health_hook'),
    'load-monitor': ('freshness',), 'monitoring': ('freshness', 'restart_count', 'material_expiry'),
}


def required(roles):
    if not roles or not set(roles) <= set(ROLES):
        fail('health_roles')
    return sorted(['host.' + check for check in HOST] + [role + '.' + check for role in roles for check in CHECKS[role]])


def accept(report, instance, bundle, roles, now=None):
    exact(report, ('schema', 'scope', 'instance_id', 'bundle_id', 'observed_at', 'checks'))
    now = time.time() if now is None else now
    if (type(report['schema']) is not int or report['schema'] != 1 or report['scope'] != 'synthetic'
            or report['instance_id'] != instance or report['bundle_id'] != bundle
            or type(report['observed_at']) is not int or not 0 <= now-report['observed_at'] <= 600
            or type(report['checks']) is not dict or set(report['checks']) != set(required(roles))
            or any(value is not True for value in report['checks'].values())):
        fail('health_acceptance_required')
    return report


def run_hooks(instance, bundle, roles, hooks, now=None):
    names = required(roles)
    if set(hooks) != set(names):
        fail('health_hooks_missing')
    checks = {}
    for name in names:
        try:
            checks[name] = hooks[name]() is True
        except Exception:
            checks[name] = False
    return dict(schema=1, scope='synthetic', instance_id=instance, bundle_id=bundle,
                observed_at=int(time.time() if now is None else now), checks=checks)
