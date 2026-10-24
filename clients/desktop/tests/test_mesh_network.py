import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location("mesh_network", Path(__file__).resolve().parents[2] / "linux/mesh_network.py")
network = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(network)


def snapshots():
    rules4 = [{"priority": 10637, "fwmark": "0xfc80", "table": "main"},
              {"priority": 10638, "fwmark": "0xfc80", "action": "prohibit"},
              {"priority": 10640, "table": 64640}]
    rules6 = [{"priority": 10640, "table": 64640}]
    blocked = [{"dst": "default", "type": "unreachable", "metric": 32760}]
    return rules4, rules6, blocked, list(blocked)


def test_network_guard_is_exact_and_reversible():
    installed = network.guard_commands("add")
    removed = network.guard_commands("del")
    assert len(installed) == 6
    assert [tuple("add" if field == "del" else field for field in command) for command in reversed(removed)] == installed
    assert all("flush" not in command and "iptables" not in command for command in installed + removed)
    assert all("to" not in command and "suppress_prefixlength" not in command for command in installed)
    assert all("-6" not in command for command in network.packet_commands())
    assert not any("replace" in command for command in network.packet_commands())
    assert ("resolvectl", "revert", "fcmesh0") in network.packet_cleanup()


def test_crash_and_recovery_keep_unreachable_fallback():
    snapshots4, snapshots6, routes4, routes6 = snapshots()
    network.verify_guard(snapshots4, snapshots6, routes4, routes6)
    routes4.append({"dst": "default", "dev": "fcmesh0", "metric": 10})
    network.verify_guard(snapshots4, snapshots6, routes4, routes6)
    with pytest.raises(ValueError):
        network.verify_guard(snapshots4, snapshots6, routes4[1:], routes6)


def test_no_other_vpn_or_reserved_resources_are_adopted():
    network.available([{"priority": 0}, {"priority": 32766}], [{"priority": 0}], [], [])
    for rules, routes, links in [([{"priority": 100, "table": 51820}], [], []),
                                ([{"priority": 10637}], [], []),
                                ([], [{"table": 64640}], []), ([], [], [{"ifname": "fcmesh0"}])]:
        with pytest.raises(ValueError):
            network.available(rules, [], routes, links)


def test_underlying_selection_does_not_follow_a_vpn():
    route = [{"dev": "eth0", "type": "unicast"}]
    links = [{"ifindex": 2, "ifname": "eth0", "flags": ["UP"]}]
    assert network.underlying_index(route, links) == 2
    links[0]["linkinfo"] = {"info_kind": "wireguard"}
    with pytest.raises(ValueError):
        network.underlying_index(route, links)


def test_packet_readiness_requires_route_address_and_mtu():
    links = [{"ifname": "fcmesh0", "mtu": 1280, "flags": ["UP"], "addr_info": [{"local": "10.79.1.2", "prefixlen": 32}]}]
    routes = [{"dst": "default", "dev": "fcmesh0", "metric": 10}]
    network.verify_packet(links, routes)
    for broken in ([], [{"dst": "default", "dev": "eth0", "metric": 10}]):
        with pytest.raises(ValueError):
            network.verify_packet(links, broken)


@pytest.mark.parametrize("change", [{"fwmask": "0xff"}, {"src": "192.0.2.0/24"}, {"dst": "192.0.2.0/24"},
                                    {"iif": "eth0"}, {"uidrange": "0-1000"}, {"goto": 32766}, {"not": True}])
def test_guard_readback_rejects_leaking_selectors(change):
    rules4, rules6, routes4, routes6 = snapshots()
    rules4[0].update(change)
    with pytest.raises(ValueError):
        network.verify_guard(rules4, rules6, routes4, routes6)


def test_guard_rejects_extra_route_bypass():
    rules4, rules6, routes4, routes6 = snapshots()
    routes4.append({"dst": "192.0.2.0/24", "dev": "eth0"})
    with pytest.raises(ValueError):
        network.verify_guard(rules4, rules6, routes4, routes6)


@pytest.mark.parametrize('owned', range(7))
def test_partial_guard_recovery_adds_only_missing_owned_prefix(owned):
    rules4, rules6, routes4, routes6 = snapshots()
    present4 = rules4[:max(0, min(3, owned - 2))]
    present6 = rules6 if owned == 6 else []
    actual4 = routes4 if owned >= 1 else []
    actual6 = routes6 if owned >= 2 else []
    assert network.missing_guard(present4, present6, actual4, actual6, owned) == list(range(owned, 6))
    if owned:
        with pytest.raises(ValueError, match='Unowned'):
            network.missing_guard(present4, present6, actual4, actual6, owned - 1)


def test_partial_guard_recovery_rejects_wrong_routes_and_marks():
    rules4, rules6, routes4, routes6 = snapshots()
    rules4[0]['fwmark'] = 1234
    with pytest.raises(ValueError):
        network.missing_guard(rules4, rules6, routes4, routes6, 6)
    with pytest.raises(ValueError):
        network.missing_guard([], [], [{'dst': 'default', 'dev': 'eth0'}], [], 1)
