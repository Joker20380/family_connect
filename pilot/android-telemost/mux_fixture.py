"""Bounded loopback-only concurrent echo fixture, never a forwarding proxy."""
import argparse
import hashlib
import json
import signal
import socket
import threading
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['echo'], required=True)
    parser.add_argument('--bind', choices=['127.0.0.1'], required=True)
    args = parser.parse_args()
    signal.alarm(900)
    slots = threading.BoundedSemaphore(32)
    output = threading.Lock()

    def echo(connection, identity):
        started = time.monotonic()
        digest = hashlib.sha256()
        count = 0
        complete = False
        try:
            with connection:
                connection.settimeout(650)
                while True:
                    payload = connection.recv(8192)
                    if not payload:
                        complete = True
                        break
                    count += len(payload)
                    if count > 64 * 1024 * 1024:
                        raise RuntimeError('fixture byte bound')
                    digest.update(payload)
                    connection.sendall(payload)
                connection.shutdown(socket.SHUT_WR)
        except (OSError, RuntimeError):
            pass
        finally:
            with output:
                print(json.dumps({'event': 'fixture_result', 'connection': identity, 'bytes': count,
                                  'sha256': digest.hexdigest(), 'eof': complete,
                                  'seconds': time.monotonic() - started}), flush=True)
            slots.release()

    with socket.socket() as listener:
        listener.bind((args.bind, 0))
        listener.listen(32)
        listener.settimeout(700)
        print(json.dumps({'event': 'fixture_ready', 'port': listener.getsockname()[1], 'mode': 'mux'}), flush=True)
        for identity in range(256):
            connection, _ = listener.accept()
            if not slots.acquire(blocking=False):
                connection.close()
                continue
            threading.Thread(target=echo, args=(connection, identity), daemon=True).start()


if __name__ == '__main__':
    main()
