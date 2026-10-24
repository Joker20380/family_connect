"""Exact99 observation copy; no install, policy change or historical rewrite."""
import json
import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[3]
WORK = ROOT / 'state-client-build/p1-owner-acceptance-20261021'
BASE = ROOT / 'state-client-build/support-cadence99-20261021'
JAVA = Path('clients/android/app/src/main/java/com/familyconnect/app')
sys.path.insert(0, str(ROOT / 'tests/fixtures/speed_candidate'))
from prepare import digest, replace, write


def instrument(source):
    write(source / 'tcpforward/mux_lifecycle.go', Path(__file__).with_name('mux_lifecycle.go').read_text())
    replace(source / 'tcpforward/mux.go', 'type MuxConfig struct {', 'type MuxConfig struct {\n Lifecycle bool')
    replace(source / 'tcpforward/mux.go', 'type MuxStats struct {', 'type MuxStats struct {\n Lifecycle *MuxLifecycle')
    replace(source / 'tcpforward/mux.go', 'type Mux struct {', 'type Mux struct {\n life muxLifeBuffer')
    replace(source / 'tcpforward/mux.go', 'return mux.stats', 'stats := mux.stats\n stats.Lifecycle = mux.lifeSnapshotLocked()\n return stats')
    replace(source / 'tcpforward/mux.go', 'if mux.err == nil {\n\t\tmux.err = err', 'if mux.err == nil {\n mux.lifeLocked("failure", 0, 0, lifeReason(err))\n\t\tmux.err = err')
    replace(source / 'tcpforward/mux.go', 'func (mux *Mux) Close() error {', 'func (mux *Mux) Close() error {\n mux.mu.Lock(); mux.lifeLocked("close", 0, 0, "caller"); mux.mu.Unlock();')
    replace(source / 'tcpforward/mux.go', 'func (mux *Mux) controlLocked(frame muxFrame) {', 'func (mux *Mux) controlLocked(frame muxFrame) {\n mux.lifeLocked("enqueue", frame.id, frame.kind, "control")')
    replace(source / 'tcpforward/mux.go', 'delete(mux.streams, id)', 'mux.lifeLocked("remove", id, 0, "terminal")\n delete(mux.streams, id)')
    replace(source / 'tcpforward/mux.go', 'func (mux *Mux) dispatchLocked(frame muxFrame) {', 'func (mux *Mux) dispatchLocked(frame muxFrame) {\n mux.lifeLocked("receive", frame.id, frame.kind, "wire")')
    path=source/'tcpforward/mux.go'
    counter='mux.protocolErrorLocked' if 'mux.protocolErrorLocked' in path.read_text() else 'mux.stats.ProtocolErrors++'
    marker='if stream == nil {\n\t\t'+counter
    replace(path,marker,'if stream == nil {\n mux.lifeLocked("unknown", frame.id, frame.kind, "missing")\n\t\t'+counter)
    replace(source/'tcpforward/mux.go','stream.opened = true\n\t\t\tmux.stats.OpenOK++','stream.opened = true\n mux.lifeLocked("opened", stream.id, openOK, "peer")\n\t\t\tmux.stats.OpenOK++')
    replace(source/'tcpforward/mux.go','stream.opened = true\n\t\tstream.send','stream.opened = true\n mux.lifeLocked("opened", stream.id, openOK, "lease")\n\t\tstream.send')
    replace(source/'tcpforward/mux.go','stream.opened = true\n\tmux.stats.ActiveSockets','stream.opened = true\n mux.lifeLocked("opened", stream.id, openOK, "socket")\n\tmux.stats.ActiveSockets')
    anchor='changed := mux.changed\n\t\tif sessiontrace.PerformanceEnabled && ok {' if 'if sessiontrace.PerformanceEnabled && ok {' in path.read_text() else 'changed := mux.changed\n\t\tmux.mu.Unlock()\n\t\tif !ok {'
    replace(path,anchor,'for _, current := range frames { mux.lifeLocked("send_start", current.id, current.kind, "batch") }\n '+anchor)
    replace(path,'terminal := current.kind == resetFrame','mux.lifeLocked("send_done", current.id, current.kind, "local")\n terminal := current.kind == resetFrame')
    replace(source/'tcpforward/mux_stream.go','type MuxStream struct {','type MuxStream struct {\n life MuxLifeStream')
    replace(source/'tcpforward/mux_stream.go','mux.streams[id] = stream','mux.streams[id] = stream\n mux.lifeLocked("create", id, 0, "new")')
    replace(source/'tcpforward/mux_stream.go','stream.terminal = err','stream.mux.lifeLocked("finish", stream.id, 0, lifeReason(err))\n stream.terminal = err')
    replace(source/'tcpforward/mux_stream.go','stream.sent += uint64(count)','mux.lifeLocked("enqueue", stream.id, dataFrame, "data")\n stream.sent += uint64(count)')
    replace(source/'sessiondiag/report.go','type Report struct {','type Report struct {\n MuxLifecycle *tcpforward.MuxLifecycle `json:"mux_lifecycle,omitempty"`')
    replace(source/'sessiondiag/report.go','report := Report{','report := Report{MuxLifecycle: mux.Lifecycle,')


def main():
    os.umask(0o077)
    source=WORK/'android-source'
    assert not source.exists()
    inventory=json.loads((BASE/'build/source-inventory.json').read_text())
    assert all(digest(BASE/'android-source'/name)==value for name,value in inventory.items())
    shutil.copytree(BASE/'android-source',source,ignore=shutil.ignore_patterns('.git','.gradle','__pycache__','build'))
    instrument(source/'carrier')
    write(source/'carrier/tcpforward/mux_lifecycle_test.go',Path(__file__).with_name('mux_lifecycle_test.go').read_text())
    replace(source/'carrier/wholedevice/session.go','WaitForSlot: true','WaitForSlot: true, Lifecycle: true')
    write(source/JAVA/'MuxLifecycle.java',Path(__file__).with_name('MuxLifecycle.java').read_text())
    replace(source/JAVA/'DiagnosticRing.java','SpeedReceipt.project(source,safe);','SpeedReceipt.project(source,safe);\n MuxLifecycle.project(source,safe);')
    replace(source/'clients/android/app/build.gradle',"versionCodeOverride = 99; versionNameOverride = '0.1.18-beta99-support'","versionCodeOverride = 100; versionNameOverride = '0.1.18-beta100-lifecycle'")
    print('PREPARED100_OBSERVATION_NOT_INSTALLED')


if __name__=='__main__': main()
