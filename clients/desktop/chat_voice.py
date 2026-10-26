"""Voice controls for the existing GTK conversation; explicit capture and send."""
import base64
from concurrent.futures import ThreadPoolExecutor
import time

from gi.repository import Gtk, GLib, Graphene

from provisioning.chat_audio import Recorder, Player, _wipe


class VoiceControls(Gtk.Box):
    def __init__(self, pane, *, source_factory=None, sink_factory=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.pane = pane
        self.source_factory, self.sink_factory = source_factory, sink_factory
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix='fc-chat-voice')
        self.address = None
        self.generation = 0
        self.busy = self.closed = False
        self.state = 'idle'
        self.recorder = self.player = self.draft = None
        self.mode = 16
        self.settings = {'mode': 16, 'confirmed': []}
        self.started = 0
        self.press_timer = 0
        self.pointer = False
        self.press_origin = None
        self.mouse_activation = False
        self.labels_language = None
        self.status = Gtk.Label(xalign=0, wrap=True)
        self.append(self.status)
        self.record = pane.button_class()
        self.record.connect('clicked', lambda *_: self.keyboard())
        self.append(self.record)
        gesture = Gtk.GestureDrag()
        gesture.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        gesture.connect('drag-update', self.move)
        gesture.connect('drag-end', self.release)
        gesture.connect('cancel', self.gesture_cancel)
        self.add_controller(gesture)
        click = Gtk.GestureClick()
        click.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        click.connect('pressed', lambda controller, count, position_x, position_y: self.press(controller, position_x, position_y))
        click.connect('released', self.release)
        self.add_controller(click)
        click.group(gesture)
        self.preview = pane.button_class()
        self.preview.connect('clicked', lambda *_: self.play_draft())
        self.append(self.preview)
        self.send = pane.button_class()
        self.send.connect('clicked', lambda *_: self.send_draft())
        self.append(self.send)
        self.cancel_button = pane.button_class()
        self.cancel_button.connect('clicked', lambda *_: self.cancel())
        self.append(self.cancel_button)
        self.profile = Gtk.MenuButton()
        self.profile.add_css_class('fc-voice-profile')
        popover = Gtk.Popover()
        panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.profile_notice = Gtk.Label(wrap=True, max_width_chars=40)
        panel.append(self.profile_notice)
        self.picker = Gtk.DropDown()
        panel.append(self.picker)
        self.picker.connect('notify::selected', self.select_mode)
        popover.set_child(panel)
        self.profile.set_popover(popover)
        self.append(self.profile)
        self.confirm = pane.button_class()
        self.confirm.connect('clicked', lambda *_: self.confirm_peer())
        self.append(self.confirm)
        self.pause = pane.button_class()
        self.pause.connect('clicked', lambda *_: self.submit(self.toggle_pause, lambda _: None))
        self.append(self.pause)
        self.progress = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 1, 1)
        self.progress.set_draw_value(False)
        self.progress.connect('change-value', self.seek)
        self.append(self.progress)
        for button in (self.record, self.preview, self.send, self.cancel_button, self.confirm, self.pause):
            button.add_css_class('fc-action')
            button.add_css_class('fc-secondary')
        self.timer = GLib.timeout_add(200, self.tick)
        self.render()

    def bind(self, address):
        if self.address == address:
            return
        self.leave()
        self.address = address
        self.submit(lambda: self.pane.owner.invoke('voice_settings'), self.loaded)

    def loaded(self, settings):
        self.settings = settings
        self.render()

    def submit(self, action, callback):
        if self.busy or self.closed:
            return
        self.busy = True
        expected = self.generation
        def work():
            if expected != self.generation:
                return None
            return action()
        future = self.pool.submit(work)
        future.add_done_callback(lambda result: GLib.idle_add(self.complete, expected, result, callback))
        self.render()

    def complete(self, expected, future, callback):
        if expected != self.generation or self.closed:
            return False
        self.busy = False
        previous = self.state
        try:
            result = future.result()
        except Exception:
            self.pane.notice.set_text(self.pane.t('chat_voice_failed'))
            self.cancel()
        else:
            callback(result)
        self.render()
        if previous == 'processing' and self.state == 'ready':
            self.preview.grab_focus()
        return False

    def render(self):
        text = self.pane.t
        self.record.set_label(text('voice_stop_preview') if self.state in ('holding', 'locked') else text('chat_voice_hold'))
        self.record.set_sensitive(self.state in ('idle', 'starting', 'holding', 'locked') and
                                  (not self.busy or self.state == 'starting'))
        self.record.set_tooltip_text(self.pane.words('Удерживайте; ↑ закрепить, ← отменить. Enter: начать/остановить.',
                                                   'Hold; ↑ lock, ← cancel. Enter: start/stop.'))
        self.preview.set_label(text('voice_preview'))
        self.preview.set_visible(self.state == 'ready')
        self.preview.set_sensitive(not self.busy)
        self.send.set_label(text('chat_send'))
        self.send.set_visible(self.state == 'ready')
        self.send.set_sensitive(not self.busy)
        self.cancel_button.set_label(text('chat_voice_cancel'))
        self.cancel_button.set_visible(self.state != 'idle' or self.player is not None)
        self.profile.set_label(text('radio_title'))
        self.profile.set_sensitive(not self.busy and self.state == 'idle')
        self.profile_notice.set_text(text('radio_notice'))
        self.updating = True
        if self.labels_language != self.pane.ru:
            self.picker.set_model(Gtk.StringList.new([text('radio_normal'), 'Codec2 · 1600 bit/s',
                                                    'Codec2 · 2400 bit/s', 'Codec2 · 3200 bit/s']))
            self.labels_language = self.pane.ru
        self.picker.set_selected((16, 7, 8, 9).index(self.settings['mode']))
        self.updating = False
        self.confirm.set_label(text('radio_confirm'))
        self.confirm.set_visible(self.state == 'confirm')
        self.confirm.set_sensitive(not self.busy)
        player = self.player
        self.pause.set_label(text('chat_voice_play') if player and player.paused else text('chat_voice_pause'))
        self.pause.set_visible(player is not None)
        self.pause.set_sensitive(not self.busy)
        self.progress.set_visible(player is not None)
        self.progress.set_tooltip_text(text('chat_voice_progress'))
        if self.state == 'idle':
            self.status.set_text(text('chat_voice_hint'))
        elif self.state == 'confirm':
            self.status.set_text(text('radio_confirm_body'))
        elif self.state == 'ready':
            self.status.set_text(text('chat_voice_preview'))
        elif self.busy:
            self.status.set_text(self.pane.words('Обработка записи…', 'Processing recording…'))
        for button in (self.record, self.preview, self.send, self.cancel_button, self.confirm, self.pause):
            child = button.get_child()
            if isinstance(child, Gtk.Label):
                child.set_wrap(True)

    def select_mode(self, *_):
        if self.updating or self.busy or self.state != 'idle' or not self.address:
            return
        mode = (16, 7, 8, 9)[self.picker.get_selected()]
        self.submit(lambda: self.pane.owner.invoke('voice_mode', mode=mode), self.loaded)

    def confirm_peer(self):
        address = self.address
        def confirmed(settings):
            self.settings = settings
            self.state = 'idle'
        self.submit(lambda: self.pane.owner.invoke('voice_confirm', address=address), confirmed)

    def start(self, locked=False):
        if self.busy or self.closed or not self.address or not self.pane.active or self.state != 'idle':
            return
        self.mode = self.settings['mode']
        if self.mode != 16 and self.address not in self.settings['confirmed']:
            self.state = 'confirm'
            self.render()
            return
        mode = self.mode
        self.state = 'starting'
        def begin():
            self.cleanup()
            self.recorder = Recorder(mode, source_factory=self.source_factory)
        def ready(_):
            self.started = time.monotonic()
            self.state = 'locked' if locked else 'holding'
            if not locked and not self.pointer:
                self.finish()
        self.submit(begin, ready)

    def keyboard(self):
        if self.pointer or self.mouse_activation:
            return
        if self.state == 'idle':
            self.start(locked=True)
        elif self.state in ('holding', 'locked'):
            self.finish()

    def press(self, gesture, start_x, start_y):
        success, bounds = self.record.compute_bounds(self)
        if not success or not (bounds.get_x() <= start_x <= bounds.get_x() + bounds.get_width() and
                               bounds.get_y() <= start_y <= bounds.get_y() + bounds.get_height()):
            gesture.set_state(Gtk.EventSequenceState.DENIED)
            return
        if self.state != 'idle' or self.busy:
            return
        gesture.set_state(Gtk.EventSequenceState.CLAIMED)
        self.mouse_activation = True
        self.pointer = True
        root = self.get_root()
        success, origin = self.compute_point(root, Graphene.Point().init(0, 0)) if root else (False, None)
        self.press_origin = (origin.x, origin.y) if success else None
        def begin():
            self.press_timer = 0
            self.start()
            return False
        self.press_timer = GLib.timeout_add(180, begin)

    def move(self, gesture, delta_x, delta_y):
        if not self.pointer:
            return
        root = self.get_root()
        if root and self.press_origin is not None:
            success, origin = self.compute_point(root, Graphene.Point().init(0, 0))
            if success:
                delta_x += origin.x - self.press_origin[0]
                delta_y += origin.y - self.press_origin[1]
        if self.press_timer and (abs(delta_x) > 24 or abs(delta_y) > 24):
            self.cancel()
        elif self.state == 'holding':
            if -delta_x >= 80 and -delta_x >= -delta_y:
                self.cancel()
            elif -delta_y >= 64 and -delta_y > -delta_x:
                self.state = 'locked'
                self.render()

    def release(self, *_):
        GLib.idle_add(self.clear_mouse_activation)
        if not self.pointer:
            return
        self.pointer = False
        if self.press_timer:
            GLib.source_remove(self.press_timer)
            self.press_timer = 0
        if self.state == 'holding':
            self.finish()

    def clear_mouse_activation(self):
        self.mouse_activation = False
        return False

    def gesture_cancel(self, *_):
        if self.pointer and self.state in ('idle', 'starting', 'holding'):
            self.cancel()
        else:
            self.pointer = False
            GLib.idle_add(self.clear_mouse_activation)

    def finish(self):
        if self.busy or self.state not in ('holding', 'locked'):
            return
        self.state = 'processing'
        def finish():
            try:
                self.draft = self.recorder.finish()
            finally:
                self.recorder = None
        self.submit(finish, lambda _: setattr(self, 'state', 'ready'))

    def play_draft(self):
        if self.state == 'ready':
            self.submit(lambda: self.load_player(self.draft, self.mode), lambda _: None)

    def play_message(self, message_id):
        if self.state != 'idle':
            return
        def load():
            result = self.pane.owner.invoke('audio', message_id=message_id)
            self.load_player(base64.b64decode(result['audio'], validate=True), result['mode'])
        self.submit(load, lambda _: None)

    def load_player(self, raw, mode):
        if self.player:
            self.player.close()
            self.player = None
        self.player = Player(raw, mode, sink_factory=self.sink_factory)
        self.player.play()

    def toggle_pause(self):
        if self.player:
            if self.player.pipeline is None:
                self.player.play()
            else:
                self.player.pause()

    def seek(self, widget, scroll, position):
        if self.player is not None and not self.busy:
            self.submit(lambda: self.player.seek(position), lambda _: None)
        return True

    def send_draft(self):
        if self.state != 'ready' or self.busy:
            return
        address, mode = self.address, self.mode
        confirmed = address in self.settings['confirmed']
        self.state = 'sending'
        def send():
            arguments = {'address': address, 'audio': base64.b64encode(self.draft).decode('ascii')}
            if mode != 16:
                arguments.update(mode=mode, confirmed=confirmed)
            self.pane.owner.invoke('queue_audio' if mode == 16 else 'queue_radio', **arguments)
            self.cleanup()
        def sent(_):
            self.state = 'idle'
            self.pane.last_snapshot = None
            self.pane.refresh()
        self.submit(send, sent)

    def tick(self):
        if self.closed:
            return False
        if self.state in ('holding', 'locked'):
            elapsed = min(60, int(time.monotonic() - self.started))
            self.status.set_text(self.pane.t('chat_voice_recording').replace('%1$d', str(elapsed)))
            if self.recorder is not None and self.recorder.finished.is_set():
                self.finish()
        if self.player is not None and not self.busy:
            try:
                position, playing = self.player.position()
                self.progress.set_range(0, max(1, self.player.duration_ms))
                self.progress.set_value(position)
                self.pause.set_label(self.pane.t('chat_voice_pause' if playing and not self.player.paused else 'chat_voice_play'))
            except Exception:
                self.cancel()
                self.pane.notice.set_text(self.pane.t('chat_voice_failed'))
        return True

    def cleanup(self):
        if self.recorder is not None:
            self.recorder.finish(cancel=True)
            self.recorder = None
        if self.player is not None:
            self.player.close()
            self.player = None
        if self.draft is not None:
            _wipe(self.draft)
            self.draft = None

    def cancel(self):
        self.generation += 1
        self.busy = False
        self.state = 'idle'
        self.pointer = False
        GLib.idle_add(self.clear_mouse_activation)
        if self.press_timer:
            GLib.source_remove(self.press_timer)
            self.press_timer = 0
        if not self.closed:
            self.pool.submit(self.cleanup)
        self.render()

    def leave(self):
        self.cancel()
        self.address = None

    def close(self):
        self.leave()
        self.closed = True
        GLib.source_remove(self.timer)

    def join(self):
        self.pool.shutdown(wait=True)
