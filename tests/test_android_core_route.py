import socket
import threading

from android_core_route import forward_http


def test_http_response_close_releases_adapter_without_client_fin():
    client, incoming = socket.socketpair()
    outgoing, origin = socket.socketpair()
    counts = []
    worker = threading.Thread(target=forward_http, args=(incoming, outgoing, counts.append), daemon=True)
    worker.start()
    try:
        client.settimeout(2)
        origin.settimeout(2)
        client.sendall(b'request')
        assert origin.recv(7) == b'request'
        origin.sendall(b'response')
        origin.shutdown(socket.SHUT_WR)
        assert client.recv(8) == b'response'
        assert client.recv(1) == b''
        worker.join(2)
        assert not worker.is_alive(), 'origin EOF must not retain two descriptors until client FIN'
        assert sum(counts) == 15
    finally:
        for connection in (client, incoming, outgoing, origin):
            connection.close()
        worker.join(2)


def test_client_half_close_preserves_complete_http_response():
    client, incoming = socket.socketpair()
    outgoing, origin = socket.socketpair()
    counts = []
    worker = threading.Thread(target=forward_http, args=(incoming, outgoing, counts.append), daemon=True)
    worker.start()
    try:
        client.settimeout(2)
        origin.settimeout(2)
        client.sendall(b'request')
        client.shutdown(socket.SHUT_WR)
        assert origin.recv(7) == b'request'
        assert origin.recv(1) == b''
        origin.sendall(b'response')
        origin.shutdown(socket.SHUT_WR)
        assert client.recv(8) == b'response'
        assert client.recv(1) == b''
        worker.join(2)
        assert not worker.is_alive()
        assert sum(counts) == 15
    finally:
        for connection in (client, incoming, outgoing, origin):
            connection.close()
        worker.join(2)
