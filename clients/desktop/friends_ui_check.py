import sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from friends_ui import FriendsWindow
from gi.repository import Gtk,Adw,GLib
Adw.init()
class Owner:
 def activate(self,code):assert code=='test-invitation'
 def referral(self):return {'url':'https://185.251.89.19:8443/invite/#'+'a'*64,'remaining':499}
 def configuration(self,country):
  class Configuration:sequence=2
  result=Configuration();result.country=country;return result
w=FriendsWindow(None,Owner());w.present()
def pump(until):
 end=time.monotonic()+5
 while not until() and time.monotonic()<end:
  while GLib.MainContext.default().iteration(False):pass
  time.sleep(.01)
 assert until()
w.code.set_text('test-invitation');w.activate.emit('clicked');pump(lambda:not w.busy);assert w.code.get_text()==''
w.share.emit('clicked');pump(lambda:not w.busy);assert w.copy.get_sensitive() and '499' in w.status.get_text()
w.prepare.emit('clicked');pump(lambda:not w.busy);assert 'сохранены' in w.status.get_text()
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
w.window.close()
print('GTK invitation activation/referral/configuration and completion checks passed; no HTTP or VPN mutations.')
