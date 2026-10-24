"""Text operations; contacts enter only through explicit out-of-band verification."""
import LXMF
import RNS
import time

from . import codec


class Chat:
    def __init__(self, store, *, create_identity=True, durable_delivery=False,
                 platform='android', version=0):
        self.store = store
        self.identity = store.chat_identity(create=create_identity)
        self.public = self.identity.get_public_key()
        self.address = codec.address(self.public)
        self.durable_delivery = durable_delivery
        self.platform, self.version = platform, version
        self.store.inbox()

    def pin_service_publisher(self, public):
        self.store.pin_service_publisher(codec.address(public).hex(), public.hex())

    def queue_service(self, recipient, event):
        from .notices import validate_notice
        return self.queue(recipient, '', codec.fields_for(dict(kind='service', event=validate_notice(event))))

    def trust_contact(self, public):
        address = codec.address(public)
        self.store.save_contact(address.hex(), public.hex())
        return address

    def contacts(self):
        return {bytes.fromhex(k): bytes.fromhex(v) for k, v in self.store.contacts().items()}

    def delivery_contacts(self):
        return {**self.contacts(), **{bytes.fromhex(address): bytes.fromhex(public)
                for address, public in self.store.service_publishers().items()}}

    def queue(self, recipient, text, fields=None):
        contacts = self.contacts()
        if recipient not in contacts:
            raise ValueError('Contact verification required')
        raw = codec.pack(self.identity, contacts[recipient], text, fields=fields)
        own = {self.address: self.public}
        message = codec.unpack(raw, recipient=contacts[recipient], contacts=own)
        message['peer'] = recipient.hex()
        if self.durable_delivery and message.get('kind') != 'stored':
            message['require_stored'] = True
            message['expires_at'] = min(time.time() + 7 * 86400,
                                        message.get('event', {}).get('expires', float('inf')))
        self.store.add(message, raw, outgoing=True)
        return message['id']

    def receive(self, raw):
        publishers = self.store.service_publishers()
        contacts = self.contacts()
        contacts.update({bytes.fromhex(address): bytes.fromhex(public) for address, public in publishers.items()})
        message = codec.unpack(raw, recipient=self.public, contacts=contacts)
        if message.get('kind') == 'stored':
            return self.store.accept_stored_receipt(message)
        if message.get('kind') == 'service':
            from .notices import applicable
            if message['peer'] not in publishers:
                raise ValueError('Service publisher not pinned')
            if not applicable(message['event'], self.platform, self.version):
                raise ValueError('Service event not applicable')
        elif bytes.fromhex(message['peer']) not in self.contacts():
            raise ValueError('Contact verification required')
        if self.durable_delivery or message.get('kind') == 'service':
            def receipt():
                public = contacts[bytes.fromhex(message['peer'])]
                packed = codec.pack(self.identity, public, '', codec.fields_for(dict(kind='stored', target=message['id'])))
                value = codec.unpack(packed, recipient=public, contacts={self.address: self.public})
                value['peer'] = message['peer']
                return value, packed
            return self.store.commit_received(message, raw, receipt if self.durable_delivery else None)
        return self.store.add(message, raw, outgoing=False)

    def attach(self, router):
        """Router must belong to this chat and use private runtime storage."""
        source = router.register_delivery_identity(self.identity)
        if source is None:
            raise ValueError('Router already has a delivery identity')
        router.register_delivery_callback(lambda message: self.receive(message.packed))
        return source

    def send(self, router, source, message_id, *, via_relay=False):
        if type(via_relay) is not bool:
            raise ValueError('Explicit relay selection required')
        if via_relay and router.get_outbound_propagation_node() is None:
            raise ValueError('A trusted propagation node must be configured first')
        token, raw = self.store.begin_attempt(message_id)
        try:
            peer = raw[:16]
            public = self.contacts()[peer]
            parsed = codec.unpack(raw, recipient=public, contacts={self.address: self.public})
            destination = RNS.Destination(codec.identity(public), RNS.Destination.OUT,
                                          RNS.Destination.SINGLE, 'lxmf', 'delivery')
            method = LXMF.LXMessage.PROPAGATED if via_relay else LXMF.LXMessage.DIRECT
            message = LXMF.LXMessage(destination, source, parsed['text'], fields=codec.fields_for(parsed), desired_method=method)
            message.timestamp = parsed['timestamp']
            message.pack()
            if message.packed != raw:
                raise ValueError('Retry changed signed message')
            def completed(result):
                delivered = result.state == LXMF.LXMessage.DELIVERED
                relayed = via_relay and result.state == LXMF.LXMessage.SENT
                if delivered or relayed:
                    self.store.finish_attempt(message_id, token, delivered=delivered, relayed=relayed)
            message.register_delivery_callback(completed)
            message.register_failed_callback(lambda _: self.store.finish_attempt(message_id, token, delivered=False))
            router.handle_outbound(message)
        except Exception:
            self.store.finish_attempt(message_id, token, delivered=False)
            raise
        return message
