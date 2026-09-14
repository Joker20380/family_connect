"""Display-backed recovery intent and stale-completion regressions."""
from concurrent.futures import Future
from app import App,Adw
from backend import AuthorizationError,ConnectionSnapshot,ConnectionBusy
from layout_check import pump

def done(value):
    f=Future();f.set_result(value);return f

def main():
    Adw.init();app=App(smoke=True)
    class Driver:
        connected=True
        repairs=0
        def active(self,ident):return self.connected
        def supports_recovery(self,ident):return True
        def healthy(self,ident):return False
        def recover(self,ident):self.repairs+=1;self.connected=True
        def disconnect(self,ident):self.connected=False
        def connect(self,ident):self.connected=True
    d=Driver();app.driver=d;app.items=[('vpn','VPN')];app.selected_id='vpn';app.active=True
    try:
        app.complete('connected',done(True),app.revision,None)
        assert app.recovery.identity=='vpn'
        app.complete('health',done((True,False)),app.revision,'vpn')
        assert d.repairs==0
        app.complete('health',done((True,False)),app.revision,'vpn')
        pump(.2)
        assert d.repairs==1 and not app.busy and app.active and app.recovery.attempts==1
        # The explicit Disconnect intent invalidates a health check already in flight.
        revision=app.revision
        app.toggle_vpn();pump(.2)
        app.complete('health',done((True,False)),revision,'vpn')
        assert d.repairs==1 and app.recovery.identity is None and not app.active
        app.recovery.arm('vpn')
        cancelled=Future();cancelled.set_exception(AuthorizationError('cancelled'))
        app.complete('recovered',cancelled,app.revision,None)
        assert app.recovery.identity is None, 'Authorization cancellation would repeat prompts'
        # A standalone TCP keeps monitoring without opening authorization dialogs.
        d.allows_automatic_recovery=lambda _:False
        app.active=True;app.recovery.arm('vpn')
        for _ in range(5):app.complete('health',done((True,False)),app.revision,'vpn')
        assert d.repairs==1 and not app.busy and app.active
        assert app.recovery.identity=='vpn' and app.recovery.attempts==0
        assert 'вручную' in app.detail_text or 'manually' in app.detail_text
        app.complete('health',done((True,True)),app.revision,'vpn')
        assert app.detail_text=='' and app.recovery.failures==0
        # A control transaction committed a new profile while an old GUI health
        # check was in flight: sync selection and never recover the old profile.
        app.operation_generation=1;app.recovery.arm('vpn')
        snapshot=ConnectionSnapshot(2,[('vpn','Old'),('new','New')],['new'],False,False)
        app.complete('health',done(snapshot),app.revision,'vpn')
        assert app.selected_id=='new' and app.active and d.repairs==1
        assert app.recovery.identity=='new'
        busy=Future();busy.set_exception(ConnectionBusy('pending'))
        app.complete('poll',busy,app.revision,'new')
        assert app.recovery.identity is None and not app.polling
        app.selected_id='vpn'
        # Changing selection must not let old results resume another profile.
        app.recovery.arm('vpn');app.selected_id='other'
        app.complete('health',done((False,False)),app.revision,'vpn')
        assert d.repairs==1
        app.recovery.arm('vpn');app.close(True)
        assert app.recovery.identity is None
        app.complete('health',done((False,False)),app.revision,'vpn')
        assert d.repairs==1
        print('GTK recovery: threshold, reconnect, explicit disconnect, stale selection and close passed.')
    finally:
        app.busy=False;app.close(True)

if __name__=='__main__':main()
