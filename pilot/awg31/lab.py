#!/usr/bin/env python3
"""Root-only, isolated network-namespace AWG experiment; no host route changes.

Run: pkexec unshare --net /usr/bin/python3 lab.py --engine PATH --awg PATH --wg PATH
Only synthetic ephemeral keys; stdout contains metrics, never configurations.
"""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import select
import socket
import subprocess
import tempfile
import time


def run(argv, *, ns=None, data=None, check=True):
    command = (["ip", "netns", "exec", ns] if ns else []) + list(map(str, argv))
    result = subprocess.run(command, input=data, capture_output=True)
    if check and result.returncode:
        # Tools can quote rejected configuration values. Do not expose stderr.
        raise RuntimeError(f"command {Path(str(argv[0])).name} failed ({result.returncode})")
    return result


def link_bytes():
    row = json.loads(run(["ip", "-s", "-j", "link", "show", "fc31c"]).stdout)[0]
    stats = row.get("stats64", row.get("stats"))
    return stats["rx"]["bytes"] + stats["tx"]["bytes"]


def usage(processes):
    ticks = rss = 0
    for process in processes:
        fields = Path(f"/proc/{process.pid}/stat").read_text().split(")", 1)[1].split()
        ticks += int(fields[11]) + int(fields[12])
        rss += int(fields[21]) * os.sysconf("SC_PAGE_SIZE")
    return ticks / os.sysconf("SC_CLK_TCK"), rss


def stop(process):
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=3)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("engine", "awg", "wg"):
        parser.add_argument("--" + name, required=True, type=Path)
    parser.add_argument("--repetitions", type=int, default=3, choices=range(1, 6))
    parser.add_argument("--resilience", action="store_true")
    args = parser.parse_args()
    payload_size = 1024 * 1024 if args.resilience else 8 * 1024 * 1024
    if os.geteuid() != 0 or os.readlink("/proc/self/ns/net") == os.readlink("/proc/1/ns/net"):
        raise SystemExit("Run as root inside unshare --net; refusing the host namespace")
    # Also reject an existing network setup inside a supplied namespace.
    links = json.loads(run(["ip", "-j", "link"]).stdout)
    if {row["ifname"] for row in links} != {"lo"}:
        raise SystemExit("Requires a fresh namespace containing only lo")
    for path in (args.engine, args.awg, args.wg):
        if not path.is_file():
            raise SystemExit("Missing experimental binary")
    args.engine, args.awg, args.wg = (p.resolve() for p in (args.engine, args.awg, args.wg))
    namespace = f"fc31lab-{os.getpid()}"
    client, server = f"ac{os.getpid()}", f"as{os.getpid()}"
    records = []
    print(json.dumps({"event": "start", "shaping_each_direction": "35ms,20mbit,no injected loss",
                      "mtu": 1280, "payload_bytes": payload_size, "resilience": args.resilience,
                      "gomaxprocs_per_engine": 1,
                      "binaries": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                   for p in (args.engine, args.awg, args.wg)}}), flush=True)
    run(["ip", "netns", "add", namespace])
    try:
        run(["ip", "link", "set", "lo", "up"])
        run(["ip", "link", "set", "lo", "up"], ns=namespace)
        run(["ip", "link", "add", "fc31c", "type", "veth", "peer", "name", "fc31s"])
        run(["ip", "link", "set", "fc31s", "netns", namespace])
        for ns, link, ip in ((None, "fc31c", "198.18.0.1/30"), (namespace, "fc31s", "198.18.0.2/30")):
            run(["ip", "addr", "add", ip, "dev", link], ns=ns)
            run(["ip", "link", "set", link, "up"], ns=ns)
            run(["ethtool", "-K", link, "tso", "off", "gso", "off", "gro", "off"], ns=ns)
            run(["tc", "qdisc", "add", "dev", link, "root", "netem", "delay", "35ms", "rate", "20mbit"], ns=ns)
        with tempfile.TemporaryDirectory(prefix="fc31-private-") as directory:
            private_dir = Path(directory)
            os.chmod(private_dir, 0o700)
            # Rotate ordering to reduce systematic warm-up/order bias.
            cases = ["wireguard", "awg31_base", "awg31_padding", "awg31_trailers"]
            if args.resilience:
                cases = ["awg31_base"]
            for repetition in range(args.repetitions):
                order = cases[repetition % len(cases):] + cases[:repetition % len(cases)]
                for case in order:
                    processes = []
                    tcp = None
                    log = (private_dir / "engine.log").open("wb")
                    try:
                        tool = args.wg if case == "wireguard" else args.awg
                        keys = [run([tool, "genkey"]).stdout.strip() for _ in range(2)]
                        pubs = [run([tool, "pubkey"], data=key+b"\n").stdout.strip().decode() for key in keys]
                        header_key = base64.b64encode(os.urandom(32)).decode()
                        for i, (ns, interface, local_ip, peer_ip, endpoint) in enumerate((
                            (None, client, "10.90.0.2", "10.90.0.1", "198.18.0.2"),
                            (namespace, server, "10.90.0.1", "10.90.0.2", "198.18.0.1"),
                        )):
                            if case == "wireguard":
                                run(["ip", "link", "add", interface, "type", "wireguard"], ns=ns)
                            else:
                                ipc = Path("/var/run/amneziawg") / (interface + ".sock")
                                if ipc.exists():
                                    raise RuntimeError("Refusing existing IPC socket")
                                command = (["ip", "netns", "exec", ns] if ns else []) + [str(args.engine), "-f", interface]
                                processes.append(subprocess.Popen(command, stdout=log, stderr=log,
                                    env={**os.environ, "LOG_LEVEL": "error", "GOMAXPROCS": "1"}))
                                deadline = time.monotonic() + 5
                                while not ipc.exists():
                                    if processes[-1].poll() is not None or time.monotonic() > deadline:
                                        raise RuntimeError("Engine IPC startup failed")
                                    time.sleep(0.02)
                            extra = ""
                            if case != "wireguard":
                                extra = "S1 = 16\nS2 = 16\nS3 = 16\nS4 = 16\nH1 = 1\nH2 = 2\nH3 = 3\nH4 = 4\nHeaderProtectionKey = " + header_key + "\n"
                                if case == "awg31_padding":
                                    extra += "ContentPaddingAddition = 0-32\n"
                                elif case == "awg31_trailers":
                                    extra += "RandomTrailers = on\n"
                            config = private_dir / (interface + ".conf")
                            config.write_text("[Interface]\nPrivateKey = " + keys[i].decode() + "\nListenPort = 51820\n" + extra +
                                "[Peer]\nPublicKey = " + pubs[i ^ 1] + "\nAllowedIPs = " + peer_ip + "/32\nEndpoint = " + endpoint + ":51820\n")
                            os.chmod(config, 0o600)
                            run([tool, "setconf", interface, config], ns=ns)
                            run(["ip", "addr", "add", local_ip + "/24", "dev", interface], ns=ns)
                            run(["ip", "link", "set", interface, "mtu", "1280", "up"], ns=ns)
                        if args.resilience:
                            from resilience import preflight
                            preflight(run, tool, namespace, client, server, private_dir)
                        started = time.monotonic()
                        run(["ping", "-n", "-c", "1", "-W", "3", "10.90.0.1"])
                        readiness = time.monotonic() - started
                        ping = run(["ping", "-n", "-c", "10", "-i", "0.1", "-W", "2", "10.90.0.1"]).stdout.decode()
                        loss = float(re.search(r"([\d.]+)% packet loss", ping)[1])
                        avg = float(re.search(r"= [\d.]+/([\d.]+)/", ping)[1])
                        code = "import socket; s=socket.socket(); s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1); s.bind(('10.90.0.1',9090)); s.listen(1); print('ready',flush=True); c,_=s.accept(); c.settimeout(90); c.sendall(bytes(PAYLOAD_BYTES)); c.close(); s.close()"
                        code = code.replace("PAYLOAD_BYTES", str(payload_size))
                        tcp = subprocess.Popen(["ip", "netns", "exec", namespace, "/usr/bin/python3", "-c", code], stdout=subprocess.PIPE, stderr=log)
                        if not select.select([tcp.stdout], [], [], 5)[0] or tcp.stdout.readline() != b"ready\n":
                            raise RuntimeError("Synthetic TCP server did not become ready")
                        before_bytes = link_bytes()
                        before_cpu, _ = usage(processes)
                        started = time.monotonic()
                        received = 0
                        with socket.create_connection(("10.90.0.1", 9090), timeout=20) as connection:
                            while data := connection.recv(131072):
                                if any(data):
                                    raise RuntimeError("Synthetic payload integrity mismatch")
                                received += len(data)
                                if time.monotonic() - started > 90:
                                    raise RuntimeError("Transfer exceeded 90s budget")
                        duration = time.monotonic() - started
                        after_cpu, rss = usage(processes)
                        transferred = link_bytes() - before_bytes
                        if received != payload_size or tcp.wait(timeout=3) != 0:
                            raise RuntimeError("Incomplete synthetic transfer")
                        run(["ping", "-n", "-c", "1", "-W", "3", "10.90.0.1"])
                        record = {"case": case, "repetition": repetition+1, "first_ping_s": round(readiness, 4),
                            "ping_loss_percent": loss, "ping_avg_ms": avg, "payload_bytes": received,
                            "tcp_seconds": round(duration, 4), "tcp_mbit_s": round(received * 8 / duration / 1e6, 3),
                            "underlay_link_bytes": transferred, "link_bytes_per_payload_byte": round(transferred / received, 4),
                            "two_engines_cpu_s": round(after_cpu-before_cpu, 4) if processes else None,
                            "two_engines_rss_bytes": rss if processes else None}
                        if args.resilience:
                            from resilience import postflight
                            postflight(run, namespace, client, server, tool, args.engine, processes, private_dir, log, stop)
                        records.append(record)
                        print(json.dumps(record), flush=True)
                    finally:
                        if tcp is not None:
                            stop(tcp)
                        for process in reversed(processes):
                            stop(process)
                        for ns, interface in ((None, client), (namespace, server)):
                            run(["ip", "link", "del", interface], ns=ns, check=False)
                        log.close()
    finally:
        run(["ip", "netns", "del", namespace])
    print(json.dumps({"event": "complete", "runs": len(records), "server_namespace_removed": True}), flush=True)


if __name__ == "__main__":
    main()
