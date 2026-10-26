import os
from pathlib import Path
import shutil

import pytest

pytest.importorskip('gi')
pytestmark = pytest.mark.skipif(not os.environ.get('DISPLAY'), reason='Real GTK display required')

from app import Gdk, GLib, Gtk
from smiley_catalog import FACES, find
import smiley_widgets
from smiley_widgets import AnimationClock, SmileyLabel
from scripts.smiley_assets import ROOT, ASSETS
from test_messenger_ux import window, pump, settle


@pytest.fixture(autouse=True)
def bundled_assets(tmp_path, monkeypatch):
    directory = tmp_path / 'icq-classic'
    shutil.copytree(ROOT / ASSETS, directory)
    monkeypatch.setattr(smiley_widgets, 'ASSETS', directory)
    smiley_widgets.animation.cache_clear()
    yield directory
    smiley_widgets.animation.cache_clear()


def test_picker_order_selection_spaces_focus_no_send(window):
    pane, owner = window[0].pane, window[1]
    pane.compose.set_text('Привет мир')
    buffer = pane.compose.get_buffer()
    buffer.place_cursor(buffer.get_iter_at_offset(7))
    pane.smileys.buttons[1].emit('clicked')
    assert pane.compose.get_text() == 'Привет :) мир'
    buffer.select_range(buffer.get_iter_at_offset(7), buffer.get_iter_at_offset(9))
    pane.smileys.buttons[35].emit('clicked')
    assert pane.compose.get_text() == 'Привет *LOL* мир'
    assert pane.drafts[pane.peer['address']] == pane.compose.get_text()
    assert window[0].get_focus() == pane.compose
    assert len(pane.smileys.buttons) == 49
    assert [button.get_tooltip_text() for button in pane.smileys.buttons] == [face['label'] for face in FACES]
    assert [button.get_child().get_text() for button in pane.smileys.buttons] == [face['token'] for face in FACES]
    assert not any(operation == 'queue' for operation, _ in owner.calls)
    pane.emoji_button.popup()
    pump()
    assert pane.smileys.key_pressed(None, Gdk.KEY_Right, 0, 0, 0)
    assert window[0].get_focus() == pane.smileys.buttons[1]
    assert pane.smileys.key_pressed(None, Gdk.KEY_Escape, 0, 0, 1)
    pump()
    assert not pane.smileys.get_visible()
    assert window[0].get_focus() == pane.compose


def test_token_utf8_boundary_atomic_rejection(window):
    composer = window[0].pane.compose
    original = 'я' * 2046 + 'a'
    composer.set_text(original)
    composer.get_buffer().place_cursor(composer.get_buffer().get_end_iter())
    assert composer.insert_smiley(':)')
    assert len(composer.get_text().encode()) == 4096
    assert not composer.insert_smiley('*LOL*')
    assert composer.get_text() == original + ' :)'
    buffer = composer.get_buffer()
    buffer.select_range(buffer.get_start_iter(), buffer.get_end_iter())
    assert composer.insert_smiley('*HI*')
    assert composer.get_text() == '*HI*'


def test_render_copy_original_and_eight_limit(window):
    pane = window[0].pane
    original = 'Привет :) *LOL* @}->-- *DANCE* 🙂 ' + ' '.join([':)'] * 8)
    label = SmileyLabel(original, pane.animation_clock)
    pane.content.append(label)
    pump()
    assert len(label.images) == 8
    assert label.get_text() == original
    assert label.get_selectable()
    label.select_region(0, -1)
    label.emit('copy-clipboard')
    result = []
    label.get_clipboard().read_text_async(None, lambda clipboard, value: result.append(clipboard.read_text_finish(value)))
    pump(.2)
    assert result == [original]
    layout = label.get_layout()
    start, end, _ = find(original)[1]
    assert layout.index_to_pos(len(original[:start].encode())).width == label.images[1]['width'] * 1024
    assert layout.index_to_pos(len(original[:start + 1].encode())).width == 0


def test_missing_corrupt_asset_keeps_literal(bundled_assets):
    clock = AnimationClock()
    (bundled_assets / 'ab.gif').unlink()
    (bundled_assets / 'bj.gif').write_bytes(b'not gif')
    original = ':) *LOL* *HI*'
    label = SmileyLabel(original, clock)
    assert label.get_text() == original
    assert len(label.images) == 1
    clock.close()


def test_decoder_failure_keeps_literal(bundled_assets, monkeypatch):
    import hashlib
    raw = b'GIF89a-invalid'
    (bundled_assets / 'ab.gif').write_bytes(raw)
    faces = list(FACES)
    faces[1] = dict(faces[1], sha256=hashlib.sha256(raw).hexdigest())
    monkeypatch.setattr(smiley_widgets, 'FACES', tuple(faces))
    clock = AnimationClock()
    label = SmileyLabel(':)', clock)
    assert label.get_text() == ':)' and not label.images
    clock.close()


def test_alias_frames_and_single_clock_pause_recycle(window):
    pane = window[0].pane
    clock = pane.animation_clock
    labels = [SmileyLabel(token, clock) for token in (':)', ':-)', '=)', '*DANCE*')]
    for label in labels:
        pane.content.append(label)
    pump()
    pane.messages_scroll.get_vadjustment().set_value(pane.messages_scroll.get_vadjustment().get_upper())
    clock.set_active(True)
    assert clock.source
    source = clock.source
    pump(.3)
    assert clock.source == source
    assert any(label.elapsed > 0 for label in labels)
    before = [label.elapsed for label in labels]
    clock.set_active(False)
    pump(.15)
    assert not clock.source and [label.elapsed for label in labels] == before
    for label in labels:
        pane.content.remove(label)
    pump()
    assert not any(label in clock.widgets for label in labels)
    window[0].app.select_page('status')
    pump()
    assert not clock.source and not clock.widgets
    window[0].app.select_page('messenger')
    settle(pane)
    clock.close()
    assert not clock.source and not clock.widgets


def test_one_queue_preserves_android_tokens_and_unicode(window):
    pane, owner = window[0].pane, window[1]
    text = 'Привет :) *LOL* @}->-- *DANCE* 🙂\nБез нормализации е\u0301'
    pane.compose.set_text(text)
    pane.send_button.emit('clicked')
    settle(pane)
    assert [arguments['text'] for operation, arguments in owner.calls if operation == 'queue'] == [text]
    assert owner.messages[-1]['text'] == text
    assert len(find(text)) == 4


def test_actual_gif_frame_changes():
    clock = AnimationClock()
    label = SmileyLabel(':P', clock)
    first = bytes(label.images[0]['texture'].save_to_png_bytes().get_data())
    label.advance(0)
    label.advance(100)
    second = bytes(label.images[0]['texture'].save_to_png_bytes().get_data())
    assert first != second
    clock.close()


def test_offscreen_and_inactive_window_pause(window, monkeypatch):
    from types import SimpleNamespace
    pane = window[0].pane
    pane.content.append(Gtk.Box(height_request=1800))
    label = SmileyLabel('*DANCE*', pane.animation_clock)
    pane.content.append(label)
    pump()
    pane.messages_scroll.get_vadjustment().set_value(0)
    pump(.1)
    elapsed = label.elapsed
    pane.animation_clock.set_active(True)
    pump(.2)
    assert not label.eligible() and label.elapsed == elapsed
    pane.messages_scroll.get_vadjustment().set_value(pane.messages_scroll.get_vadjustment().get_upper())
    pump(.2)
    assert label.eligible() and label.elapsed > 0
    monkeypatch.setattr(pane, 'get_root', lambda: SimpleNamespace(is_active=lambda: False))
    pane.animation_active()
    assert not pane.animation_clock.active and not pane.animation_clock.source
