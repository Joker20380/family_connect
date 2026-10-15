import argparse
import base64
import os
from pathlib import Path
import resource
import sys
import time

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import load_pem_private_key

from credential_renewal import DAY, Validator, atomic, canonical, digest, parse, read_private, require
from offline_handoff import DOMAIN, verify


def sign(request, anchor, key_bytes, validator, now):
    require(set(request) == {'schema','operation_id','previous_authority','successor_payload','request_expires_at'}
            and request['schema'] == 1 and now < request['request_expires_at'] <= now+DAY, 'HANDOFF_REQUEST_SCHEMA')
    if len(key_bytes) == 32:
        signer = Ed25519PrivateKey.from_private_bytes(key_bytes)
    elif key_bytes.startswith(b'-----BEGIN'):
        signer = load_pem_private_key(key_bytes,None)
    else:
        signer = Ed25519PrivateKey.from_private_bytes(base64.b64decode(key_bytes.strip(),validate=True))
    require(isinstance(signer,Ed25519PrivateKey) and signer.public_key().public_bytes_raw() == anchor, 'TRUST_ROOT_KEY_MISMATCH')
    payload = canonical(request['successor_payload'])
    envelope = dict(payload=base64.b64encode(payload).decode(),
        signature=base64.b64encode(signer.sign(b'family-connect/restricted-issuer/v1\0'+payload)).decode())
    handoff = canonical(dict(schema=2,operation_id=request['operation_id'],
        previous_authority_sha256=digest(canonical(request['previous_authority'])),authority=envelope,
        expires_at=request['request_expires_at']))
    bundle = canonical(dict(payload=base64.b64encode(handoff).decode(),
                            signature=base64.b64encode(signer.sign(DOMAIN+handoff)).decode()))
    verify(bundle,validator,request['previous_authority'],request['operation_id'],now)
    return bundle


def main():
    os.umask(0o077)
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    parser = argparse.ArgumentParser(description='Offline-only signing; never install this command on RU/NL')
    parser.add_argument('--request',type=Path,required=True)
    parser.add_argument('--anchor',type=Path,required=True)
    parser.add_argument('--root-key-fd',type=int,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--confirm-authority-renewal',action='store_true',required=True)
    parser.add_argument('--expired-recovery', action='store_true')
    args = parser.parse_args()
    try:
        from control.friends.restricted import delegation
        require(args.root_key_fd >= 3, 'PRIVATE_KEY_FD_REQUIRED')
        with os.fdopen(os.dup(args.root_key_fd),'rb') as stream:
            key_bytes = stream.read(8193)
        require(0 < len(key_bytes) <= 8192, 'PRIVATE_KEY_INPUT_BOUND')
        request = parse(read_private(args.request))
        anchor = base64.b64decode(args.anchor.read_bytes().strip(),validate=True)
        if args.expired_recovery:
            from expired_recovery import sign as recovery_sign
            if len(key_bytes) == 32:
                signer = Ed25519PrivateKey.from_private_bytes(key_bytes)
            elif key_bytes.startswith(b'-----BEGIN'):
                signer = load_pem_private_key(key_bytes,None)
            else:
                signer = Ed25519PrivateKey.from_private_bytes(base64.b64decode(key_bytes.strip(),validate=True))
            require(isinstance(signer,Ed25519PrivateKey), 'TRUST_ROOT_KEY_MISMATCH')
            output = recovery_sign(request,Validator(anchor,delegation),signer,int(time.time()))
        else:
            output = sign(request,anchor,key_bytes,Validator(anchor,delegation),int(time.time()))
        require(not args.output.exists(), 'SIGNED_BUNDLE_ALREADY_EXISTS')
        atomic(args.output,output)
        print(canonical(dict(result='SIGNED_OFFLINE',bundle_sha256=digest(output),root_key_exported=False)).decode())
    except Exception as error:
        from credential_renewal import Rejected
        print(canonical(dict(result='OFFLINE_SIGNING_REJECTED', cause=str(error) if isinstance(error,Rejected) else 'RECOVERY_SIGNING_INVALID')).decode())
        raise SystemExit(1) from None


if __name__ == '__main__':
    main()
