"""Disposable bounded TCP endpoint, never a proxy; run only on authorized hosts."""
import argparse
import hashlib
import json
import signal
import socket
import struct
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['echo', 'remote_close', 'remote_reset', 'remote_half_close', 'timeout'], required=True)
    parser.add_argument('--bind', choices=['127.0.0.1', '0.0.0.0'], default='127.0.0.1')
    args = parser.parse_args()
    signal.alarm(900)
    started = time.monotonic()
    with socket.socket() as listener:
        listener.bind((args.bind, 0))
        listener.listen(1)
        listener.settimeout(60)
        fillers = []
        if args.mode == 'timeout':
            for _ in range(2):
                fillers.append(socket.create_connection(('127.0.0.1', listener.getsockname()[1]), timeout=2))
        print(json.dumps({'event': 'fixture_ready', 'port': listener.getsockname()[1], 'mode': args.mode}), flush=True)
        if args.mode == 'timeout':
            try:
                time.sleep(60)
            finally:
                for connection in fillers:
                    connection.close()
            return
        while True:
            connection, address = listener.accept()
            if address[0] in ('127.0.0.1', '186.246.45.246'):
                break
            connection.close()
        with connection:
            connection.settimeout(650)
            if args.mode == 'remote_reset':
                payload = connection.recv(777)
                connection.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 0))
                print(json.dumps({'event': 'fixture_reset', 'received_before_reset': len(payload)}), flush=True)
                return
            if args.mode == 'remote_close':
                print(json.dumps({'event': 'fixture_clean_close'}), flush=True)
                return
            if args.mode == 'remote_half_close':
                connection.shutdown(socket.SHUT_WR)
            count = 0
            digest = hashlib.sha256()
            while True:
                payload = connection.recv(777)
                if not payload:
                    break
                count += len(payload)
                if count > 96 * 1024 * 1024:
                    raise RuntimeError('fixture bound exceeded')
                digest.update(payload)
                if args.mode == 'echo':
                    connection.sendall(payload)
            print(json.dumps({'event': 'fixture_result', 'bytes': count, 'sha256': digest.hexdigest(),
                              'seconds': time.monotonic() - started, 'eof': True}), flush=True)


if __name__ == '__main__':
    main()
