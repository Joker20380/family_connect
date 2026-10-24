#!/usr/bin/python3 -I
"""Explicitly authorized, single-owner system service for the MESH packet path."""
import fcntl
import json
import os
from pathlib import Path
import signal
import socket
import stat
import sys
import threading
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
if __name__ == '__main__':
    from system_runtime import configure, shared_gate
    RUNTIME_GATE = shared_gate()
    configure()
import mesh_ipc as ipc
from mesh_service import Supervisor
from mesh_ownership import Ownership
from mesh_materials import CacheStore, MaterialOwner
from mesh_intent import Intent, Notifier
from mesh_system import Network, command
from mesh_chat_host import Host as ChatHost, remove_endpoint as remove_chat_endpoint

RUN = Path("/run/family-connect-mesh")


def owner(value):
    if not value.isascii() or not value.isdecimal() or str(int(value)) != value or not 1 <= int(value) < 2**31:
        raise ValueError("Invalid MESH owner")
    return int(value)


def directory():
    try:
        RUN.mkdir(mode=0o711)
        RUN.chmod(0o711)
    except FileExistsError:
        pass
    info = RUN.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != 0 or stat.S_IMODE(info.st_mode) != 0o711:
        raise ValueError("Unsafe MESH runtime directory")


def locked(name):
    descriptor = os.open(name, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    info = os.fstat(descriptor)
    if not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or info.st_nlink != 1 or stat.S_IMODE(info.st_mode) != 0o600:
        os.close(descriptor)
        raise ValueError("Unsafe MESH runtime lock")
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return descriptor
    except Exception:
        os.close(descriptor)
        raise


def serve(uid):
    directory()
    if (RUN / 'active.json').exists():
        Network(RUN / 'active.json', uid).restore()
    notifier = Notifier('family-connect-mesh@' + str(uid) + '.service')
    intent = Intent(RUN / (str(uid) + '.intent.json'), uid, notifier)
    recovered = intent.recover()
    descriptor = locked("/run/family-connect-mesh-runtime.lock")
    endpoint = RUN / (str(uid) + ".sock")
    storage = CacheStore("/var/lib/family-connect-mesh", uid)
    receipts = CacheStore("/var/lib/family-connect-mesh", uid, receipt=True)
    supervisor = Supervisor(Network(RUN / "active.json", uid, retain=intent.desired, resuming=recovered is not None), MaterialOwner(storage, receipts), Ownership('vpn'))
    stopping = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: stopping.set())
    signal.signal(signal.SIGINT, lambda *_: stopping.set())
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    chat = ChatHost(RUN / (str(uid) + '.chat.sock'), uid, supervisor.chat_binding)
    bound = False
    try:
        if endpoint.exists():
            raise ValueError("MESH stale socket requires cleanup")
        listener.bind(str(endpoint))
        bound = True
        os.chmod(endpoint, 0o600)
        os.chown(endpoint, uid, 0)
        listener.listen(4)
        listener.settimeout(1)
        chat.start()
        if recovered is not None:
            supervisor.start(recovered, restoring=True)
        elif intent.desired():
            supervisor.intent = True
            supervisor.transition('FAILED', 'RECOVERY_CREDENTIAL_UNAVAILABLE')
        notifier.ready()
        idle_deadline = time.monotonic() + 300
        while not stopping.is_set():
            if supervisor.thread is None and time.monotonic() >= idle_deadline:
                break
            try:
                connection, _ = listener.accept()
            except TimeoutError:
                continue
            with connection:
                try:
                    if ipc.peer_uid(connection) != uid:
                        continue
                    deadline = time.monotonic() + 4
                    request = ipc.validate_request(ipc.receive(connection.fileno(), ipc.MAX_REQUEST, deadline))
                    accepted = dispatch(supervisor, intent, request, stopping)
                    reply = dict(supervisor.status(), schema=1, id=request["id"], ok=accepted)
                    ipc.send(connection.fileno(), reply, ipc.MAX_REPLY, time.monotonic() + 4)
                    request.clear()
                except (OSError, EOFError, ValueError, TimeoutError):
                    pass
    finally:
        listener.close()
        try:
            if not supervisor.stop():
                raise RuntimeError("MESH owner cleanup is still pending")
        finally:
            chat.close()
        storage.close()
        receipts.close()
        intent.close()
        if bound:
            endpoint.unlink(missing_ok=True)
        os.close(descriptor)


def dispatch(supervisor, intent, request, stopping):
    action = request['action']
    if action == 'start':
        if stopping.is_set() or supervisor.state != 'DISCONNECTED' or supervisor.thread is not None:
            return False
        intent.begin(request['materials'])
        if stopping.is_set():
            intent.revoke()
            return False
        accepted = supervisor.start(request['materials'])
        if not accepted:
            intent.revoke()
        return accepted
    if action == 'stop':
        try:
            intent.revoke()
        finally:
            supervisor.cancel.set()
            stopping.set()
        return supervisor.stop()
    if action != 'status':
        raise ValueError('Invalid MESH service operation')
    return True


def cleanup(uid):
    directory()
    descriptor = locked("/run/family-connect-mesh-runtime.lock")
    try:
        intent = Intent(RUN / (str(uid) + '.intent.json'), uid)
        network = Network(RUN / "active.json", uid, retain=intent.desired)
        if network.journal.exists():
            network.restore()
            network.cleanup()
        endpoint = RUN / (str(uid) + ".sock")
        if endpoint.exists():
            info = endpoint.lstat()
            if not stat.S_ISSOCK(info.st_mode) or info.st_uid != uid:
                raise ValueError("Unsafe MESH socket")
            endpoint.unlink()
        remove_chat_endpoint(RUN / (str(uid) + '.chat.sock'), uid)
    finally:
        os.close(descriptor)


def main():
    if sys.argv[1:] == ["session"]:
        from backend import privileged_session
        return privileged_session()
    if os.geteuid() != 0 or len(sys.argv) != 3:
        raise ValueError("Authorized MESH setup required")
    action, argument = sys.argv[1:]
    if action in ("serve", "cleanup") and not os.environ.get("PKEXEC_UID"):
        return (serve if action == "serve" else cleanup)(owner(argument))
    uid = owner(os.environ.get("PKEXEC_UID", ""))
    if action == 'chat-up':
        if argument != 'fcchat0':
            raise ValueError('Invalid chat setup')
        import pwd
        from backend import system_component_status
        pwd.getpwuid(uid)
        if system_component_status() != 'READY':
            raise ValueError('Verified chat system component required')
        for kind in ('direct', 'mesh'):
            command('systemctl', 'start', 'family-connect-chat-' + kind + '@' + str(uid) + '.service')
        print(json.dumps({'chat_services': 'ready', 'vpn_started': False}))
        return
    if action in ('auto-up', 'auto-down'):
        from auto_intent import AutoIntent
        from auto_service import DIRECTORY, command_gate, manage_unit
        if action == 'auto-up' and argument != 'fcauto0':
            raise ValueError('Invalid Auto setup')
        if action == 'auto-down' and (len(argument) != 32 or any(part not in '0123456789abcdef' for part in argument)):
            raise ValueError('Invalid Auto generation')
        with command_gate():
            if action == 'auto-down':
                intent = AutoIntent(DIRECTORY / (str(uid) + '.intent.json'), uid)
                record = intent.read()
                if record is None or record['generation'] != argument:
                    raise ValueError('Stale Auto stop')
                try:
                    intent.revoke()
                except Exception:
                    manage_unit('stop', uid)
                    raise
            manage_unit('start' if action == 'auto-up' else 'stop', uid)
        print(json.dumps({'service': 'ready' if action == 'auto-up' else 'stopped'}))
        return
    if action not in ("up", "down") or argument != "fcmesh0":
        raise ValueError("Invalid MESH operation")
    if action == 'down':
        directory()
        try:
            Intent(RUN / (str(uid) + '.intent.json'), uid).revoke()
        except Exception:
            command('systemctl', 'stop', 'family-connect-mesh@' + str(uid) + '.service')
            raise
    command("systemctl", "start" if action == "up" else "stop", "family-connect-mesh@" + str(uid) + ".service")
    print(json.dumps({"service": "ready" if action == "up" else "stopped"}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("MESH operation failed; inspect the bounded application diagnostic export.", file=sys.stderr)
        raise SystemExit(1)
