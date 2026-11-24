import json

import RNS

from control.friends.chat import ChatAccess
from messenger.admission import message
from tests.test_friends_http_runtime import runtime, running, request


def test_packaged_registration_preserves_legacy_shape_and_requires_valid_opt_in(runtime):
    ChatAccess(runtime['access']).initialize()
    identity = RNS.Identity()
    public = identity.get_public_key().hex()
    device = runtime['canary']
    with running(runtime):
        for protocol in (None, 1, True, 2):
            status, raw = request(runtime['backend'], '/friends/chat/challenge', body=dict(
                public_identity=device.public_identity, wireguard_public_key=device.wireguard_public_key, chat_public=public))
            assert status == 200
            challenge = json.loads(raw)
            body = dict(proof=device.prove_transport_key(challenge['challenge']), chat_public=public,
                        chat_signature=identity.sign(message(public, challenge['device'], challenge['challenge'])).hex())
            if protocol is not None:
                body['support_protocol'] = protocol
            status, raw = request(runtime['backend'], '/friends/chat/register', body=body)
            if protocol is True or protocol == 2:
                assert status == 400
            else:
                assert status == 200
                assert json.loads(raw) == dict(device=device.reference, chat_public=public, status='pending-node')
