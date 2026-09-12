"""Opt-in reference Linux control runner and relay, separate from stable releases.

Coordinates with the updated desktop GUI through the shared operation arbiter.
Older desktop versions do not participate and must remain closed. RNS starts with
explicit operator config, never generated interfaces or VPN lifecycle hooks.
"""
import argparse
import base64
import json
import logging
from pathlib import Path
import signal
import sys
import threading
import time

import RNS
from device_identity.device import load_or_create
from .configuration import ConfigVerifier
from .transaction import ControlJournal, ProvisioningCore
from .relay import ControlRelay
from .reticulum import ReticulumAdapter, ReticulumControlProvider


class DiagnosticFormatter(logging.Formatter):
    def format(self, record):
        # Never format exception text, message parameters, payloads or profiles.
        return json.dumps({key: getattr(record, key, None) for key in
            ('control_event', 'config_id', 'sequence', 'state', 'error_category')})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['init-client', 'once', 'recover', 'serve', 'init-relay', 'publish'])
    parser.add_argument('--state', type=Path, required=True)
    parser.add_argument('--identity', type=Path)
    parser.add_argument('--anchor', type=Path)
    parser.add_argument('--provider-public')
    parser.add_argument('--rns-config', type=Path)
    parser.add_argument('--public-identity')
    parser.add_argument('--wg-public')
    parser.add_argument('--sequence', type=int)
    parser.add_argument('--envelope', type=Path)
    parser.add_argument('--exclusive-connection-owner', action='store_true')
    args = parser.parse_args()
    clock = lambda: int(time.time())
    handler = logging.StreamHandler()
    handler.setFormatter(DiagnosticFormatter())
    logger = logging.getLogger('family_connect.control')
    logger.addHandler(handler); logger.setLevel(logging.INFO)
    if args.operation in {'init-relay', 'publish', 'serve'}:
        relay = ControlRelay(args.state, clock=clock)
        if args.operation == 'init-relay':
            relay.initialize(); return
        if args.operation == 'publish':
            if not args.envelope:
                parser.error('--envelope required')
            with args.envelope.open('rb') as stream:
                raw = stream.read(65537)
            relay.publish(public=args.public_identity, wg=args.wg_public,
                sequence=args.sequence, envelope=raw)
            return
        if not args.rns_config or not args.identity:
            parser.error('--rns-config and --identity required')
        transport = load_or_create(args.identity)
        RNS.Reticulum(configdir=str(args.rns_config), loglevel=RNS.LOG_CRITICAL)
        provider = ReticulumControlProvider(relay, transport._identity)
        print(json.dumps(dict(provider_public=transport.public_identity)), flush=True)
        stop = threading.Event()
        for number in (signal.SIGTERM, signal.SIGINT):
            signal.signal(number, lambda *_: stop.set())
        while not stop.is_set():
            provider.destination.announce()
            stop.wait(60)
        return
    if not args.identity or not args.anchor:
        parser.error('--identity and --anchor required')
    device = load_or_create(args.identity)
    verifier = ConfigVerifier(anchor=base64.b64decode(args.anchor.read_text().strip(), validate=True),
        device=device, client_version=(Path(__file__).resolve().parents[1] / 'VERSION').read_text().strip())
    journal = ControlJournal(args.state, verifier)
    if args.operation == 'init-client':
        journal.initialize(); return
    if args.operation == 'once' and (not args.rns_config or not args.provider_public):
        parser.error('once requires --rns-config and --provider-public')
    # No native Windows/Android claim: these have separate protected application
    # boundaries. This reference runner calls the existing Linux backend only.
    if not sys.platform.startswith('linux'):
        parser.error('reference application boundary requires Linux')
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'clients/desktop'))
    from backend import LinuxTCP
    from .application import BackendApplication
    core = ProvisioningCore(journal=journal, application=BackendApplication(LinuxTCP(), device),
        device=device, clock=clock)
    # Recover local pending application even if the carrier cannot start.
    recovered = core.recover()
    if args.operation == 'recover':
        # Local recovery only: retain pending ACKs and never fetch another config.
        print(json.dumps(dict(result=recovered)))
        if recovered == 'FAILED':
            raise SystemExit(1)
        return
    RNS.Reticulum(configdir=str(args.rns_config), loglevel=RNS.LOG_CRITICAL)
    cancel = threading.Event()
    for number in (signal.SIGTERM, signal.SIGINT):
        signal.signal(number, lambda *_: cancel.set())
    carrier = ReticulumAdapter(provider_public=base64.b64decode(args.provider_public, validate=True),
        device=device, clock=clock, cancel=cancel)
    print(json.dumps(dict(result=core.refresh(carrier))))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        # Operator logs may be retained; exceptions from profiles/backends can
        # contain credentials. Never print their text or a traceback here.
        print('{"control_event":"control.operation.failed","error_category":"OPERATION"}', file=sys.stderr)
        raise SystemExit(1)
