from device_identity.device import DeviceIdentity
from control.friends import support_ids


def proof(access, device, purpose, code=''):
    challenge = access.challenge(device.public_identity, device.wireguard_public_key, purpose, code)
    return device.prove_transport_key(challenge['challenge'])


def enroll(access):
    device = DeviceIdentity.generate()
    access.complete(proof(access, device, 'activate', access.invite()), 'activate')
    with access.db() as database:
        support = support_ids.registered(database, device.reference)
    return device, support
