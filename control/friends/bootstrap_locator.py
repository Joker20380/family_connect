"""Public bounded locator signed only inside the existing restricted issuer custody."""
import base64
import json

from cryptography import x509
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.x509.oid import ExtendedKeyUsageOID

from provisioning.friends_catalog import require
from .restricted import directory, gateway_target, clock_nanoseconds, timestamp

DOMAIN = b'family-connect/provisioning-locator/v1\0'


def issue(service, seed, server_certificate, sequence):
    now = int(service.access.clock())
    trust, authority, crl, _, _ = service._trust(now)
    published = directory(seed, trust['family'], trust['gateway'], now_ns=clock_nanoseconds(service.access.clock))
    require(len(published['seeds']) == 1 and type(sequence) is int and 0 < sequence < 2**53)
    certificate = x509.load_pem_x509_certificate(server_certificate.encode())
    certificate.verify_directly_issued_by(authority)
    require(server_certificate == certificate.public_bytes(Encoding.PEM).decode())
    require(ExtendedKeyUsageOID.SERVER_AUTH in certificate.extensions.get_extension_for_class(x509.ExtendedKeyUsage).value)
    require('gateway.family-connect.test' in certificate.extensions.get_extension_for_class(x509.SubjectAlternativeName).value.get_values_for_type(x509.DNSName))
    require(certificate.not_valid_before_utc.timestamp() <= now < certificate.not_valid_after_utc.timestamp())
    require(crl.get_revoked_certificate_by_serial_number(certificate.serial_number) is None)
    expires = min(timestamp(published['expires_at']), trust['expires_at'], int(certificate.not_valid_after_utc.timestamp()), int(crl.next_update_utc.timestamp()))
    require(now < expires <= now + 14400)
    payload = dict(version=1, purpose='family-connect-provisioning-v1', sequence=sequence,
                   issued_at=now, expires_at=expires, gateway_id=gateway_target(service.gateway_id),
                   room=published['seeds'][0]['join_url'], server_certificate=server_certificate)
    raw = json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()
    result = dict(version=1, issuer=service.manifest, payload=base64.b64encode(raw).decode(),
                  signature=base64.b64encode(service.signing_key.sign(DOMAIN + raw)).decode())
    encoded = json.dumps(result, separators=(',', ':')).encode()
    require(len(encoded) <= 16384)
    return encoded
