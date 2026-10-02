"""Read one owner-bound safe ACK through the existing private server DB, never app state."""
import argparse
import json
import os
from pathlib import Path

from control.friends.access import Access
from control.friends.restricted import from_env
from control.friends.readiness_receipts import readback


def inspect(database, material, correlation):
    previous = os.environ.get('FC_FRIENDS_RESTRICTED_DIR')
    os.environ['FC_FRIENDS_RESTRICTED_DIR'] = str(material)
    try:
        service = from_env(Access(database))
        if service.eligible_devices is None or len(service.eligible_devices) != 1 or '*' in service.eligible_devices:
            raise ValueError('Sole admitted owner required')
        return readback(service, correlation, next(iter(service.eligible_devices)))
    finally:
        if previous is None:
            os.environ.pop('FC_FRIENDS_RESTRICTED_DIR', None)
        else:
            os.environ['FC_FRIENDS_RESTRICTED_DIR'] = previous


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path, required=True)
    parser.add_argument('--material', type=Path, required=True)
    parser.add_argument('--correlation', required=True)
    arguments = parser.parse_args()
    try:
        print(json.dumps(inspect(arguments.database, arguments.material, arguments.correlation)))
    except Exception:
        print(json.dumps(dict(version=1, status='UNKNOWN', reason='READBACK_UNAVAILABLE')))
        raise SystemExit(1) from None


if __name__ == '__main__':
    main()
