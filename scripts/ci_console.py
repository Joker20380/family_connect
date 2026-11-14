"""Bound console lines; tee retains the exact full diagnostic artifact upstream."""
import hashlib
import sys

LIMIT = 2048


def relay(source, destination):
    pending = bytearray()
    length = 0
    number = 1
    digest = hashlib.sha256()

    def emit():
        if length <= LIMIT:
            destination.write(pending)
        else:
            destination.write((f'CI_LOG line={number} bytes={length} sha256={digest.hexdigest()} '
                               'retained in full-pytest.log\n').encode())
        destination.flush()

    while chunk := source.read1(8192):
        for piece in chunk.splitlines(keepends=True):
            digest.update(piece)
            length += len(piece)
            if length <= LIMIT:
                pending.extend(piece)
            else:
                pending.clear()
            if piece.endswith(b'\n'):
                emit()
                pending.clear()
                length = 0
                number += 1
                digest = hashlib.sha256()
    if length:
        emit()


if __name__ == '__main__':
    relay(sys.stdin.buffer, sys.stdout.buffer)
