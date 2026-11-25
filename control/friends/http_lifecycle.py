"""Drain receiving HTTP work on termination without killing admitted writers."""
from contextlib import ExitStack
from http.server import ThreadingHTTPServer
import signal
import threading


class Retention(threading.Event):
    def start(self, target, *, name):
        self.worker = threading.Thread(target=target, name=name, daemon=False)
        self.worker.start()
        return self

    def join(self):
        self.worker.join()


class DrainingHTTPServer(ThreadingHTTPServer):
    daemon_threads = False
    block_on_close = True
    timeout = .2

    def get_request(self):
        connection, address = super().get_request()
        connection.settimeout(5)
        return connection, address


def serve(address, handler, retention_factories):
    stopping = False

    def request_stop(signum, frame):
        nonlocal stopping
        stopping = True

    with ExitStack() as cleanup:
        for signum in (signal.SIGTERM, signal.SIGINT):
            previous = signal.signal(signum, request_stop)
            cleanup.callback(signal.signal, signum, previous)
        server = DrainingHTTPServer(address, handler)
        cleanup.callback(server.server_close)
        workers = []
        try:
            for factory in retention_factories:
                if stopping:
                    break
                worker = factory()
                workers.append(worker)
                cleanup.callback(worker.join)
            while not stopping:
                server.handle_request()
        finally:
            with ExitStack() as stop:
                for worker in workers:
                    stop.callback(worker.set)
                server.socket.close()
