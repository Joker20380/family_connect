"""Observation-only edits on the pinned copy; no writer policy or Q1 activation."""
import subprocess
from interaction_prepare import FIX, SOURCE, TOOLS, WORK, write, save, inventory, delta, PARENT


def replace(name, old, new):
    path = SOURCE/name
    text = path.read_text()
    assert text.count(old) == 1, (name, old)
    write(path, text.replace(old, new))


def main():
    assert not (WORK/'observation-inventory.json').exists()
    write(SOURCE/'tcpforward/lab_interaction.go', (FIX/'interaction/observe.go').read_text())
    write(SOURCE/'familysession/lab_interaction.go', '''package familysession
import (
 "context"
 "github.com/Joker20380/family_connect/carrier/reliablestream"
)
func LabOpenMuxReliable(ctx context.Context, endpoint PacketEndpoint, raw []byte, server, credit128 bool, config reliablestream.Config) (*Session,error) {
 return openReliable(ctx,endpoint,raw,server,config,credit128)
}
''')
    replace('tcpforward/mux.go', 'type Mux struct {', 'type Mux struct {\n lab labMuxObservation')
    replace('tcpforward/mux.go', 'stream.creditPending = 0', 'mux.labEventLocked("credit_selected",id,stream.creditPending)\n stream.creditPending = 0')
    replace('tcpforward/mux.go', 'var pending *muxFrame\n\tfor mux.ctx.Err() == nil {\n\t\tmux.mu.Lock()', '''var pending *muxFrame
 for mux.ctx.Err() == nil {
  lockStarted := time.Now()
  mux.mu.Lock()
  lockWait := time.Since(lockStarted).Nanoseconds()
  mux.lab.WriterLockNS += lockWait
  mux.lab.WriterLockMaxNS = max(mux.lab.WriterLockMaxNS,lockWait)''')
    replace('tcpforward/mux.go', '\t\tchanged := mux.changed\n\t\tif sessiontrace.PerformanceEnabled && ok {', '''
  for _, current := range frames { mux.labEventLocked("writer_selected",current.id,int(current.kind)); }
  changed := mux.changed
  if sessiontrace.PerformanceEnabled && ok {''')
    replace('tcpforward/mux.go', '\t\tvar err error\n\t\tif len(frames) == 1 {', '\t\twriteStarted := time.Now()\n var err error\n\t\tif len(frames) == 1 {')
    replace('tcpforward/mux.go', '\t\tmux.mu.Lock()\n\t\tmux.stats.SchedulerFrames', '''
  mux.mu.Lock()
  sendWait := time.Since(writeStarted).Nanoseconds()
  mux.lab.WriterSendNS += sendWait
  mux.lab.WriterSendMaxNS = max(mux.lab.WriterSendMaxNS,sendWait)
  for _, current := range frames { mux.labEventLocked("writer_returned",current.id,int(current.kind)) }
  mux.stats.SchedulerFrames''')
    replace('tcpforward/mux.go', 'func (mux *Mux) dispatchLocked(frame muxFrame) {', 'func (mux *Mux) dispatchLocked(frame muxFrame) {\n mux.labEventLocked("reader_frame",frame.id,int(frame.kind))')
    replace('tcpforward/mux.go', '\t\t\tstream.sendCredit += credit', '\t\t\tstream.sendCredit += credit\n mux.labEventLocked("credit_applied",frame.id,credit)')
    replace('tcpforward/mux_stream.go', '\t\t\tstream.creditPending += count', '\t\t\tstream.creditPending += count\n mux.labEventLocked("read_credit_pending",stream.id,count)')
    replace('tcpforward/mux_stream.go', '\t\tmux.stats.FlowStalls++', '\t\tmux.labEventLocked("producer_wait",stream.id,len(payload))\n mux.stats.FlowStalls++')
    replace('tcpforward/mux_stream.go', '\t\t\tstream.sendCredit -= count', '\t\t\tstream.sendCredit -= count\n mux.labEventLocked("producer_queued",stream.id,count)')
    replace('cmd/telemost-binary/capacity.go', 'type capacityConfig struct {', 'type capacityConfig struct {\n MuxCredit128 bool')
    replace('cmd/telemost-binary/capacity.go', 'familysession.OpenReliable(ctx, endpoint, credentials, server, reliability)', 'familysession.LabOpenMuxReliable(ctx, endpoint, credentials, server, config.MuxCredit128, reliability)')
    replace('cmd/telemost-binary/capacity.go', '"event": "mux_lab_sample", "mux": stats', '"event": "mux_lab_sample", "mux": stats, "performance":mux.PerformanceSnapshot(), "reliability":reliableStats(), "packing":packingStats()')
    replace('cmd/telemost-binary/capacity.go', '"event": "mux_lab_final", "mux": mux.Stats()', '"event": "mux_lab_final", "mux": mux.Stats(), "observation":mux.LabObservation()')
    changed = [path for path in SOURCE.rglob('*.go') if not (PARENT/'source'/path.relative_to(SOURCE)).exists() or path.read_bytes() != (PARENT/'source'/path.relative_to(SOURCE)).read_bytes()]
    subprocess.run([TOOLS/'go/bin/gofmt','-w',*changed], check=True)
    write(WORK/'observation.patch', delta(PARENT/'source', SOURCE))
    save(WORK/'observation-inventory.json', inventory(SOURCE))


if __name__ == '__main__':
    main()
