"""Root-only, journaled ownership of the dedicated MESH network resources."""
import json
import os
from pathlib import Path
import secrets
import stat
import subprocess

import mesh_network as network
import mesh_ipc as ipc

ENV = {"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "HOME": "/root", "LANG": "C"}


def command(*arguments, check=True):
    result = subprocess.run(arguments, capture_output=True, env=ENV, timeout=10)
    if len(result.stdout) > 512 * 1024 or (check and result.returncode):
        raise RuntimeError("MESH system operation failed")
    return result


def private_read(path, expected_owner=0):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != expected_owner or info.st_nlink != 1 or stat.S_IMODE(info.st_mode) != 0o600:
            raise ValueError("Unsafe MESH ownership journal")
        raw = os.read(descriptor, 4097)
        if len(raw) > 4096:
            raise ValueError("Oversized MESH ownership journal")
        return ipc.decode(raw, 4096)
    finally:
        os.close(descriptor)


def private_write(path, value):
    temporary = path.with_name(".mesh-" + secrets.token_hex(16))
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        with os.fdopen(descriptor, "w") as stream:
            json.dump(value, stream, separators=(",", ":"))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_DIRECTORY | os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        temporary.unlink(missing_ok=True)


class Network:
    def __init__(self, journal, uid, retain=None, resuming=False, auto_guard=None):
        self.journal = Path(journal)
        self.uid = uid
        self.owns_journal = False
        self.retain = retain or (lambda: False)
        self.resuming = resuming
        self.auto_guard = auto_guard
        self.record = {"schema": 1, "uid": uid, "generation": secrets.token_hex(16), "guard_count": 0, "packet_index": 0}

    def query(self, *arguments):
        return json.loads(command("ip", "-j", *arguments).stdout)

    def save(self):
        private_write(self.journal, self.record)
        self.owns_journal = True

    def restore(self):
        value = private_read(self.journal)
        if not isinstance(value, dict) or set(value) != set(self.record) or value["schema"] != 1 or value["uid"] != self.uid:
            raise ValueError("MESH journal owner mismatch")
        if type(value["guard_count"]) is not int or not 0 <= value["guard_count"] <= len(network.guard_commands("add")):
            raise ValueError("Invalid MESH journal")
        if type(value["packet_index"]) is not int or not 0 <= value["packet_index"] <= 2**31 - 1:
            raise ValueError("Invalid MESH journal")
        if not isinstance(value["generation"], str) or len(value["generation"]) != 32 or any(part not in "0123456789abcdef" for part in value["generation"]):
            raise ValueError("Invalid MESH journal")
        self.record = value
        self.owns_journal = True

    def prepare(self):
        from backend import privileged_transport_start
        with privileged_transport_start('mesh', auto_guard=self.auto_guard):
            self._prepare()

    def _prepare(self):
        if self.journal.exists():
            if not self.resuming:
                raise ValueError("MESH cleanup is pending")
            self.restore()
            self.detach()
            self.reconcile_guard()
            return
        links = self.query("-d", "link", "show")
        routes = self.query("-4", "route", "show", "table", "all") + self.query("-6", "route", "show", "table", "all")
        network.available(self.query("-4", "rule", "show"), self.query("-6", "rule", "show"), routes, links)
        self.save()
        for index, arguments in enumerate(network.guard_commands("add"), 1):
            self.record["guard_count"] = index
            self.save()
            command(*arguments)
        self.verify_guard()

    def reconcile_guard(self):
        rules4 = self.query('-4', 'rule', 'show')
        rules6 = self.query('-6', 'rule', 'show')
        routes = self.query('-4', 'route', 'show', 'table', 'all') + self.query('-6', 'route', 'show', 'table', 'all')
        links = self.query('-d', 'link', 'show')
        network.available([rule for rule in rules4 if rule.get('priority') not in network.PRIORITIES],
                          [rule for rule in rules6 if rule.get('priority') not in network.PRIORITIES],
                          [route for route in routes if str(route.get('table')) != str(network.TABLE)],
                          [link for link in links if link.get('ifname') != network.INTERFACE])
        missing = network.missing_guard(rules4, rules6,
            self.query('-4', 'route', 'show', 'table', str(network.TABLE)),
            self.query('-6', 'route', 'show', 'table', str(network.TABLE)), self.record['guard_count'])
        commands = network.guard_commands('add')
        for index in missing:
            self.record['guard_count'] = max(self.record['guard_count'], index + 1)
            self.save()
            command(*commands[index])
        self.verify_guard()

    def verify_guard(self):
        network.verify_guard(self.query("-4", "rule", "show"), self.query("-6", "rule", "show"),
                             self.query("-4", "route", "show", "table", str(network.TABLE)),
                             self.query("-6", "route", "show", "table", str(network.TABLE)))

    def underlying(self):
        route = self.query("-4", "route", "get", "1.1.1.1", "mark", str(network.MARK))
        return network.underlying_index(route, self.query("-d", "link", "show"))

    def attach(self):
        links = self.query("link", "show", "dev", network.INTERFACE)
        if len(links) != 1 or type(links[0].get("ifindex")) is not int:
            raise ValueError("MESH interface missing")
        self.record["packet_index"] = links[0]["ifindex"]
        self.save()
        for arguments in network.packet_commands():
            command(*arguments)
        self.verify_guard()
        network.verify_packet(self.query("address", "show", "dev", network.INTERFACE),
                              self.query("-4", "route", "show", "table", str(network.TABLE)))
        dns = command("resolvectl", "dns", network.INTERFACE).stdout.decode().split(":", 1)[-1].split()
        domains = command("resolvectl", "domain", network.INTERFACE).stdout.decode().split(":", 1)[-1].split()
        default = command("resolvectl", "default-route", network.INTERFACE).stdout.decode().split(":", 1)[-1].strip()
        if dns != ["1.1.1.1", "9.9.9.9"] or domains != ["~."] or default != "yes":
            raise ValueError("MESH DNS readback mismatch")

    def detach(self):
        index = self.record["packet_index"]
        if not index:
            return
        links = self.query("link", "show")
        owned = [link for link in links if link.get("ifname") == network.INTERFACE]
        if owned and owned[0].get("ifindex") != index:
            raise ValueError("MESH interface ownership changed")
        if owned:
            for arguments in network.packet_cleanup():
                command(*arguments, check=False)
            routes = self.query("-4", "route", "show", "table", str(network.TABLE))
            if any(route.get("dev") == network.INTERFACE for route in routes):
                raise RuntimeError("MESH packet cleanup incomplete")
            addresses = self.query("address", "show", "dev", network.INTERFACE)
            if any(address.get("local") == "10.79.1.2" for link in addresses for address in link.get("addr_info", [])):
                raise RuntimeError("MESH address cleanup incomplete")
            for mode in ("dns", "domain"):
                result = command("resolvectl", mode, network.INTERFACE).stdout.decode()
                if result.split(":", 1)[-1].strip():
                    raise RuntimeError("MESH DNS cleanup incomplete")
        self.record["packet_index"] = 0
        self.save()

    def cleanup(self):
        if not self.owns_journal or not self.journal.exists():
            return
        self.detach()
        if self.retain():
            self.reconcile_guard()
            return
        added = network.guard_commands("add")[:self.record["guard_count"]]
        for arguments in reversed(added):
            command(*(tuple("del" if part == "add" else part for part in arguments)), check=False)
        for family in ("-4", "-6"):
            rules = self.query(family, "rule", "show")
            routes = self.query(family, "route", "show", "table", "all")
            if any(rule.get("priority") in network.PRIORITIES for rule in rules) or any(str(route.get("table")) == str(network.TABLE) for route in routes):
                raise RuntimeError("MESH cleanup incomplete; guard retained")
        self.journal.unlink()
        self.owns_journal = False
