"""GTK-only presentation helpers; message text is never normalized."""
from datetime import datetime
import hashlib

from gi.repository import Gdk, GObject, Gtk, Pango

from messenger.codec import MAX_TEXT


def accessible(widget, label):
    widget.set_tooltip_text(label)
    widget.update_property([Gtk.AccessibleProperty.LABEL], [label])
    return widget


def icon_button(icon, label, action):
    button = accessible(Gtk.Button(icon_name=icon), label)
    button.connect('clicked', lambda *_: action())
    return button


def initials(card):
    name = card.get('name', '').strip()
    words = name.split()
    return ''.join(word[0] for word in words[:2]).upper() if words else card['address'][:2].upper()


def preview(message, ru=True):
    if message is None:
        return 'Начните разговор' if ru else 'Start a conversation'
    if message.get('kind') == 'audio':
        return 'Голосовое сообщение' if ru else 'Voice message'
    return ' '.join(message['text'].split())


def stamp(timestamp, pattern='%H:%M'):
    try:
        return datetime.fromtimestamp(timestamp).strftime(pattern)
    except (TypeError, ValueError, OverflowError, OSError):
        return '—'


class Composer(Gtk.TextView):
    __gsignals__ = {'activate': (GObject.SignalFlags.RUN_LAST, None, ())}

    def __init__(self, text='', *, changed=lambda text: None, rejected=lambda: None):
        super().__init__(wrap_mode=Gtk.WrapMode.WORD_CHAR, accepts_tab=False)
        self.add_css_class('messenger-input')
        self.set_top_margin(10)
        self.set_bottom_margin(10)
        self.set_left_margin(10)
        self.set_right_margin(10)
        self.rejected = rejected
        buffer = self.get_buffer()
        buffer.connect('insert-text', self.inserting)
        self.set_text(text)
        buffer.connect('changed', lambda *_: changed(self.get_text()))
        self.keys = Gtk.EventControllerKey()
        self.keys.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        self.keys.connect('key-pressed', self.key_pressed)
        self.add_controller(self.keys)

    def get_text(self):
        buffer = self.get_buffer()
        return buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), True)

    def set_text(self, text):
        if len(text.encode('utf-8')) <= MAX_TEXT:
            self.get_buffer().set_text(text)
        else:
            self.rejected()

    def inserting(self, buffer, location, text, length):
        if len(self.get_text().encode('utf-8')) + len(text.encode('utf-8')) > MAX_TEXT:
            GObject.signal_stop_emission_by_name(buffer, 'insert-text')
            self.rejected()

    def insert_emoji(self, emoji):
        buffer = self.get_buffer()
        selection = buffer.get_selection_bounds()
        selected = buffer.get_text(*selection, True) if selection else ''
        if len(self.get_text().encode('utf-8')) - len(selected.encode('utf-8')) + len(emoji.encode('utf-8')) > MAX_TEXT:
            self.rejected()
            return False
        buffer.begin_user_action()
        if selection:
            buffer.delete(*selection)
        buffer.insert_at_cursor(emoji)
        buffer.end_user_action()
        self.grab_focus()
        return True

    def key_pressed(self, controller, keyval, keycode, modifiers):
        if keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter) and not modifiers & Gdk.ModifierType.SHIFT_MASK:
            if not modifiers & (Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.ALT_MASK | Gdk.ModifierType.SUPER_MASK):
                self.emit('activate')
                return True
        return False


class DialogRow(Gtk.ListBoxRow):
    def __init__(self, card, message, unread, ru):
        super().__init__()
        self.card = card
        name = card.get('name') or card['address'][:12]
        self.search_name = name.casefold()
        row = Gtk.Box(spacing=10)
        row.add_css_class('messenger-dialog')
        avatar = Gtk.Label(label=initials(card))
        avatar.add_css_class('messenger-avatar')
        avatar.add_css_class('avatar-' + str(hashlib.sha256(card['address'].encode()).digest()[0] % 4))
        row.append(avatar)
        labels = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4, hexpand=True)
        title = Gtk.Label(label=name, xalign=0, ellipsize=Pango.EllipsizeMode.END, max_width_chars=18)
        title.add_css_class('heading')
        self.preview = Gtk.Label(label=preview(message, ru), xalign=0, ellipsize=Pango.EllipsizeMode.END, max_width_chars=22)
        self.preview.add_css_class('dim-label')
        labels.append(title)
        labels.append(self.preview)
        row.append(labels)
        trailing = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        timestamp = Gtk.Label(label=stamp(message['timestamp']) if message else '')
        timestamp.add_css_class('caption')
        trailing.append(timestamp)
        self.badge = Gtk.Label(label=str(unread), halign=Gtk.Align.END, visible=bool(unread))
        self.badge.add_css_class('messenger-unread')
        trailing.append(self.badge)
        row.append(trailing)
        self.set_child(row)
        accessible(self, name + (f' · {unread} ' + ('непрочитанных' if ru else 'unread') if unread else ''))


class Bubble(Gtk.Box):
    def __init__(self, pane, message, grouped=False):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.message = message
        self.set_halign(Gtk.Align.END if message['outgoing'] else Gtk.Align.START)
        self.set_margin_top(2 if grouped else 10)
        self.add_css_class('messenger-bubble')
        self.add_css_class('outgoing' if message['outgoing'] else 'incoming')
        if grouped:
            self.add_css_class('grouped')
        if message.get('kind') == 'audio':
            duration = message.get('duration_ms', 0) // 1000
            label = pane.words('Голосовое сообщение', 'Voice message') + f' · {duration // 60}:{duration % 60:02}'
            self.play = icon_button('media-playback-start-symbolic', label, lambda: pane.play_voice(message['id']))
            audio = Gtk.Box(spacing=8)
            audio.append(self.play)
            audio.append(Gtk.Label(label=label, wrap=True, max_width_chars=24))
            self.append(audio)
        else:
            text = Gtk.Label(label=message['text'], xalign=0, wrap=True, selectable=True, max_width_chars=48)
            text.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
            attributes = Pango.AttrList()
            attributes.insert(Pango.attr_insert_hyphens_new(False))
            text.set_attributes(attributes)
            self.append(text)
        footer = Gtk.Box(spacing=8, halign=Gtk.Align.END)
        timestamp = stamp(message['timestamp'])
        if message.get('revision', 0) > 0:
            timestamp += ' · ' + pane.words('изменено', 'edited')
        footer.append(Gtk.Label(label=timestamp, css_classes=['caption', 'dim-label']))
        if message['outgoing']:
            label = pane.delivery_label(message['status'])
            symbols = {'queued': '◷', 'sending': '↑', 'relayed': '↥', 'recipient_stored': '✓', 'delivered': '✓', 'failed': '!', 'expired': '!'}
            footer.append(accessible(Gtk.Label(label=symbols.get(message['status'], '·')), label))
            if message.get('kind', 'text') == 'text':
                self.menu = accessible(Gtk.MenuButton(icon_name='view-more-symbolic'), pane.words('Действия с сообщением', 'Message actions'))
                self.menu.add_css_class('flat')
                popover = Gtk.Popover()
                action = Gtk.Button(label=pane.words('Изменить', 'Edit'))
                action.connect('clicked', lambda *_: (popover.popdown(), pane.edit(message)))
                popover.set_child(action)
                self.menu.set_popover(popover)
                footer.append(self.menu)
        self.append(footer)
