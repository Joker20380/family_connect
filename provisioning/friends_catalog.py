"""Verify invite-test schema 2 templates; never apply a VPN or persist a floor here.

The authority verifies domain-separated bytes. Device assignments arrive through the
existing authenticated HTTPS response, not inside the signed common template.
"""
import base64
import hashlib
import ipaddress
import json
import re
import uuid
from dataclasses import dataclass
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from clients.desktop import profile_config

DOMAIN = b'family-connect/invited-test/v1\0'
MAX_SEQUENCE = 9007199254740991


def require(ok):
    if not ok:
        raise ValueError('Invalid Friends configuration')


def unique(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result)
        result[key] = value
    return result


def parse(raw):
    return json.loads(raw, object_pairs_hook=unique,
                      parse_constant=lambda _: require(False))


def fields(value, names):
    require(type(value) is dict and set(value) == set(names.split()))


def key(text, size):
    require(type(text) is str)
    raw = base64.b64decode(text, validate=True)
    require(len(raw) == size and base64.b64encode(raw).decode() == text)
    return raw


@dataclass(frozen=True)
class FriendsConfiguration:
    country: str
    sequence: int
    catalog_hash: str
    address: str
    # These contain device credentials: callers must keep them out of logs and IPC.
    tcp: str
    awg: str

    def __repr__(self):
        return f'FriendsConfiguration(country={self.country!r}, sequence={self.sequence})'


def verify(reply, anchor, device, country, wireguard_key, *, floor=0, previous_hash=None):
    """Same-sequence payload changes are rejected when resuming a saved catalog.

    The owner must atomically persist the verified response/floor before apply. This
    function does not provide offline fallback or turn an access rejection into success.
    """
    try:
        require(type(floor) is int and 0 <= floor <= MAX_SEQUENCE)
        require(country in ('ru', 'nl') and type(anchor) is bytes and len(anchor) == 32)
        fields(reply, 'device country address tcp_id catalog')
        require(reply['device'] == device and reply['country'] == country)
        e = reply['catalog']; fields(e, 'payload signature')
        require(len(json.dumps(e).encode()) <= 16384)
        require(type(e['payload']) is str)
        raw = base64.b64decode(e['payload'], validate=True)
        require(0 < len(raw) <= 8192 and base64.b64encode(raw).decode() == e['payload'])
        Ed25519PublicKey.from_public_bytes(anchor).verify(key(e['signature'], 64), DOMAIN + raw)
        value = parse(raw.decode("utf-8")); fields(value, 'schema sequence access gateways')
        require(type(value['schema']) is int and value['schema'] == 2 and value['access'] == 'invite-test')
        sequence = value['sequence']
        require(type(sequence) is int and max(1, floor) <= sequence <= MAX_SEQUENCE)
        digest = hashlib.sha256(raw).hexdigest()
        if previous_hash is not None:
            require(type(previous_hash) is str and re.fullmatch('[0-9a-f]{64}', previous_hash))
            require(sequence != floor or digest == previous_hash)
        gateways = value['gateways']
        require(type(gateways) is list and len(gateways) == 2)
        profiles = {}
        sample = base64.b64encode(bytes([1])*32).decode()
        for gateway in gateways:
            fields(gateway, 'country tcp awg')
            region = gateway['country']; require(type(region) is str and region in ('ru', 'nl') and region not in profiles)
            tcp = gateway['tcp']; fields(tcp, 'type server port id public_key server_name short_id')
            require(tcp['id'] == 'DEVICE_CREDENTIAL')
            parsed = profile_config.parse_tcp(json.dumps({**tcp, 'id': '11111111-1111-4111-8111-111111111111'}))
            ip = ipaddress.IPv4Address(parsed['server'])
            require(not ip.is_loopback and 0 < int(str(ip).split('.')[0]) < 224)
            require(any(base64.urlsafe_b64decode(parsed['public_key']+'=')))
            awg = gateway['awg']; require(type(awg) is str and len(awg.encode()) <= 8192)
            require(awg.count('LOCAL_DEVICE_KEY') == awg.count('ASSIGNED_ADDRESS') == 1)
            require(re.search(r'(?m)^PrivateKey = LOCAL_DEVICE_KEY$', awg) and re.search(r'(?m)^Address = ASSIGNED_ADDRESS$', awg))
            normalized = awg.replace('LOCAL_DEVICE_KEY', sample).replace('ASSIGNED_ADDRESS', '10.83.0.2/32')
            parts = profile_config.parse(normalized, allow_awg=True, allow_awg31=True)
            require({'HeaderProtectionKey', 'ContentPaddingAddition'} <= set(parts['Interface']))
            face = parts['Interface']
            require(int(face['Jc']) >= 1 and int(face['Jmin']) >= 1 and int(face['Jmax']) >= 1)
            host = parts['Peer']['Endpoint'].rsplit(':', 1)[0]
            endpoint = ipaddress.IPv4Address(host)
            require(str(endpoint) == host and not endpoint.is_loopback and 0 < int(host.split('.')[0]) < 224)
            profiles[region] = (tcp, awg)
        address = reply['address']; require(type(address) is str)
        ip = ipaddress.IPv4Interface(address)
        network = ipaddress.IPv4Network('10.84.0.0/16' if country == 'ru' else '10.83.0.0/16')
        require(str(ip) == address and ip.network.prefixlen == 32 and ip.ip in network)
        require(ip.ip not in (network.network_address, network.network_address+1, network.broadcast_address))
        credential = reply['tcp_id']; require(type(credential) is str and str(uuid.UUID(credential)) == credential and uuid.UUID(credential).int != 0)
        require(type(wireguard_key) is bytes and len(wireguard_key) == 32)
        tcp, awg = profiles[country]
        tcp = json.dumps({**tcp, 'id': credential}, separators=(',', ':'))
        awg = profile_config.validate(awg.replace('LOCAL_DEVICE_KEY', base64.b64encode(wireguard_key).decode()).replace('ASSIGNED_ADDRESS', address), allow_awg=True, allow_awg31=True)
        return FriendsConfiguration(country, sequence, digest, address, tcp, awg)
    except Exception:
        raise ValueError('Invalid Friends configuration') from None
