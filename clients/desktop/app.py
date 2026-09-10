"""Family Connect desktop pilot. No profiles or packet contents are logged."""
import concurrent.futures
import locale
import queue
import sys
import tkinter as tk
from tkinter import filedialog,ttk,messagebox
import urllib.request
from backend import backend, BackendError
import webbrowser

APP_VERSION='0.2.1'

RU=locale.getlocale()[0] and locale.getlocale()[0].lower().startswith('ru')
WORDS={
 'title':('Связь для вашей семьи','Connectivity for your family'),
 'unknown':('Статус недоступен','Status unavailable'),'off':('VPN выключен','VPN is off'),'on':('Туннель включён','Tunnel is on'),
 'connect':('Подключить','Connect'),'disconnect':('Отключить','Disconnect'),
 'import':('Добавить профиль','Add profile'),'check':('Проверить внешний IP','Check public IP'),
 'empty':('Добавьте профиль вашего устройства','Add this device’s profile'),
 'hint':('Прямое подключение','Direct connection'),
 'pending':('Выполняется…','Working…'),
 'error':('Не удалось выполнить действие. Проверьте профиль, системный VPN и разрешения.','Operation failed. Check the profile, system VPN and permissions.'),
 'retry':('Повторить проверку','Retry setup'),
 'install':('Установить WireGuard','Install WireGuard'),
 'system':('Linux: нужен NetworkManager. Windows: официальный WireGuard и запуск от администратора.','Linux: NetworkManager required. Windows: official WireGuard and administrator rights required.'),
 'quality':('Включённый туннель не подтверждает доступность интернета.','An active tunnel does not confirm Internet connectivity.'),
 'closing':('Закрытие окна не отключает VPN. Продолжить?','Closing this window keeps the VPN running. Continue?'),
 'checks':('Проверка обращается к Cloudflare через текущее соединение.','This check contacts Cloudflare over the current connection.')}


class App:
    def __init__(self,root,smoke=False):
        self.root=root;self.ru=bool(RU);self.driver=None;self.items=[];self.active=False;self.busy=False
        self.closed=False;self.pool=concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self.events=queue.SimpleQueue();self.update_plan=None;self.updater=None
        root.title(f'Family Connect · {APP_VERSION}');root.geometry('480x620');root.minsize(360,420);root.configure(bg='#101923')
        style=ttk.Style(root);style.theme_use('clam')
        style.configure('FC.TButton',background='#203040',foreground='#e0eaf2',bordercolor='#365064',padding=(10,7),font=('Segoe UI',10))
        style.map('FC.TButton',background=[('active','#2d465a')],foreground=[('disabled','#8a9ba9')])
        style.configure('FC.TCombobox',fieldbackground='#203040',background='#203040',foreground='#e0eaf2',arrowcolor='#b3c3d1',padding=6)
        style.map('FC.TCombobox',fieldbackground=[('readonly','#203040'),('disabled','#203040')],foreground=[('disabled','#8a9ba9')])
        style.configure('FC.Vertical.TScrollbar',background='#294052',troughcolor='#101923',arrowcolor='#91a9bd',bordercolor='#101923')
        root.option_add('*TCombobox*Listbox.background','#203040');root.option_add('*TCombobox*Listbox.foreground','#e0eaf2')
        root.rowconfigure(0,weight=1);root.columnconfigure(0,weight=1)
        self.canvas=tk.Canvas(root,bg='#101923',highlightthickness=0,bd=0)
        self.scrollbar=ttk.Scrollbar(root,style='FC.Vertical.TScrollbar',orient='vertical',command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.grid(row=0,column=0,sticky='nsew');self.scrollbar.grid(row=0,column=1,sticky='ns')
        self.frame=tk.Frame(self.canvas,bg='#101923',padx=24,pady=18)
        self.content=self.canvas.create_window(0,0,anchor='nw',window=self.frame)
        self.frame.columnconfigure(0,weight=1)
        self.brand=tk.Label(self.frame,text='FAMILY CONNECT',bg='#101923',fg='#66dbc0',font=('Segoe UI',18,'bold'))
        self.brand.grid(row=0,column=0,sticky='ew',pady=(0,6))
        self.subtitle=tk.Label(self.frame,bg='#101923',fg='#b3c3d1',font=('Segoe UI',11));self.subtitle.grid(row=1,column=0,sticky='ew')
        self.dot=tk.Label(self.frame,text='●',bg='#101923',fg='#60758a',font=('Segoe UI',42));self.dot.grid(row=2,column=0,pady=(10,0))
        self.state=tk.Label(self.frame,bg='#101923',fg='white',font=('Segoe UI',20,'bold'));self.state.grid(row=3,column=0,sticky='ew')
        self.hint=tk.Label(self.frame,bg='#101923',fg='#91a9bd',font=('Segoe UI',10));self.hint.grid(row=4,column=0,sticky='ew',pady=(6,14))
        self.choose=ttk.Combobox(self.frame,style='FC.TCombobox',state='readonly',width=1);self.choose.grid(row=5,column=0,sticky='ew');self.choose.bind('<<ComboboxSelected>>',lambda _:self.refresh())
        self.toggle=tk.Button(self.frame,command=self.toggle_vpn,bg='#66dbc0',fg='#101923',activebackground='#a0ead8',relief='flat',font=('Segoe UI',14,'bold'),pady=8);self.toggle.grid(row=6,column=0,sticky='ew',pady=(12,8))
        self.actions=tk.Frame(self.frame,bg='#101923');self.actions.grid(row=7,column=0,sticky='ew')
        self.actions.columnconfigure(0,weight=1);self.actions.columnconfigure(1,weight=1)
        self.add=ttk.Button(self.actions,style='FC.TButton',command=self.import_profile)
        self.check=ttk.Button(self.actions,style='FC.TButton',command=self.check_ip)
        self.note=tk.Label(self.frame,bg='#101923',fg='#91a9bd',justify='center');self.note.grid(row=8,column=0,sticky='ew',pady=(16,8))
        self.detail=tk.Label(self.frame,bg='#101923',fg='#e8cda4',justify='center');self.detail.grid(row=9,column=0,sticky='ew')
        self.setup=tk.Frame(self.frame,bg='#101923');self.setup.grid(row=10,column=0,sticky='ew',pady=8);self.setup.columnconfigure(0,weight=1)
        self.retry=ttk.Button(self.setup,style='FC.TButton',command=lambda:self.submit(self.initialize))
        self.install=ttk.Button(self.setup,style='FC.TButton',command=lambda:webbrowser.open('https://www.wireguard.com/install/'))
        self.update_button=ttk.Button(self.frame,style='FC.TButton',command=self.update_application)
        self.update_button.grid(row=11,column=0,sticky='ew',pady=(4,8))
        footer=tk.Frame(root,bg='#101923',padx=24,pady=8);footer.grid(row=1,column=0,columnspan=2,sticky='ew')
        tk.Label(footer,text=f'v{APP_VERSION}',bg='#101923',fg='#91a9bd').pack(side='left')
        self.language_button=ttk.Button(footer,style='FC.TButton',text='RU / EN',command=self.language);self.language_button.pack(side='right')
        self.frame.bind('<Configure>',lambda _:self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        self.canvas.bind('<Configure>',self.layout)
        root.bind('<MouseWheel>',lambda e:self.canvas.yview_scroll(-1 if e.delta>0 else 1,'units'))
        root.bind('<Button-4>',lambda _:self.canvas.yview_scroll(-1,'units'))
        root.bind('<Button-5>',lambda _:self.canvas.yview_scroll(1,'units'))
        root.bind('<FocusIn>',self.reveal_focus)
        root.protocol('WM_DELETE_WINDOW',self.close)
        self.paint();self.drain_timer=root.after(100,self.drain)
        if not smoke:self.submit(self.initialize)
    def t(self,key):return WORDS[key][0 if self.ru else 1]
    def paint(self):
        self.subtitle.config(text=self.t('title'));self.state.config(text=self.t('pending' if self.busy else ('unknown' if self.active is None else ('on' if self.active else 'off'))))
        self.dot.config(fg='#66dbc0' if self.active else '#60758a');self.hint.config(text=self.t('hint'))
        self.toggle.config(text=self.t('disconnect' if self.active else 'connect'),state='disabled' if self.busy or not self.items or self.active is None else 'normal')
        self.toggle.config(bg='#294c4a' if self.toggle['state']=='disabled' else '#66dbc0',disabledforeground='#b4ccc7')
        if not self.items:self.choose.set(self.t('empty'))
        self.add.config(text=self.t('import'),state='disabled' if self.busy or self.driver is None else 'normal')
        self.check.config(text=self.t('check'),state='normal' if self.active and not self.busy else 'disabled')
        self.retry.config(text=self.t('retry'),state='disabled' if self.busy else 'normal');self.install.config(text=self.t('install'))
        if self.driver is None:
            self.retry.grid(row=0,column=0,sticky='ew',pady=3)
            if sys.platform=='win32':self.install.grid(row=1,column=0,sticky='ew',pady=3)
        else:self.retry.grid_remove();self.install.grid_remove()
        self.note.config(text=self.t('quality'));self.choose.config(state='disabled' if self.busy or not self.items else 'readonly')
        self.update_button.config(text=('Установить обновление' if self.ru else 'Install update') if self.update_plan else ('Проверить обновления' if self.ru else 'Check for updates'),state='disabled' if self.busy else 'normal')
        self.root.after_idle(self.layout)
    def layout(self,event=None):
        # ttk buttons cannot wrap text: keep a font-aware minimum width at HiDPI.
        minimum=max(360,max(w.winfo_reqwidth() for w in (self.add,self.check,self.retry,self.install,self.toggle,self.update_button))+48+self.scrollbar.winfo_reqwidth())
        self.root.minsize(minimum,420)
        width=max(1,self.canvas.winfo_width())
        self.canvas.itemconfigure(self.content,width=width)
        usable=max(80,width-48)
        for label in (self.brand,self.subtitle,self.state,self.hint,self.note,self.detail):
            label.configure(wraplength=usable)
        needed=self.add.winfo_reqwidth()+self.check.winfo_reqwidth()+12
        self.add.grid_forget();self.check.grid_forget()
        if needed>usable:
            self.add.grid(row=0,column=0,columnspan=2,sticky='ew',pady=3)
            self.check.grid(row=1,column=0,columnspan=2,sticky='ew',pady=3)
        else:
            self.add.grid(row=0,column=0,sticky='ew',padx=(0,4),pady=3)
            self.check.grid(row=0,column=1,sticky='ew',padx=(4,0),pady=3)
    def reveal_focus(self,event):
        widget=event.widget
        if widget==self.canvas or not str(widget).startswith(str(self.frame)+'.'):return
        self.root.update_idletasks()
        top=widget.winfo_rooty()-self.frame.winfo_rooty()
        bottom=top+widget.winfo_height()
        visible=self.canvas.canvasy(0);height=self.canvas.winfo_height()
        total=max(1,self.frame.winfo_height())
        if top<visible:self.canvas.yview_moveto(top/total)
        elif bottom>visible+height:self.canvas.yview_moveto((bottom-height)/total)
    def language(self):self.ru=not self.ru;self.paint()
    def selected(self):
        index=self.choose.current()
        return self.items[index][0] if 0<=index<len(self.items) else None
    def initialize(self):
        self.driver=backend();return self.driver.profiles()
    def submit(self,fn,kind='profiles'):
        if self.busy:return
        self.busy=True;self.paint()
        future=self.pool.submit(fn)
        future.add_done_callback(lambda f:self.events.put((kind,f)))
    def drain(self):
        if self.closed:return
        try:
            while True:
                kind,future=self.events.get_nowait();self.busy=False
                try:
                    answer=future.result()
                    if kind=='profiles':
                        previous=self.selected();self.items=answer;self.choose['values']=[x[1] for x in answer]
                        if answer:self.choose.current(next((i for i,x in enumerate(answer) if x[0]==previous),len(answer)-1))
                        self.detail.config(text='' if answer else self.t('empty'));self.active=None
                    elif kind=='updates':
                        self.update_plan=answer
                        self.detail.config(text=(('Доступна версия ' if self.ru else 'Version available: ')+answer['version']) if answer else ('Установлена последняя версия.' if self.ru else 'You are up to date.'))
                    elif kind=='update_installed':
                        import subprocess
                        subprocess.Popen([sys.executable,str(answer)],start_new_session=True)
                        self.close(confirmed=True);return
                    elif kind=='state':self.active=answer
                    elif kind=='ip':self.detail.config(text=answer)
                except Exception as exc:
                    if kind in ('updates','update_installed'):
                        self.detail.config(text='Обновление недоступно или не прошло проверку. Текущая версия сохранена.' if self.ru else 'Update unavailable or verification failed. The current version is preserved.')
                        self.paint();continue
                    self.active=None
                    messages={
                        'WireGuard not installed':('Установите официальный WireGuard, затем нажмите «Повторить проверку».','Install official WireGuard, then click Retry setup.'),
                        'Administrator rights required':('Перезапустите Family Connect от имени администратора.','Run Family Connect as administrator.'),
                        'WireGuard signature verification failed':('Подпись WireGuard не прошла проверку. Переустановите его с официального сайта.','WireGuard signature verification failed. Reinstall it from the official website.')}
                    if isinstance(exc,BackendError):
                        code=str(exc)
                        text=messages[code][0 if self.ru else 1] if code in messages else self.t('error')+'\n'+code
                    elif isinstance(exc,ValueError):
                        text=('Профиль не поддерживается: нужен отдельный полный профиль WireGuard для Windows.' if self.ru else 'Unsupported profile: import a separate full-tunnel WireGuard profile for Windows.')
                    elif isinstance(exc,PermissionError):
                        text=('Нет доступа к файлу или хранилищу профилей. Проверьте права администратора.' if self.ru else 'Access to the file or profile store denied. Check administrator permissions.')
                    else:text=self.t('error')+'\n'+type(exc).__name__
                    self.detail.config(text=text)
                self.paint()
        except queue.Empty:pass
        self.drain_timer=self.root.after(100,self.drain)
        if not self.busy and self.driver and self.selected():
            if getattr(self,'next_poll',0)<=__import__('time').monotonic():
                self.next_poll=__import__('time').monotonic()+3;self.refresh()
    def refresh(self):
        ident=self.selected()
        if self.driver and ident and not self.busy:self.submit(lambda:self.driver.active(ident),'state')
    def toggle_vpn(self):
        ident=self.selected();was_active=self.active
        if not ident:return
        def action():
            (self.driver.disconnect if was_active else self.driver.connect)(ident)
            return self.driver.active(ident)
        self.submit(action,'state')
    def import_profile(self):
        if self.active:
            self.detail.config(text='Сначала отключите туннель.' if self.ru else 'Disconnect the tunnel first.');return
        path=filedialog.askopenfilename(filetypes=[('WireGuard','*.conf')])
        if path:
            def action():self.driver.import_profile(path);return self.driver.profiles()
            self.submit(action)
    def check_ip(self):
        ident=self.selected()
        if not ident or not self.active:return
        self.detail.config(text=self.t('checks'))
        def action():
            if not self.driver.active(ident):raise RuntimeError('Tunnel is down')
            with urllib.request.urlopen('https://www.cloudflare.com/cdn-cgi/trace',timeout=10) as response:
                values=dict(line.split('=',1) for line in response.read(4096).decode().splitlines() if '=' in line)
            if not self.driver.active(ident):raise RuntimeError('Tunnel changed')
            return 'IP: '+values.get('ip','?')+' · '+values.get('loc','?')
        self.submit(action,'ip')
    def update_application(self):
        if self.busy:return
        from updates import Updater
        if self.updater is None:self.updater=Updater(APP_VERSION)
        if self.update_plan is None:
            self.submit(self.updater.check,'updates');return
        plan=self.update_plan
        question=(f"Скачать и установить версию {plan['version']}? Окно перезапустится. Профили и ключи сохранятся." if self.ru else f"Download and install {plan['version']}? The window will restart. Profiles and keys will be preserved.")
        if not messagebox.askyesno('Family Connect',question):return
        def install():
            archive=self.updater.download(plan)
            return self.updater.install(plan,archive)
        self.submit(install,'update_installed')
    def close(self,confirmed=False):
        if self.busy:return
        if self.active and not confirmed and not messagebox.askokcancel('Family Connect',self.t('closing')):return
        self.root.after_cancel(self.drain_timer)
        self.closed=True;self.pool.shutdown(wait=False,cancel_futures=True);self.root.destroy()


if __name__=='__main__':
    root=tk.Tk();app=App(root,smoke='--smoke' in sys.argv)
    if '--smoke' in sys.argv:root.after(300,app.close)
    root.mainloop()
