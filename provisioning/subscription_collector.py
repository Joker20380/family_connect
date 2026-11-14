"""Root collector: pinned read-only source to private file; no message authority."""
import argparse
import json
from pathlib import Path
import re
import socket

from provisioning.support_bindings import collect


def command(path):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        connection.settimeout(5)
        connection.connect(str(path))
        connection.sendall(b'{"operation":"notification_cursor","arguments":{}}\n')
        with connection.makefile('rb') as stream:
            raw = stream.readline(4097)
    if len(raw) > 4096 or not raw.endswith(b'\n'):
        raise ValueError('invalid_cursor_response')
    response = json.loads(raw)
    if not response['ok']:
        raise ValueError('cursor_unavailable')
    cursor, anchor = response['result']['cursor'], response['result']['anchor']
    if type(cursor) is not int or cursor < -1 or (anchor is not None and re.fullmatch('[0-9a-f]{64}', anchor) is None):
        raise ValueError('invalid_cursor')
    return 'subscription-notifications ' + str(cursor) + ' ' + (anchor or 'none')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', required=True)
    for name in ('key', 'known-hosts', 'output', 'socket'):
        parser.add_argument('--'+name, required=True, type=Path)
    args = parser.parse_args()
    try:
        collect(args.host, args.key, args.known_hosts, args.output, command=command(args.socket))
    except Exception:
        parser.exit(1, 'Subscription source unavailable; checkpoint and queue retained.\n')


if __name__ == '__main__':
    main()
