"""Family Connect desktop pilot. No profiles or packet contents are logged."""
import concurrent.futures
import locale
import queue
import sys
import tkinter as tk
from tkinter import filedialog,ttk,messagebox
import urllib.request
from backend import backend

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
 'system':('Linux: нужен NetworkManager. Windows: официальный WireGuard и запуск от администратора.','Linux: NetworkManager required. Windows: official WireGuard and administrator rights required.'),
 'quality':('Включённый туннель не подтверждает доступность интернета.','An active tunnel does not confirm Internet connectivity.'),
 'closing':('Закрытие окна не отключает VPN. Продолжить?','Closing this window keeps the VPN running. Continue?'),
 'checks':('Проверка обращается к Cloudflare через текущее соединение.','This check contacts Cloudflare over the current connection.')}


class App:
    def __init__(self,root,smoke=False):
        self.root=root;self.ru=bool(RU);self.driver=None;self.items=[];self.active=False;self.busy=False
        self.closed=False;self.pool=concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self.events=queue.SimpleQueue()
        root.title('Family Connect');root.geometry('470x600');root.minsize(440,570);root.configure(bg='#101923')
        self.frame=tk.Frame(root,bg='#101923',padx=34,pady=30);self.frame.pack(fill='both',expand=True)
        tk.Label(self.frame,text='FAMILY CONNECT',bg='#101923',fg='#66dbc0',font=('Segoe UI',19,'bold')).pack(pady=(5,8))
        self.subtitle=tk.Label(self.frame,bg='#101923',fg='#b3c3d1',font=('Segoe UI',11));self.subtitle.pack()
        self.dot=tk.Label(self.frame,text='●',bg='#101923',fg='#60758a',font=('Segoe UI',70));self.dot.pack(pady=(14,0))
        self.state=tk.Label(self.frame,bg='#101923',fg='white',font=('Segoe UI',22,'bold'));self.state.pack()
        self.hint=tk.Label(self.frame,bg='#101923',fg='#91a9bd',font=('Segoe UI',10));self.hint.pack(pady=(8,20))
        self.choose=ttk.Combobox(self.frame,state='readonly',width=35);self.choose.pack(fill='x');self.choose.bind('<<ComboboxSelected>>',lambda _:self.refresh())
        self.toggle=tk.Button(self.frame,command=self.toggle_vpn,bg='#66dbc0',fg='#101923',activebackground='#a0ead8',relief='flat',font=('Segoe UI',14,'bold'),pady=10);self.toggle.pack(fill='x',pady=15)
        row=tk.Frame(self.frame,bg='#101923');row.pack(fill='x')
        self.add=ttk.Button(row,command=self.import_profile);self.add.pack(side='left')
        self.check=ttk.Button(row,command=self.check_ip);self.check.pack(side='right')
        self.note=tk.Label(self.frame,bg='#101923',fg='#91a9bd',wraplength=390,justify='center');self.note.pack(pady=(20,8))
        self.detail=tk.Label(self.frame,bg='#101923',fg='#e8cda4',wraplength=390,justify='center');self.detail.pack()
        ttk.Button(self.frame,text='RU / EN',command=self.language).pack(side='bottom',pady=10)
        root.protocol('WM_DELETE_WINDOW',self.close)
        self.paint();root.after(100,self.drain)
        if not smoke:self.submit(self.initialize)
    def t(self,key):return WORDS[key][0 if self.ru else 1]
    def paint(self):
        self.subtitle.config(text=self.t('title'));self.state.config(text=self.t('pending' if self.busy else ('unknown' if self.active is None else ('on' if self.active else 'off'))))
        self.dot.config(fg='#66dbc0' if self.active else '#60758a');self.hint.config(text=self.t('hint'))
        self.toggle.config(text=self.t('disconnect' if self.active else 'connect'),state='disabled' if self.busy or not self.items or self.active is None else 'normal')
        self.add.config(text=self.t('import'),state='disabled' if self.busy or self.driver is None else 'normal')
        self.check.config(text=self.t('check'),state='normal' if self.active and not self.busy else 'disabled')
        self.note.config(text=self.t('quality'));self.choose.config(state='disabled' if self.busy else 'readonly')
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
                    elif kind=='state':self.active=answer
                    elif kind=='ip':self.detail.config(text=answer)
                except Exception:
                    if kind=='state':self.active=None
                    self.detail.config(text=self.t('error')+'\n'+self.t('system'))
                self.paint()
        except queue.Empty:pass
        self.root.after(100,self.drain)
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
    def close(self):
        if self.busy:return
        if self.active and not messagebox.askokcancel('Family Connect',self.t('closing')):return
        self.closed=True;self.pool.shutdown(wait=False,cancel_futures=True);self.root.destroy()


if __name__=='__main__':
    root=tk.Tk();app=App(root,smoke='--smoke' in sys.argv)
    if '--smoke' in sys.argv:root.after(300,app.close)
    root.mainloop()
