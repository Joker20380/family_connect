"""Exercise invitation delivery to one GTK instance on an isolated session bus.

No real identity, HTTP request or VPN helper is used.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

if '--child' in sys.argv:
    import app as frontend
    from gi.repository import Gtk,GLib
    log=Path(sys.argv[2]);uri=sys.argv[3]
    def record(event):
        with log.open('a') as stream:stream.write(json.dumps(dict(event=event,pid=os.getpid()))+'\n')
    class FakeApp:
        def __init__(self,application,smoke=False,invitation=''):
            assert invitation=='a'*64
            record('create');self.closed=False;self.busy=False;self.friends_window=None
            self.pending_invitation=invitation
            self.window=Gtk.ApplicationWindow(application=application)
            self.window.set_default_size(320,240)
            GLib.timeout_add(4000,lambda:(application.quit(),False)[1])
        def present(self):self.window.present()
        def select_page(self,page):assert page=='status'
        def initialize(self):assert self.pending_invitation=='a'*64;record('reuse')
        def submit(self,action,kind):assert kind=='initialized';action()
    frontend.App=FakeApp;sys.argv=[sys.argv[0],uri]
    raise SystemExit(frontend.main())

with tempfile.TemporaryDirectory(prefix='fc-invitation-ui-') as directory:
    log=Path(directory)/'events.jsonl'
    command=[sys.executable,str(Path(__file__).resolve()),'--child',str(log)]
    first=subprocess.Popen(command+['familyconnect://invite/'+'a'*64],stdout=subprocess.DEVNULL)
    try:
        deadline=time.monotonic()+10
        while not log.exists() and time.monotonic()<deadline:time.sleep(.05)
        assert log.exists(),'First instance did not open'
        subprocess.run(command+['familyconnect://invite/'+'a'*64],check=True,timeout=10)
        subprocess.run(command+['familyconnect://invite/invalid'],check=True,timeout=10)
        assert first.wait(timeout=10)==0
        events=[json.loads(line) for line in log.read_text().splitlines()]
        assert [event['event'] for event in events]==['create','reuse'],events
        assert len({event['pid'] for event in events})==1
    finally:
        if first.poll() is None:first.terminate();first.wait(timeout=5)
print('GTK invitation link: existing instance reused; malformed link ignored; no HTTP or VPN actions.')
