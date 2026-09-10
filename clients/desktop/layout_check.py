"""Display-backed geometry regression. No backend, network or VPN operations."""
import argparse
import json
import tkinter as tk
from pathlib import Path

from app import App


def check_polling():
    from concurrent.futures import Future
    class Pool:
        def __init__(self):self.pending=[]
        def submit(self,fn):
            future=Future();self.pending.append((fn,future));return future
        def finish(self):
            fn,future=self.pending.pop(0);future.set_result(fn())
        def shutdown(self,**kwargs):pass
    class Driver:
        value=False
        def active(self,ident):
            if self.value is None:raise RuntimeError('unavailable')
            return self.value
    root=tk.Tk();app=App(root,smoke=True);app.pool.shutdown(wait=True);app.pool=Pool();app.poll_pool.shutdown(wait=True);app.poll_pool=Pool()
    app.driver=Driver();app.items=[('one','Family')];app.choose['values']=['Family'];app.choose.current(0)
    app.next_poll=float('inf');app.paint();root.update()
    paints=[];original=app.paint
    def paint():paints.append(True);original()
    app.paint=paint
    def drain():root.after_cancel(app.drain_timer);app.drain();root.update()
    try:
        before=(app.state['text'],str(app.toggle['state']),app.toggle.winfo_height())
        for _ in range(4):
            app.refresh();assert not app.busy
            assert (app.state['text'],str(app.toggle['state']),app.toggle.winfo_height())==before
            app.refresh();assert len(app.poll_pool.pending)==1
            app.poll_pool.finish();drain()
        assert not paints,'Unchanged polls must not repaint'
        app.driver.value=True;app.refresh();app.poll_pool.finish();drain();assert app.active is True and len(paints)==1
        app.refresh();app.submit(lambda:False,'state')
        app.poll_pool.finish();drain();assert app.busy and app.active is True
        app.pool.finish();drain();assert app.active is False and not app.busy
        app.driver.value=None;app.refresh();app.poll_pool.finish();drain();assert app.active is None
        app.driver.value=False;app.refresh();app.poll_pool.finish();drain();assert app.active is False and not app.detail['text']
    finally:app.active=False;app.close()
    print('Polling checks passed: no flicker, single poll, stale result, error recovery')


def check_slow_poll():
    import threading,time
    started=threading.Event();release=threading.Event();action=threading.Event()
    class Driver:
        def active(self,ident):started.set();release.wait(3);return False
    root=tk.Tk();app=App(root,smoke=True);app.driver=Driver()
    app.items=[('test','Family')];app.choose['values']=['Family'];app.choose.current(0);app.next_poll=float('inf')
    try:
        app.refresh();assert started.wait(1)
        app.submit(lambda:(action.set(),False)[1],'state')
        assert action.wait(1),'User action queued behind slow poll'
    finally:
        release.set();app.busy=False;app.close()
    print('Slow poll does not block user actions')


def check(output=None):
    import faulthandler
    faulthandler.dump_traceback_later(20,exit=True)
    check_polling();check_slow_poll()
    results=[]
    for scale in (1.0,1.5,2.0,2.5):
        root=tk.Tk();root.tk.call('tk','scaling',scale*96/72)
        app=App(root,smoke=True)
        root.update()
        if root.winfo_screenheight()>=2000:
            for button in (app.toggle,app.add,app.check,app.update_button):
                assert button.winfo_rooty()+button.winfo_height()<=app.canvas.winfo_rooty()+app.canvas.winfo_height(),(scale,'startup action hidden')
        try:
            for ru in (True,False):
                app.ru=ru
                for size in ('360x420','480x620','800x700'):
                    root.geometry(size)
                    app.detail.configure(text=app.t('error')+'\n'+app.t('system'))
                    app.paint();root.update()
                    # Every child fits horizontally; all actions remain reachable
                    # in the scroll region, including with long localized errors.
                    for widget in (app.brand,app.state,app.choose,app.toggle,app.add,app.check,app.note,app.detail,app.retry,app.update_button):
                        left=widget.winfo_rootx()-app.canvas.winfo_rootx()
                        assert left>=0,(size,scale,'left',str(widget))
                        assert left+widget.winfo_width()<=app.canvas.winfo_width(),(size,scale,'right',str(widget))
                    for button in (app.toggle,app.add,app.check,app.retry,app.update_button):
                        assert button.winfo_width()>=button.winfo_reqwidth(),(size,scale,'button text clipped')
                    app.language_button.focus_force();root.update();app.retry.focus_force();root.update()
                    top=app.retry.winfo_rooty()-app.canvas.winfo_rooty()
                    assert 0<=top and top+app.retry.winfo_height()<=app.canvas.winfo_height(),(size,scale,'focus')
                    assert app.language_button.winfo_viewable()
                    results.append(dict(scale=scale,ru=ru,size=size))
                    if output and scale==1.0 and size=='480x620' and ru:
                        from PIL import ImageGrab
                        app.canvas.yview_moveto(0);root.update()
                        x,y=root.winfo_rootx(),root.winfo_rooty()
                        ImageGrab.grab(bbox=(x,y,x+root.winfo_width(),y+root.winfo_height())).save(output)
        finally:
            app.close()
    faulthandler.cancel_dump_traceback_later()
    print(json.dumps({'layout_cases_passed':len(results)}))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--screenshot',type=Path)
    check(parser.parse_args().screenshot)
