import sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from friends_ui import FriendsWindow
from gi.repository import Gtk,Adw,GLib
Adw.init()
class Owner:
 connected=[]
 def connect(self,country,driver):self.connected.append((country,driver));return {'profile':'fctcp12345678','country':country,'transport':'tcp','sequence':2}
 def activate(self,code):assert code=='test-invitation'
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
w.code.set_text('test-invitation');w.activate.emit('clicked');pump(lambda:not w.busy);assert w.code.get_text()==''
w.share.emit('clicked');pump(lambda:not w.busy);assert w.copy.get_sensitive() and '499' in w.status.get_text()
w.prepare.emit('clicked');pump(lambda:not w.busy);assert 'сохранены' in w.status.get_text()
w.region.set_selected(1);w.connect_button.emit('clicked');pump(lambda:not w.busy)
assert owner.connected==[('ru',driver)] and 'проверен' in w.status.get_text()
# Busy close is rejected and duplicate network actions remain disabled.
w.busy=True;w.sensitivity();assert w.close() is True and not w.connect_button.get_sensitive()
w.busy=False;w.sensitivity()
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
w.window.close();assert closed==[True]
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
parent=frontend.App(smoke=True);parent.friends_owner_class=ParentOwner
original=frontend.backend;frontend.backend=Driver
try:
 driver,items,active=parent.initialize()
 assert calls==['recover','profiles'] and items[-1][0]=='active' and active
 parent.driver=driver;parent.present();settle()
 parent.initialize=lambda:(driver,items,active)
 parent.open_friends();settle();assert parent.busy
 parent.friends_window.window.close();settle();assert not parent.busy and parent.selected_id=='active'
finally:
 frontend.backend=original;parent.busy=False;parent.close(True)
print('GTK parent startup recovery, active selection and modal ownership passed.')
