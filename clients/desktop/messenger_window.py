"""One adaptive messenger window in the existing GTK process and chat session."""
import os
from pathlib import Path

from gi.repository import Adw, GLib, Gtk

from chat_ui import ChatPane, ERRORS
from messenger_widgets import Bubble, Composer, DialogRow, accessible, icon_button, stamp
from messenger.codec import MAX_TEXT


CSS = '''
.messenger { background: #101d1d; color: #e2eee8; font-family: sans-serif; }
.messenger .fc-chat { font-size: 1em; }
.messenger-detail { background: #101d1d; }
.messenger .fc-chat-title { font-size: 1.25em; font-weight: bold; }
.messenger-sidebar { background: #142323; border-right: 1px solid #2c4140; }
.messenger-header { padding: 12px; }
.messenger-dialog { padding: 12px 10px; }
.messenger list { background: transparent; }
.messenger row:selected { background: #294541; }
.messenger button { border-radius: 10px; min-height: 28px; }
.messenger-avatar { min-width: 40px; min-height: 40px; border-radius: 20px; background: #375b56; font-weight: bold; }
.messenger .avatar-1 { background: #4f4866; }
.messenger .avatar-2 { background: #615243; }
.messenger .avatar-3 { background: #345267; }
.messenger-unread { background: #8bcbb5; color: #102321; border-radius: 10px; padding: 1px 6px; font-size: .85em; }
.messenger-bubble { border-radius: 16px; padding: 10px 12px 6px; }
.messenger-bubble.incoming { background: #243534; margin-right: 32px; }
.messenger-bubble.outgoing { background: #294c44; margin-left: 32px; }
.messenger-bubble.grouped { border-top-left-radius: 9px; border-top-right-radius: 9px; }
.messenger-bubble button { padding: 2px; min-height: 24px; min-width: 24px; }
.messenger .caption { font-size: .8em; }
.messenger-composer { padding: 10px 12px; border-top: 1px solid #2c4140; background: #142323; }
.messenger-input, .messenger-input text { background: #203432; color: #e2eee8; border-radius: 12px; }
.messenger-status { margin: 8px 12px; padding: 12px; background: #243534; border-radius: 12px; }
.messenger .fc-action { font-family: sans-serif; font-size: 1em; border-radius: 10px; }
.messenger .fc-chat-toolbar button { background: #243534; color: #e2eee8; padding: 4px; border: none; }
.messenger .suggested-action { background: #8bcbb5; color: #102321; }
.messenger .fc-caption { font-family: sans-serif; font-size: .85em; }
'''


def preparation_status():
    from backend import system_component_status
    component = system_component_status()
    prepared = all((Path('/run') / directory / (str(os.getuid()) + '.chat.sock')).is_socket()
                   for directory in ('family-connect-chat-direct', 'family-connect-chat-mesh'))
    return component, prepared


class MessengerPane(ChatPane):
    def __init__(self, **options):
        self.component, self.prepared = 'UNKNOWN', False
        self.open_error = None
        self.status_busy = False
        self.sidebar_snapshot = None
        self.loaded_contacts = 50
        self.displayed_address = None
        super().__init__(**options)
        for child in (self.heading, self.content, self.notice):
            self.remove(child)
        self.set_spacing(0)
        self.split = Adw.Leaflet(can_unfold=True, can_navigate_back=True, can_navigate_forward=False)
        self.split.set_transition_type(Adw.LeafletTransitionType.SLIDE)
        self.split.set_vexpand(True)
        self.append(self.split)
        self.sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.sidebar.set_size_request(280, -1)
        self.sidebar.set_hexpand(False)
        self.sidebar.add_css_class('messenger-sidebar')
        self.split.append(self.sidebar).set_name('dialogs')
        self.detail = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, hexpand=True)
        self.detail.set_size_request(320, -1)
        self.detail.add_css_class('messenger-detail')
        self.split.append(self.detail).set_name('conversation')
        self.sidebar_header = Gtk.Box(spacing=8)
        self.sidebar_header.add_css_class('messenger-header')
        self.sidebar_title = Gtk.Label(xalign=0, hexpand=True, css_classes=['title-3'])
        self.sidebar_header.append(self.sidebar_title)
        self.add_button = icon_button('list-add-symbolic', '', self.add_contact)
        self.sidebar_header.append(self.add_button)
        self.options = Gtk.MenuButton(icon_name='open-menu-symbolic')
        self.sidebar_header.append(self.options)
        self.sidebar.append(self.sidebar_header)
        self.search = Gtk.SearchEntry(placeholder_text='Поиск')
        self.search.set_margin_start(12)
        self.search.set_margin_end(12)
        self.search.connect('search-changed', lambda *_: self.dialogs.invalidate_filter())
        self.sidebar.append(self.search)
        self.dialogs = Gtk.ListBox(selection_mode=Gtk.SelectionMode.SINGLE)
        self.dialogs.set_filter_func(lambda row: self.search.get_text().casefold() in row.search_name)
        self.dialogs.connect('row-activated', lambda box, row: self.service_events() if row.card['address'] == 'service' else self.conversation(row.card))
        self.sidebar_scroll = Gtk.ScrolledWindow(vexpand=True, hscrollbar_policy=Gtk.PolicyType.NEVER)
        self.sidebar_scroll.set_child(self.dialogs)
        self.sidebar.append(self.sidebar_scroll)
        self.more_contacts = Gtk.Button(label='Ещё контакты')
        self.more_contacts.connect('clicked', self.load_contacts)
        self.sidebar.append(self.more_contacts)
        self.heading.add_css_class('messenger-header')
        self.header_back.set_size_request(32, 32)
        self.header_menu.set_size_request(32, 32)
        self.detail.append(self.heading)
        self.status_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.status_card.add_css_class('messenger-status')
        self.status_label = Gtk.Label(xalign=0, wrap=True)
        self.status_action = Gtk.Button()
        self.status_action.connect('clicked', lambda *_: self.onboarding_action())
        self.status_card.append(self.status_label)
        self.status_card.append(self.status_action)
        self.detail.append(self.status_card)
        self.notice.set_margin_start(12)
        self.notice.set_margin_end(12)
        self.notice.set_lines(3)
        self.detail.append(self.notice)
        self.messages_scroll = Gtk.ScrolledWindow(vexpand=True, hscrollbar_policy=Gtk.PolicyType.NEVER)
        self.follow_bottom = True
        self.messages_scroll.get_vadjustment().connect('changed', self.history_layout)
        for edge in ('start', 'end', 'top', 'bottom'):
            getattr(self.content, 'set_margin_' + edge)(12)
        self.messages_scroll.set_child(self.content)
        self.detail.append(self.messages_scroll)
        self.composer_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6, visible=False)
        self.composer_box.add_css_class('messenger-composer')
        self.detail.append(self.composer_box)
        self.split.connect('notify::folded', lambda *_: self.navigation())
        self.split.connect('notify::visible-child', self.navigation_changed)
        self.localize()
        self.welcome()

    def localize(self):
        self.sidebar_title.set_text(self.t('chat_dialogs'))
        accessible(self.add_button, self.t('chat_add'))
        accessible(self.options, self.t('chat_menu'))
        accessible(self.search, self.words('Поиск в загруженных контактах', 'Search loaded contacts'))
        self.search.set_placeholder_text(self.words('Поиск', 'Search'))
        self.more_contacts.set_label(self.words('Ещё контакты', 'More contacts'))
        popover = Gtk.Popover()
        actions = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        for label, action in ((self.t('chat_profile'), self.profile), (self.t('chat_background'), self.notification_settings)):
            button = Gtk.Button(label=label)
            button.connect('clicked', lambda *_, action=action: (popover.popdown(), action()))
            actions.append(button)
        popover.set_child(actions)
        self.options.set_popover(popover)

    def clear(self, screen, title):
        super().clear(screen, title)
        if hasattr(self, 'split'):
            if screen != 'conversation':
                self.displayed_address = None
                self.composer_box.set_visible(False)
            self.split.set_visible_child(self.detail)
            self.navigation()

    def navigation(self):
        menu = self.rename if self.screen == 'conversation' else self.announcements.listing if self.screen == 'service' else self.menu_action
        back = self.contacts if self.screen in ('contacts', 'conversation') else self.back_action or self.contacts
        self.toolbar(back=back if self.split.get_folded() or self.screen not in ('contacts', 'conversation') else None, menu=menu)
        if self.screen == 'conversation':
            accessible(self.header_menu, self.t('chat_rename'))

    def navigation_changed(self, *_):
        if self.split.get_visible_child() == self.sidebar and self.screen == 'conversation':
            self.voice.leave()
            self.view_revision += 1
            self.screen = 'contacts'
            self.peer = None
            self.displayed_address = None
            self.composer_box.set_visible(False)
            self.last_snapshot = None
        self.navigation()

    def activate(self, active, ru):
        changed = self.ru != ru
        super().activate(active, ru)
        if active and self.owner is not None and not self.opened and not self.busy:
            self.open(False)
        if changed:
            self.localize()
            self.voice.render()
            self.sidebar_snapshot = None
            self.displayed_address = None
        if active:
            self.check_preparation()

    def check_preparation(self):
        if self.owner_factory is not None:
            self.component, self.prepared = 'READY', True
            self.onboarding()
            return
        if self.status_busy or self.closing:
            return
        self.status_busy = True
        future = self.pool.submit(preparation_status)
        def finished(result):
            self.status_busy = False
            if not self.closing:
                try:
                    self.component, self.prepared = result.result()
                except Exception:
                    self.component, self.prepared = 'UNKNOWN', False
                self.onboarding()
            return False
        future.add_done_callback(lambda result: GLib.idle_add(finished, result))

    def onboarding(self):
        if not hasattr(self, 'status_card'):
            return
        self.onboarding_kind = ('activation' if self.open_error == 'identity_unavailable' else
                                'keyring' if self.open_error == 'keyring_unavailable' else
                                'system' if self.component != 'READY' else
                                'prepare' if not self.prepared else
                                'create' if not self.opened and self.open_error in (None, 'not_created') else
                                'retry' if not self.opened else 'ready')
        labels = {
            'activation': ('Активируйте этот компьютер', 'Activate this computer', 'Открыть настройки', 'Open Settings'),
            'system': ('Для сообщений нужны системные компоненты.', 'Messaging needs system components.', 'Установить компоненты сообщений', 'Install messaging components'),
            'prepare': ('Остался один шаг перед доставкой сообщений.', 'One more step before messages can be delivered.', 'Включить защищённые сообщения', 'Enable secure messaging'),
            'keyring': ('Разблокируйте системное хранилище ключей. История и ключи сохранены.', 'Unlock the system keyring. History and keys are preserved.', 'Повторить', 'Retry'),
            'create': ('Личные разговоры, всегда под рукой.', 'Your private conversations, close at hand.', 'Начать общение', 'Start messaging'),
            'retry': ('Сообщения пока недоступны. Сохранённые данные не изменены.', 'Messages are unavailable. Saved data is unchanged.', 'Повторить', 'Retry'),
        }
        self.status_card.set_visible(self.onboarding_kind != 'ready')
        self.add_button.set_sensitive(self.opened and not self.busy)
        self.options.set_sensitive(self.opened and not self.busy)
        if self.onboarding_kind in labels:
            ru, en, action_ru, action_en = labels[self.onboarding_kind]
            self.status_label.set_text(self.words(ru, en))
            self.status_action.set_label(self.words(action_ru, action_en))
            accessible(self.status_action, self.words(action_ru, action_en))
            self.status_action.set_sensitive(not self.busy)

    def onboarding_action(self):
        if self.busy or self.closing:
            return
        actions = {'activation': self.show_settings, 'system': self.setup_system,
                   'prepare': self.prepare_services, 'create': lambda: self.open(True),
                   'keyring': lambda: self.open(getattr(self, 'open_mode', False)), 'retry': lambda: self.open(False)}
        action = actions.get(self.onboarding_kind)
        if action:
            action()

    def prepare_services(self):
        from backend import prepare_chat_services
        self.submit(prepare_chat_services, lambda _: self.check_preparation())

    def setup_system(self):
        from backend import setup_candidate_system
        self.submit(setup_candidate_system, lambda _: self.check_preparation())

    def welcome(self):
        if not hasattr(self, 'split'):
            return super().welcome()
        self.clear('welcome', self.t('chat_title'))
        self.notice.set_text('')
        self.label(self.words('Ваши разговоры появятся здесь.', 'Your conversations will appear here.'))
        self.onboarding()

    def contacts(self):
        super().contacts()
        self.clear('contacts', self.t('chat_title'))
        self.label(self.words('Выберите разговор или добавьте контакт.', 'Choose a conversation or add a contact.'))
        self.split.set_visible_child(self.sidebar if self.opened else self.detail)
        self.composer_box.set_visible(False)

    def load_contacts(self, *_):
        self.loaded_contacts += 50
        self.last_snapshot = None
        self.refresh()

    def history_layout(self, adjustment):
        if self.follow_bottom:
            adjustment.set_value(max(0, adjustment.get_upper() - adjustment.get_page_size()))

    def snapshot(self, address, offset):
        sidebar = super().snapshot(None, 0)
        cards = sidebar['contacts'][:self.loaded_contacts]
        previews = {}
        for card in cards:
            peer = card['address']
            first = self.owner.invoke('history', address=peer, offset=0, limit=1)
            if first['total'] > 1:
                last = first['total'] - 1
                previews[peer] = (self.owner.invoke('history', address=peer, offset=last, limit=1)['messages'][0]
                                  if last <= 1000 else dict(text=self.words('Откройте историю', 'Open history'), timestamp=None))
            else:
                previews[peer] = next(iter(first['messages']), None)
        sidebar['previews'] = previews
        return {'sidebar': sidebar, 'page': super().snapshot(address, offset) if address else None}

    def display_sidebar(self, result):
        if self.sidebar_snapshot == result:
            return
        self.sidebar_snapshot = result
        while self.dialogs.get_first_child() is not None:
            self.dialogs.remove(self.dialogs.get_first_child())
        for card in result['contacts'][:self.loaded_contacts]:
            unread = sum(item['peer'] == card['address'] and not item['read'] for item in result['inbox'])
            row = DialogRow(card, result['previews'][card['address']], unread, self.ru)
            self.dialogs.append(row)
        service = DialogRow({'address': 'service', 'name': self.words('События', 'Events')}, None, result['events']['unread'], self.ru)
        service.preview.set_text(self.words('Новости и уведомления', 'News and notifications'))
        self.dialogs.append(service)
        self.more_contacts.set_visible(len(result['contacts']) > self.loaded_contacts)
        self.onboarding()

    def select_dialog(self):
        row = self.dialogs.get_first_child()
        selected = self.peer['address'] if self.peer else 'service' if self.screen == 'service' else None
        self.dialogs.unselect_all()
        while row is not None:
            if row.card['address'] == selected:
                self.dialogs.select_row(row)
            row = row.get_next_sibling()

    def display(self, result):
        self.display_sidebar(result['sidebar'])
        self.select_dialog()
        if self.voice.state != 'idle' or self.voice.pointer or self.voice.press_timer:
            return
        if result == self.last_snapshot:
            return
        self.last_snapshot = result
        if self.screen == 'service':
            self.display_events(result['page'])
            return
        if self.peer is None:
            if not result['sidebar']['contacts']:
                self.clear('contacts', self.t('chat_title'))
                self.label(self.words('Начните с близких', 'Start with someone close'))
                self.label(self.words('Добавьте проверенный контакт, чтобы начать защищённый разговор.', 'Add a verified contact to start a secure conversation.'))
                self.button(self.t('chat_add'), self.add_contact)
            return
        page = result['page']
        address = self.peer['address']
        new_conversation = self.displayed_address != address
        adjustment = self.messages_scroll.get_vadjustment()
        at_bottom = adjustment.get_value() + adjustment.get_page_size() >= adjustment.get_upper() - 30
        position = adjustment.get_value()
        self.follow_bottom = new_conversation or at_bottom
        while self.content.get_first_child() is not None:
            self.content.remove(self.content.get_first_child())
        self.title.set_text(self.peer.get('name') or address[:12])
        self.navigation()
        if self.offset:
            self.button(self.words('Раньше', 'Earlier'), lambda: self.page(max(0, self.offset - 50)))
        previous = None
        for message in page['messages']:
            date = stamp(message['timestamp'], '%d %B %Y')
            same_date = previous is not None and date == stamp(previous['timestamp'], '%d %B %Y')
            if not same_date:
                separator = self.label(date)
                separator.set_halign(Gtk.Align.CENTER)
                separator.add_css_class('caption')
                separator.add_css_class('dim-label')
            grouped = same_date and previous['outgoing'] == message['outgoing'] and abs(message['timestamp'] - previous['timestamp']) < 300
            self.content.append(Bubble(self, message, grouped))
            previous = message
        if page['next_offset'] is not None and page['next_offset'] <= 1000:
            self.button(self.words('Позже', 'Later'), lambda: self.page(page['next_offset']))
        if new_conversation:
            self.build_composer(address)
            self.displayed_address = address
        self.composer_box.set_visible(True)
        self.voice.bind(address)
        self.split.set_visible_child(self.detail)
        def scroll():
            adjustment.set_value(adjustment.get_upper() - adjustment.get_page_size() if new_conversation or at_bottom else position)
            return False
        GLib.idle_add(scroll)
        receipts = [{'id': message['id'], 'revision': message.get('revision', 0)} for message in page['messages'] if not message['outgoing']]
        if receipts and self.visible_peer() == address:
            self.submit(lambda: self.owner.invoke('visible_read', peer=address, receipts=receipts), lambda _: self.refresh(), interactive=False)

    def build_composer(self, address):
        if self.voice.get_parent() is not None:
            self.voice.get_parent().remove(self.voice)
        while self.composer_box.get_first_child() is not None:
            self.composer_box.remove(self.composer_box.get_first_child())
        self.byte_count = Gtk.Label(xalign=1, visible=False, css_classes=['caption'])
        hint = Gtk.Label(label=self.words('Сообщение…', 'Message…'), halign=Gtk.Align.START, valign=Gtk.Align.START,
                         margin_start=10, margin_top=10, css_classes=['dim-label'], can_target=False)
        def changed(text):
            self.drafts[address] = text
            hint.set_visible(not text)
            size = len(text.encode('utf-8'))
            self.byte_count.set_text(f'{size} / {MAX_TEXT} ' + self.words('байт', 'bytes'))
            self.byte_count.set_visible(size >= 3500)
        def rejected():
            self.notice.set_text(self.words('Не больше 4096 байт. Текст не отправлен.', 'Maximum 4096 bytes. Text was not sent.'))
        self.compose = accessible(Composer(self.drafts.get(address, ''), changed=changed, rejected=rejected),
                                  self.words('Сообщение. Enter — отправить, Shift+Enter — новая строка.', 'Message. Enter to send, Shift+Enter for a new line.'))
        self.compose.connect('activate', lambda *_: self.send())
        scroll = Gtk.ScrolledWindow(hexpand=True, hscrollbar_policy=Gtk.PolicyType.NEVER,
                                   min_content_height=44, max_content_height=120, propagate_natural_height=True)
        scroll.set_child(self.compose)
        overlay = Gtk.Overlay()
        overlay.set_child(scroll)
        overlay.add_overlay(hint)
        self.composer_box.append(overlay)
        controls = Gtk.Box(spacing=8)
        self.emoji_button = accessible(Gtk.MenuButton(icon_name='face-smile-symbolic'), self.words('Выбрать эмодзи', 'Choose emoji'))
        self.emoji = Gtk.EmojiChooser()
        self.emoji.set_position(Gtk.PositionType.TOP)
        self.emoji.connect('emoji-picked', lambda chooser, emoji: self.compose.insert_emoji(emoji))
        self.emoji.connect('closed', lambda *_: self.compose.grab_focus())
        self.emoji_button.set_popover(self.emoji)
        self.emoji_button.set_direction(Gtk.ArrowType.UP)
        controls.append(self.emoji_button)
        self.voice_button = icon_button('audio-input-microphone-symbolic', self.words('Голосовое сообщение', 'Voice message'), self.show_voice)
        controls.append(self.voice_button)
        self.byte_count.set_hexpand(True)
        controls.append(self.byte_count)
        spacer = Gtk.Box(hexpand=True)
        controls.append(spacer)
        self.send_button = icon_button('mail-send-symbolic', self.t('chat_send'), self.send)
        self.send_button.add_css_class('suggested-action')
        controls.append(self.send_button)
        self.composer_box.append(controls)
        self.composer_box.append(self.voice)
        self.voice.render()
        self.voice.set_visible(False)
        changed(self.compose.get_text())

    def show_voice(self):
        self.voice.set_visible(True)
        self.voice.record.grab_focus()

    def send(self):
        if self.busy or self.closing or self.peer is None:
            return
        address, text = self.peer['address'], self.compose.get_text()
        if not text.strip() or len(text.encode('utf-8')) > MAX_TEXT:
            return
        self.composer_box.set_sensitive(False)
        def sent(_):
            self.drafts.pop(address, None)
            if self.peer and self.peer['address'] == address:
                self.compose.set_text('')
                self.drafts.pop(address, None)
                self.compose.grab_focus()
            self.last_snapshot = None
            self.refresh()
        def restored(result):
            self.composer_box.set_sensitive(True)
            sent(result)
        self.submit(lambda: self.owner.invoke('queue', address=address, text=text), restored)

    def complete(self, future, callback):
        try:
            future.result()
        except Exception as failure:
            self.open_error = str(failure)
            if not self.opened and not self.closing:
                self.busy = False
                self.content.set_sensitive(True)
                self.welcome()
                if self.open_error not in ('not_created', 'identity_unavailable', 'keyring_unavailable'):
                    self.notice.set_text(ERRORS.get(self.open_error, ERRORS['store_unavailable'])[0 if self.ru else 1])
                return False
        else:
            self.open_error = None
        result = super().complete(future, callback)
        if self.notice.get_text() == self.t('chat_local_only'):
            self.notice.set_text('')
        if hasattr(self, 'composer_box') and not self.closing:
            self.composer_box.set_sensitive(True)
        self.onboarding()
        return result

    def edit(self, message):
        self.clear('edit', self.words('Изменить сообщение', 'Edit message'))
        value = Composer(message['text'], rejected=lambda: self.notice.set_text(self.words('Не больше 4096 байт.', 'Maximum 4096 bytes.')))
        accessible(value, self.words('Текст сообщения', 'Message text'))
        self.content.append(value)
        card = self.peer
        def save():
            text = value.get_text()
            if text.strip():
                self.submit(lambda: self.owner.invoke('edit_message', address=card['address'], message_id=message['id'], text=text),
                            lambda _: self.conversation(card))
        self.button(self.words('Сохранить', 'Save'), save)
        self.button(self.words('Отмена', 'Cancel'), lambda: self.conversation(card))

    def play_voice(self, message_id):
        self.voice.set_visible(True)
        self.voice.play_message(message_id)

    def delivery_text(self):
        if self.delivery_state.get('registration_error') or self.delivery_state.get('error'):
            return self.words('Пока не удалось доставить сообщения. История и черновики сохранены.', 'Messages cannot be delivered yet. History and drafts are safe.')
        return ''


class MessengerWindow(Adw.ApplicationWindow):
    def __init__(self, application=None, *, show_settings=None, **options):
        super().__init__(application=application, title='Family Connect · Чаты', default_width=900, default_height=680)
        self.add_css_class('messenger')
        self.pane = MessengerPane(show_chat=self.present_chat, show_settings=show_settings, **options)
        shell = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        shell.append(Adw.HeaderBar(title_widget=Gtk.Label(label='Family Connect')))
        shell.append(self.pane)
        self.set_content(shell)
        self.provider = Gtk.CssProvider()
        self.provider.load_from_data(CSS.encode())
        Gtk.StyleContext.add_provider_for_display(self.get_display(), self.provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 1)
        self.connect('close-request', self.hide_chat)

    def present_chat(self, ru=None):
        self.present()
        self.pane.activate(True, self.pane.ru if ru is None else ru)

    def hide_chat(self, *_):
        self.pane.activate(False, self.pane.ru)
        self.set_visible(False)
        self.pane.poll()
        return True

    def dispose_window(self):
        Gtk.StyleContext.remove_provider_for_display(self.get_display(), self.provider)
        self.destroy()
