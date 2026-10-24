"""Accepted announcement list, compose and explicit publish/edit confirmation."""
import time
import uuid

from gi.repository import Gtk

from messenger.local import LocalError


def limited_text(text, maximum):
    result = []
    size = 0
    for char in text:
        size += 2 if ord(char) > 65535 else 1
        if size > maximum:
            break
        result.append(char)
    return ''.join(result)


class Announcements:
    def __init__(self, pane):
        self.pane = pane
        self.original = None
        self.title = self.body = ''
        self.request_id = None
        self.prepared = None
        self.offset = 0
        self.limiting = False

    def job(self, operation, arguments, callback):
        pane = self.pane
        revision = pane.view_revision
        def work():
            try:
                return {'value': pane.owner.invoke(operation, **arguments)}
            except LocalError as failure:
                return {'error': str(failure)}
        def complete(result):
            if revision != pane.view_revision:
                return
            if 'error' in result:
                code = result['error']
                pane.notice.set_text(pane.t(code if code in ('notice_denied', 'notice_conflict') else 'notice_unavailable'))
            else:
                callback(result['value'])
        pane.submit(work, complete)

    def listing(self, offset=0):
        pane = self.pane
        if pane.busy:
            return
        self.offset = offset
        pane.clear('notice-admin', pane.t('notice_admin'))
        pane.toolbar(back=pane.service_events)
        pane.notice.set_text(pane.t('notice_role_check'))
        def display(page):
            pane.notice.set_text(pane.t('notice_admin_active'))
            pane.button(pane.t('notice_new'), self.new)
            pane.label(pane.t('notice_published_list')).add_css_class('fc-chat-notice-section')
            if not page['events']:
                pane.label(pane.t('service_events_empty'))
            for event in page['events']:
                pane.button(event['title'], lambda event=event: self.edit(event))
                pane.label(event['author'] + ' · ' + pane.event_date(event['created'])).add_css_class('fc-chat-key-caption')
                if event['expires'] <= time.time():
                    pane.label(pane.t('notice_expired')).add_css_class('fc-chat-key-caption')
            if offset:
                pane.button(pane.t('notice_recent'), self.listing)
            if page['next_offset'] is not None:
                pane.button(pane.t('notice_older'), lambda: self.listing(page['next_offset']))
        self.job('announcements_list', dict(offset=offset), display)

    def new(self):
        self.original = self.prepared = None
        self.title = self.body = ''
        self.request_id = uuid.uuid4().hex
        self.compose()

    def edit(self, original):
        self.original = dict(original)
        self.title, self.body = original['title'], original['body']
        self.request_id = uuid.uuid4().hex
        self.prepared = None
        self.compose()

    def compose(self):
        pane = self.pane
        if pane.busy:
            return
        pane.clear('notice-compose', pane.t('notice_new' if self.original is None else 'notice_edit'))
        pane.toolbar(back=self.listing)
        pane.notice.set_text(pane.delivery_text())
        self.title = limited_text(self.title, 160)
        self.body = limited_text(self.body, 4000)
        if self.original is not None:
            pane.label(pane.t('notice_revision').replace('%1$d', str(self.original['revision']))).add_css_class('fc-chat-key-caption')
        self.title_input = pane.entry(self.title, maximum=160)
        self.title_input.set_placeholder_text(pane.t('notice_title'))
        self.title_input.set_tooltip_text(pane.t('notice_title'))
        self.title_input.update_property([Gtk.AccessibleProperty.LABEL], [pane.t('notice_title')])
        self.title_input.connect('changed', self.title_changed)
        self.body_input = Gtk.TextView(wrap_mode=Gtk.WrapMode.WORD_CHAR)
        self.body_input.set_accepts_tab(False)
        self.body_input.set_tooltip_text(pane.t('notice_body'))
        self.body_input.update_property([Gtk.AccessibleProperty.LABEL], [pane.t('notice_body')])
        self.body_input.add_css_class('fc-chat-editor')
        self.buffer = self.body_input.get_buffer()
        self.buffer.set_text(self.body)
        self.buffer.connect('changed', self.body_changed)
        self.buffer.connect('insert-text', self.body_inserting)
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_propagate_natural_height(True)
        scroll.set_child(self.body_input)
        overlay = Gtk.Overlay()
        overlay.set_child(scroll)
        self.placeholder = Gtk.Label(label=pane.t('notice_body'), halign=Gtk.Align.START, valign=Gtk.Align.START)
        self.placeholder.set_margin_start(10)
        self.placeholder.set_margin_top(10)
        self.placeholder.set_can_target(False)
        self.placeholder.add_css_class('fc-chat-placeholder')
        self.placeholder.set_visible(not self.body)
        overlay.add_overlay(self.placeholder)
        pane.content.append(overlay)
        line_height = self.body_input.create_pango_layout('M').get_pixel_size()[1]
        scroll.set_min_content_height(line_height * 3 + 16)
        scroll.set_max_content_height(line_height * 6 + 16)
        pane.label(pane.t('notice_audience' if self.original is None else 'notice_edit_hint')).add_css_class('fc-chat-notice-hint')
        pane.button(pane.t('notice_preview'), self.preview)
        self.title_input.grab_focus()
        pane.layout_changed()

    def title_changed(self, entry):
        if self.limiting:
            return
        self.title = limited_text(entry.get_text(), 160)
        if self.title != entry.get_text():
            self.limiting = True
            entry.set_text(self.title)
            entry.set_position(-1)
            self.limiting = False

    def body_changed(self, buffer):
        if self.limiting:
            return
        text = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), True)
        self.body = limited_text(text, 4000)
        self.placeholder.set_visible(not self.body)
        if self.body != text:
            self.limiting = True
            buffer.set_text(self.body)
            buffer.place_cursor(buffer.get_end_iter())
            self.limiting = False

    def body_inserting(self, buffer, location, text, length):
        if self.limiting:
            return
        remaining = 4000 - len(self.body.encode('utf-16-le')) // 2
        clipped = limited_text(text, remaining)
        if clipped != text:
            buffer.stop_emission_by_name('insert-text')
            self.limiting = True
            if clipped:
                buffer.insert(location, clipped)
            self.limiting = False
            self.body_changed(buffer)

    def preview(self):
        pane = self.pane
        if pane.busy:
            return
        self.title, self.body = self.title.strip(), self.body.strip()
        if not self.title or not self.body:
            pane.notice.set_text(pane.t('notice_required'))
            return
        value = dict(title=self.title, body=self.body)
        if self.original is None:
            value.update(id=self.request_id, kind='information', platforms=['android', 'windows', 'linux'], days=30)
        else:
            value.update(id=self.original['id'], revision=self.original['revision'], request_id=self.request_id)
        self.prepared = value
        pane.clear('notice-preview', pane.t('notice_preview'))
        pane.toolbar(back=self.compose)
        pane.notice.set_text(pane.delivery_text())
        pane.label(self.title).add_css_class('fc-chat-notice-title')
        pane.label(self.body)
        hint = pane.label(pane.t('notice_audience' if self.original is None else 'notice_edit_hint'))
        hint.add_css_class('fc-chat-notice-hint')
        hint.add_css_class('fc-chat-amber')
        pane.button(pane.t('notice_publish' if self.original is None else 'notice_save_edit'), self.publish)
        pane.layout_changed()

    def publish(self):
        pane = self.pane
        if pane.busy or self.prepared is None or pane.screen != 'notice-preview':
            return
        def completed(_):
            self.title = self.body = ''
            self.prepared = None
            self.listing()
        self.job('announcements_publish' if self.original is None else 'announcements_edit',
                 dict(notice=dict(self.prepared)), completed)

    def localize(self):
        if self.pane.screen == 'notice-admin':
            self.listing(self.offset)
        elif self.pane.screen == 'notice-compose':
            self.compose()
        elif self.pane.screen == 'notice-preview':
            self.preview()

    def back(self):
        if self.pane.screen == 'notice-admin':
            self.pane.service_events()
        elif self.pane.screen == 'notice-preview':
            self.compose()
        else:
            self.listing()
