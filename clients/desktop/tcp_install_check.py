"""Real GTK dialogs/buttons; broker execution mocked to avoid host changes in UI tests."""
from concurrent.futures import Future
import sys
import backend
from app import App,Adw
from layout_check import pump

def main():
 Adw.init();sys.argv.append('--awg-pilot');app=App(smoke=True);app.ru=True
 app.active=False;app.items=[('wg','VPN')];app.selected_id='wg';app.present();app.paint();pump()
 original=(backend.tcp_updater_available,backend.install_tcp_component)
 calls=[];dialogs=[];confirm=app.confirm
 def capture(*args):
  dialog=confirm(*args);dialogs.append(dialog);return dialog
 app.confirm=capture
 try:
  backend.tcp_updater_available=lambda:False
  app.tcp_button.emit('clicked');pump();assert 'администратором' in app.detail_text
  backend.tcp_updater_available=lambda:True
  backend.install_tcp_component=lambda:calls.append(True) or True
  app.tcp_button.emit('clicked');pump();dialogs[-1].emit('response','cancel');pump();assert not calls
  app.tcp_button.emit('clicked');pump();dialogs[-1].emit('response','accept');pump(.4)
  assert calls==[True] and 'TCP установлен' in app.detail_text
  def cancelled():raise backend.AuthorizationError('cancelled')
  backend.install_tcp_component=cancelled
  app.tcp_button.emit('clicked');pump();dialogs[-1].emit('response','accept');pump(.4)
  assert 'отменена' in app.detail_text and app.active is False and not app.busy
  count=len(dialogs);app.active=True;app.paint();pump();assert not app.tcp_button.get_sensitive()
  app.install_tcp();assert len(dialogs)==count
  app.active=False;app.busy=True;app.paint();pump();assert not app.tcp_button.get_sensitive()
  app.busy=False;app.active=False;app.detail_text=''
  for ru in (True,False):
   app.ru=ru
   for width in (360,420,680):
    app.window.set_default_size(width,-1);app.paint();pump(.15)
    previous=0
    for widget in (app.toggle,app.add,app.check,app.update_button,app.tcp_button):
     ok,rect=widget.compute_bounds(app.body);assert ok and rect.get_y()>=previous
     previous=rect.get_y()+rect.get_height()
     assert rect.get_x()>=0 and rect.get_x()+rect.get_width()<=app.body.get_width()+1
     minimum,_,_,_=widget.measure(__import__('app').Gtk.Orientation.HORIZONTAL,-1)
     assert widget.get_width()>=minimum
  print('TCP GTK: missing bootstrap, confirm/cancel, success, auth cancel and busy/connected guards passed')
 finally:
  backend.tcp_updater_available,backend.install_tcp_component=original
  for dialog in dialogs:dialog.destroy()
  app.busy=False;app.close(True);pump()
if __name__=='__main__':main()
