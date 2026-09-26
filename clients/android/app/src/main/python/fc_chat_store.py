"""Android chat owner. Private keys and bootstrap are never exposed by JSON API."""
import json

from messenger.local import LocalChat, LocalError, contact_card
from fc_rns_transport import initialize


class _JavaCipher:
    def __init__(self, callback):
        self.callback = callback

    def encrypt(self, nonce, data, aad):
        return bytes(self.callback.encrypt(nonce, data, aad))

    def decrypt(self, nonce, data, aad):
        return bytes(self.callback.decrypt(nonce, data, aad))


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise LocalError('invalid_input')
        result[key] = value
    return result


class Session:
    def __init__(self, directory, runtime_directory, cipher, create):
        self.local = None
        self.carrier = None
        try:
            initialize(str(runtime_directory))
            self.local = LocalChat(str(directory), create=create, cipher=_JavaCipher(cipher))
        except Exception:
            raise LocalError('store_unavailable') from None

    def invoke(self, operation, payload):
        try:
            if self.local is None:
                raise LocalError('closed')
            if type(payload) is not str or len(payload.encode('utf-8')) > (1048608 if operation == 'import_events' else 180000 if operation=='queue_audio' else 32768):
                raise LocalError('invalid_input')
            data = json.loads(payload, object_pairs_hook=_object)
            signatures = {'profile': (), 'contacts': (), 'preview_contact': ('public',),
                          'trust_contact': ('public', 'fingerprint'), 'queue': ('address', 'text'),
                          'history': ('address', 'offset', 'limit'), 'delivery_state': (), 'request_sync': (), 'inbox': (),
                          'mark_inbox': ('ids', 'flag'), 'rename_contact': ('address', 'name'), 'service_events': (),
                          'edit_message': ('address','message_id','text'), 'queue_audio': ('address','audio'), 'audio': ('message_id',),
                          'import_events': ('feed',), 'mark_events': ('ids', 'flag')}
            if operation not in signatures or type(data) is not dict or set(data) != set(signatures[operation]):
                raise LocalError('invalid_input')
            if operation == 'preview_contact':
                value = contact_card(data['public'])
            else:
                value = getattr(self.local, operation)(**data)
            return json.dumps(dict(ok=True, value=value), ensure_ascii=False, separators=(',', ':'))
        except LocalError as error:
            code = str(error)
            if code not in ('closed', 'closing', 'close_pending', 'delivery_unavailable', 'invalid_input', 'fingerprint_mismatch', 'own_contact',
                            'contact_not_saved', 'store_unavailable', 'unverified_contact', 'message_not_saved'):
                code = 'store_unavailable'
        except (ValueError, TypeError, RecursionError):
            code = 'invalid_input'
        except Exception:
            code = 'store_unavailable'
        return json.dumps(dict(ok=False, error=code), separators=(',', ':'))

    def configure_delivery(self, host, port, public_hex, callbacks):
        if self.local is None:
            raise LocalError('closed')
        if self.carrier is not None:
            raise LocalError('delivery_already_attached')
        from fc_chat_transport import CarrierMailbox
        public = bytes.fromhex(public_hex)
        self.carrier = self.local.attach_carrier(
            lambda chat: CarrierMailbox(chat, host, port, public, callbacks))

    def enrollment_proof(self, device, challenge):
        if self.local is None:
            raise LocalError('closed')
        return json.dumps(self.local.enrollment_proof(device, challenge), separators=(',', ':'))

    def delivery_update(self, online, foreground):
        if self.local is None:
            raise LocalError('closed')
        return self.local.delivery_update(online=online, foreground=foreground)

    def close(self):
        if self.local is not None:
            self.local.close()
            if self.carrier is not None:
                self.carrier.close()
                self.carrier = None
            self.local = None
