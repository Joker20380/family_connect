"""Activate the pinned policy before the new empty Engine accepts its first request."""
import argparse
import os
from pathlib import Path
import threading

from control.capture_docker import Engine, Handler, Server
from control.capture_docker_domain import DomainAdmission
from control.docker_cold import Transition


class LazyAdmission:
    def __init__(self, factory):
        self.factory, self.admission = factory, None
        self.lock = threading.Lock()

    def __getattr__(self, name):
        if name not in ('request', 'response', 'control'):
            raise AttributeError(name)
        with self.lock:
            if self.admission is None:
                self.admission = self.factory()
            return getattr(self.admission, name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    transition = Transition(args.root)
    transition.guard()
    plan = transition.plan
    os.umask(0o077)
    def factory():
        transition.guard()
        return DomainAdmission(Engine(plan['socket']), plan['protected'], plan['pidfile'],
            args.root / 'admission', config=plan['configuration'], plugin=plan['plugin'], parent=plan['parent'])
    with Server(plan['plugin_socket'], Handler) as server:
        server.admission = LazyAdmission(factory)
        server.serve_forever(poll_interval=.1)


if __name__ == '__main__':
    main()
