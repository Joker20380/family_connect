"""GTK display-backed checks: geometry, state updates and asynchronous operations."""
import argparse
from concurrent.futures import Future
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
from app import App,Adw,Gtk,GLib


def pump(seconds=.08):
    context=GLib.MainContext.default();end=time.monotonic()+seconds
    while time.monotonic()<end:
        while context.pending():context.iteration(False)
        time.sleep(.001)


def settled_size(window):
    # Wayland acknowledges initial content-fit resizing asynchronously. Measure
    # invariance only after that startup negotiation, not after a fixed 80 ms.
    previous=None;stable=0;deadline=time.monotonic()+3
    while time.monotonic()<deadline:
        pump(.05)
        size=(window.get_width(),window.get_height())
        stable=stable+1 if size==previous and min(size)>0 else 0
        if stable>=4:return size
        previous=size
    raise AssertionError('Initial window geometry did not settle')


def regressions():
    Adw.init();app=App(smoke=True)
    class Driver:
        def profiles(self):return [('first','First'),('last','Last')]
        def active(self,ident):return ident=='last'
    try:
        import app as module
        original=module.backend;module.backend=Driver
        try:driver,items,active=app.initialize()
        finally:module.backend=original
        assert app.driver is None and not app.items,'Worker mutated UI state'
        done=Future();done.set_result((driver,items,active))
        app.complete('initialized',done,0,None);app.present();pump()
        assert app.selected()=='last' and app.active is True
        size=settled_size(app.window);changes=app.widget_changes;renders=app.render_count
        for _ in range(20):app.paint()
        pump();assert app.widget_changes==changes and app.render_count==renders+1
        assert size==(app.window.get_width(),app.window.get_height())
        renders=app.render_count;app.set_detail('First');app.set_detail('Final');pump()
        assert app.detail.get_label()=='Final' and app.render_count==renders+1
        status=app.status.get_label();app.busy=True;app.paint();pump();assert app.status.get_label()==status;app.busy=False
        current=Future();current.set_result(True);changes=app.widget_changes
        app.complete('poll',current,app.revision,app.selected());pump();assert app.widget_changes==changes
        stale=Future();stale.set_result(False);app.revision+=1
        app.complete('poll',stale,app.revision-1,app.selected());pump();assert app.active is True
        failed=Future();failed.set_exception(RuntimeError('unavailable'))
        app.complete('poll',failed,app.revision,app.selected());pump();assert app.active is None and app.detail.get_visible()
        app.complete('poll',current,app.revision,app.selected());pump();assert app.active is True and not app.detail.get_visible()
        accepted=[];dialog=app.confirm('Test confirmation','Accept',lambda:accepted.append(True))
        dialog.emit('response','cancel');dialog.destroy();pump();assert not accepted
        started=threading.Event();release=threading.Event();action=threading.Event()
        class Slow:
            def active(self,ident):started.set();release.wait(3);return False
        app.driver=Slow();app.refresh();assert started.wait(1)
        app.submit(lambda:(action.set(),True)[1],'state');assert action.wait(1),'Foreground action waits behind poll'
        pump();release.set();pump();assert app.active is True,'Late poll replaced user action'
    finally:app.busy=False;app.close(True);pump()
    print('GTK state/poll/confirmation regressions passed',flush=True)


def layouts(scale):
    Adw.init();results=[]
    for ru in (True,False):
        app=App(smoke=True);app.ru=ru;app.driver=object();app.items=[('demo','Family connection')];app.active=False;app.paint();app.present();pump(.15)
        try:
            for width in (360,420,680):
                app.window.set_default_size(width,-1)
                app.set_detail(app.t('error')+'\n'+app.t('system'));pump(.1)
                previous=-1
                for widget in (app.toggle,app.add,app.check,app.update_button):
                    ok,rect=widget.compute_bounds(app.body);assert ok
                    assert rect.get_y()>=previous,'Buttons must stay in one column'
                    previous=rect.get_y()+rect.get_height()
                    assert rect.get_x()>=0 and rect.get_x()+rect.get_width()<=app.body.get_width()+1,'Horizontal clipping'
                    minimum,natural,_,_=widget.measure(Gtk.Orientation.HORIZONTAL,-1)
                    assert widget.get_width()>=minimum,'Clipped button label'
                for label in (app.status,app.hint,app.note,app.detail):
                    _,height=label.get_layout().get_pixel_size()
                    assert label.get_height()>=height,'Clipped label'
                app.update_button.grab_focus();pump()
                assert app.update_button.has_focus(),'Keyboard focus lost'
                results.append(dict(scale=scale,ru=ru,width=width))
        finally:app.close(True);pump()
    print(json.dumps({'gtk_layout_cases_passed':len(results),'scale':scale}),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--scale',type=float);args=parser.parse_args()
    if args.scale:layouts(args.scale)
    else:
        regressions()
        for scale in (1,1.5,2,2.5):
            env=dict(os.environ,GDK_SCALE=str(1 if scale<2 else 2),GDK_DPI_SCALE=str(scale/(1 if scale<2 else 2)))
            subprocess.run([sys.executable,__file__,'--scale',str(scale)],env=env,check=True,timeout=35)
        print('GTK: 24 layout cases passed',flush=True)
