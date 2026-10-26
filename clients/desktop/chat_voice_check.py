"""Actual GTK/codec/encrypted-owner check with synthetic capture and silent sink."""
import base64
import ctypes
import ctypes.util
import json
import os
from pathlib import Path
import sys
import time
import threading
from types import SimpleNamespace

from app import App, Adw, Gtk, Gdk, Graphene
from chat_ui_check import MemoryKeyring, settled, click
from mesh_ui_check import capture, pump, Driver, done
from device_identity.friends import load_friends_identity
from messenger.local import LocalChat
from provisioning.chat_owner import ChatOwner
from provisioning.chat_audio import _element


def wait_for(predicate, seconds=10):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        pump(.03)
        if predicate():
            return
    raise AssertionError('voice operation did not reach expected state')


def pointer_checks(app, voice, destination):
    trace = []
    controllers = voice.observe_controllers()
    for index in range(controllers.get_n_items()):
        controller = controllers.get_item(index)
        signals = (('pressed', 'released', 'cancel') if isinstance(controller, Gtk.GestureClick) else
                   ('drag-begin', 'drag-update', 'drag-end', 'cancel') if isinstance(controller, Gtk.GestureDrag) else ())
        for signal in signals:
            controller.connect(signal, lambda *arguments, signal=signal: trace.append(dict(
                event=signal, state=voice.state, pointer=voice.pointer, busy=voice.busy,
                pending_hold=bool(voice.press_timer), offsets=list(arguments[1:]) if signal == 'drag-update' else [])))
    x11 = ctypes.CDLL(ctypes.util.find_library('X11'))
    xtest = ctypes.CDLL(ctypes.util.find_library('Xtst'))
    signatures = {'XOpenDisplay': (ctypes.c_void_p, [ctypes.c_char_p]),
                  'XDefaultRootWindow': (ctypes.c_ulong, [ctypes.c_void_p]),
                  'XFlush': (ctypes.c_int, [ctypes.c_void_p]),
                  'XCloseDisplay': (ctypes.c_int, [ctypes.c_void_p]),
                  'XKeysymToKeycode': (ctypes.c_ubyte, [ctypes.c_void_p, ctypes.c_ulong]),
                  'XTranslateCoordinates': (ctypes.c_int, [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_ulong,
                                                          ctypes.c_int, ctypes.c_int, ctypes.c_void_p,
                                                          ctypes.c_void_p, ctypes.c_void_p])}
    for name, (result, arguments) in signatures.items():
        getattr(x11, name).restype, getattr(x11, name).argtypes = result, arguments
    xtest.XTestFakeMotionEvent.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_ulong]
    xtest.XTestFakeButtonEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_int, ctypes.c_ulong]
    xtest.XTestFakeKeyEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_int, ctypes.c_ulong]
    display = x11.XOpenDisplay(os.environ['DISPLAY'].encode())
    assert display
    try:
        voice.source_factory = lambda: _element('audiotestsrc', is_live=True, samplesperbuffer=160)
        voice.pane.show_voice()
        pump(.2)
        success, point = voice.record.compute_point(app.messenger_window, Graphene.Point().init(
            voice.record.get_width() / 2, voice.record.get_height() / 2))
        assert success
        position_x, position_y, child = ctypes.c_int(), ctypes.c_int(), ctypes.c_ulong()
        scale = app.messenger_window.get_scale_factor()
        assert x11.XTranslateCoordinates(display, app.messenger_window.get_surface().get_xid(), x11.XDefaultRootWindow(display),
                                         round(point.x * scale), round(point.y * scale), ctypes.byref(position_x),
                                         ctypes.byref(position_y), ctypes.byref(child))
        def motion(delta_x=0, delta_y=0):
            xtest.XTestFakeMotionEvent(display, -1, position_x.value + round(delta_x * scale),
                                      position_y.value + round(delta_y * scale), 0)
            x11.XFlush(display)
            pump(.05)
        def button(pressed):
            xtest.XTestFakeButtonEvent(display, 1, int(pressed), 0)
            x11.XFlush(display)
            pump(.05)
        motion()
        xtest.XTestFakeButtonEvent(display, 1, 1, 0)
        xtest.XTestFakeButtonEvent(display, 1, 0, 0)
        x11.XFlush(display)
        pump(.25)
        assert voice.state == 'idle' and voice.recorder is None, (voice.state, voice.pointer, voice.busy)
        button(True)
        voice.pane.last_snapshot = None
        voice.pane.refresh()
        settled(voice.pane)
        wait_for(lambda: voice.state == 'holding')
        voice.pane.last_snapshot = None
        voice.pane.refresh()
        settled(voice.pane)
        assert voice.state == 'holding'
        wait_for(lambda: voice.recorder is not None and len(voice.recorder.data) >= voice.recorder.rate * 2 * .6)
        button(False)
        wait_for(lambda: voice.state == 'ready')
        voice.cancel()
        wait_for(lambda: voice.draft is None)
        motion()
        button(True)
        wait_for(lambda: voice.state == 'holding')
        motion(-90, 0)
        button(False)
        wait_for(lambda: voice.recorder is None)
        assert voice.state == 'idle'
        motion()
        button(True)
        wait_for(lambda: voice.state == 'holding')
        motion(0, -70)
        wait_for(lambda: voice.state == 'locked')
        button(False)
        assert voice.state == 'locked'
        voice.cancel()
        wait_for(lambda: voice.recorder is None)
        voice.record.grab_focus()
        pump(.1)
        def key(keysym):
            code = x11.XKeysymToKeycode(display, keysym)
            xtest.XTestFakeKeyEvent(display, code, 1, 0)
            xtest.XTestFakeKeyEvent(display, code, 0, 0)
            x11.XFlush(display)
        key(Gdk.KEY_Return)
        wait_for(lambda: voice.state == 'locked')
        wait_for(lambda: voice.recorder is not None and len(voice.recorder.data) >= voice.recorder.rate * 2 * .6)
        key(Gdk.KEY_Return)
        wait_for(lambda: voice.state == 'ready')
        key(Gdk.KEY_Escape)
        wait_for(lambda: voice.state == 'idle' and voice.draft is None)
    finally:
        (destination / 'pointer-events.json').write_text(json.dumps(dict(events=trace, final_state=voice.state,
            pointer=voice.pointer, busy=voice.busy, timer=bool(voice.press_timer)), indent=2) + '\n')
        xtest.XTestFakeButtonEvent(display, 1, 0, 0)
        x11.XFlush(display)
        x11.XCloseDisplay(display)


def main(destination, scale):
    failures = []
    def failed(kind, value, traceback):
        failures.append(kind.__name__)
        sys.__excepthook__(kind, value, traceback)
    sys.excepthook = failed
    destination.mkdir(parents=True, exist_ok=False)
    Adw.init()
    Gtk.Settings.get_default().set_property('gtk-enable-animations', False)
    Gtk.Settings.get_default().set_property('gtk-xft-dpi', round(96 * scale / int(os.environ.get('GDK_SCALE', '1')) * 1024))
    app = App(smoke=True)
    driver = Driver()
    app.complete('initialized', done((driver, driver.profiles(), False)), app.revision, None)
    assert app.window.get_display().__gtype__.name == 'GdkX11Display'
    device = load_friends_identity(destination / 'synthetic-device', create=True)
    def offline():
        raise OSError('synthetic offline test')
    friends = SimpleNamespace(_device=lambda create: device, http_factory=offline)
    vault = MemoryKeyring()
    pane = app.chat_pane
    pane.owner_factory = lambda: ChatOwner(destination / 'chat', friends, keyring=vault)
    voice = pane.voice
    voice.source_factory = lambda: _element('audiotestsrc', is_live=True, num_buffers=100, samplesperbuffer=160)
    voice.sink_factory = lambda: _element('fakesink', sync=True)
    app.present()
    app.select_page('messenger')
    pane.activate(True, True)
    settled(pane)
    click(pane, pane.t('chat_create'))
    profile = pane.owner.invoke('profile')
    peer = LocalChat(destination / 'peer', os.urandom(32), create=True, platform='android', version=118)
    card = peer.profile()
    peer.trust_contact(profile['public'], profile['fingerprint'])
    pane.owner.invoke('trust_contact', public=card['public'], fingerprint=card['fingerprint'])
    modes = []
    try:
        for mode in (16, 7, 8, 9):
            ru = mode in (16, 8)
            app.ru = ru
            app.paint()
            pane.activate(True, ru)
            pane.conversation(card)
            settled(pane)
            wait_for(lambda: not voice.busy)
            voice.picker.set_selected((16, 7, 8, 9).index(mode))
            wait_for(lambda: not voice.busy)
            voice.record.emit('clicked')
            if mode == 7:
                assert voice.state == 'confirm' and voice.recorder is None
                pump(.2)
                capture(app, destination / 'en-radio-confirm.png')
                voice.confirm.emit('clicked')
                wait_for(lambda: not voice.busy)
                assert voice.state == 'idle'
                voice.record.emit('clicked')
            wait_for(lambda: voice.state == 'locked')
            pane.show_voice()
            pump(.2)
            capture(app, destination / f'{mode}-recording.png')
            wait_for(lambda: voice.state == 'ready')
            assert voice.draft and voice.recorder is None
            count = pane.owner.invoke('history', address=card['address'], offset=0, limit=50)['total']
            assert count == len(modes)
            voice.preview.emit('clicked')
            wait_for(lambda: not voice.busy)
            assert voice.player is not None
            voice.pause.emit('clicked')
            wait_for(lambda: not voice.busy)
            assert voice.player.paused
            voice.seek(voice.progress, None, 250)
            wait_for(lambda: not voice.busy)
            assert voice.player.paused
            pane.show_voice()
            pump(.1)
            capture(app, destination / f'{mode}-preview.png')
            voice.send.grab_focus()
            assert app.messenger_window.get_focus() == voice.send
            voice.send.emit('clicked')
            wait_for(lambda: not voice.busy and not pane.busy and voice.state == 'idle')
            history = pane.owner.invoke('history', address=card['address'], offset=0, limit=50)
            assert history['total'] == count + 1
            message = history['messages'][-1]
            assert message['kind'] == 'audio' and message['duration_ms'] >= 400
            original = pane.owner.invoke('audio', message_id=message['id'])
            assert original['mode'] == mode
            packed = next(item for item in pane.owner.local._store.messages() if item['id'] == message['id'])
            assert peer._chat.receive(bytes.fromhex(packed['packed']))
            assert peer.audio(message['id']) == original
            for path in (destination / 'chat').rglob('*'):
                if path.is_file():
                    assert base64.b64decode(original['audio']) not in path.read_bytes()
            voice.play_message(message['id'])
            wait_for(lambda: not voice.busy)
            assert voice.player is not None
            assert pane.key_pressed(None, Gdk.KEY_Escape, 0, 0)
            wait_for(lambda: voice.player is None)
            assert pane.screen == 'conversation'
            modes.append(mode)
        entered, release, drained = threading.Event(), threading.Event(), threading.Event()
        previous_source = voice.source_factory
        def delayed_source():
            entered.set()
            assert release.wait(3)
            return previous_source()
        voice.source_factory = delayed_source
        voice.record.emit('clicked')
        wait_for(entered.is_set)
        pane.contacts()
        release.set()
        voice.pool.submit(drained.set)
        settled(pane)
        wait_for(drained.is_set)
        wait_for(lambda: voice.recorder is None and voice.draft is None)
        voice.source_factory = previous_source
        assert pane.owner.invoke('history', address=card['address'], offset=0, limit=50)['total'] == 4
        pane.conversation(card)
        settled(pane)
        wait_for(lambda: not voice.busy)
        voice.record.emit('clicked')
        wait_for(lambda: voice.state == 'locked')
        assert pane.key_pressed(None, Gdk.KEY_Escape, 0, 0)
        wait_for(lambda: voice.recorder is None)
        pointer_checks(app, voice, destination)
        assert pane.owner.invoke('history', address=card['address'], offset=0, limit=50)['total'] == 4
        app.close(True)
        wait_for(lambda: app.closed)
        reopened = ChatOwner(destination / 'chat', friends, keyring=vault)
        try:
            assert reopened.open() == profile
            assert reopened.invoke('voice_settings') == {'mode': 9, 'confirmed': [card['address']]}
            assert reopened.invoke('history', address=card['address'], offset=0, limit=50)['total'] == 4
        finally:
            reopened.close()
        assert not failures, failures
        (destination / 'result.json').write_text(json.dumps(dict(result='PASS', modes=modes,
            capture='GStreamer audiotestsrc', playback='GStreamer fakesink', microphone_opened=False,
            preview_pause_seek=True, explicit_send=True, encrypted_reopen=True, cancel_navigation=True,
            radio_confirmation=True, device_scale=int(os.environ.get('GDK_SCALE', '1')),
            actual_x11_pointer_hold_release_cancel_lock=True,
            actual_x11_keyboard_enter_escape=True,
            background_snapshot_does_not_interrupt_hold=True,
            stale_capture_completion_discarded=True,
            font_scale=scale, display='GdkX11Display', remote_network=False), indent=2) + '\n')
    finally:
        peer.close()
        if not app.closed:
            app.close(True)
            pump(2)


if __name__ == '__main__':
    main(Path(sys.argv[1]), float(sys.argv[2]))
