"""Native Linux GTK 4 client. Keys and network operations stay in the backend."""
APP_VERSION='0.2.9'
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
from gi.repository import Gtk, Adw, Gdk, Gio, GLib, Pango, Graphene, GdkPixbuf
from backend import backend, BackendError, AuthorizationError, RecoveryPolicy, ConnectionBusy, StaleConnection, ConnectionSnapshot

CSS='''
 .fc-shell { background: #03110e; }
window.fc-window { background: #03110e; color: #dafff2; font-family: monospace; }
.fc-window headerbar { background: #03110e; box-shadow: none; }
.fc-brand { font-size: 17px; font-weight: 700; }
.fc-caption, .fc-note { color: #99c4b5; font-size: 12px; }
.fc-card { background: transparent; border: none; padding: 0; }
.fc-status { font-size: 16px; font-weight: 400; }
.fc-window button.fc-action label { font-weight: 400; }
.fc-window button.fc-action:focus-visible { outline: 1px solid #98f7d8; outline-offset: -4px; }
.fc-dot { color: #ffad46; }
.fc-dot.connected { color: #98f7d8; }
.fc-window button.fc-action { background: transparent; background-image: none; border: none; box-shadow: none; min-height: 46px; padding: 0; color: #dafff2; }
.fc-window button.fc-action:disabled { color: #75988a; }
.fc-window dropdown > button { background: #072018; color: #dafff2; border: 1px solid #438e79; padding: 10px 14px; border-radius: 0; }
.fc-detail { color: #ffad46; }
.fc-window button.fc-nav { padding: 0; min-height: 58px; font-size: 9px; }
'''


def terminal_texture(svg):
    loader=GdkPixbuf.PixbufLoader.new_with_type('svg');loader.write(svg.encode());loader.close()
    return Gdk.Texture.new_for_pixbuf(loader.get_pixbuf())


def terminal_frame(snapshot,widget,fill='#072018',stroke='#438e79',extra=''):
    w,h=widget.get_width(),widget.get_height()
    if min(w,h)<4:return
    c=min(6,w/5,h/4)
    scale=widget.get_scale_factor()
    key=(w,h,scale,fill,stroke,extra)
    if getattr(widget,'terminal_key',None)!=key:
        svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="{w*scale}" height="{h*scale}" viewBox="0 0 {w} {h}"><path d="M{c},1 H{w-c} L{w-1},{c} V{h-c} L{w-c},{h-1} H{c} L1,{h-c} V{c} Z" fill="{fill}" stroke="{stroke}" stroke-width=".8"/>{extra}</svg>'
        widget.terminal_cache=terminal_texture(svg);widget.terminal_key=key
    snapshot.append_texture(widget.terminal_cache,Graphene.Rect().init(0,0,w,h))


class TerminalButton(Gtk.Button):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.connect("notify::label",self.prepare_label)
    def prepare_label(self,*_):
        child=self.get_child()
        if isinstance(child,Gtk.Label):
            child.set_margin_start(2 if self.has_css_class("fc-nav") else 12)
            child.set_margin_end(2 if self.has_css_class("fc-nav") else 12)
            if self.has_css_class("fc-nav"):
                child.set_margin_top(29);child.set_margin_bottom(6)
            if self.has_css_class("fc-primary"):
                child.set_xalign(0);child.set_margin_end(90)
    def do_snapshot(self,snapshot):
        selected=self.has_css_class('selected') or self.has_css_class('connected')
        stroke='#ffad46' if self.has_css_class('selected') else '#438e79'
        fill='#103d2e' if self.get_state_flags() & Gtk.StateFlags.PRELIGHT else '#072018'
        extra=''
        if self.has_css_class('fc-primary'):
            w,h=self.get_width(),self.get_height();x=w-78;y=h/2
            color='#98f7d8' if selected else '#ffad46'
            if not self.get_sensitive():color='#75988a'
            extra=f'<rect x="{x}" y="{y-13}" width="62" height="26" rx="13" fill="#17392d" stroke="{color}"/><circle cx="{x+(48 if selected else 14)}" cy="{y}" r="10" fill="{color}"/>'
        if self.has_css_class('fc-nav'):
            color='#ffad46' if self.has_css_class('selected') else '#98f7d8'
            fill='#072018' if self.has_css_class('selected') else '#03110e'
            icons={
                'status':'<path d="M1 13 H6 L9 4 L13 21 L16 10 L19 13 H23"/>',
                'messenger':'<path d="M4 3 H20 Q22 3 22 5 V16 Q22 18 20 18 H12 L6 23 V18 H4 Q2 18 2 16 V5 Q2 3 4 3Z"/>',
                'route':'<circle cx="12" cy="4" r="3"/><circle cx="4" cy="20" r="3"/><circle cx="20" cy="20" r="3"/><path d="M12 7 L4 17 M12 7 L20 17"/>',
                'settings':'<circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/><path d="M12 2 V6 M12 18 V22 M2 12 H6 M18 12 H22 M5 5 L8 8 M16 16 L19 19 M5 19 L8 16 M16 8 L19 5"/>'}
            extra=f'<g transform="translate({self.get_width()/2-10.5} 9) scale(.875)" fill="none" stroke="{color}" stroke-width="1.2">{icons.get(getattr(self,"nav_page",""),"")}</g>'
        terminal_frame(snapshot,self,fill,stroke,extra)
        Gtk.Button.do_snapshot(self,snapshot)


class TerminalCard(Gtk.Box):
    def do_snapshot(self,snapshot):
        terminal_frame(snapshot,self)
        Gtk.Box.do_snapshot(self,snapshot)


class TerminalHeader(Gtk.Box):
    def __init__(self):
        super().__init__();self.set_size_request(-1,72)
    def do_snapshot(self,snapshot):
        w=self.get_width();size=min(27,max(15,(w-90)/8.8))
        logo='<g transform="translate(17 12) scale(.46)"><path fill-rule="evenodd" fill="#98f7d8" d="M50 3 L90 25 L90 77 L50 99 L10 77 L10 25 Z M50 12 L18 30 L18 73 L50 91 L82 73 L82 30 Z"/><path fill="#8debcd" d="M23 36 L50 20 L50 99 L23 81 Z"/><path fill="#c1ffe9" d="M55 50 H60 V65 H55 Z"/><path fill="#255e4e" d="M50 12 L82 30 V36 L50 19 Z"/></g>'
        text=f'<text x="77" y="33" fill="#dafff2" font-family="sans-serif" font-weight="900" font-size="{size}">FAMILY CONNECT</text><text x="78" y="54" fill="#98f7d8" font-family="monospace" font-size="9">SECURE NETWORK TERMINAL</text><path d="M78 40 H205 M78 60 H205" stroke="#438e79" opacity=".25"/><path d="M8 28 v5 M8 37 v5 M8 46 v5" stroke="#ffad46" stroke-width="2"/>'
        terminal_frame(snapshot,self,'#03110e','#98f7d8',logo+text)


class TerminalGauge(Gtk.Box):
    """Static Android composition; motion design is a separate follow-up."""
    def __init__(self):
        super().__init__();self.set_size_request(-1,230);self.connected=False
    def do_snapshot(self,snapshot):
        w,h=self.get_width(),self.get_height();scale=self.get_scale_factor()
        if min(w,h)<4:return
        key=(w,h,scale,self.connected)
        if getattr(self,'gauge_key',None)!=key:
            import math
            x,y=w/2,h/2;r=min(w/2-24,h/2-16)
            color='#98f7d8' if self.connected else '#ffad46'
            marks=''.join(f'<path d="M{x+math.cos(a)*r*.87:.2f} {y+math.sin(a)*r*.87:.2f} L{x+math.cos(a)*r*.92:.2f} {y+math.sin(a)*r*.92:.2f}" opacity="{.8 if i%6==0 else .23}"/>' for i in range(48) for a in [i*math.pi/24])
            svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w*scale}" height="{h*scale}" viewBox="0 0 {w} {h}">
            <g fill="none" stroke="#438e79" stroke-width=".7"><circle cx="{x}" cy="{y}" r="{r}"/><circle cx="{x}" cy="{y}" r="{r*.67}"/></g>
            <g stroke="{color}" stroke-width="2">{marks}</g>
            <text x="{x}" y="{y+9}" text-anchor="middle" fill="{color}" font-family="sans-serif" font-weight="500" font-size="28">VPN</text></svg>'''
            self.gauge_cache=terminal_texture(svg);self.gauge_key=key
        snapshot.append_texture(self.gauge_cache,Graphene.Rect().init(0,0,w,h))




def translated(key,ru):return WORDS[key][0 if ru else 1]


class App:
    def __init__(self,application=None,smoke=False):
        self.ru=bool(locale.getlocale()[0] and locale.getlocale()[0].lower().startswith('ru'))
        self.driver=None;self.items=[];self.selected_id=None;self.active=None;self.busy=False;self.initializing=False
        self.closed=False;self.revision=0;self.polling=False;self.poll_error=False
        self.recovery=RecoveryPolicy();self.operation_generation=None
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
        shell=Gtk.Box(orientation=Gtk.Orientation.VERTICAL);shell.add_css_class("fc-shell")
        header=Adw.HeaderBar();brand=Gtk.Box(spacing=9)
        texture=Gdk.Texture.new_from_bytes(GLib.Bytes.new(base64.b64decode(ICON_PNG)))
        icon=Gtk.Image.new_from_paintable(texture);icon.set_pixel_size(28);brand.append(icon)
        name=Gtk.Label(label='Family Connect');name.add_css_class('fc-brand');brand.append(name)
        header.set_title_widget(Gtk.Label(label=''));shell.append(header)
        brand_header=TerminalHeader();brand_header.set_margin_start(12);brand_header.set_margin_end(12);shell.append(brand_header)
        self.body=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=10)
        for side in ('top','bottom','start','end'):getattr(self.body,'set_margin_'+side)(12)
        self.body.set_margin_top(0)
        self.subtitle=self.label('fc-caption')
        self.card=TerminalCard(orientation=Gtk.Orientation.VERTICAL,spacing=8);self.card.add_css_class('fc-card');self.card.set_margin_top(2);self.card.set_margin_bottom(0)
        self.gauge=TerminalGauge();self.card.append(self.gauge)
        status_row=Gtk.Box(spacing=10);status_row.set_margin_top(0);status_row.set_margin_start(18);status_row.set_margin_end(18);self.dot=Gtk.Label(label='●');self.dot.add_css_class('fc-dot');self.dot.set_visible(False);status_row.append(self.dot)
        self.status=self.label('fc-status');self.status.set_xalign(.5);self.status.set_justify(Gtk.Justification.CENTER);status_row.append(self.status);self.card.append(status_row)
        self.hint=self.label('fc-caption');self.hint.set_margin_start(18);self.hint.set_margin_end(18);self.hint.set_margin_bottom(4);self.hint.set_xalign(.5);self.card.append(self.hint);self.body.append(self.card)
        self.model=Gtk.StringList.new([]);self.choose=Gtk.DropDown(model=self.model);self.choose.set_hexpand(True)
        self.choose.set_tooltip_text('WireGuard / AmneziaWG');self.choose.connect('notify::selected',self.selection_changed);self.body.append(self.choose)
        self.friends_owner_class=None
        try:
            from provisioning.friends_owner import FriendsOwner
            self.friends_owner_class=FriendsOwner
        except ImportError:pass  # Standalone six-file archive has no paired core.
        self.friends_button=self.button('fc-secondary',self.open_friends) if self.friends_owner_class else None
        self.toggle=self.button('fc-primary',self.toggle_vpn)
        self.body.remove(self.toggle);self.card.append(self.toggle)
        for edge in ('start','end','bottom'):getattr(self.toggle,'set_margin_'+edge)(10)
        self.add=self.button('fc-secondary',self.import_profile)
        self.check=self.button('fc-quiet',self.check_ip)
        self.note=self.label('fc-note');self.note.set_margin_top(4);self.body.append(self.note)
        self.detail=self.label('fc-detail');self.body.append(self.detail)
        self.retry=self.button('fc-secondary',lambda:self.submit(self.initialize,'initialized'))
        self.update_button=self.button('fc-quiet',self.update_application)
        self.tcp_button=self.button('fc-quiet',self.install_tcp)
        self.scroll=Gtk.ScrolledWindow();self.scroll.set_policy(Gtk.PolicyType.NEVER,Gtk.PolicyType.AUTOMATIC)
        self.scroll.set_propagate_natural_height(True)
        monitors=self.window.get_display().get_monitors()
        self.height_limit=max(360,monitors.get_item(0).get_geometry().height-160) if monitors.get_n_items() else 720
        self.scroll.set_max_content_height(self.height_limit);self.scroll.set_vexpand(True);self.scroll.set_child(self.body);shell.append(self.scroll)
        self.page='status'
        self.language_button=TerminalButton(label='RU / EN');self.language_button.add_css_class('fc-action');self.language_button.connect('clicked',lambda _:self.language());self.body.append(self.language_button)
        self.version_label=Gtk.Label(label='v'+APP_VERSION,xalign=0);self.version_label.add_css_class('fc-caption');self.body.append(self.version_label)
        self.route_title=Gtk.Label(label='',xalign=0,wrap=True);self.body.prepend(self.route_title)
        self.messenger_note=Gtk.Label(label='',xalign=0,wrap=True);self.body.append(self.messenger_note)
        self.pages={'status':[self.card,self.toggle,self.note], 'route':[self.route_title,self.choose,self.check],
            'settings':[self.add,self.update_button,self.tcp_button,self.language_button,self.version_label]+([self.friends_button] if self.friends_button else []), 'messenger':[self.messenger_note]}
        footer=Gtk.Box(spacing=2);footer.set_homogeneous(True);footer.set_margin_start(12);footer.set_margin_end(12);footer.set_margin_bottom(12)
        self.nav={}
        for page in ('status','messenger','route','settings'):
            button=TerminalButton();button.nav_page=page;button.add_css_class('fc-action');button.add_css_class('fc-nav');button.set_hexpand(True)
            button.connect('clicked',lambda _,p=page:self.select_page(p));footer.append(button);self.nav[page]=button
        shell.append(footer);self.window.set_content(shell)
        self.last_profiles=None
        if not smoke:self.register_icon();self.submit(self.initialize,'initialized')
        if self.render_source:GLib.source_remove(self.render_source);self.render_source=0
        self.render();self.poll_source=GLib.timeout_add_seconds(3,self.refresh)
    def label(self,css):
        label=Gtk.Label(xalign=0);label.set_wrap(True);label.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
        label.set_max_width_chars(36);label.set_hexpand(True);label.add_css_class(css);return label
    def button(self,css,action):
        button=TerminalButton();button.set_hexpand(True);button.add_css_class('fc-action');button.add_css_class(css)
        button.connect('clicked',lambda _:action());self.body.append(button);return button
    def t(self,key):return translated(key,self.ru)
    def present(self):self.window.present()
    def set_value(self,widget,prop,value):
        if widget.get_property(prop)!=value:widget.set_property(prop,value);self.widget_changes+=1
    def paint(self):
        if not self.closed and not self.render_source:self.render_source=GLib.idle_add(self.render)
    def render(self):
        if self.friends_button:self.friends_button.set_label("Доступ по приглашению" if self.ru else "Invitation access");self.friends_button.set_sensitive(not self.busy)
        self.render_source=0
        if self.closed:return GLib.SOURCE_REMOVE
        self.render_count+=1;self.rendering=True;before=self.widget_changes
        try:
            self.set_value(self.subtitle,'label',self.t('title'))
            text=('Проверяем подключение' if self.ru else 'Checking connection') if self.initializing else self.t('unknown' if self.active is None else ('on' if self.active else 'off'))
            self.set_value(self.status,'label',text);self.set_value(self.hint,'label',self.t('hint'))
            connected=self.active is True
            if self.gauge.connected!=connected:self.gauge.connected=connected;self.gauge.queue_draw()
            if self.toggle.has_css_class('connected')!=connected:
                (self.toggle.add_css_class if connected else self.toggle.remove_css_class)('connected');self.toggle.queue_draw()
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
            self.set_value(self.tcp_button,'visible','--awg-pilot' in sys.argv)
            self.set_value(self.tcp_button,'label','Установить / обновить TCP' if self.ru else 'Install / update TCP')
            self.set_value(self.tcp_button,'sensitive',not self.busy and self.active is False)
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
            self.apply_page()
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
    def select_page(self,page):
        self.page=page;self.paint()
    def apply_page(self):
        for page,widgets in self.pages.items():
            for widget in widgets:
                visible=page==self.page and (widget is not self.tcp_button or self.friends_owner_class is not None or '--awg-pilot' in sys.argv)
                self.set_value(widget,'visible',visible)
        names={'status':('СТАТУС','STATUS'),'messenger':('МЕССЕНДЖЕР','MESSENGER'),'route':('МАРШРУТ','ROUTE'),'settings':('НАСТРОЙКИ','SETTINGS')}
        for page,button in self.nav.items():
            self.set_value(button,'label',names[page][0 if self.ru else 1])
            if button.has_css_class('selected')!=(page==self.page):
                (button.add_css_class if page==self.page else button.remove_css_class)('selected');button.queue_draw()
        self.set_value(self.route_title,'label','Выберите профиль подключения и проверьте внешний IP.' if self.ru else 'Choose a connection profile and check your public IP.')
        self.set_value(self.messenger_note,'label','Мессенджер пока доступен в Android. Версия для компьютера в разработке.' if self.ru else 'Messaging is currently available on Android. Desktop messaging is in development.')

    def open_friends(self):
        if self.busy or not self.friends_owner_class:return
        from friends_ui import FriendsWindow
        path=Path.home()/'.local/share/family-connect/friends-identity'
        owner=self.friends_owner_class(path,Path(__file__).with_name('update.pub'))
        def finished():
            self.busy=False
            if not self.closed:self.submit(self.initialize,'initialized')
        self.friends_window=FriendsWindow(self.window,owner,self.ru,driver=self.driver,on_close=finished)
        self.busy=True;self.revision+=1;self.recovery.stop();self.paint()
        self.friends_window.present()

    def language(self):self.ru=not self.ru;self.paint()
    def set_detail(self,text):self.detail_text=text;self.paint()
    def selected(self):
        return self.selected_id
    def selection_changed(self,*_):
        if not self.rendering:
            self.recovery.stop()
            index=self.choose.get_selected();self.selected_id=self.items[index][0] if 0<=index<len(self.items) else None
            self.refresh()
    def initialize(self):
        driver=backend()
        if self.friends_owner_class:
            owner=self.friends_owner_class(Path.home()/'.local/share/family-connect/friends-identity',Path(__file__).with_name('update.pub'))
            owner.recover(driver)
        items=driver.profiles()
        active_ids=[ident for ident,_ in items if driver.active(ident)]
        # Keep the selected connection last for the existing UI result contract.
        if active_ids:items=sorted(items,key=lambda item:item[0]==active_ids[0])
        active=bool(active_ids)
        return driver,items,active
    def submit(self,fn,kind='profiles'):
        if self.busy or self.closed:return
        self.busy=True;self.revision+=1
        if kind=='initialized':self.initializing=True
        self.paint();revision=self.revision;future=self.pool.submit(fn)
        future.add_done_callback(lambda f:GLib.idle_add(self.complete,kind,f,revision,None))
    def complete(self,kind,future,revision,ident):
        if self.closed:return GLib.SOURCE_REMOVE
        if kind in ('poll','health'):
            try:observed=future.result()
            except ConnectionBusy:
                if revision!=self.revision or ident!=self.selected() or self.busy:
                    self.polling=False;return GLib.SOURCE_REMOVE
                self.polling=False;self.recovery.stop()
                self.detail_text=('Обновляются настройки подключения. Ожидаем завершения.' if self.ru else 'Connection settings are being updated. Waiting for completion.')
                self.paint();return GLib.SOURCE_REMOVE
            except Exception:observed=None
            if isinstance(observed,ConnectionSnapshot):
                if revision!=self.revision or ident!=self.selected() or self.busy:
                    self.polling=False;return GLib.SOURCE_REMOVE
                if observed.generation!=self.operation_generation:
                    self.operation_generation=observed.generation
                    self.polling=False;self.recovery.stop();self.revision+=1
                    self.items=observed.items
                    ids=[key for key,_ in self.items]
                    self.selected_id=(observed.active_ids[0] if observed.active_ids else
                        (ident if ident in ids else (ids[-1] if ids else None)))
                    self.active=self.selected_id in observed.active_ids
                    self.detail_text=''
                    if self.active:self.recovery.arm(self.selected_id)
                    self.paint();return GLib.SOURCE_REMOVE
                from concurrent.futures import Future
                completed=Future()
                completed.set_result((observed.active,observed.healthy) if kind=='health' else observed.active)
                future=completed
        if kind=='health':
            self.polling=False
            if revision!=self.revision or ident!=self.selected() or self.busy or self.recovery.identity!=ident:
                return GLib.SOURCE_REMOVE
            try:self.active,healthy=future.result()
            except Exception:healthy=False
            automatic=getattr(self.driver,'allows_automatic_recovery',lambda _:True)(ident)
            should_recover=self.recovery.observe(healthy,allow_recovery=automatic)
            if should_recover:
                self.detail_text='Восстанавливаем соединение…' if self.ru else 'Restoring connection…'
                driver=self.driver;generation=self.operation_generation
                def restore():
                    if hasattr(driver,'recover_if_current'):
                        return driver.recover_if_current(ident,generation)
                    driver.recover(ident);return driver.active(ident)
                self.submit(restore,'recovered')
            elif not healthy and not automatic and self.recovery.failures>=2:
                self.detail_text=('Проверки связи не проходят. При необходимости переподключитесь вручную.' if self.ru else 'Connection checks are failing. Reconnect manually if needed.')
            elif self.recovery.exhausted:
                self.detail_text='Автовосстановление остановлено. Повторите подключение.' if self.ru else 'Recovery stopped. Reconnect to try again.'
            elif healthy and self.detail_text in ('Связь нестабильна. Проверяем повторно…','Connection unstable. Checking again…','Проверки связи не проходят. При необходимости переподключитесь вручную.','Connection checks are failing. Reconnect manually if needed.'):
                self.detail_text=''
            elif not healthy:
                self.detail_text='Связь нестабильна. Проверяем повторно…' if self.ru else 'Connection unstable. Checking again…'
            self.paint();return GLib.SOURCE_REMOVE
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
            elif kind=='connected':
                self.active=result
                if result and hasattr(self.driver,'supports_recovery') and self.driver.supports_recovery(self.selected()):
                    self.recovery.arm(self.selected())
                self.detail_text=''
            elif kind=='recovered':
                self.active=result;self.recovery.recovered(bool(result))
                self.detail_text=('Соединение восстановлено.' if self.ru else 'Connection restored.') if result else self.t('error')
            elif kind=='state':self.active=result
            elif kind=='ip':self.detail_text=result
            elif kind=='updates':
                self.update_plan=result;self.detail_text=(('Доступна версия ' if self.ru else 'Version available: ')+result['version']) if result else ('Установлена последняя версия.' if self.ru else 'You are up to date.')
            elif kind=='tcp_installed':
                self.detail_text='TCP установлен. Добавьте TCP-профиль для подключения.' if self.ru else 'TCP installed. Add a TCP profile to connect.'
            elif kind=='update_installed':
                subprocess.Popen([sys.executable,str(result)],start_new_session=True);self.close(True);return GLib.SOURCE_REMOVE
        except Exception as exc:
            if kind=='recovered':
                if isinstance(exc,(AuthorizationError,ConnectionBusy,StaleConnection)):self.recovery.stop()
                else:self.recovery.recovered(False)
            if kind=='tcp_installed':
                self.detail_text=(('Установка TCP отменена.' if self.ru else 'TCP installation cancelled.') if isinstance(exc,AuthorizationError) else ('Не удалось установить TCP. Проверьте интернет и системный установщик; TCP должен быть отключён.' if self.ru else 'TCP installation failed. Check Internet access and system updater; TCP must be disconnected.'))
            elif kind in ('updates','update_installed'):
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
        if self.recovery.due(ident):
            kind='health'
            future=self.poll_pool.submit(lambda:driver.poll_state(ident,True) if hasattr(driver,'poll_state') else (driver.active(ident),driver.healthy(ident)))
        else:
            kind='poll';future=self.poll_pool.submit(lambda:driver.poll_state(ident) if hasattr(driver,'poll_state') else driver.active(ident))
        future.add_done_callback(lambda f:GLib.idle_add(self.complete,kind,f,revision,ident))
        return GLib.SOURCE_CONTINUE
    def toggle_vpn(self):
        ident=self.selected();active=self.active
        if self.busy or not ident or active is None:return
        self.recovery.stop()
        driver=self.driver
        def action():
            (driver.disconnect if active else driver.connect)(ident);return driver.active(ident)
        self.submit(action,'state' if active else 'connected')
    def import_profile(self):
        if self.busy:return
        if self.active:self.set_detail('Сначала отключите туннель.' if self.ru else 'Disconnect the tunnel first.');return
        chooser=Gtk.FileChooserNative(title=self.t('import'),transient_for=self.window,action=Gtk.FileChooserAction.OPEN,accept_label=self.t('import'),cancel_label='Отмена' if self.ru else 'Cancel')
        filter_=Gtk.FileFilter();filter_.set_name('VPN profiles (*.conf)');filter_.add_pattern('*.conf');chooser.add_filter(filter_)
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
    def install_tcp(self):
        if self.busy or self.active is not False:return
        from backend import tcp_updater_available,install_tcp_component
        if not tcp_updater_available():
            self.set_detail('Для установки TCP требуется настройка системного установщика администратором.' if self.ru else 'An administrator must set up the TCP system updater first.')
            return
        text=('Скачать проверенный TCP-компонент и установить его? Система запросит права администратора. Профили сохранятся; VPN автоматически не включится.' if self.ru else 'Download and install the verified TCP component? Administrator authorization is required. Profiles will be preserved; VPN will not start automatically.')
        def install():
            if not self.busy and self.active is False:self.submit(install_tcp_component,'tcp_installed')
        self.confirm(text,'Установить TCP' if self.ru else 'Install TCP',install)

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
        if self.active:
            message=self.t('closing')
            if self.recovery.identity:message+='\n'+('Автовосстановление работает только при открытом приложении.' if self.ru else 'Automatic recovery runs only while the app is open.')
            self.confirm(message,'Закрыть окно' if self.ru else 'Close window',lambda:self.close(True));return True
        self.close(True);return True
    def close(self,confirmed=False):
        if self.closed or self.busy:return False
        if self.active and not confirmed:return self.on_close()
        self.recovery.stop()
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
            import hashlib
            raw=base64.b64decode(ICON_PNG)
            icon_path=root/('app-'+hashlib.sha256(raw).hexdigest()[:16]+'.png')
            if not icon_path.is_file():atomic(icon_path,raw)
            theme=Path.home()/'.local/share/icons/hicolor/256x256/apps'
            theme.mkdir(parents=True,exist_ok=True)
            atomic(theme/'com.familyconnect.Client.png',raw)
            entry=Path.home()/'.local/share/applications/family-connect.desktop'
            if entry.is_file() and not entry.is_symlink():
                lines=[s for s in entry.read_text().splitlines() if not s.startswith(('Icon=','StartupWMClass='))]
                data=('\n'.join(lines)+'\nIcon='+str(icon_path)+'\nStartupWMClass=com.familyconnect.Client\n').encode()
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
