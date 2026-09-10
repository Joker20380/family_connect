"""Display-backed geometry regression. No backend, network or VPN operations."""
import argparse
import json
import tkinter as tk
from pathlib import Path

from app import App


def check(output=None):
    import faulthandler
    faulthandler.dump_traceback_later(20,exit=True)
    results=[]
    for scale in (1.0,1.5,2.0):
        root=tk.Tk();root.tk.call('tk','scaling',scale*96/72)
        app=App(root,smoke=True)
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
