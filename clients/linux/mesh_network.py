"""Exact, private MESH routing operations; the installed helper owns execution."""
import ipaddress

INTERFACE = "fcmesh0"
MARK = 64640
TABLE = 64640
PRIORITIES = (10637, 10638, 10640)
BLOCK_METRIC = 32760
TUN_METRIC = 10
ADDRESS = "10.79.1.2/32"
MTU = 1280


def guard_routes():
    return [(family, ("unreachable", "default", "metric", str(BLOCK_METRIC), "table", str(TABLE)))
            for family in ("-4", "-6")]


def guard_rules():
    return [
        ("-4", ("priority", "10637", "fwmark", str(MARK), "lookup", "main")),
        ("-4", ("priority", "10638", "fwmark", str(MARK), "prohibit")),
        ("-4", ("priority", "10640", "lookup", str(TABLE))),
        ("-6", ("priority", "10640", "lookup", str(TABLE))),
    ]


def guard_commands(action):
    if action not in ("add", "del"):
        raise ValueError("invalid guard operation")
    commands = [("ip", family, "route", action, *route) for family, route in guard_routes()]
    commands += [("ip", family, "rule", action, *rule) for family, rule in guard_rules()]
    return commands if action == "add" else list(reversed(commands))


def packet_commands():
    return [
        ("ip", "address", "add", ADDRESS, "dev", INTERFACE),
        ("ip", "link", "set", "dev", INTERFACE, "mtu", str(MTU), "up"),
        ("ip", "-4", "route", "add", "default", "dev", INTERFACE, "metric", str(TUN_METRIC), "table", str(TABLE)),
        ("resolvectl", "dns", INTERFACE, "1.1.1.1", "9.9.9.9"),
        ("resolvectl", "domain", INTERFACE, "~."),
        ("resolvectl", "default-route", INTERFACE, "yes"),
    ]


def packet_cleanup():
    return [
        ("resolvectl", "revert", INTERFACE),
        ("ip", "-4", "route", "del", "default", "dev", INTERFACE, "metric", str(TUN_METRIC), "table", str(TABLE)),
        ("ip", "address", "del", ADDRESS, "dev", INTERFACE),
    ]


def available(rules4, rules6, routes, interfaces):
    if any(link.get("ifname") == INTERFACE for link in interfaces):
        raise ValueError("MESH interface already exists")
    if any("UP" in link.get("flags", []) and link.get("linkinfo", {}).get("info_kind") in ("wireguard", "tun", "gre", "ipip", "vti", "vti6") for link in interfaces):
        raise ValueError("Another VPN interface is active")
    for rule in rules4 + rules6:
        if rule.get("priority") in PRIORITIES or str(rule.get("table")) == str(TABLE):
            raise ValueError("MESH routing namespace occupied")
        if rule.get("priority") not in (0, 32766, 32767):
            raise ValueError("Existing policy routing must be resolved before MESH")
    if any(str(route.get("table")) == str(TABLE) for route in routes):
        raise ValueError("MESH route table occupied")


def underlying_index(route, interfaces):
    if not isinstance(route, list) or len(route) != 1:
        raise ValueError("Underlying route unavailable")
    device = route[0].get("dev")
    if route[0].get("type", "unicast") != "unicast" or device in (None, "lo", INTERFACE):
        raise ValueError("Underlying route unavailable")
    for link in interfaces:
        if link.get("ifname") == device:
            kind = link.get("linkinfo", {}).get("info_kind")
            if kind in ("wireguard", "tun", "gre", "gretap", "ipip", "sit", "vti", "vti6") or "UP" not in link.get("flags", []):
                raise ValueError("Underlying interface is not an available physical route")
            index = link.get("ifindex")
            if type(index) is not int or index <= 0:
                break
            return index
    raise ValueError("Underlying interface unavailable")


def verify_guard(rules4, rules6, routes4, routes6):
    def number(value):
        try:
            return int(str(value), 0)
        except (ValueError, TypeError):
            return -1

    for family, rules in ((4, rules4), (6, rules6)):
        selected = [rule for rule in rules if rule.get("priority") in PRIORITIES]
        expected = 3 if family == 4 else 1
        if len(selected) != expected:
            raise ValueError("MESH rule readback mismatch")
        for rule in selected:
            if set(rule) - {"priority", "src", "dst", "table", "fwmark", "fwmask", "action", "type", "protocol"}:
                raise ValueError("MESH rule contains unexpected selectors")
            if rule.get("src", "all") not in ("all", "0.0.0.0/0", "::/0") or rule.get("dst", "all") not in ("all", "0.0.0.0/0", "::/0"):
                raise ValueError("MESH rule does not cover the full address space")
            if "fwmask" in rule and number(rule["fwmask"]) != 0xffffffff:
                raise ValueError("MESH service mark is not exact")
        by_priority = {rule["priority"]: rule for rule in selected}
        capture = by_priority.get(10640, {})
        if number(capture.get("table")) != TABLE or "fwmark" in capture or "fwmask" in capture:
            raise ValueError("MESH capture rule mismatch")
        if family == 4:
            bypass = by_priority.get(10637, {})
            block = by_priority.get(10638, {})
            if number(bypass.get("fwmark")) != MARK or bypass.get("table") not in ("main", 254) or bypass.get("not"):
                raise ValueError("MESH service routing mismatch")
            if number(block.get("fwmark")) != MARK or block.get("action", block.get("type")) != "prohibit" or "table" in block:
                raise ValueError("MESH service routing fallback is not blocked")
    for routes in (routes4, routes6):
        if any(route.get("type") != "unreachable" and not (route.get("dev") == INTERFACE and route.get("dst") == "default" and route.get("metric") == TUN_METRIC) for route in routes):
            raise ValueError("MESH table contains an unowned bypass route")
        blocks = [route for route in routes if route.get("dst") == "default" and route.get("type") == "unreachable" and route.get("metric") == BLOCK_METRIC]
        if len(blocks) != 1:
            raise ValueError("MESH crash containment route missing")


def verify_packet(links, routes):
    owned = [link for link in links if link.get("ifname") == INTERFACE]
    if len(owned) != 1 or owned[0].get("mtu") != MTU or "UP" not in owned[0].get("flags", []):
        raise ValueError("MESH packet interface not ready")
    addresses = owned[0].get("addr_info", [])
    expected = str(ipaddress.ip_interface(ADDRESS).ip)
    if not any(address.get("local") == expected and address.get("prefixlen") == 32 for address in addresses):
        raise ValueError("MESH packet address not ready")
    if not any(route.get("dst") == "default" and route.get("dev") == INTERFACE and route.get("metric") == TUN_METRIC for route in routes):
        raise ValueError("MESH packet route not ready")


def missing_guard(rules4, rules6, routes4, routes6, owned_count):
    if type(owned_count) is not int or not 0 <= owned_count <= 6:
        raise ValueError('Invalid MESH guard ownership')
    expected4 = [{'priority': 10637, 'fwmark': MARK, 'table': 'main'},
                 {'priority': 10638, 'fwmark': MARK, 'action': 'prohibit'},
                 {'priority': 10640, 'table': TABLE}]
    expected6 = [{'priority': 10640, 'table': TABLE}]
    block = {'type': 'unreachable', 'dst': 'default', 'metric': BLOCK_METRIC}
    present = [bool(routes4), bool(routes6)]
    if len(routes4) > 1 or len(routes6) > 1:
        raise ValueError('MESH recovery table is not empty or blocked')
    complete = []
    for actual, expected in ((rules4, expected4), (rules6, expected6)):
        filled = list(actual)
        for rule in expected:
            found = any(item.get('priority') == rule['priority'] for item in actual)
            present.append(found)
            if not found:
                filled.append(rule)
        complete.append(filled)
    if any(present[index] for index in range(owned_count, 6)):
        raise ValueError('Unowned MESH recovery resources')
    verify_guard(*complete, routes4 or [block], routes6 or [block])
    return [index for index, exists in enumerate(present) if not exists]
