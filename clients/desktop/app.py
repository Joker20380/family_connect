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

APP_VERSION='0.2.3'

# Generated from clients/assets/dodecahedron.svg; embedded for 0.2.1 updater compatibility.
ICON_PNG='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'

BUTTON_IMAGES={'normal': 'iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAABR0lEQVR4nO2XsUqcQRRGz3dn9hU0WOgi8RnSpDGQxt53iC+Q2jovoO+Q3kZwmzR5BkVWC1FfYWfuZ7FICIE07v5r8R+Y+hyGGbhXLBHgrYPP+xPqVxNTmWYcrAChtKgi5wva5fP1r9tXp+C4wM++8/HwpET9bnIqtArvPxgjYt6z/Xi4mZ3BcRHAzv6Xb2VSzpwN2w17PQWSJVVFpS/6ycPt1bk+TA/36iR+Q27Z7kBdi/wPTVKBeG6L/BQRHAm2nc4B5ADV6RRsR3AUFO8iGTyA+xWDZIp3Q1aHNb26/yNZPbwZObC8h5X887cwBowBY8AYMAaMAWPAGBAadhj8C4HDcmEzEbZcgq775SIy5GgosEXXfWRyYXhSKIA2gL0pFIanTC7icT67y+5TRZWkCjTsvpaz3Iqqoiq7Tx/ns7v3sZyywfX8BYmo4e+LLXa6AAAAAElFTkSuQmCC', 'hover': 'iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAABWklEQVR4nO2XMUpkQRRF771VraMLGLO2ESYwHBB0A5OYdyIDproBY2M3oOmAdGJu4gYUBEMDQVozXYCObdW7BtqRgYH9bYN/oOJz4FHwHvEKAfjXysaSlP9I6BEscAiTgArDOQLDiHJydT64HjuJfj/h6Kgur/7dTnl2x44eOG6aJAYMkBrW8rR3eXa4j34/EQCW1za3Usr7UZ/hiOLJ2wEABEwpK3VQa9m+PP13wN7vjcX5H50z2D8jaiWZm5CPsV2klEDeP/x/XtXcjNZJLkRENC0HAJL5zbUwN6N1ieiCctPi9yWyiK4MVTQ0848SDFXBnob8FZuT+eefoA1oA9qANqANaAPagDZAIL9+HxxDWkQkANOIMBFJYdzC8fV7oYNh3OpxFMe27yTJdmnca5c3193jKI41vBjc2NhV6lBKGUaxUZt4MIqUslKHNnaHF4Ob73GcYorn+QuqZ/V7TM/NswAAAABJRU5ErkJggg==', 'pressed': 'iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAABZUlEQVR4nO2XMUpDQRRF730zfMUFaKdibyEpRLBRsLH/C1BEdAPW1m4gIhIXkD6NoI0gFmJhL5pOFyDymXnXIklhI4L50eIfePU98GbgXWIAAWh5fWepKOIWwEUak+SGMUCayxUBPVdVuny8uXgaZbIsy9DtdnNrY/8wxOJIyovkyGmcCBJAhuecqpP767N2WZaBANDa3DuIcbqdUwWXJ0jjTh9AymgxxAIpfRzeX52fcmVtdyHOFHdSnnV5JhhrCR8iKBktkOEtvVerZgW3Sc655HWHAwDB6JKTnLOC24bAeXC4oEkhAYQQOG+kZYD17PxbSNKyCTU9uB8giGP557+hEWgEGoFGoBFoBBqBRsAITvAY/ApBmeQBE71IR0iSB0NWHwInepeSgEBk9c0r9SS9GmmCUt3Zg2JCk/TqlXr2cNt5caXjEKdoDFFAkpRrGSAZQwxxiq50/HDbefkf5RR/WM8/AaV7GPll9h5vAAAAAElFTkSuQmCC', 'disabled': 'iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAABN0lEQVR4nO2XMU5CQRRF733vB3YgHRITtbIwFK7AhhLDHmQDLsIN4B6MlDSuwILKSk0MocMdQP68a2GwISEmMmIxZwPnFG+SucQXBKDjs/6RNewSSB3RakiGXUAGFRXgs1jF49vz+H3tJAYDx/19Oun2h+7NG0XqgDvRbiKA5rOUlrev0/EIg4ETAE67V9fmPkopARG1oCwJBAWzyt0RKQ1fpg937Jz3D5tuT1AcREQiWeWQr5FUm5mD9rFMcWENRQ9gKyIitxwASFYREQBbDUWvorNNQrnFmyEQnG0TLQHMdXZbE0RLBuU5uB8hcTfv/BeUgBJQAkpACSgBJaAEGMg//w9+Q8qocEB7iJCo8EpJczDbFtqiB5U0txVtAmhhZiapzi9WbWYGaLGiTfY/zf7FOMUe5/knowmzXFmsGFoAAAAASUVORK5CYII=', 'focus': 'iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAABvElEQVR4nO2Xv04UURjFz7lz+VNjdmbXFdyI0ezGYDlQUdnwGiZGfAA1sSYBH2AhJr4GjRWVTMmGzEYDGwKuu4uRGoeZeyxGjI02zi7NnOSrbnF+957c5DsEAEkkqc4n3avdwZOrFA1apEphUIBo4ZTCTlmcDL7gw9JD9q49KckjmX3+qvUkSV/u7X1sDPp9kATIIvwBCZJQq9exurpyMj1t3z64zW1JniWZHQ31/Pi4337z+hW63cMUAKFivH8rv4uazUeNjc2t9tFQIrnDXk93v/+4il48e+rH8UFW8QPrnCvYPZcxBt/OR2mr9dhrv3t/fmtmKjSzc1iL9qMg7nZcxQ9skiTIsmwskyQJKn5g427HRftRMDuHNQNiYTg4EwA45/LsxySSuH7d4eBMIBYMgcwYr/jM/yUBxngkkBkBnKT3HwwQwEL++f+oBCgBSoASoAQoAUqAEsAQ0Pi2wL+L+cgI8JzLhElSEHAukwDPQDit1uYJ5Hu7NL4NURKMyVOv1uYJ4dReXmA3XA5HreaSH8cH6aSKSbgcji4vsEsA+FXNtidUzezG5hYWF+vr96vcufFyyvz85ur5T/nVNslfZW2rAAAAAElFTkSuQmCC', 'primary': 'iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAABgElEQVR4nO2XMU4cQRREq373jMSOsTM2gxWX8AkcsLFly7ETcwEOwQXYwMQrRsTjwCfwJawVGc5sPIs00/PLgVkiAmM1bDIVdNZ6r7vV0i8CgCSS1Pnl7WG1W7wxhJmIJHdDhtDMKUTHsGpv+q8f3+583zBjXSuQHJaNjl/s+knX2QwASADIwgcASEBAwN6Uq2WjU5Jnda1AALj4ok87Fc7WLZBSSgJ4ty0TnptVMcY4qYDbFsfvj7jg50sdvHrp3wbHXup8oDFmoj4YuVIsLQTDj5+/7LVVk35uZtOuc39qOADQGLvO3cym1aSfG0OxT4PIXNf9DxIUaBBDsW8GH3D/5s8aGnww11bgAAAXmO+f/WdGgVFgFBgFRoFRYBQYBcyYbfZ+PJyQOSwgXwF4TOSwYBr6KzkoPd9oKBFyUEN/Ze26aNz9uizN5EpPDnelsjRz9+t2XTRbr2axrhXeHXGxbMS/5TTOgE05zRfdnaUsffX7xk4/zLm4L6fbrOd/AE0Wzc+mTLgtAAAAAElFTkSuQmCC', 'primaryhover': 'iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAABZUlEQVR4nO3XO04bURjF8f/55iGw8qpASkFQWteEKmUaVhI2kEWwAbyGWQANJUrhRCndRhYdqfLSgGbG91BYhI4mM3YzR7r1+UmfbnEEYFuSfPXl9u3k+c4HJw7J6JwIeoiCxIpcwbL+c3f5/t3u94fOvKqcSVrNFz599TJ9ur3jUAKpj+rH2Ou397pczhc+k3ReVc4E8HXhj5NnnNc1tE3qgJ7rHx1FGflkAvVfTo+mmunzN7+ZvGDetey1bVpJygcqXwvsrigiywt+1L85jig5Qew3TUpDlwNIypsmJcR+lJxEkXMQwn3f/GkEhHCRcxCIlTTYzZ9CCLEKp82XP8QJ9fLP/ycjYASMgBEwAkbACBgBocDbKlfgwGT25hE2xmTRdlwnI2+QYEMyajuuIzVcYG7KMsJ2N3y5u7KMwNykhoutT7O8qpwdTTWbL6z1OI1Bx+nuTlr+/BVnx1PN/o3Tbc7ze52owVl4xn7ZAAAAAElFTkSuQmCC', 'primaryfocus': 'iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAABaklEQVR4nO2XQWoUURRFz33/01Z1QIJNd4FIDG7CDEVwkpWYDbgINxBXkokgDuMmJAQRqkMFCdhVNvX/y0RBhGSSSsVBnQX8e3jw4V4BuLskedv6i6LgDbAP9BmMATDIQATOuo6PZamvfzLl7kFSard+FMW77w37PzswgfsQ8SBBdtgp4OmCs955X8507O5BANutv+0Sx59P4eKy7wEhcIYx+P0YgC+fxPjqAIrA0WymD7rc+PNHxpdPp3m1blKaFxYHSb2BTZf71SKE1we2/pV5GR+XHH6rqeomp53SYs73GQ/z0mLd5HTxw6pnFYcWYG/T4pIz0MVvx0FyNi0eYM8yJAmNkf2XAxLKkAzQiNn/okH++V2YBCaBSWASmAQmgUlgEjDGaYI34WYQ3PExe5kAd9wgWILzeYncNU47FLiLeYkSnMerlpPlLnW1sNW6Sf29D5M299UihOUu9VXLycNPs/9inD7kPL8GDJnGYsF/j5kAAAAASUVORK5CYII='}

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
        self.poll_inflight=False;self.revision=0;self.poll_error=False
        self.closed=False;self.pool=concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self.events=queue.SimpleQueue();self.update_plan=None;self.updater=None
        root.title(f'Family Connect · {APP_VERSION}');root.geometry('480x680');root.minsize(360,420);root.configure(bg='#0b1020')
        self.icon=tk.PhotoImage(data=ICON_PNG);root.iconphoto(True,self.icon)
        style=ttk.Style(root);style.theme_use('clam')
        style.configure('FC.TButton',background='#0b1020',foreground='#e8edff',bordercolor='#334164',lightcolor='#1b2440',darkcolor='#1b2440',borderwidth=0,padding=(14,10),font=('Segoe UI',10))
        style.map('FC.TButton',background=[('disabled','#0b1020'),('active','#0b1020')],foreground=[('disabled','#8894b2')])
        self.button_images={name:tk.PhotoImage(data=data) for name,data in BUTTON_IMAGES.items()}
        for prefix,normal,hover,focus in [('FC','normal','hover','focus'),('Primary','primary','primaryhover','primaryfocus')]:
            element=prefix+'.rounded'
            style.element_create(element,'image',self.button_images[normal],
                ('disabled',self.button_images['disabled']),('pressed',self.button_images['pressed']),
                ('focus',self.button_images[focus]),('active',self.button_images[hover]),border=8,sticky='nsew')
            style.layout(prefix+'.TButton',[(element,{'sticky':'nsew','children':[('Button.padding',{'sticky':'nsew','children':[('Button.label',{'sticky':'nsew'})]})]})])
        style.configure('Primary.TButton',background='#0b1020',padding=(14,12),foreground='#0b1020',font=('Segoe UI',14,'bold'))
        style.map('Primary.TButton',background=[('disabled','#0b1020'),('active','#0b1020')],foreground=[('disabled','#9caaca')])
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
        self.toggle=ttk.Button(self.frame,style='Primary.TButton',command=self.toggle_vpn,cursor='hand2');self.toggle.grid(row=6,column=0,sticky='ew',pady=(12,8))
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
        stacked=needed>usable
        if getattr(self,'_stacked',None)==stacked:return
        self._stacked=stacked
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
        self.revision+=1;self.busy=True;self.paint()
        future=self.pool.submit(fn)
        future.add_done_callback(lambda f:self.events.put((kind,f)))
    def drain(self):
        if self.closed:return
        try:
            while True:
                kind,future=self.events.get_nowait()
                if kind=='poll':
                    self.poll_inflight=False
                    ident,revision,result,error=future.result()
                    if revision!=self.revision or ident!=self.selected() or self.busy:continue
                    changed=result is not self.active or error!=self.poll_error
                    self.active=result
                    if error:self.detail.config(text=self.t('error'))
                    elif self.poll_error:self.detail.config(text='')
                    self.poll_error=error
                    if changed:self.paint()
                    continue
                self.busy=False
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
        if not self.driver or not ident or self.busy or self.poll_inflight:return
        self.poll_inflight=True;revision=self.revision;driver=self.driver
        def poll():
            try:return ident,revision,driver.active(ident),False
            except Exception:return ident,revision,None,True
        future=self.pool.submit(poll)
        future.add_done_callback(lambda f:self.events.put(('poll',f)))
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
