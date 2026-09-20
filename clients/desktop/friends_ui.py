"""Invitation screen for the paired Linux frontend, using GTK 4/libadwaita.

The ordinary six-file archive remains standalone. This screen is packaged with its
Python core, rather than downloading executable components at runtime.
"""
import concurrent.futures
import gi

gi.require_version('Gtk','4.0')
gi.require_version('Adw','1')
from gi.repository import Gtk, Adw, GLib, Gdk


class FriendsWindow:
    def __init__(self,parent,owner,ru=True,driver=None,on_close=None):
        self.owner=owner;self.ru=ru;self.busy=False;self.closed=False
        self.driver=driver;self.on_closed=on_close;self.qr_window=None
        self.pool=concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self.window=Adw.Window(title=self.t('Доступ по приглашению','Invitation access'),transient_for=parent,modal=True)
        self.window.set_default_size(440,520)
        self.window.add_css_class('fc-friends')
        self.provider=Gtk.CssProvider()
        self.provider.load_from_data(b'''
.fc-friends { background-color: #03110e; color: #dafff2; }
.fc-friends label { color: #dafff2; }
.fc-friends button, .fc-friends entry, .fc-friends dropdown {
 background-image: none; background-color: #072018; color: #dafff2;
 border: 1px solid #468b75; border-radius: 4px; min-height: 32px;
}
.fc-friends entry text { background-color: transparent; color: #dafff2; }
.fc-friends button:hover { background-color: #185442; }
.fc-friends button:disabled { background-color: #142b25; color: #6a8d7d; }
''')
        Gtk.StyleContext.add_provider_for_display(self.window.get_display(),self.provider,Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        box=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=12)
        for name in ('top','bottom','start','end'):getattr(box,'set_margin_'+name)(20)
        scroll=Gtk.ScrolledWindow();scroll.set_child(box);self.window.set_content(scroll)
        def label(text):
            widget=Gtk.Label(label=text,xalign=0,wrap=True);box.append(widget);return widget
        label(self.t('Вставьте код приглашения. При обновлении повторная активация не нужна.','Paste your invitation code. App updates do not require activation again.'))
        self.code=Gtk.Entry(placeholder_text='FC-…',max_length=128);box.append(self.code)
        self.activate=Gtk.Button(label=self.t('Активировать','Activate'));box.append(self.activate)
        self.region=Gtk.DropDown.new_from_strings([self.t('Нидерланды','Netherlands'),self.t('Россия','Russia')]);box.append(self.region)
        self.prepare=Gtk.Button(label=self.t('Получить настройки','Get configuration'));box.append(self.prepare)
        self.transport=Gtk.DropDown.new_from_strings(['TCP REALITY','AWG 3.1']);box.append(self.transport)
        self.connect_button=Gtk.Button(label=self.t('Подключиться','Connect'));box.append(self.connect_button)
        self.connect_button.set_sensitive(driver is not None)
        label(self.t('Выберите транспорт. При неудаче вернём прежнее подключение.','Choose a transport. A failed connection restores the previous one.'))
        self.share=Gtk.Button(label=self.t('Получить ссылку для друга','Get invitation link'));box.append(self.share)
        self.link=Gtk.Entry(editable=False);box.append(self.link)
        self.copy=Gtk.Button(label=self.t('Скопировать ссылку','Copy link'));self.copy.set_sensitive(False);box.append(self.copy)
        self.qr=Gtk.Button(label=self.t('Показать QR-код','Show QR code'));self.qr.set_sensitive(False);box.append(self.qr)
        self.qr.connect('clicked',lambda *_:self.show_qr())
        self.status=label('')
        self.activate.connect('clicked',lambda *_:self.submit(lambda:self.owner.activate(self.code.get_text().strip()),'activate'))
        self.prepare.connect('clicked',lambda *_:self.prepare_configuration())
        self.connect_button.connect('clicked',lambda *_:self.connect_vpn())
        self.share.connect('clicked',lambda *_:self.submit(self.owner.referral,'referral'))
        self.copy.connect('clicked',lambda *_:Gdk.Display.get_default().get_clipboard().set(self.link.get_text()))
        self.window.connect('close-request',self.close)
    def t(self,r,e):return r if self.ru else e
    def show_qr(self):
        if self.busy or self.closed:return
        if self.qr_window is not None:
            self.qr_window.present();return
        try:
            from friends_qr import invitation_matrix
            matrix=invitation_matrix(self.link.get_text())
        except (ValueError,RuntimeError,OSError):
            self.status.set_text(self.t('QR-код недоступен. Можно скопировать ссылку.','QR code unavailable. You can copy the link.'));return
        dialog=Adw.Window(title=self.t('Пригласить друга','Invite a friend'),transient_for=self.window,modal=True)
        dialog.add_css_class('fc-friends')
        dialog.set_default_size(320,370)
        box=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=12)
        for side in ('top','bottom','start','end'):getattr(box,'set_margin_'+side)(16)
        area=Gtk.DrawingArea();area.set_content_width(280);area.set_content_height(280)
        area.set_hexpand(True);area.set_vexpand(True)
        def draw(_,cr,width,height):
            # Integral modules and four white modules around every edge.
            size=len(matrix);scale=max(1,min(width,height)//(size+8))
            left=(width-(size+8)*scale)//2;top=(height-(size+8)*scale)//2
            cr.set_source_rgb(1,1,1);cr.paint();cr.set_source_rgb(0,0,0)
            for y,row in enumerate(matrix):
                for x,dark in enumerate(row):
                    if dark:cr.rectangle(left+(x+4)*scale,top+(y+4)*scale,scale,scale)
            cr.fill()
        area.set_draw_func(draw);box.append(area)
        box.append(Gtk.Label(label=self.t('Откройте камеру телефона и наведите её на код.','Point your phone camera at the code.'),wrap=True))
        close=Gtk.Button(label=self.t('Готово','Done'));close.connect('clicked',lambda *_:dialog.close());box.append(close)
        dialog.set_content(box);self.qr_window=dialog
        def closed(*_):self.qr_window=None;area.set_draw_func(None);return False
        dialog.connect('close-request',closed);dialog.present()
    def prepare_configuration(self):
        country='ru' if self.region.get_selected()==1 else 'nl'
        # Credentials stay in the worker/owner, not in GTK callback results.
        def action():
            config=self.owner.configuration(country)
            return config.country,config.sequence
        self.submit(action,'configuration')
    def connect_vpn(self):
        if self.driver is None:return
        country='ru' if self.region.get_selected()==1 else 'nl'
        transport='awg' if self.transport.get_selected()==1 else 'tcp'
        self.submit(lambda:self.owner.connect(country,self.driver,transport=transport),'connected')
    def submit(self,action,kind):
        if self.busy or self.closed:return
        # Snapshot GTK input on the UI thread before creating the worker.
        if kind=='activate':
            code=self.code.get_text().strip();action=lambda:self.owner.activate(code)
        self.busy=True;self.sensitivity();self.status.set_text(self.t('Подождите…','Please wait…'))
        future=self.pool.submit(action)
        future.add_done_callback(lambda f:GLib.idle_add(self.complete,f,kind))
    def complete(self,future,kind):
        if self.closed:return GLib.SOURCE_REMOVE
        try:
            result=future.result()
            if kind=='activate':self.code.set_text('');text=self.t('Доступ активирован.','Access activated.')
            elif kind=='referral':
                self.link.set_text(result['url']);text=self.t('Осталось приглашений: ','Invitations remaining: ')+str(result['remaining'])
            elif kind=='connected':text=self.t('VPN подключён. Доступ в интернет проверен.','VPN connected. Internet access verified.')
            else:text=self.t('Настройки проверены и сохранены.','Configuration verified and saved.')
            self.status.set_text(text)
        except Exception:self.status.set_text(self.t('Действие не выполнено. Проверьте код и сеть. Повреждённые данные требуют восстановления.','Could not complete the action. Check the code and network. Damaged data requires recovery.'))
        self.busy=False;self.sensitivity();return GLib.SOURCE_REMOVE
    def sensitivity(self):
        for widget in (self.code,self.activate,self.region,self.transport,self.prepare,self.share):widget.set_sensitive(not self.busy)
        self.connect_button.set_sensitive(not self.busy and self.driver is not None)
        self.copy.set_sensitive(not self.busy and bool(self.link.get_text()))
        self.qr.set_sensitive(not self.busy and bool(self.link.get_text()))
    def close(self,*_):
        if self.busy:return True
        if self.qr_window is not None:self.qr_window.close()
        self.link.set_text('')
        self.closed=True;self.pool.shutdown(wait=False,cancel_futures=True);Gtk.StyleContext.remove_provider_for_display(self.window.get_display(),self.provider)
        if self.on_closed:self.on_closed()
        return False
    def present(self):self.window.present()
