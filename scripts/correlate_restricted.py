"""Offline, allowlisted join of client exports and restricted gateway JSONL."""

import argparse
import json
from pathlib import Path
import re
import sys


TAG = re.compile(r"[0-9a-f]{64}\Z")
UUID = re.compile(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\Z")
SUPPORT = re.compile(r"FC-[A-Z0-9]{4}-[A-Z0-9]{4}\Z")
STAGES = "AUTHORIZED|ROOM_CREATION|DESCRIPTOR|GATEWAY_JOIN|SIGNALING|WEBSOCKET|ICE|PEER_CONNECTION|CARRIER|CARRIER_ACTIVITY|FAMILY_TLS|GATEWAY_SESSION|HEARTBEAT|LIVENESS|LOCAL_CLOSE|REMOTE_CLOSE|RECOVERY|CLEANUP"
STATES = "STARTED|ESTABLISHED|ISSUED|TX|RX|FAILED|CLOSED|COMPLETED|ATTEMPTED|NOT_ATTEMPTED|new|checking|connecting|connected|completed|disconnected|failed|closed"
REASONS = "NONE|SIGNAL_WS_CLOSE|ICE_DISCONNECTED|ICE_FAILED|PEER_CONNECTION_FAILED|CARRIER_EOF|CARRIER_ERROR|FAMILY_TLS_EOF|FAMILY_TLS_ERROR|GATEWAY_CLOSE|HEARTBEAT_TIMEOUT|REMOTE_CLOSE|RECOVERY_CLEANUP_FAILED|RECOVERY_DESCRIPTOR_FAILED|RECOVERY_JOIN_FAILED|RECOVERY_CARRIER_FAILED|UNKNOWN_INTERNAL"
CLOSE_REASONS = "ping|timeout|duplicate|expired|inactivity|shutdown|restart|invalid|ack|idle|session|READ_ERROR|READ_TIMEOUT|INVALID_MESSAGE|WRITE_ERROR"
BROKER_REASONS = "cancelled|lifetime_expired|authorization_changed|unused_expired|gateway_session_failed|gateway_failed|gateway_ready_timeout|provider_failure|provider_response|provider_cancelled|provider_timeout|provider_transport|provider_request|provider_bad_request|provider_unauthorized|provider_forbidden|provider_rate_limited|provider_unavailable|provider_status|provider_body|provider_json|provider_id|provider_join_url|unknown"
REQUIRED = {"AUTHORIZED/ESTABLISHED", "ROOM_CREATION/ESTABLISHED", "DESCRIPTOR/ISSUED", "GATEWAY_JOIN/ESTABLISHED", "SIGNALING/ESTABLISHED", "WEBSOCKET/ESTABLISHED", "ICE/connected", "PEER_CONNECTION/connected", "CARRIER/STARTED", "CARRIER/ESTABLISHED", "FAMILY_TLS/ESTABLISHED", "GATEWAY_SESSION/ESTABLISHED", "HEARTBEAT/TX", "HEARTBEAT/RX", "CLEANUP/COMPLETED"}


def matches(pattern, value):
    return isinstance(value, str) and pattern.fullmatch(value) is not None


def number(value):
    return type(value) is int and 0 <= value <= 9007199254740991


def event(source):
    if not isinstance(source, dict) or not matches(TAG, source.get("session_tag")):
        raise ValueError("invalid trace correlation")
    safe = {"session_tag": source["session_tag"]}
    for field, choices in (("stage", STAGES), ("state", STATES), ("reason", REASONS)):
        if source.get(field) not in choices.split("|"):
            raise ValueError("invalid trace enum")
        safe[field] = source[field]
    for field in ("sequence", "timestamp_ms"):
        if not number(source.get(field)) or source[field] == 0:
            raise ValueError("invalid trace sequence/time")
        safe[field] = source[field]
    for field in ("tx", "rx"):
        if number(source.get(field)):
            safe[field] = source[field]
    if source.get("target") in ("SUBSCRIBER", "PUBLISHER"):
        safe["target"] = source["target"]
    if number(source.get("close_code")) and 1000 <= source["close_code"] <= 4999:
        safe["close_code"] = source["close_code"]
    if source.get("close_reason") in CLOSE_REASONS.split("|"):
        safe["close_reason"] = source["close_reason"]
    if source.get("broker_reason") in BROKER_REASONS.split("|"):
        safe["broker_reason"] = source["broker_reason"]
    return safe


def insert(events, source, expected=None):
    safe = event(source)
    if expected is not None and safe["session_tag"] != expected:
        raise ValueError("cross-session evidence")
    key = safe["sequence"]
    if key in events and events[key] != safe:
        raise ValueError("conflicting sequence evidence")
    events[key] = safe


def correlate(clients, server, lookup):
    bindings, client_events, server_events, firsts = {}, {}, {}, {}
    recovery = []
    for bundle in clients:
        if not isinstance(bundle, dict):
            raise ValueError("invalid client export")
        for record in (bundle.get("ring", {}), bundle.get("incident", {})):
            if not isinstance(record, dict):
                raise ValueError("invalid client record")
            history = record.get("restricted_history", [])
            if not isinstance(history, list) or len(history) > 4:
                raise ValueError("invalid history bound")
            for session in history + [record.get("restricted_session", {})]:
                if not isinstance(session, dict):
                    raise ValueError("invalid session")
                tag = session.get("session_tag")
                if tag is None:
                    continue
                if not matches(TAG, tag) or session.get("correlation_status") != "VALID":
                    raise ValueError("invalid session tag")
                binding = {"session_tag": tag}
                for field, pattern in (("device_support_id", SUPPORT), ("connection_id", UUID), ("incident_id", UUID)):
                    value = session.get(field)
                    if not matches(pattern, value):
                        raise ValueError("missing or invalid client binding")
                    binding[field] = value
                if bindings.get(tag, binding) != binding:
                    raise ValueError("ambiguous tag binding")
                bindings[tag] = binding
                trace = client_events.setdefault(tag, {})
                lifecycle = session.get("lifecycle", {})
                if not isinstance(lifecycle, dict):
                    raise ValueError("invalid lifecycle")
                entries = lifecycle.get("trace", [])
                if not isinstance(entries, list) or len(entries) > 192:
                    raise ValueError("invalid lifecycle bound")
                for entry in entries:
                    insert(trace, entry, tag)
                first = lifecycle.get("first_failure")
                if first is not None:
                    safe = event(first)
                    if safe["session_tag"] != tag or safe["reason"] == "NONE" or firsts.get(tag, safe) != safe:
                        raise ValueError("ambiguous first failure")
                    firsts[tag] = safe
            entries = record.get("events", [])
            if not isinstance(entries, list) or len(entries) > 128:
                raise ValueError("invalid event bound")
            for entry in entries:
                if not isinstance(entry, dict) or entry.get("event") not in ("restoration_attempted", "restoration_succeeded", "restoration_failed", "cleanup_completed", "cleanup_failed"):
                    continue
                tag = entry.get("session_tag", entry.get("previous_session_tag"))
                if not matches(TAG, tag):
                    continue
                safe = {"session_tag": tag, "event": entry["event"]}
                for field in ("connection_id", "incident_id"):
                    if not matches(UUID, entry.get(field)):
                        raise ValueError("invalid recovery binding")
                    safe[field] = entry[field]
                if number(entry.get("timestamp")):
                    safe["timestamp_ms"] = entry["timestamp"]
                reason = entry.get("reason_code")
                safe["reason"] = reason if reason in REASONS.split("|") else "UNKNOWN_INTERNAL"
                for field, allowed in (("recovery_stage", ("CLEANUP", "RECOVERY")), ("recovery_state", ("STARTED", "ESTABLISHED", "FAILED")), ("restricted_descriptor", ("ATTEMPTED", "NOT_ATTEMPTED"))):
                    if entry.get(field) in allowed:
                        safe[field] = entry[field]
                if safe not in recovery:
                    recovery.append(safe)
    for record in server:
        if not isinstance(record, dict) or record.get("event") != "restricted_trace":
            continue
        safe = event(record.get("trace"))
        insert(server_events.setdefault(safe["session_tag"], {}), safe)
    results = []
    for tag, binding in sorted(bindings.items()):
        related = [entry for entry in recovery if entry["session_tag"] == tag and entry["connection_id"] == binding["connection_id"]]
        if lookup not in binding.values() and not any(lookup == entry["incident_id"] for entry in related):
            continue
        remote = [entry for _, entry in sorted(server_events.get(tag, {}).items())]
        local = [entry for _, entry in sorted(client_events.get(tag, {}).items())]
        gaps = any(entry["sequence"] != index for index, entry in enumerate(remote, start=1))
        stages = {entry["stage"] + "/" + entry["state"] for entry in remote}
        missing = sorted(REQUIRED - stages)
        activity = any(entry["stage"] == "CARRIER_ACTIVITY" and entry.get("tx", 0) > 0 and entry.get("rx", 0) > 0 for entry in remote)
        first_remote = None
        for entry in remote:
            if entry["stage"] == "LOCAL_CLOSE":
                break
            if entry["reason"] != "NONE":
                first_remote = entry
                break
        results.append({**binding, "client": local, "server": remote, "recovery": related,
                        "first_client_failure": firsts.get(tag), "first_server_failure": first_remote,
                        "server_sequence_gaps": gaps, "missing_server_stages": missing,
                        "carrier_bidirectional_activity": activity,
                        "correlation_proven": bool(local and remote) and not gaps,
                        "owner_lifecycle_complete": bool(local and remote and activity) and not gaps and not missing})
    return {"schema": 1, "binding_source": "client_export_not_authorization", "ordering": "per_endpoint_sequence_not_cross_host_causality", "sessions": results}


def read(path, limit):
    with Path(path).open("rb") as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise ValueError("input exceeds bound")
    return raw.decode("utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--client", action="append", required=True)
    parser.add_argument("--server", required=True)
    parser.add_argument("--find", required=True)
    args = parser.parse_args()
    try:
        if len(args.client) > 8:
            raise ValueError("client bound")
        clients = [json.loads(read(path, 1024 * 1024)) for path in args.client]
        lines = read(args.server, 8 * 1024 * 1024).splitlines()
        if len(lines) > 10000:
            raise ValueError("server event bound")
        server, ignored = [], 0
        for line in lines:
            if not line.strip():
                continue
            try:
                server.append(json.loads(line))
            except json.JSONDecodeError:
                ignored += 1
        result = correlate(clients, server, args.find)
        result["ignored_non_json_lines"] = ignored
        print(json.dumps(result, ensure_ascii=True, indent=2))
        return 0 if result["sessions"] else 2
    except (OSError, UnicodeError, ValueError, TypeError, KeyError, RecursionError):
        print("Restricted diagnostic input rejected; check schema, bounds and correlation bindings.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
