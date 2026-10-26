"""Selectable original token text with bundled, visibility-bound GIF presentation."""
from functools import lru_cache
import hashlib
from pathlib import Path
import time
import weakref

import gi
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import Gdk, GdkPixbuf, GLib, Graphene, Gtk, Pango, PangoCairo

from smiley_catalog import FACES, find

ASSETS = Path(__file__).resolve().parent / 'assets/chat/icq-classic'


@lru_cache(maxsize=49)
def animation(index):
    try:
        face = FACES[index]
        path = ASSETS / face['asset']
        if path.is_symlink() or not 1 <= path.stat().st_size <= 32768:
            return None
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != face['sha256']:
            return None
        loader = GdkPixbuf.PixbufLoader.new_with_type('gif')
        loader.write(raw)
        loader.close()
        image = loader.get_animation()
        if image and 1 <= image.get_width() <= 64 and 1 <= image.get_height() <= 64:
            return image
    except (OSError, ValueError, GLib.Error):
        return None


def frame_time(milliseconds):
    value = GLib.TimeVal()
    value.tv_sec, value.tv_usec = int(milliseconds // 1000), int(milliseconds % 1000) * 1000
    return value


def texture(pixbuf):
    width, height = pixbuf.get_width(), pixbuf.get_height()
    source, stride, channels = pixbuf.get_pixels(), pixbuf.get_rowstride(), pixbuf.get_n_channels()
    pixels = bytearray()
    for row in range(height):
        for column in range(width):
            offset = row * stride + column * channels
            pixels.extend(source[offset:offset + 3])
            pixels.append(source[offset + 3] if channels == 4 else 255)
    original = bytes(pixels)
    for row in range(height):
        for column in range(width):
            offset = (row * width + column) * 4
            red, green, blue, alpha = original[offset:offset + 4]
            light = min(red, green, blue)
            if not alpha or light < 170 or max(red, green, blue) - light > 55:
                continue
            exterior = any(not (0 <= column + horizontal < width and 0 <= row + vertical < height)
                           or original[((row + vertical) * width + column + horizontal) * 4 + 3] == 0
                           for vertical in (-1, 0, 1) for horizontal in (-1, 0, 1))
            if exterior:
                pixels[offset:offset + 4] = bytes((0, 0, 0, alpha * (255 - light) // 255))
    return Gdk.MemoryTexture.new(width, height, Gdk.MemoryFormat.R8G8B8A8, GLib.Bytes.new(bytes(pixels)), width * 4)


class AnimationClock:
    def __init__(self):
        self.widgets = weakref.WeakSet()
        self.active = False
        self.source = 0
        self.closed = False

    def add(self, widget):
        self.widgets.add(widget)
        self.schedule()

    def remove(self, widget):
        self.widgets.discard(widget)
        widget.previous = None
        if not self.widgets:
            self.stop()

    def set_active(self, active):
        self.active = active
        if active:
            self.schedule()
        else:
            self.stop()

    def schedule(self):
        if self.active and self.widgets and not self.closed and not self.source:
            self.source = GLib.timeout_add(40, self.tick)

    def stop(self):
        if self.source:
            GLib.source_remove(self.source)
            self.source = 0
        for widget in self.widgets:
            widget.previous = None

    def tick(self):
        now = time.monotonic() * 1000
        for widget in tuple(self.widgets):
            if widget.eligible():
                widget.advance(now)
            else:
                widget.previous = None
        return GLib.SOURCE_CONTINUE

    def close(self):
        self.closed = True
        self.stop()
        self.widgets.clear()


class SmileyLabel(Gtk.Label):
    def __init__(self, original, clock, *, selectable=True, preview=False):
        super().__init__(label=original, xalign=0, wrap=True, selectable=selectable, max_width_chars=48)
        self.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.update_property([Gtk.AccessibleProperty.LABEL], [original])
        self.clock = clock
        self.images = []
        self.elapsed = 0
        self.previous = None
        attributes = Pango.AttrList()
        attributes.insert(Pango.attr_insert_hyphens_new(False))
        font = self.get_pango_context().get_font_description()
        resolution = PangoCairo.context_get_resolution(self.get_pango_context())
        scale = 1 if font.get_size_is_absolute() else (resolution if resolution > 0 else 96) / 72
        height = max(16, min(96, round(font.get_size() / Pango.SCALE * scale * 1.15)))
        if preview:
            height = max(16, min(96, round(22 * (resolution if resolution > 0 else 96) / 96 * 1.15)))
        for start, end, index in find(original):
            if len(self.images) == 8:
                break
            image = animation(index)
            if image is None:
                continue
            width = max(1, height * image.get_width() // image.get_height())
            first = len(original[:start].encode('utf-8'))
            last = len(original[:end].encode('utf-8'))
            ink = Pango.Rectangle()
            logical = Pango.Rectangle()
            logical.y, logical.width, logical.height = -height * Pango.SCALE, width * Pango.SCALE, height * Pango.SCALE
            shape = Pango.attr_shape_new(ink, logical)
            shape.start_index, shape.end_index = first, first + 1
            attributes.insert(shape)
            logical.width = 0
            tail = Pango.attr_shape_new(ink, logical)
            tail.start_index, tail.end_index = first + 1, last
            attributes.insert(tail)
            breaks = Pango.attr_allow_breaks_new(False)
            breaks.start_index, breaks.end_index = first, last
            attributes.insert(breaks)
            iterator = image.get_iter(frame_time(0))
            self.images.append(dict(index=first, width=width, height=height, iterator=iterator,
                                    texture=texture(iterator.get_pixbuf())))
        self.set_attributes(attributes)
        self.connect('map', lambda widget: clock.add(widget) if self.images else None)
        self.connect('unmap', lambda widget: clock.remove(widget))

    def eligible(self):
        if not self.get_mapped() or not self.clock.active:
            return False
        ancestor = self.get_parent()
        while ancestor is not None:
            if isinstance(ancestor, Gtk.ScrolledWindow):
                valid, bounds = self.compute_bounds(ancestor)
                if not valid or bounds.get_x() >= ancestor.get_width() or bounds.get_y() >= ancestor.get_height() or bounds.get_x() + bounds.get_width() <= 0 or bounds.get_y() + bounds.get_height() <= 0:
                    return False
            ancestor = ancestor.get_parent()
        return True

    def advance(self, now):
        if self.previous is not None:
            self.elapsed += max(0, min(100, now - self.previous))
        self.previous = now
        changed = False
        for image in self.images:
            if image['iterator'].advance(frame_time(self.elapsed)):
                image['texture'] = texture(image['iterator'].get_pixbuf())
                changed = True
        if changed:
            self.queue_draw()

    def do_snapshot(self, snapshot):
        Gtk.Label.do_snapshot(self, snapshot)
        layout = self.get_layout()
        offset_x, offset_y = self.get_layout_offsets()
        baselines = []
        iterator = layout.get_iter()
        while True:
            baselines.append(iterator.get_baseline() / Pango.SCALE)
            if not iterator.next_line():
                break
        for image in self.images:
            line, horizontal = layout.index_to_line_x(image['index'], False)
            bounds = Graphene.Rect().init(offset_x + horizontal / Pango.SCALE,
                                          offset_y + baselines[line] - image['height'], image['width'], image['height'])
            snapshot.append_texture(image['texture'], bounds)


class SmileyPicker(Gtk.Popover):
    def __init__(self, composer, clock):
        super().__init__(position=Gtk.PositionType.TOP)
        self.composer = composer
        self.buttons = []
        grid = Gtk.Grid(column_spacing=4, row_spacing=4)
        scroll = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER, min_content_height=220,
                                   max_content_height=280, propagate_natural_height=True)
        scroll.set_child(grid)
        self.set_child(scroll)
        for index, face in enumerate(FACES):
            button = Gtk.Button(width_request=44, height_request=44, tooltip_text=face['label'])
            button.update_property([Gtk.AccessibleProperty.LABEL], [face['label']])
            label = SmileyLabel(face['token'], clock, selectable=False, preview=True)
            label.set_max_width_chars(4)
            button.set_child(label)
            button.connect('clicked', lambda _, token=face['token']: self.pick(token))
            keys = Gtk.EventControllerKey()
            keys.connect('key-pressed', self.key_pressed, index)
            button.add_controller(keys)
            grid.attach(button, index % 5, index // 5, 1, 1)
            self.buttons.append(button)
        self.focus_source = 0
        self.connect('closed', self.restore_focus)

    def restore_focus(self, *_):
        if not self.focus_source:
            self.focus_source = GLib.idle_add(self.focus_composer)

    def focus_composer(self):
        self.focus_source = 0
        if self.composer.get_mapped():
            self.composer.grab_focus()
        return GLib.SOURCE_REMOVE

    def pick(self, token):
        self.composer.insert_smiley(token)
        self.popdown()
        self.composer.grab_focus()

    def key_pressed(self, controller, keyval, keycode, modifiers, index):
        if keyval == Gdk.KEY_Escape:
            self.popdown()
            return True
        delta = {Gdk.KEY_Left: -1, Gdk.KEY_Right: 1, Gdk.KEY_Up: -5, Gdk.KEY_Down: 5}.get(keyval)
        if delta is not None:
            self.buttons[max(0, min(len(self.buttons) - 1, index + delta))].grab_focus()
            return True
        return False
