"""Read one owner-bound safe ACK through the existing private server DB, never app state."""
import argparse
import json
import os
from pathlib import Path

from control.friends.access import Access
from control.friends.restricted import PRIMARY_GATEWAY, SECONDARY_GATEWAY, bounded_file, from_env, gateway_target
from control.friends.readiness_receipts import readback, request_id


def inspect(database, material, correlation, *, gateway_id=None, device_reference=None, version_code=None):
    target = gateway_target(gateway_id)
    if device_reference is not None:
        request_id(device_reference)
    if version_code is not None and (type(version_code) is not int or not 1 <= version_code < 2**53):
        raise ValueError('Invalid expected version')
    previous = os.environ.get('FC_FRIENDS_RESTRICTED_DIR')
    os.environ['FC_FRIENDS_RESTRICTED_DIR'] = str(material)
    try:
        service = from_env(Access(database), target)
        expected_owner = device_reference
        if expected_owner is None:
            if service.eligible_devices is None or len(service.eligible_devices) != 1 or '*' in service.eligible_devices:
                raise ValueError('Explicit device or sole admitted owner required')
            expected_owner = next(iter(service.eligible_devices))
        result = readback(service, correlation, expected_owner)
        if version_code is not None:
            if result['status'] == 'ACK_RECEIVED' and result['receipt']['version_code'] != version_code:
                result = dict(version=1, correlation_id=correlation, status='UNKNOWN', receipt=None,
                              reason='VERSION_MISMATCH')
            result['expected_version_code'] = version_code
        if gateway_id is not None or device_reference is not None or version_code is not None:
            result['gateway_id'] = target
        return result
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
    parser.add_argument('--gateway-id', choices=(PRIMARY_GATEWAY, SECONDARY_GATEWAY))
    parser.add_argument('--device-file', type=Path, help='Private 0600 file containing the expected device reference')
    parser.add_argument('--version-code', type=int, help='Require this exact acknowledged Android version code')
    arguments = parser.parse_args()
    try:
        device = None if arguments.device_file is None else bounded_file(arguments.device_file, 33, True).decode('ascii').removesuffix('\n')
        print(json.dumps(inspect(arguments.database, arguments.material, arguments.correlation,
                                 gateway_id=arguments.gateway_id, device_reference=device, version_code=arguments.version_code)))
    except Exception:
        print(json.dumps(dict(version=1, status='UNKNOWN', reason='READBACK_UNAVAILABLE')))
        raise SystemExit(1) from None


if __name__ == '__main__':
    main()
