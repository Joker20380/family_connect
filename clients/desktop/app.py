"""Native Linux GTK 4 client. Keys and network operations stay in the backend."""
APP_VERSION='0.2.7'
ICON_PNG='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'
WORDS={'title': ('Связь для вашей семьи', 'Connectivity for your family'), 'unknown': ('Статус недоступен', 'Status unavailable'), 'off': ('Готов к подключению', 'Ready to connect'), 'on': ('Туннель включён', 'Tunnel is on'), 'connect': ('Подключить', 'Connect'), 'disconnect': ('Отключить', 'Disconnect'), 'import': ('Добавить профиль', 'Add profile'), 'check': ('Проверить внешний IP', 'Check public IP'), 'empty': ('Добавьте профиль вашего устройства', 'Add this device’s profile'), 'hint': ('Прямое подключение', 'Direct connection'), 'pending': ('Выполняется…', 'Working…'), 'error': ('Не удалось выполнить действие. Проверьте профиль, системный VPN и разрешения.', 'Operation failed. Check the profile, system VPN and permissions.'), 'retry': ('Повторить проверку', 'Retry setup'), 'install': ('Установить WireGuard', 'Install WireGuard'), 'system': ('Linux: нужен NetworkManager. Windows: официальный WireGuard и запуск от администратора.', 'Linux: NetworkManager required. Windows: official WireGuard and administrator rights required.'), 'quality': ('Включённый туннель не подтверждает доступность интернета.', 'An active tunnel does not confirm Internet connectivity.'), 'closing': ('Закрытие окна не отключает VPN. Продолжить?', 'Closing this window keeps the VPN running. Continue?'), 'checks': ('Проверка обращается к Cloudflare через текущее соединение.', 'This check contacts Cloudflare over the current connection.')}
import base64
import concurrent.futures
import locale
from pathlib import Path
import subprocess
import sys
import time
import urllib.request
import gi
gi.require_version('Gtk','4.0')
gi.require_version('Adw','1')
from gi.repository import Gtk, Adw, Gdk, Gio, GLib, Pango
from backend import backend, BackendError

CSS='''
window.fc-window { background: #0e1423; color: #e9edf7; }
.fc-window headerbar { background: #0e1423; box-shadow: none; }
.fc-brand { font-size: 17px; font-weight: 700; }
.fc-caption { color: #98a6c0; font-size: 12px; }
.fc-card { background: #182136; border: 1px solid #29344b; border-radius: 16px; padding: 18px; }
.fc-status { font-size: 20px; font-weight: 700; }
.fc-dot { color: #8796b0; }
.fc-dot.connected { color: #6ee7b7; }
.fc-window button.fc-action { min-height: 24px; padding: 11px 16px; border-radius: 12px; }
.fc-window button.fc-primary { background: #a5b4fc; color: #11172b; font-weight: 700; }
.fc-window button.fc-primary:hover { background: #bec9ff; }
.fc-window button.fc-primary:disabled { background: #2b3650; color: #93a1bc; }
.fc-window button.fc-secondary { background: #202b42; }
.fc-window button.fc-quiet { background: transparent; color: #aab7ce; }
.fc-window dropdown > button { background: #202b42; padding: 10px 14px; border-radius: 12px; }
.fc-note { color: #98a6c0; font-size: 12px; }
.fc-detail { color: #edc99b; }
'''


def translated(key,ru):return WORDS[key][0 if ru else 1]


class App:
    def __init__(self,application=None,smoke=False):
        self.ru=bool(locale.getlocale()[0] and locale.getlocale()[0].lower().startswith('ru'))
        self.driver=None;self.items=[];self.selected_id=None;self.active=None;self.busy=False;self.initializing=False
        self.closed=False;self.revision=0;self.polling=False;self.poll_error=False
        self.detail_text='';self.update_plan=None;self.updater=None;self.render_source=0;self.fit_source=0;self.fitted_height=None
        self.render_count=0;self.widget_changes=0;self.rendering=False
        self.pool=concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self.poll_pool=concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self.window=Adw.ApplicationWindow(application=application,title='Family Connect')
        self.window.add_css_class('fc-window');self.window.set_default_size(390,-1)
        self.window.set_icon_name('com.familyconnect.Client')
        self.window.connect('close-request',self.on_close)
        Adw.StyleManager.get_default().set_color_scheme(Adw.ColorScheme.FORCE_DARK)
        provider=Gtk.CssProvider();provider.load_from_data(CSS.encode())
        Gtk.StyleContext.add_provider_for_display(self.window.get_display(),provider,Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self.provider=provider
        shell=Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        header=Adw.HeaderBar();brand=Gtk.Box(spacing=9)
        texture=Gdk.Texture.new_from_bytes(GLib.Bytes.new(base64.b64decode(ICON_PNG)))
        icon=Gtk.Image.new_from_paintable(texture);icon.set_pixel_size(28);brand.append(icon)
        name=Gtk.Label(label='Family Connect');name.add_css_class('fc-brand');brand.append(name)
        header.set_title_widget(brand);shell.append(header)
        self.body=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=10)
        for side in ('top','bottom','start','end'):getattr(self.body,'set_margin_'+side)(20)
        self.body.set_margin_top(8)
        self.subtitle=self.label('fc-caption');self.body.append(self.subtitle)
        self.card=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=8);self.card.add_css_class('fc-card');self.card.set_margin_top(6);self.card.set_margin_bottom(6)
        status_row=Gtk.Box(spacing=10);self.dot=Gtk.Label(label='●');self.dot.add_css_class('fc-dot');status_row.append(self.dot)
        self.status=self.label('fc-status');status_row.append(self.status);self.card.append(status_row)
        self.hint=self.label('fc-caption');self.card.append(self.hint);self.body.append(self.card)
        self.model=Gtk.StringList.new([]);self.choose=Gtk.DropDown(model=self.model);self.choose.set_hexpand(True)
        self.choose.set_tooltip_text('WireGuard');self.choose.connect('notify::selected',self.selection_changed);self.body.append(self.choose)
        self.toggle=self.button('fc-primary',self.toggle_vpn)
        self.add=self.button('fc-secondary',self.import_profile)
        self.check=self.button('fc-quiet',self.check_ip)
        self.note=self.label('fc-note');self.note.set_margin_top(4);self.body.append(self.note)
        self.detail=self.label('fc-detail');self.body.append(self.detail)
        self.retry=self.button('fc-secondary',lambda:self.submit(self.initialize,'initialized'))
        self.update_button=self.button('fc-quiet',self.update_application)
        self.scroll=Gtk.ScrolledWindow();self.scroll.set_policy(Gtk.PolicyType.NEVER,Gtk.PolicyType.AUTOMATIC)
        self.scroll.set_propagate_natural_height(True)
        monitors=self.window.get_display().get_monitors()
        self.height_limit=max(360,monitors.get_item(0).get_geometry().height-160) if monitors.get_n_items() else 720
        self.scroll.set_max_content_height(self.height_limit);self.scroll.set_child(self.body);shell.append(self.scroll)
        footer=Gtk.Box(spacing=8);footer.set_margin_start(20);footer.set_margin_end(20);footer.set_margin_bottom(14)
        version=Gtk.Label(label='v'+APP_VERSION,xalign=0);version.add_css_class('fc-caption');version.set_hexpand(True);footer.append(version)
        self.language_button=Gtk.Button(label='RU / EN');self.language_button.add_css_class('flat');self.language_button.connect('clicked',lambda _:self.language());footer.append(self.language_button)
        shell.append(footer);self.window.set_content(shell)
        self.last_profiles=None
        if not smoke:self.register_icon();self.submit(self.initialize,'initialized')
        if self.render_source:GLib.source_remove(self.render_source);self.render_source=0
        self.render();self.poll_source=GLib.timeout_add_seconds(3,self.refresh)
    def label(self,css):
        label=Gtk.Label(xalign=0);label.set_wrap(True);label.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
        label.set_max_width_chars(36);label.set_hexpand(True);label.add_css_class(css);return label
    def button(self,css,action):
        button=Gtk.Button();button.set_hexpand(True);button.add_css_class('fc-action');button.add_css_class(css)
        button.connect('clicked',lambda _:action());self.body.append(button);return button
    def t(self,key):return translated(key,self.ru)
    def present(self):self.window.present()
    def set_value(self,widget,prop,value):
        if widget.get_property(prop)!=value:widget.set_property(prop,value);self.widget_changes+=1
    def paint(self):
        if not self.closed and not self.render_source:self.render_source=GLib.idle_add(self.render)
    def render(self):
        self.render_source=0
        if self.closed:return GLib.SOURCE_REMOVE
        self.render_count+=1;self.rendering=True;before=self.widget_changes
        try:
            self.set_value(self.subtitle,'label',self.t('title'))
            text=('Проверяем подключение' if self.ru else 'Checking connection') if self.initializing else self.t('unknown' if self.active is None else ('on' if self.active else 'off'))
            self.set_value(self.status,'label',text);self.set_value(self.hint,'label',self.t('hint'))
            connected=self.active is True
            if self.dot.has_css_class('connected')!=connected:
                (self.dot.add_css_class if connected else self.dot.remove_css_class)('connected');self.widget_changes+=1
            names=tuple(name for _,name in self.items) or ((('Загружаем профили…' if self.ru else 'Loading profiles…') if self.initializing else self.t('empty')),)
            if names!=self.last_profiles:
                selected=self.selected_id;self.last_profiles=names
                if selected not in [item[0] for item in self.items]:selected=self.items[-1][0] if self.items else None
                self.selected_id=selected
                self.model.splice(0,self.model.get_n_items(),list(names))
                self.choose.set_selected(next((i for i,item in enumerate(self.items) if item[0]==selected),max(0,len(self.items)-1)))
                self.widget_changes+=1
            self.set_value(self.choose,'sensitive',bool(self.items) and not self.busy)
            for widget,text,enabled in (
                (self.toggle,self.t('disconnect' if connected else 'connect'),not self.busy and bool(self.items) and self.active is not None),
                (self.add,self.t('import'),not self.busy and self.driver is not None),
                (self.check,self.t('check'),connected and not self.busy),
                (self.retry,self.t('retry'),not self.busy),
                (self.update_button,('Установить обновление' if self.ru else 'Install update') if self.update_plan else ('Проверить обновления' if self.ru else 'Check for updates'),not self.busy)):
                self.set_value(widget,'label',text);self.set_value(widget,'sensitive',enabled)
            self.set_value(self.note,'label',self.t('quality'));self.set_value(self.detail,'label',self.detail_text)
            self.set_value(self.detail,'visible',bool(self.detail_text));self.set_value(self.retry,'visible',self.driver is None and not self.initializing)
        finally:self.rendering=False
        if before!=self.widget_changes and not self.fit_source:self.fit_source=GLib.idle_add(self.fit_height)
        return GLib.SOURCE_REMOVE
    def fit_height(self):
        self.fit_source=0
        if self.closed:return GLib.SOURCE_REMOVE
        width=max(390,self.window.get_width())
        _,natural,_,_=self.window.get_content().measure(Gtk.Orientation.VERTICAL,width)
        if natural!=self.fitted_height:
            self.fitted_height=natural;self.window.set_default_size(width,natural)
        return GLib.SOURCE_REMOVE
    def language(self):self.ru=not self.ru;self.paint()
    def set_detail(self,text):self.detail_text=text;self.paint()
    def selected(self):
        return self.selected_id
    def selection_changed(self,*_):
        if not self.rendering:
            index=self.choose.get_selected();self.selected_id=self.items[index][0] if 0<=index<len(self.items) else None
            self.refresh()
    def initialize(self):
        driver=backend();items=driver.profiles();active=driver.active(items[-1][0]) if items else False
        return driver,items,active
    def submit(self,fn,kind='profiles'):
        if self.busy or self.closed:return
        self.busy=True;self.revision+=1
        if kind=='initialized':self.initializing=True
        self.paint();revision=self.revision;future=self.pool.submit(fn)
        future.add_done_callback(lambda f:GLib.idle_add(self.complete,kind,f,revision,None))
    def complete(self,kind,future,revision,ident):
        if self.closed:return GLib.SOURCE_REMOVE
        if kind=='poll':
            self.polling=False
            if revision!=self.revision or ident!=self.selected() or self.busy:return GLib.SOURCE_REMOVE
            try:active=future.result();error=False
            except Exception:active=None;error=True
            if active is self.active and error==self.poll_error:return GLib.SOURCE_REMOVE
            self.active=active
            if error:self.detail_text=self.t('error')
            elif self.poll_error:self.detail_text=''
            self.poll_error=error;self.paint();return GLib.SOURCE_REMOVE
        self.busy=False
        try:
            result=future.result()
            if kind=='initialized':self.driver,self.items,self.active=result;self.selected_id=self.items[-1][0] if self.items else None;self.initializing=False;self.detail_text='' if self.items else self.t('empty')
            elif kind=='profiles':self.items=result;self.active=None;self.detail_text='' if result else self.t('empty')
            elif kind=='state':self.active=result
            elif kind=='ip':self.detail_text=result
            elif kind=='updates':
                self.update_plan=result;self.detail_text=(('Доступна версия ' if self.ru else 'Version available: ')+result['version']) if result else ('Установлена последняя версия.' if self.ru else 'You are up to date.')
            elif kind=='update_installed':
                subprocess.Popen([sys.executable,str(result)],start_new_session=True);self.close(True);return GLib.SOURCE_REMOVE
        except Exception as exc:
            if kind in ('updates','update_installed'):
                self.detail_text='Обновление недоступно или не прошло проверку. Текущая версия сохранена.' if self.ru else 'Update unavailable or verification failed. Current version preserved.'
            else:
                self.active=None;self.initializing=False
                self.detail_text=self.t('error')
                if isinstance(exc,BackendError):self.detail_text+='\n'+str(exc)
        self.paint();return GLib.SOURCE_REMOVE
    def refresh(self):
        if self.closed:return GLib.SOURCE_REMOVE
        ident=self.selected()
        if self.busy or self.polling or self.driver is None or not ident:return GLib.SOURCE_CONTINUE
        self.polling=True;revision=self.revision;driver=self.driver
        future=self.poll_pool.submit(lambda:driver.active(ident))
        future.add_done_callback(lambda f:GLib.idle_add(self.complete,'poll',f,revision,ident))
        return GLib.SOURCE_CONTINUE
    def toggle_vpn(self):
        ident=self.selected();active=self.active
        if self.busy or not ident or active is None:return
        driver=self.driver
        def action():
            (driver.disconnect if active else driver.connect)(ident);return driver.active(ident)
        self.submit(action,'state')
    def import_profile(self):
        if self.busy:return
        if self.active:self.set_detail('Сначала отключите туннель.' if self.ru else 'Disconnect the tunnel first.');return
        chooser=Gtk.FileChooserNative(title=self.t('import'),transient_for=self.window,action=Gtk.FileChooserAction.OPEN,accept_label=self.t('import'),cancel_label='Отмена' if self.ru else 'Cancel')
        filter_=Gtk.FileFilter();filter_.set_name('WireGuard (*.conf)');filter_.add_pattern('*.conf');chooser.add_filter(filter_)
        def response(dialog,result):
            file=dialog.get_file() if result==Gtk.ResponseType.ACCEPT else None;dialog.destroy();self.file_chooser=None
            if file and file.get_path():
                def action():self.driver.import_profile(file.get_path());return self.driver.profiles()
                self.submit(action)
        self.file_chooser=chooser;chooser.set_modal(True)
        chooser.connect('response',response);chooser.show()
    def check_ip(self):
        ident=self.selected();driver=self.driver
        if self.busy or not ident or not self.active:return
        self.detail_text=self.t('checks')
        def action():
            if not driver.active(ident):raise RuntimeError('Tunnel is down')
            with urllib.request.urlopen('https://www.cloudflare.com/cdn-cgi/trace',timeout=10) as response:
                values=dict(line.split('=',1) for line in response.read(4096).decode().splitlines() if '=' in line)
            if not driver.active(ident):raise RuntimeError('Tunnel changed')
            return 'IP: '+values.get('ip','?')+' · '+values.get('loc','?')
        self.submit(action,'ip')
    def confirm(self,text,action,accepted):
        dialog=Adw.MessageDialog(transient_for=self.window,heading='Family Connect',body=text,modal=True)
        dialog.add_response('cancel','Отмена' if self.ru else 'Cancel');dialog.add_response('accept',action)
        dialog.set_response_appearance('accept',Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response('cancel');dialog.set_close_response('cancel')
        dialog.connect('response',lambda _,response:accepted() if response=='accept' and not self.closed else None)
        dialog.present();return dialog
    def update_application(self):
        if self.busy:return
        from updates import Updater
        if self.updater is None:self.updater=Updater(APP_VERSION)
        if self.update_plan is None:self.submit(self.updater.check,'updates');return
        plan=self.update_plan
        def install():
            self.submit(lambda:self.updater.install(plan,self.updater.download(plan)),'update_installed')
        text=(f"Скачать и установить версию {plan['version']}? Окно перезапустится. Профили и ключи сохранятся." if self.ru else f"Download and install {plan['version']}? The window will restart. Profiles and keys will be preserved.")
        self.confirm(text,'Установить обновление' if self.ru else 'Install update',install)
    def on_close(self,*_):
        if self.closed:return False
        if self.busy:return True
        if self.active:self.confirm(self.t('closing'),'Закрыть окно' if self.ru else 'Close window',lambda:self.close(True));return True
        self.close(True);return True
    def close(self,confirmed=False):
        if self.closed or self.busy:return False
        if self.active and not confirmed:return self.on_close()
        self.closed=True
        if self.render_source:GLib.source_remove(self.render_source);self.render_source=0
        if self.fit_source:GLib.source_remove(self.fit_source);self.fit_source=0
        GLib.source_remove(self.poll_source)
        self.pool.shutdown(wait=False,cancel_futures=True);self.poll_pool.shutdown(wait=False,cancel_futures=True)
        Gtk.StyleContext.remove_provider_for_display(self.window.get_display(),self.provider)
        self.window.destroy();return False
    @staticmethod
    def register_icon(_=None):
        root=Path.home()/'.local/share/family-connect'
        if Path(__file__).resolve().parent!=(root/'current').resolve():return
        try:
            from updates import atomic
            raw=base64.b64decode(ICON_PNG)
            if not (root/'app.png').is_file() or (root/'app.png').read_bytes()!=raw:atomic(root/'app.png',raw)
            entry=Path.home()/'.local/share/applications/family-connect.desktop'
            if entry.is_file() and not entry.is_symlink():
                lines=[s for s in entry.read_text().splitlines() if not s.startswith(('Icon=','StartupWMClass='))]
                data=('\n'.join(lines)+'\nIcon='+str(root/'app.png')+'\nStartupWMClass=com.familyconnect.Client\n').encode()
                if entry.read_bytes()!=data:atomic(entry,data)
                alias=entry.with_name('com.familyconnect.Client.desktop');hidden=data+b'NoDisplay=true\n'
                if not alias.is_file() or alias.read_bytes()!=hidden:atomic(alias,hidden)
        except OSError:pass


def main():
    application=Adw.Application(application_id='com.familyconnect.Client',flags=Gio.ApplicationFlags.NON_UNIQUE)
    def activate(application):
        app=App(application,smoke='--smoke' in sys.argv);application.client=app;app.present()
        if '--smoke' in sys.argv:GLib.timeout_add(300,app.close,True)
    application.connect('activate',activate)
    return application.run([sys.argv[0]])


if __name__=='__main__':raise SystemExit(main())
