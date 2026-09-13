"""Text operations; contacts enter only through explicit out-of-band verification."""
import LXMF
import RNS

from . import codec


class Chat:
    def __init__(self, store):
        self.store = store
        self.identity = store.chat_identity()
        self.public = self.identity.get_public_key()
        self.address = codec.address(self.public)

    def trust_contact(self, public):
        address = codec.address(public)
        self.store.save_contact(address.hex(), public.hex())
        return address

    def contacts(self):
        return {bytes.fromhex(k): bytes.fromhex(v) for k, v in self.store.contacts().items()}

    def queue(self, recipient, text):
        contacts = self.contacts()
        if recipient not in contacts:
            raise ValueError('Contact verification required')
        raw = codec.pack(self.identity, contacts[recipient], text)
        own = {self.address: self.public}
        message = codec.unpack(raw, recipient=contacts[recipient], contacts=own)
        message['peer'] = recipient.hex()
        self.store.add(message, raw, outgoing=True)
        return message['id']

    def receive(self, raw):
        message = codec.unpack(raw, recipient=self.public, contacts=self.contacts())
        return self.store.add(message, raw, outgoing=False)

    def attach(self, router):
        """Router must belong to this chat, with private storage and DIRECT only."""
        source = router.register_delivery_identity(self.identity)
        if source is None:
            raise ValueError('Router already has a delivery identity')
        router.register_delivery_callback(lambda message: self.receive(message.packed))
        return source

    def send(self, router, source, message_id):
        token, raw = self.store.begin_attempt(message_id)
        try:
            peer = raw[:16]
            public = self.contacts()[peer]
            parsed = codec.unpack(raw, recipient=public, contacts={self.address: self.public})
            destination = RNS.Destination(codec.identity(public), RNS.Destination.OUT,
                                          RNS.Destination.SINGLE, 'lxmf', 'delivery')
            message = LXMF.LXMessage(destination, source, parsed['text'], desired_method=LXMF.LXMessage.DIRECT)
            message.timestamp = parsed['timestamp']
            message.pack()
            if message.packed != raw:
                raise ValueError('Retry changed signed message')
            message.register_delivery_callback(lambda _: self.store.finish_attempt(message_id, token, delivered=True))
            message.register_failed_callback(lambda _: self.store.finish_attempt(message_id, token, delivered=False))
            router.handle_outbound(message)
        except Exception:
            self.store.finish_attempt(message_id, token, delivered=False)
            raise
        return message
