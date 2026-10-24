"""GTK front end for the shared encrypted chat owner; no keys enter widget state."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

from gi.repository import Gtk, Gio, GLib, Gdk, Pango

from chat_strings import STRINGS
from chat_notifications import Notifications


ERRORS = {
    'identity_unavailable': ('Сначала активируйте этот компьютер в настройках.', 'Activate this computer in Settings first.'),
    'keyring_unavailable': ('Разблокируйте системное хранилище ключей. История не изменена.', 'Unlock the system keyring. History is unchanged.'),
    'identity_mismatch': ('История принадлежит другому устройству. Ключи не заменены.', 'History belongs to another device. Keys were not replaced.'),
    'store_unavailable': ('Не удалось открыть историю. Данные не сброшены.', 'History could not be opened. Data was not reset.'),
    'invalid_input': ('Проверьте введённые данные.', 'Check the entered values.'),
    'own_contact': ('Это ваша карточка.', 'This is your own contact card.'),
    'fingerprint_mismatch': ('Отпечаток не совпадает.', 'The fingerprint does not match.'),
    'unverified_contact': ('Сначала проверьте контакт.', 'Verify the contact first.'),
    'message_not_saved': ('Сообщение не сохранено. Черновик оставлен.', 'Message was not saved. Your draft is retained.'),
    'close_pending': ('Завершаем доставку перед закрытием…', 'Stopping delivery before closing…'),
    'runtime_unavailable': ('Компоненты мессенджера не установлены.', 'Messaging components are not installed.'),
    'service_unavailable': ('Пользовательская служба мессенджера недоступна. История и ключи сохранены.', 'The user messaging service is unavailable. History and keys are preserved.'),
    'operation_outcome_unknown': ('Ответ службы потерян. Проверьте историю перед повторной отправкой; сообщение могло сохраниться.', 'The service reply was lost. Check history before resending; the message may have been saved.'),
    'busy': ('Служба занята. Повторите после завершения текущей операции.', 'The service is busy. Retry after the current operation completes.'),
    'request_expired': ('Запрос устарел. Обновите экран и повторите.', 'The request expired. Refresh the view and retry.'),
    'response_too_large': ('Ответ слишком большой. Откройте отдельную страницу истории.', 'The reply is too large. Open an individual history page.'),
}


class ChatPane(Gtk.Box):
    def __init__(self, button_class=Gtk.Button, *, owner_factory=None, audio_source=None, audio_sink=None,
                 notification_factory=Notifications, show_chat=None, show_settings=None, layout_changed=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.add_css_class('fc-chat')
        self.button_class = button_class
        self.owner_factory = owner_factory
        self.owner = None
        self.show_chat = show_chat
        self.show_settings = show_settings
        self.layout_changed = layout_changed or (lambda: None)
        self.notifications = notification_factory(self.notification_open)
        self.notices_busy = False
        self.posting = set()
        self.pending_notice = None
        self.foreground = False
        self.events_unavailable = False
        self.delivery_state = {}
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix='fc-chat-owner')
        self.network_pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix='fc-chat-registration')
        self.network_busy = False
        self.busy = self.closing = self.active = self.opened = False
        self.ru = True
        self.screen = 'welcome'
        self.view_revision = 0
        self.peer = None
        self.offset = 0
        self.drafts = {}
        self.last_snapshot = None
        from chat_voice import VoiceControls
        self.voice = VoiceControls(self, source_factory=audio_source, sink_factory=audio_sink)
        self.title = Gtk.Label(xalign=0, ellipsize=Pango.EllipsizeMode.END)
        self.title.set_hexpand(True)
        self.title.add_css_class('fc-chat-title')
        self.heading = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.heading.add_css_class('fc-chat-toolbar')
        self.header_back = button_class(label='‹')
        self.header_menu = button_class(label='⋮')
        self.back_action = self.menu_action = None
        for control in (self.header_back, self.header_menu):
            control.set_size_request(48, 48)
            control.add_css_class('fc-action')
            control.set_visible(False)
        self.header_back.connect('clicked', lambda *_: self.back_action() if self.back_action and not self.busy else None)
        self.header_menu.connect('clicked', lambda *_: self.menu_action() if self.menu_action and not self.busy else None)
        self.heading.append(self.header_back)
        self.heading.append(self.title)
        self.heading.append(self.header_menu)
        self.append(self.heading)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.append(self.content)
        self.notice = Gtk.Label(xalign=0, wrap=True)
        self.notice.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.notice.add_css_class('fc-caption')
        self.append(self.notice)
        self.reorder_child_after(self.notice, self.heading)
        from chat_announcements import Announcements
        self.announcements = Announcements(self)
        self.timer = GLib.timeout_add_seconds(6, self.poll)
        keys = Gtk.EventControllerKey()
        keys.connect('key-pressed', self.key_pressed)
        self.add_controller(keys)
        self.welcome()

    def t(self, name):
        return STRINGS[name][0 if self.ru else 1]

    def words(self, ru, en):
        return ru if self.ru else en

    def clear(self, screen, title):
        self.view_revision += 1
        if screen != 'conversation':
            self.voice.leave()
        self.screen = screen
        if screen.startswith('notice-'):
            self.add_css_class('fc-announcements')
        else:
            self.remove_css_class('fc-announcements')
        self.title.set_text(title)
        self.toolbar()
        while self.content.get_first_child() is not None:
            self.content.remove(self.content.get_first_child())

    def toolbar(self, *, back=None, menu=None):
        self.back_action, self.menu_action = back, menu
        self.header_back.set_visible(back is not None)
        self.header_menu.set_visible(menu is not None)
        self.header_back.set_tooltip_text(self.t('chat_dialogs'))
        self.header_menu.set_tooltip_text(self.t('chat_menu'))
        self.header_back.update_property([Gtk.AccessibleProperty.LABEL], [self.t('chat_dialogs')])
        self.header_menu.update_property([Gtk.AccessibleProperty.LABEL], [self.t('chat_menu')])

    def label(self, text, selectable=False):
        widget = Gtk.Label(label=text, xalign=0, wrap=True, selectable=selectable)
        widget.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
        if selectable:
            attributes = Pango.AttrList()
            attributes.insert(Pango.attr_insert_hyphens_new(False))
            widget.set_attributes(attributes)
        self.content.append(widget)
        return widget

    def button(self, text, action):
        widget = self.button_class(label=text)
        widget.add_css_class('fc-action')
        widget.add_css_class('fc-secondary')
        child = widget.get_child()
        if isinstance(child, Gtk.Label):
            child.set_wrap(True)
            child.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
        widget.connect('clicked', lambda *_: action())
        self.content.append(widget)
        return widget

    def entry(self, text='', maximum=4096):
        widget = Gtk.Entry(text=text, max_length=maximum)
        widget.set_hexpand(True)
        self.content.append(widget)
        return widget

    def submit(self, action, callback, *, interactive=True):
        if self.busy or self.closing:
            return
        self.busy = True
        if interactive:
            self.content.set_sensitive(False)
        future = self.pool.submit(action)
        future.add_done_callback(lambda result: GLib.idle_add(self.complete, result, callback))

    def complete(self, future, callback):
        self.busy = False
        if self.closing:
            return False
        self.content.set_sensitive(True)
        try:
            result = future.result()
        except Exception as failure:
            code = str(failure)
            if code == 'not_created':
                self.welcome()
            else:
                if isinstance(failure, ImportError):
                    code = 'runtime_unavailable'
                if not self.opened:
                    self.clear('unavailable', self.t('chat_title'))
                    self.button(self.words('Повторить', 'Retry'), lambda: self.open(self.open_mode))
                    self.button(self.words('Открыть сохранённую историю', 'Open saved history'), lambda: self.open(False))
                self.notice.set_text(ERRORS.get(code, ERRORS['store_unavailable'])[0 if self.ru else 1])
        else:
            callback(result)
        if self.pending_notice is not None and not self.busy:
            self.notification_open(self.pending_notice)
        self.layout_changed()
        return False

    def activate(self, active, ru):
        changed = self.ru != ru
        self.ru, self.active = ru, active
        if not active:
            self.view_revision += 1
            self.voice.leave()
        if active and self.owner is None and not self.busy:
            self.open(False)
        elif changed and not self.busy:
            if not self.opened:
                self.welcome()
            elif self.screen in ('contacts', 'conversation', 'service'):
                self.last_snapshot = None
                self.refresh()
            elif self.screen == 'profile':
                self.profile()
            elif self.screen == 'notifications':
                self.notification_settings()
            elif self.screen.startswith('notice-'):
                self.announcements.localize()
        if self.opened:
            self.poll()
        if active and self.opened and not self.busy:
            self.refresh()

    def open(self, create):
        self.open_mode = create
        def work():
            if self.owner is None:
                if self.owner_factory is not None:
                    self.owner = self.owner_factory()
                else:
                    from provisioning.chat_client import ChatClient
                    self.owner = ChatClient()
            return self.owner.open(create=create)
        def ready(_):
            self.opened = True
            if getattr(self.owner, 'owns_notifications', False):
                self.notifications.close()
            self.notice.set_text(self.t('chat_local_only'))
            self.contacts()
        self.submit(work, ready)

    def resume_existing(self):
        if not self.closing and self.owner is None and (Path.home() / '.local/share/family-connect/chat/account.json').exists():
            self.open(False)
        return False

    def visible_peer(self):
        root = self.get_root()
        if not self.active or not self.get_mapped() or root is None or not root.is_active():
            return None
        if self.screen == 'service':
            return 'service'
        if self.screen == 'conversation' and self.peer:
            return self.peer['address']
        return None

    def notification_open(self, peer):
        if self.closing or not self.opened:
            return
        present = self.pending_notice is None
        self.pending_notice = peer
        if present and self.show_chat:
            self.show_chat()
        if self.busy:
            return
        self.pending_notice = None
        self.notifications.withdraw(peer)
        if peer == 'service':
            self.service_events()
        else:
            def opened(cards):
                card = next((card for card in cards if card['address'] == peer), None)
                if card:
                    self.conversation(card)
            self.submit(lambda: self.owner.invoke('contacts'), opened)

    def refresh_notifications(self):
        if not self.opened or self.closing or self.notices_busy or getattr(self.owner, 'owns_notifications', False):
            return
        self.notices_busy = True
        future = self.pool.submit(self.owner.invoke, 'notification_snapshot')
        def complete(result):
            self.notices_busy = False
            if self.closing:
                return False
            try:
                snapshot = result.result()
            except Exception:
                return False
            visible = self.visible_peer()
            enabled = snapshot['settings']['notifications']
            self.notifications.retain(set(snapshot['peers']) - {visible} if enabled else set())
            if enabled:
                for batch in snapshot['batches']:
                    peer = batch['peer']
                    if peer == visible or peer in self.posting:
                        continue
                    self.posting.add(peer)
                    self.notifications.notify(peer, batch['unread'], self.ru,
                        lambda accepted, batch=batch: self.notification_posted(batch, accepted))
            return False
        future.add_done_callback(lambda result: GLib.idle_add(complete, result))

    def notification_posted(self, batch, accepted):
        peer = batch['peer']
        if not accepted or self.closing:
            self.posting.discard(peer)
            return
        future = self.pool.submit(self.owner.invoke, 'notification_posted', peer=peer, receipts=batch['receipts'])
        def completed(result):
            self.posting.discard(peer)
            try:
                result.result()
            except Exception:
                pass
            return False
        future.add_done_callback(lambda result: GLib.idle_add(completed, result))

    def welcome(self):
        self.clear('welcome', self.t('chat_title'))
        self.notice.set_text(self.t('chat_local_notice'))
        self.label(self.t('chat_welcome'))
        self.button(self.t('chat_create'), lambda: self.open(True))

    def contacts(self):
        self.view_revision += 1
        self.voice.leave()
        self.peer = None
        self.offset = 0
        self.screen = 'contacts'
        self.last_snapshot = None
        self.refresh()

    def snapshot(self, address, offset):
        if address is None:
            contacts = self.owner.invoke('contacts')
            inbox = self.owner.invoke('inbox_summary')
            return {'contacts': contacts, 'inbox': inbox, 'events': self.owner.invoke('event_counts')}
        if address == 'service':
            return self.owner.invoke('service_events_page', offset=offset, limit=50)
        return self.owner.invoke('history', address=address, offset=offset, limit=50)

    def refresh(self):
        if self.active and self.opened and self.screen in ('contacts', 'conversation', 'service'):
            revision, offset = self.view_revision, self.offset
            address = 'service' if self.screen == 'service' else self.peer['address'] if self.peer else None
            def display(result):
                if revision == self.view_revision:
                    self.display(result)
                else:
                    self.refresh()
            self.submit(lambda: self.snapshot(address, offset), display, interactive=False)

    def display(self, result):
        if (self.peer is not None and self.voice.address == self.peer['address'] and
                (self.voice.state != 'idle' or self.voice.pointer or self.voice.press_timer)):
            return
        if result == self.last_snapshot:
            return
        self.last_snapshot = result
        if self.screen == 'service':
            self.display_events(result)
            return
        if self.peer is None:
            self.clear('contacts', self.t('chat_dialogs'))
            self.button(self.t('chat_add'), self.add_contact)
            self.button(self.t('chat_profile'), self.profile)
            self.button(self.t('chat_background'), self.notification_settings)
            unread_events = result['events']['unread']
            self.button(self.t('service_events') + (' · ' + str(unread_events) if unread_events else ''), self.service_events)
            if not result['contacts']:
                self.label(self.t('chat_empty_simple'))
            for card in result['contacts']:
                unread = sum(1 for item in result['inbox'] if item['peer'] == card['address'] and not item['read'])
                text = card.get('name') or card['address']
                if unread:
                    text += ' · ' + str(unread)
                self.button(text, lambda card=card: self.conversation(card))
        else:
            self.clear('conversation', self.peer.get('name') or self.peer['address'])
            self.button(self.t('chat_contacts'), self.contacts)
            self.button(self.t('chat_rename'), self.rename)
            if self.offset:
                self.button(self.words('Предыдущие', 'Previous'), lambda: self.page(max(0, self.offset - 50)))
            for message in result['messages']:
                prefix = self.words('Вы', 'You') if message['outgoing'] else self.words('Собеседник', 'Contact')
                text = self.label(prefix + ': ' + (message['text'] if message.get('kind', 'text') == 'text' else
                                                 self.words('[Голосовое сообщение]', '[Voice message]')), True)
                if message.get('kind') == 'audio':
                    self.button(self.t('chat_voice_duration').replace('%1$d', str(message.get('duration_ms', 0) // 1000)),
                                lambda item=message: self.voice.play_message(item['id']))
                if message['outgoing'] and message.get('kind', 'text') == 'text':
                    self.content.remove(text)
                    row = Gtk.Box(spacing=8)
                    text.set_hexpand(True)
                    row.append(text)
                    menu = Gtk.MenuButton(icon_name='view-more-symbolic')
                    menu.set_tooltip_text(self.words('Действия с сообщением', 'Message actions'))
                    menu.add_css_class('fc-chat-menu')
                    popover = Gtk.Popover()
                    action = Gtk.Button(label=self.words('Изменить', 'Edit'))
                    def edit_action(button, item=message, popup=popover):
                        popup.popdown()
                        self.edit(item)
                    action.connect('clicked', edit_action)
                    popover.set_child(action)
                    menu.set_popover(popover)
                    row.append(menu)
                    self.content.append(row)
                self.label(self.delivery_label(message['status']))
            if result['next_offset'] is not None and result['next_offset'] <= 1000:
                self.button(self.words('Следующие', 'Next'), lambda: self.page(result['next_offset']))
            self.compose = self.entry(self.drafts.get(self.peer['address'], ''))
            self.compose.set_placeholder_text(self.t('chat_message_hint'))
            self.compose.connect('changed', lambda widget: self.drafts.update({self.peer['address']: widget.get_text()}))
            self.compose.connect('activate', lambda *_: self.send())
            self.button(self.t('chat_send'), self.send)
            self.content.append(self.voice)
            self.voice.bind(self.peer['address'])
            self.voice.render()
            receipts = [{'id': message['id'], 'revision': message.get('revision', 0)}
                        for message in result['messages'] if not message['outgoing']]
            if receipts and self.visible_peer() == self.peer['address']:
                peer = self.peer['address']
                self.submit(lambda: self.owner.invoke('visible_read', peer=peer, receipts=receipts),
                            lambda _: self.refresh(), interactive=False)

    def service_events(self):
        self.clear('service', self.t('service_events'))
        self.peer = None
        self.offset = 0
        self.last_snapshot = None
        self.refresh()

    def display_events(self, result):
        self.clear('service', self.t('service_events'))
        self.toolbar(back=self.contacts, menu=self.announcements.listing)
        events = result['events']
        if not events:
            self.label(self.t('service_events_empty'))
        if self.offset:
            self.button(self.words('Предыдущие', 'Previous'), lambda: self.page(max(0, self.offset - 50)))
        visible = events
        for event in visible:
            if event.get('publisher'):
                self.label(self.t('exit_official'))
            kind = event.get('kind', 'information')
            self.label(self.t('event_' + kind))
            self.label(event['title'])
            self.label(event['body'], True)
            self.label(self.t('event_valid_until').replace('%1$s', self.event_date(event['expires'])))
            targets = ' · '.join(event['platforms'])
            if 'min_version' in event:
                targets += ' · ' + self.t('event_builds').replace('%1$s', str(event['min_version'])).replace('%2$s', str(event['max_version']))
            self.label(targets)
            if kind == 'update' and self.show_settings:
                self.button(self.t('update_check'), self.show_settings)
            if event.get('revision', 1) > 1:
                self.label(self.t('notice_edited'))
            self.label(event['author'] + ' · ' + self.event_date(event['created']))
        if result['next_offset'] is not None:
            self.button(self.words('Следующие', 'Next'), lambda: self.page(result['next_offset']))
        if self.events_unavailable:
            self.label(self.t('service_events_unavailable'))
        receipts = [{'id': event['id'], 'revision': event.get('revision', 1)} for event in visible if not event['read']]
        if receipts and self.visible_peer() == 'service':
            self.submit(lambda: self.owner.invoke('visible_read', peer='service', receipts=receipts), lambda _: self.refresh(), interactive=False)

    @staticmethod
    def event_date(timestamp):
        try:
            return datetime.fromtimestamp(timestamp).strftime('%x %X')
        except (OverflowError, OSError, ValueError):
            return '—'

    def notification_settings(self):
        def display(settings):
            self.clear('notifications', self.t('chat_notifications'))
            if self.owner_factory is None:
                self.button(self.words('Подготовить защищённый доступ чатов (без VPN)', 'Prepare protected chat access (no VPN)'), self.prepare_services)
            self.delivery_switches = {}
            for field, operation, label in (
                    ('background', 'background_delivery', self.t('chat_background_hint')),
                    ('notifications', 'notification_settings', self.t('chat_enable_notifications'))):
                row = Gtk.Box(spacing=12)
                row.add_css_class('fc-chat-toggle')
                caption = Gtk.Label(label=label, xalign=0, wrap=True, hexpand=True)
                caption.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
                row.append(caption)
                toggle = Gtk.Switch(active=settings[field], valign=Gtk.Align.CENTER)
                toggle.update_property([Gtk.AccessibleProperty.LABEL], [label])
                row.append(toggle)
                self.delivery_switches[field] = toggle
                def changed(widget, spec, operation=operation, field=field):
                    if self.busy:
                        widget.set_active(settings[field])
                        return
                    enabled = widget.get_active()
                    if enabled == settings[field]:
                        return
                    def saved(result):
                        settings.update(result)
                        widget.set_active(result[field])
                        self.settings_changed()
                    self.submit(lambda: self.owner.invoke(operation, enabled=enabled), saved, interactive=False)
                toggle.connect('notify::active', changed)
                self.content.append(row)
            if getattr(self.owner, 'owns_notifications', False):
                self.label(self.words('Фоновая доставка работает в пользовательской службе после закрытия окна. Отключите её здесь, чтобы остановить доставку без открытого чата.',
                    'Background delivery continues in the user service after the window closes. Disable it here to stop delivery when no chat window is open.'))
            else:
                self.label(self.words('Доставка продолжается на других вкладках и при свёрнутом окне. Выход из приложения останавливает мессенджер.',
                    'Delivery continues on other tabs and while minimized. Quitting the app stops messaging.'))
            self.label(self.words('Системные уведомления не содержат текст, аудио или имя контакта.',
                                 'System notifications contain no message text, audio or contact name.'))
            self.button(self.t('chat_contacts'), self.contacts)
        self.submit(lambda: self.owner.invoke('delivery_settings'), display)

    def prepare_services(self):
        from backend import prepare_chat_services
        self.submit(prepare_chat_services, lambda _: self.notice.set_text(self.words(
            'Службы чатов готовы. VPN не включён; настройки фоновой доставки сохранены.',
            'Chat services are ready. VPN is unchanged; background delivery settings are preserved.')))

    def settings_changed(self):
        self.refresh_notifications()
        self.poll()

    def delivery_label(self, status):
        labels = {'queued': ('В очереди', 'Queued'), 'sending': ('Отправляется', 'Sending'),
                  'relayed': ('Принято узлом; получатель ещё не подтвердил', 'Accepted by relay; not yet confirmed by recipient'),
                  'recipient_stored': ('Сохранено получателем', 'Stored by recipient'),
                  'delivered': ('Доставлено', 'Delivered'), 'received': ('Получено', 'Received'),
                  'failed': ('Не доставлено', 'Not delivered'), 'expired': ('Срок доставки истёк', 'Delivery expired')}
        return labels.get(status, (status, status))[0 if self.ru else 1]

    def conversation(self, card):
        self.view_revision += 1
        if self.voice.address != card['address']:
            self.voice.leave()
        self.peer = card
        self.offset = 0
        self.screen = 'conversation'
        self.last_snapshot = None
        self.refresh()

    def page(self, offset):
        self.view_revision += 1
        self.offset = offset
        self.last_snapshot = None
        self.refresh()

    def send(self):
        address, text = self.peer['address'], self.compose.get_text()
        if not text.strip():
            return
        def sent(_):
            self.drafts.pop(address, None)
            self.last_snapshot = None
            self.refresh()
        self.submit(lambda: self.owner.invoke('queue', address=address, text=text), sent)

    def profile(self):
        def display(card):
            self.clear('profile', self.t('chat_profile'))
            self.show_card(card)
            def copy():
                self.get_clipboard().set(card['public'])
                self.notice.set_text(self.t('chat_copied'))
            self.button(self.t('chat_copy_key'), copy)
            self.button(self.t('chat_contacts'), self.contacts)
        self.submit(lambda: self.owner.invoke('profile'), display)

    def show_card(self, card):
        for name, title in (('address', 'chat_address'), ('fingerprint', 'chat_fingerprint'),
                            ('public', 'chat_public_key')):
            self.label(self.t(title)).add_css_class('fc-chat-key-caption')
            value = card[name]
            if name == 'fingerprint':
                value = ' '.join(value[index:index + 4] for index in range(0, len(value), 4))
            self.label(value, True).add_css_class('fc-chat-key-value')

    def add_contact(self):
        self.clear('add', self.t('chat_add'))
        self.label(self.t('chat_key_hint'))
        self.public_input = self.entry(maximum=128)
        def preview():
            public = self.public_input.get_text().strip().lower()
            self.submit(lambda: self.owner.invoke('preview_contact', public=public), self.verify)
        self.public_input.connect('activate', lambda *_: preview())
        self.button(self.t('chat_preview'), preview)
        self.button(self.t('chat_contacts'), self.contacts)
        self.public_input.grab_focus()

    def verify(self, card):
        self.clear('verify', self.t('chat_verify'))
        self.show_card(card)
        self.label(self.t('chat_verify_hint'))
        self.verified = Gtk.CheckButton(label=self.t('chat_verified'))
        self.content.append(self.verified)
        def save():
            if self.verified.get_active():
                self.submit(lambda: self.owner.invoke('trust_contact', public=card['public'], fingerprint=card['fingerprint']), self.conversation)
        self.save_contact = self.button(self.t('chat_save_contact'), save)
        self.save_contact.set_sensitive(False)
        self.verified.connect('toggled', lambda button: self.save_contact.set_sensitive(button.get_active()))
        self.button(self.t('chat_contacts'), self.contacts)

    def rename(self):
        self.clear('rename', self.t('chat_rename'))
        value = self.entry(self.peer.get('name', ''), 80)
        def saved(card):
            self.conversation(card)
        def save():
            name, address = value.get_text(), self.peer['address']
            self.submit(lambda: self.owner.invoke('rename_contact', address=address, name=name), saved)
        self.button(self.words('Сохранить', 'Save'), save)
        self.button(self.t('chat_contacts'), self.contacts)

    def edit(self, message):
        self.clear('edit', self.words('Изменить сообщение', 'Edit message'))
        value = self.entry(message['text'])
        def save():
            text, address = value.get_text(), self.peer['address']
            self.submit(lambda: self.owner.invoke('edit_message', address=address, message_id=message['id'], text=text),
                        lambda _: self.conversation(self.peer))
        self.button(self.words('Сохранить', 'Save'), save)
        self.button(self.t('chat_contacts'), self.contacts)

    def poll(self):
        if self.closing:
            return False
        root = self.get_root()
        foreground = bool(self.active and self.get_mapped() and root and root.is_active())
        if foreground != self.foreground:
            self.foreground = foreground
            self.last_snapshot = None
            self.refresh()
        if self.opened and not self.network_busy:
            online = Gio.NetworkMonitor.get_default().get_network_available()
            self.network(online, foreground)
        self.refresh_notifications()
        return True

    def network(self, online, visible):
        if self.network_busy or self.closing:
            return
        self.network_busy = True
        peer = self.visible_peer()
        def work():
            if hasattr(self.owner, 'foreground'):
                self.owner.foreground(peer)
            return self.owner.tick(online=online, visible=visible, background=True)
        future = self.network_pool.submit(work)
        future.add_done_callback(lambda result: GLib.idle_add(self.network_complete, result))

    def network_complete(self, future):
        self.network_busy = False
        if self.closing:
            return False
        try:
            state = future.result()
        except Exception:
            state = {'registration_error': 'delivery_unavailable'}
        self.delivery_state = state
        changed = self.events_unavailable != bool(state.get('events_unavailable'))
        self.events_unavailable = bool(state.get('events_unavailable'))
        if changed and self.screen == 'service':
            self.last_snapshot = None
        if self.active and not self.screen.startswith('notice-'):
            self.notice.set_text(self.delivery_text())
            self.refresh()
        self.refresh_notifications()
        return False

    def delivery_text(self):
        state = self.delivery_state
        return (self.t('chat_enrollment_unavailable') if state.get('registration_error') or state.get('error') else
                self.words('Доставка через системный маршрут', 'Delivery via the system route') if state.get('route') else
                self.words('Ожидание доставки', 'Waiting for delivery') if state.get('attached') else self.t('chat_local_only'))

    def key_pressed(self, controller, keyval, keycode, modifiers):
        if keyval == Gdk.KEY_Escape and self.opened:
            if self.screen.startswith('notice-') and not self.busy:
                self.announcements.back()
                return True
            if self.voice.state != 'idle' or self.voice.player is not None:
                self.voice.cancel()
                return True
            if not self.busy:
                self.contacts()
                return True
        return False

    def request_close(self, callback):
        if self.closing:
            return
        self.closing = True
        self.notifications.close()
        self.voice.close()
        if self.timer:
            GLib.source_remove(self.timer)
            self.timer = 0
        if self.owner is None and not self.busy:
            self.voice.join()
            self.network_pool.shutdown(wait=False, cancel_futures=True)
            self.pool.shutdown(wait=False, cancel_futures=True)
            callback()
            return
        self.content.set_sensitive(False)
        closing_text = (self.words('Закрываем окно. Фоновая доставка управляется настройками чатов.',
                                  'Closing window. Chat settings control background delivery.')
                        if getattr(self.owner, 'owns_notifications', False) else ERRORS['close_pending'][0 if self.ru else 1])
        self.notice.set_text(closing_text)
        def finish(result):
            try:
                result.result()
            except Exception:
                self.closing = False
                self.content.set_sensitive(True)
                self.notice.set_text(closing_text)
                return False
            self.pool.shutdown(wait=False, cancel_futures=True)
            callback()
            return False
        def close_owner():
            self.voice.join()
            self.network_pool.shutdown(wait=True, cancel_futures=True)
            if self.owner:
                self.owner.close()
        future = self.pool.submit(close_owner)
        future.add_done_callback(lambda result: GLib.idle_add(finish, result))
