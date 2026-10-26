import os
import time

import pytest

pytest.importorskip('gi')
pytestmark = pytest.mark.skipif(not os.environ.get('DISPLAY'), reason='Real GTK display required')

from app import Adw, Gdk, GLib, Gtk
from messenger_window import MessengerWindow
from messenger_widgets import Bubble, Composer, DialogRow, initials, preview
from messenger_fixture import ChatFixture


def pump(seconds=.1):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        while GLib.MainContext.default().pending():
            GLib.MainContext.default().iteration(False)
        time.sleep(.005)


def settle(pane):
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        pump()
        if not (pane.busy or pane.network_busy or pane.voice.busy or getattr(pane, 'status_busy', False)):
            return
    raise AssertionError('UI operation did not settle')


@pytest.fixture
def window():
    Adw.init()
    Gtk.Settings.get_default().set_property('gtk-enable-animations', False)
    fixture = ChatFixture()
    created = []
    def factory():
        created.append(fixture)
        return fixture
    window = MessengerWindow(owner_factory=factory)
    window.present_chat()
    settle(window.pane)
    window.pane.conversation(fixture.cards[0])
    settle(window.pane)
    yield window, fixture, created
    closed = []
    window.pane.request_close(lambda: closed.append(True))
    for attempt in range(100):
        pump(.02)
        if closed:
            break
    assert closed
    window.dispose_window()


def test_emoji_at_cursor_and_replaces_selection(window):
    pane = window[0].pane
    pane.compose.set_text('Привет мир')
    buffer = pane.compose.get_buffer()
    buffer.place_cursor(buffer.get_iter_at_offset(7))
    pane.emoji.emit('emoji-picked', '🙂')
    assert pane.compose.get_text() == 'Привет 🙂мир'
    buffer.select_range(buffer.get_iter_at_offset(7), buffer.get_end_iter())
    pane.emoji.emit('emoji-picked', '👩🏽‍💻🌿')
    assert pane.compose.get_text() == 'Привет 👩🏽‍💻🌿'
    assert window[0].get_focus() == pane.compose


@pytest.mark.parametrize('text', ['🙂' * 1024, 'я' * 2048, 'я🙂' * 682 + 'аб', 'a' * 4096])
def test_byte_boundary(text, window):
    composer = window[0].pane.compose
    composer.set_text(text)
    assert len(composer.get_text().encode()) == 4096
    assert not composer.insert_emoji('✨')
    assert composer.get_text() == text
    buffer = composer.get_buffer()
    buffer.insert_at_cursor('x')
    assert composer.get_text() == text
    buffer.select_range(buffer.get_start_iter(), buffer.get_end_iter())
    assert composer.insert_emoji('🙂')
    assert composer.get_text() == '🙂'


def test_mixed_text_no_normalization_or_duplicate_send(window):
    pane, fixture = window[0].pane, window[1]
    text = '  Привет 👨‍👩‍👧‍👦🙂🇧🇪 е\u0301\n✨  '
    pane.compose.set_text(text)
    pane.compose.emit('activate')
    pane.send()
    settle(pane)
    assert [arguments['text'] for operation, arguments in fixture.calls if operation == 'queue'] == [text]
    assert fixture.messages[-1]['text'] == text
    assert pane.compose.get_text() == ''
    assert fixture.cards[0]['address'] not in pane.drafts


def test_draft_survives_switch_failure_and_close(window):
    messenger, fixture, created = window
    pane = messenger.pane
    pane.compose.set_text('Черновик 🙂')
    pane.conversation(fixture.cards[1])
    settle(pane)
    pane.compose.set_text('Другой')
    pane.conversation(fixture.cards[0])
    settle(pane)
    assert pane.compose.get_text() == 'Черновик 🙂'
    fixture.fail_send = True
    pane.send()
    settle(pane)
    assert pane.compose.get_text() == 'Черновик 🙂'
    assert pane.composer_box.get_sensitive()
    messenger.close()
    settle(pane)
    assert not messenger.get_visible()
    assert fixture.heartbeats[-1]['visible'] is False
    messenger.present_chat()
    settle(pane)
    assert pane.compose.get_text() == 'Черновик 🙂'
    assert len(created) == fixture.open_count == 1
    assert fixture.close_count == 0


def test_enter_shift_enter_and_whitespace(window):
    pane = window[0].pane
    pane.compose.set_text('  \n')
    assert pane.compose.key_pressed(None, Gdk.KEY_Return, 0, 0)
    assert not any(operation == 'queue' for operation, _ in window[1].calls)
    assert not pane.compose.key_pressed(None, Gdk.KEY_Return, 0, Gdk.ModifierType.SHIFT_MASK)
    pane.compose.set_text('yes')
    assert pane.compose.key_pressed(None, Gdk.KEY_KP_Enter, 0, 0)
    settle(pane)
    assert sum(operation == 'queue' for operation, _ in window[1].calls) == 1


def test_real_shift_enter_key_and_keyboard_send(window):
    import ctypes
    import ctypes.util
    from chat_notifications_check import key
    pane = window[0].pane
    pane.compose.set_text('первая')
    pane.compose.get_buffer().place_cursor(pane.compose.get_buffer().get_end_iter())
    pane.compose.grab_focus()
    pump()
    x11 = ctypes.CDLL(ctypes.util.find_library('X11'))
    xtest = ctypes.CDLL(ctypes.util.find_library('Xtst'))
    x11.XOpenDisplay.argtypes, x11.XOpenDisplay.restype = [ctypes.c_char_p], ctypes.c_void_p
    x11.XKeysymToKeycode.argtypes, x11.XKeysymToKeycode.restype = [ctypes.c_void_p, ctypes.c_ulong], ctypes.c_uint
    x11.XFlush.argtypes = x11.XCloseDisplay.argtypes = [ctypes.c_void_p]
    xtest.XTestFakeKeyEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_int, ctypes.c_ulong]
    display = x11.XOpenDisplay(os.environ['DISPLAY'].encode())
    try:
        shift = x11.XKeysymToKeycode(display, Gdk.KEY_Shift_L)
        xtest.XTestFakeKeyEvent(display, shift, 1, 0)
        x11.XFlush(display)
        key(Gdk.KEY_Return)
        xtest.XTestFakeKeyEvent(display, shift, 0, 0)
        x11.XFlush(display)
        pump()
        assert pane.compose.get_text() == 'первая\n'
        pane.compose.insert_emoji('🙂')
        key(Gdk.KEY_Return)
        settle(pane)
        assert window[1].messages[-1]['text'] == 'первая\n🙂'
        assert sum(operation == 'queue' for operation, _ in window[1].calls) == 1
    finally:
        x11.XCloseDisplay(display)


def test_pagination_keeps_composer_and_local_search(window):
    pane, fixture = window[0].pane, window[1]
    fixture.messages = [dict(fixture.messages[0], id=f'{index:064x}', text=f'Сообщение {index}', timestamp=1793008800 + index)
                        for index in range(65)]
    pane.compose.set_text('Черновик')
    pane.last_snapshot = None
    pane.refresh()
    settle(pane)
    composer = pane.compose
    pane.page(50)
    settle(pane)
    assert pane.compose is composer and composer.get_text() == 'Черновик'
    assert len([child for child in children(pane.content) if isinstance(child, Bubble)]) == 15
    pane.search.set_text('МИХАИЛ')
    pump(.3)
    assert not pane.dialogs.get_row_at_index(0).get_child_visible()
    assert pane.dialogs.get_row_at_index(1).get_child_visible()


def children(widget):
    child = widget.get_first_child()
    while child is not None:
        yield child
        child = child.get_next_sibling()


def test_bubbles_delivery_preview_edit_voice_and_badge(window):
    pane = window[0].pane
    bubbles = [child for child in children(pane.content) if isinstance(child, Bubble)]
    assert len(bubbles) == 5
    assert bubbles[0].get_halign() == Gtk.Align.START
    assert bubbles[2].get_halign() == Gtk.Align.END
    assert bubbles[1].has_css_class('grouped')
    assert not bubbles[3].has_css_class('grouped')
    assert bubbles[0].get_first_child().get_selectable()
    assert 'изменено' in bubbles[2].get_last_child().get_first_child().get_text()
    assert pane.dialogs.get_row_at_index(1).badge.get_text() == '1'
    assert pane.dialogs.get_row_at_index(1).badge.get_visible()
    assert pane.dialogs.get_selected_row().card == window[1].cards[0]
    assert pane.dialogs.get_row_at_index(0).preview.get_text() == 'До завтра! ✨'
    assert preview(window[1].messages[3]) == 'Голосовое сообщение'
    assert initials(window[1].cards[0]) == 'АЛ'
    played = []
    pane.voice.play_message = played.append
    bubbles[3].play.emit('clicked')
    assert played == [window[1].messages[3]['id']]
    assert pane.voice.get_visible()
    bubbles[2].menu.get_popover().get_child().emit('clicked')
    assert pane.screen == 'edit'
    pane.content.get_first_child().set_text('Изменено 🙂')
    list(children(pane.content))[1].emit('clicked')
    settle(pane)
    assert window[1].messages[2]['text'] == 'Изменено 🙂'
    assert window[1].messages[2]['revision'] == 2


@pytest.mark.parametrize('status,label', [('queued', 'В очереди'), ('sending', 'Отправляется'), ('relayed', 'Принято узлом; получатель ещё не подтвердил'), ('recipient_stored', 'Сохранено получателем'), ('delivered', 'Доставлено'), ('failed', 'Не доставлено'), ('expired', 'Срок доставки истёк')])
def test_delivery_label_never_claims_read(window, status, label):
    assert window[0].pane.delivery_label(status) == label


@pytest.mark.parametrize('error,component,prepared,opened,expected', [
    ('identity_unavailable', 'MISSING', False, False, 'activation'),
    ('keyring_unavailable', 'READY', True, False, 'keyring'),
    (None, 'MISSING', False, True, 'system'),
    (None, 'READY', False, True, 'prepare'),
    ('not_created', 'READY', True, False, 'create'),
    (None, 'READY', True, True, 'ready'),
])
def test_onboarding_one_explicit_action(window, error, component, prepared, opened, expected):
    pane = window[0].pane
    pane.open_error, pane.component, pane.prepared, pane.opened = error, component, prepared, opened
    called = []
    pane.show_settings = lambda: called.append('activation')
    pane.setup_system = lambda: called.append('system')
    pane.prepare_services = lambda: called.append('prepare')
    pane.open = lambda create: called.append(('open', create))
    pane.onboarding()
    assert pane.onboarding_kind == expected
    assert pane.status_card.get_visible() == (expected != 'ready')
    pane.onboarding_action()
    assert called == ([] if expected == 'ready' else [('open', True)] if expected == 'create' else [('open', False)] if expected == 'keyring' else [expected])


def test_keyboard_labels_and_narrow_navigation(window):
    messenger, fixture, _ = window
    pane = messenger.pane
    for button in (pane.emoji_button, pane.voice_button, pane.send_button, pane.add_button, pane.header_menu):
        assert button.get_tooltip_text()
    pane.compose.grab_focus()
    assert messenger.child_focus(Gtk.DirectionType.TAB_FORWARD)
    messenger.set_default_size(360, 680)
    pump(.3)
    assert pane.split.get_folded()
    assert pane.header_back.get_visible()
    assert pane.composer_box.get_mapped()
    pane.header_back.emit('clicked')
    settle(pane)
    assert pane.split.get_visible_child() == pane.sidebar
    pane.dialogs.emit('row-activated', pane.dialogs.get_row_at_index(0))
    settle(pane)
    assert pane.split.get_visible_child() == pane.detail


def test_app_navigation_and_deep_link_reuse_one_window(monkeypatch):
    from app import App
    fixture = ChatFixture()
    app = App(smoke=True)
    pane = app.chat_pane
    pane.owner_factory = lambda: fixture
    app.select_page('messenger')
    pane.activate(True, True)
    settle(pane)
    messenger = app.messenger_window
    original_size = app.window.get_default_size()
    app.open_chat(fixture.cards[0]['address'])
    pump(.3)
    settle(pane)
    assert pane.peer['address'] == fixture.cards[0]['address']
    messenger.close()
    app.open_chat(fixture.cards[1]['address'])
    pump(.3)
    settle(pane)
    assert app.messenger_window is messenger and fixture.open_count == 1
    assert app.window.get_default_size() == original_size
    app.close(True)
    for attempt in range(100):
        pump(.03)
        if app.closed:
            break
    assert app.closed and fixture.close_count == 1
