"""Synthetic presentation fixtures. No real contacts, devices or network."""
from copy import deepcopy


class ChatFixture:
    owns_notifications = True

    def __init__(self):
        self.cards = [dict(address='a1' * 16, name='Анна Лесная'), dict(address='b2' * 16, name='Михаил Северный')]
        self.messages = [
            dict(id='01' * 32, peer=self.cards[0]['address'], text='Привет! Встретимся завтра? 🌿', timestamp=1793008800, outgoing=False, status='received'),
            dict(id='02' * 32, peer=self.cards[0]['address'], text='Можно прогуляться в парке.', timestamp=1793008850, outgoing=False, status='received'),
            dict(id='03' * 32, peer=self.cards[0]['address'], text='Да, отличная идея! 🙂\nВозьму термос с чаем.', timestamp=1793008900, outgoing=True, status='recipient_stored', revision=1),
            dict(id='04' * 32, peer=self.cards[0]['address'], text='', kind='audio', duration_ms=12000, timestamp=1793095200, outgoing=False, status='received'),
            dict(id='05' * 32, peer=self.cards[0]['address'], text='До завтра! ✨', timestamp=1793095260, outgoing=True, status='queued'),
        ]
        self.calls = []
        self.open_count = self.close_count = 0
        self.fail_send = False
        self.heartbeats = []

    def open(self, create=False):
        self.open_count += 1
        return {}

    def tick(self, **kwargs):
        self.heartbeats.append(kwargs)
        return {}

    def foreground(self, peer):
        self.visible_peer = peer

    def close(self):
        self.close_count += 1

    def invoke(self, operation, **arguments):
        self.calls.append((operation, arguments))
        if operation == 'contacts':
            return deepcopy(self.cards)
        if operation == 'history':
            messages = [message for message in self.messages if message['peer'] == arguments['address']]
            offset, limit = arguments['offset'], arguments['limit']
            return dict(messages=deepcopy(messages[offset:offset + limit]), total=len(messages),
                        next_offset=offset + limit if offset + limit < len(messages) else None)
        if operation == 'inbox_summary':
            return [dict(peer=self.cards[1]['address'], id='06' * 32, read=False, notified=False)]
        if operation == 'event_counts':
            return dict(total=0, unread=0)
        if operation == 'service_events_page':
            return dict(events=[], total=0, next_offset=None)
        if operation == 'voice_settings':
            return dict(mode=16, confirmed=[])
        if operation == 'delivery_settings':
            return dict(background=False, notifications=False)
        if operation == 'queue':
            if self.fail_send:
                raise RuntimeError('message_not_saved')
            self.messages.append(dict(id='ff' * 32, peer=arguments['address'], text=arguments['text'], timestamp=1793095300, outgoing=True, status='queued'))
            return 'ff' * 32
        if operation == 'edit_message':
            message = next(message for message in self.messages if message['id'] == arguments['message_id'])
            message.update(text=arguments['text'], revision=message.get('revision', 0) + 1)
        if operation == 'rename_contact':
            card = next(card for card in self.cards if card['address'] == arguments['address'])
            card['name'] = arguments['name']
            return deepcopy(card)
        return None
