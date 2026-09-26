import sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from friends_ui import FriendsWindow
from gi.repository import Gtk,Adw,GLib
Adw.init()
class Owner:
 connected=[]
 def connect(self,country,driver,*,transport="tcp"):self.connected.append((country,driver,transport));return {'profile':'fctcp12345678','country':country,'transport':'tcp','sequence':2}
 def register(self,token=''):return {'device':'a'*32,'status':'active'}
 def referral(self):return {'url':'https://185.251.89.19:8443/invite/#'+'a'*64,'remaining':499}
 def configuration(self,country):
  class Configuration:sequence=2
  result=Configuration();result.country=country;return result
owner=Owner();driver=object();closed=[]
w=FriendsWindow(None,owner,driver=driver,on_close=lambda:closed.append(True));w.present()
def pump(until):
 end=time.monotonic()+5
 while not until() and time.monotonic()<end:
  while GLib.MainContext.default().iteration(False):pass
  time.sleep(.01)
 assert until()
w.activate.emit('clicked');pump(lambda:not w.busy);assert not w.code.get_mapped() and 'Доступ готов' in w.status.get_text()
w.share.emit('clicked');pump(lambda:not w.busy);assert w.copy.get_sensitive() and 'скачать' in w.status.get_text()
assert w.qr.get_sensitive()
w.qr.emit('clicked');pump(lambda:w.qr_window is not None)
qr=w.qr_window
end=time.monotonic()+.3
while time.monotonic()<end:
 while GLib.MainContext.default().iteration(False):pass
 time.sleep(.01)
from gi.repository import Gsk
paintable=Gtk.WidgetPaintable.new(qr);snapshot=Gtk.Snapshot()
paintable.snapshot(snapshot,qr.get_width(),qr.get_height());node=snapshot.to_node()
if node is not None and len(sys.argv)>1:
 renderer=Gsk.Renderer.new_for_surface(w.window.get_surface())
 try:renderer.render_texture(node,None).save_to_png(sys.argv[1]+'.qr.png')
 finally:renderer.unrealize()
assert qr.is_ancestor(w.content)
qr.get_last_child().emit('clicked');assert w.qr_window is None
w.prepare.emit('clicked');pump(lambda:not w.busy);assert 'сохранены' in w.status.get_text()
w.region.set_selected(1);w.connect_button.emit('clicked');pump(lambda:not w.busy)
assert owner.connected==[('ru',driver,'tcp')] and 'проверен' in w.status.get_text()
w.transport.set_selected(1);w.connect_button.emit('clicked');pump(lambda:not w.busy)
assert owner.connected[-1]==('ru',driver,'awg')
# Busy close is rejected and duplicate network actions remain disabled.
w.busy=True;w.sensitivity();assert w.close() is True and not w.connect_button.get_sensitive()
w.busy=False;w.close_pending=False;w.back.set_label('Назад');w.sensitivity()
assert w.window.get_width()>=340
end=time.monotonic()+.5
while time.monotonic()<end:
 while GLib.MainContext.default().iteration(False):pass
 time.sleep(.01)
from gi.repository import Gsk
paintable=Gtk.WidgetPaintable.new(w.window.get_content())
snapshot=Gtk.Snapshot();paintable.snapshot(snapshot,w.window.get_width(),w.window.get_height())
node=snapshot.to_node()
if node is not None:
 renderer=Gsk.Renderer.new_for_surface(w.window.get_surface())
 try:renderer.render_texture(node,None).save_to_png(sys.argv[1]) if len(sys.argv)>1 else None
 finally:renderer.unrealize()
# Visible navigation remains reachable even when the content scrolls.
assert w.back.get_mapped() and w.back.get_sensitive()
w.back.emit('clicked');assert closed==[True] and w.closed
w.close();assert closed==[True]
# Escape returns to the parent; a close during work waits for completion.
from gi.repository import Gdk
import concurrent.futures
for ru in (True,False):
 done=[];dialog=FriendsWindow(None,owner,ru,on_close=lambda:done.append(True))
 dialog.present();dialog.busy=True;dialog.sensitivity()
 assert dialog.key_pressed(None,Gdk.KEY_Escape,0,0)
 assert dialog.close_pending and not dialog.closed
 future=concurrent.futures.Future();future.set_result(owner.referral())
 dialog.complete(future,'referral');assert dialog.closed and done==[True]
print('GTK invitation activation/referral/configuration/TCP and busy-close checks passed; no HTTP or VPN mutations.')

# Parent integration: startup recovery precedes profile discovery and modal close
# refreshes the active profile; no installed identity or privileged helper is used.
import app as frontend
from layout_check import pump as settle
calls=[]
class Driver:
 def profiles(self):calls.append('profiles');return [('active','Active'),('inactive','Inactive')]
 def active(self,ident):return ident=='active'
class ParentOwner:
 def __init__(self,*args):pass
 def recover(self,driver):calls.append('recover')
 def register(self,token=''):calls.append('register');return {'status':'active'}
parent=frontend.App(smoke=True);parent.friends_owner_class=ParentOwner
original=frontend.backend;frontend.backend=Driver
try:
 driver,items,active=parent.initialize()
 assert calls==['recover','register','profiles'] and items[-1][0]=='active' and active
 parent.driver=driver;parent.present();settle()
 parent.initialize=lambda:(driver,items,active)
 parent.open_friends();settle();assert parent.busy
 assert parent.friends_window.content.is_ancestor(parent.scroll)
 assert all(button.get_mapped() for button in parent.nav.values())
 settle(.5)
 if len(sys.argv)>1:
  paintable=Gtk.WidgetPaintable.new(parent.window.get_content());snapshot=Gtk.Snapshot()
  paintable.snapshot(snapshot,parent.window.get_width(),parent.window.get_height())
  renderer=Gsk.Renderer.new_for_surface(parent.window.get_surface())
  try:renderer.render_texture(snapshot.to_node(),None).save_to_png(sys.argv[1]+'.parent.png')
  finally:renderer.unrealize()
 parent.select_page('route');settle();assert parent.page=='route' and parent.friends_window is None
 assert parent.body.is_ancestor(parent.scroll)
 assert not parent.busy and parent.selected_id=='active'
 # Closing the app from the embedded screen refreshes state, then exits normally.
 parent.initialize=lambda:(driver,items,False)
 parent.open_friends();settle();parent.on_close();settle(.5);assert parent.closed
finally:
 frontend.backend=original;parent.busy=False;parent.close(True)
print('GTK parent startup recovery, active selection and modal ownership passed.')
