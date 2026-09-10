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

APP_VERSION='0.2.2'

# Generated from clients/assets/dodecahedron.svg; embedded for 0.2.1 updater compatibility.
ICON_PNG='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'

RU=locale.getlocale()[0] and locale.getlocale()[0].lower().startswith('ru')
WORDS={
 'title':('Связь для вашей семьи','Connectivity for your family'),
 'unknown':('Статус недоступен','Status unavailable'),'off':('Готов к подключению','Ready to connect'),'on':('Туннель включён','Tunnel is on'),
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
        root.title(f'Family Connect · {APP_VERSION}');root.geometry('480x680');root.minsize(360,420);root.configure(bg='#0b1020')
        self.icon=tk.PhotoImage(data=ICON_PNG);root.iconphoto(True,self.icon)
        style=ttk.Style(root);style.theme_use('clam')
        style.configure('FC.TButton',background='#1b2440',foreground='#e8edff',bordercolor='#334164',lightcolor='#1b2440',darkcolor='#1b2440',borderwidth=0,padding=(14,10),font=('Segoe UI',10))
        style.map('FC.TButton',background=[('active','#29375c')],foreground=[('disabled','#8894b2')])
        style.configure('FC.TCombobox',fieldbackground='#1b2440',background='#1b2440',foreground='#e8edff',arrowcolor='#aab6d3',bordercolor='#334164',lightcolor='#334164',darkcolor='#334164',padding=9)
        style.map('FC.TCombobox',fieldbackground=[('readonly','#1b2440'),('disabled','#1b2440')],foreground=[('disabled','#8894b2')])
        style.configure('FC.Vertical.TScrollbar',background='#273452',troughcolor='#0b1020',arrowcolor='#99a6c6',bordercolor='#0b1020',lightcolor='#273452',darkcolor='#273452',arrowsize=10)
        root.option_add('*TCombobox*Listbox.background','#1b2440');root.option_add('*TCombobox*Listbox.foreground','#e8edff')
        root.rowconfigure(0,weight=1);root.columnconfigure(0,weight=1)
        self.canvas=tk.Canvas(root,bg='#0b1020',highlightthickness=0,bd=0)
        self.scrollbar=ttk.Scrollbar(root,style='FC.Vertical.TScrollbar',orient='vertical',command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.grid(row=0,column=0,sticky='nsew');self.scrollbar.grid(row=0,column=1,sticky='ns')
        self.frame=tk.Frame(self.canvas,bg='#0b1020',padx=24,pady=18)
        self.content=self.canvas.create_window(0,0,anchor='nw',window=self.frame)
        self.frame.columnconfigure(0,weight=1)
        self.brand=tk.Label(self.frame,text='Family Connect',bg='#0b1020',fg='#a5b4fc',font=('Segoe UI',22,'bold'))
        self.brand.grid(row=0,column=0,sticky='ew',pady=(0,6))
        self.subtitle=tk.Label(self.frame,bg='#0b1020',fg='#aab6d3',font=('Segoe UI',11));self.subtitle.grid(row=1,column=0,sticky='ew')
        self.dot=tk.Label(self.frame,image=self.icon,bg='#0b1020');self.dot.grid(row=2,column=0,pady=(22,16))
        self.state=tk.Label(self.frame,bg='#0b1020',fg='white',font=('Segoe UI',20,'bold'));self.state.grid(row=3,column=0,sticky='ew')
        self.hint=tk.Label(self.frame,bg='#0b1020',fg='#99a6c6',font=('Segoe UI',10));self.hint.grid(row=4,column=0,sticky='ew',pady=(6,14))
        self.choose=ttk.Combobox(self.frame,style='FC.TCombobox',state='readonly',width=1);self.choose.grid(row=5,column=0,sticky='ew');self.choose.bind('<<ComboboxSelected>>',lambda _:self.refresh())
        self.toggle=tk.Button(self.frame,command=self.toggle_vpn,bg='#a5b4fc',fg='#0b1020',activebackground='#c7d2fe',relief='flat',font=('Segoe UI',14,'bold'),pady=12,cursor='hand2',bd=0,highlightthickness=2,highlightbackground='#334164',highlightcolor='#c7d2fe');self.toggle.grid(row=6,column=0,sticky='ew',pady=(12,8))
        self.actions=tk.Frame(self.frame,bg='#0b1020');self.actions.grid(row=7,column=0,sticky='ew')
        self.actions.columnconfigure(0,weight=1);self.actions.columnconfigure(1,weight=1)
        self.add=ttk.Button(self.actions,style='FC.TButton',command=self.import_profile)
        self.check=ttk.Button(self.actions,style='FC.TButton',command=self.check_ip)
        self.note=tk.Label(self.frame,bg='#0b1020',fg='#99a6c6',justify='center');self.note.grid(row=8,column=0,sticky='ew',pady=(16,8))
        self.detail=tk.Label(self.frame,bg='#0b1020',fg='#e8cda4',justify='center');self.detail.grid(row=9,column=0,sticky='ew')
        self.setup=tk.Frame(self.frame,bg='#0b1020');self.setup.grid(row=10,column=0,sticky='ew',pady=8);self.setup.columnconfigure(0,weight=1)
        self.retry=ttk.Button(self.setup,style='FC.TButton',command=lambda:self.submit(self.initialize))
        self.install=ttk.Button(self.setup,style='FC.TButton',command=lambda:webbrowser.open('https://www.wireguard.com/install/'))
        self.update_button=ttk.Button(self.frame,style='FC.TButton',command=self.update_application)
        self.update_button.grid(row=11,column=0,sticky='ew',pady=(4,8))
        footer=tk.Frame(root,bg='#0b1020',padx=24,pady=8);footer.grid(row=1,column=0,columnspan=2,sticky='ew')
        tk.Label(footer,text=f'v{APP_VERSION}',bg='#0b1020',fg='#99a6c6').pack(side='left')
        self.language_button=ttk.Button(footer,style='FC.TButton',text='RU / EN',command=self.language);self.language_button.pack(side='right')
        self.frame.bind('<Configure>',lambda _:self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        self.canvas.bind('<Configure>',self.layout)
        root.bind('<MouseWheel>',lambda e:self.canvas.yview_scroll(-1 if e.delta>0 else 1,'units'))
        root.bind('<Button-4>',lambda _:self.canvas.yview_scroll(-1,'units'))
        root.bind('<Button-5>',lambda _:self.canvas.yview_scroll(1,'units'))
        root.bind('<FocusIn>',self.reveal_focus)
        root.protocol('WM_DELETE_WINDOW',self.close)
        self.paint();self.drain_timer=root.after(100,self.drain)
        if not smoke:
            self.register_icon()
            self.submit(self.initialize)
    def register_icon(self):
        # Only the installed app updates its own launcher, never a source/CI run.
        import base64,os
        from pathlib import Path
        root=Path.home()/'.local/share/family-connect'
        if Path(__file__).resolve().parent!=(root/'current').resolve():return
        try:
            from updates import atomic
            atomic(root/'app.png',base64.b64decode(ICON_PNG))
            entry=Path.home()/'.local/share/applications/family-connect.desktop'
            if entry.is_file() and not entry.is_symlink():
                lines=[line for line in entry.read_text().splitlines() if not line.startswith(('Icon=','StartupWMClass='))]
                atomic(entry,('\n'.join(lines)+'\nIcon='+str(root/'app.png')+'\nStartupWMClass=FamilyConnect\n').encode())
        except OSError:
            pass  # A locked-down launcher must not prevent VPN use.
    def t(self,key):return WORDS[key][0 if self.ru else 1]
    def paint(self):
        self.subtitle.config(text=self.t('title'));self.state.config(text=self.t('pending' if self.busy else ('unknown' if self.active is None else ('on' if self.active else 'off'))))
        self.state.config(fg='#6ee7b7' if self.active else '#eef2ff');self.hint.config(text=self.t('hint'))
        self.toggle.config(text=self.t('disconnect' if self.active else 'connect'),state='disabled' if self.busy or not self.items or self.active is None else 'normal')
        self.toggle.config(bg='#263251' if self.toggle['state']=='disabled' else '#a5b4fc',disabledforeground='#9caaca')
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
    root=tk.Tk(className='FamilyConnect');app=App(root,smoke='--smoke' in sys.argv)
    if '--smoke' in sys.argv:root.after(300,app.close)
    root.mainloop()
