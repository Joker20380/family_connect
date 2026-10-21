"""Rebase the sealed Q1 correctness delta only; full candidate uses sealed .apply_patch files."""

import json
import subprocess
from prepare import ROOT, WORK, FIXTURE, GATEWAY, digest, write, replace


def q1_android(carrier):
    pins = json.loads((ROOT / 'tests/fixtures/queue_retry/source-pins.json').read_text())['patches']['completion']
    assert digest(ROOT / 'tests/fixtures/queue_retry/completion.patch') == pins['patch_sha256']
    origin = ROOT / 'state-client-build/queue-retry-20261019'
    for name, seal in pins['changes'].items():
        before, after = origin / 'baseline-source/carrier' / name, origin / 'candidate-source/carrier' / name
        assert (digest(before) if before.exists() else None) == seal['input_sha256']
        assert digest(after) == seal['output_sha256']
        current = carrier / name
        if not before.exists() or digest(current) == digest(before):
            content = after.read_text()
        else:
            merge = subprocess.run(['git', 'merge-file', '-p', str(current), str(before), str(after)], text=True, capture_output=True)
            assert merge.returncode == 0, name
            content = merge.stdout
        write(current, content)
    write(carrier / 'localwrite/scope.go', (GATEWAY / 'candidate/localwrite/scope.go').read_text())
    path = carrier / 'reliablestream/stream.go'
    replace(path, 'func (stream *Stream) run(ctx context.Context) {', 'func (stream *Stream) run(ctx context.Context) {\n\tcompletionEnabled := localwrite.Enabled(ctx)')
    replace(path, 'sendContext, cancel := context.WithDeadline(ctx, job.queued.Add(min(stream.state.config.MaxAge, 2*time.Second)))', '''deadline := time.Now().Add(min(stream.state.config.MaxAge, 2*time.Second))
		if completionEnabled { deadline = job.queued.Add(min(stream.state.config.MaxAge, 2*time.Second)) }
		sendContext, cancel := context.WithDeadline(ctx, deadline)''')
    replace(path, 'sendContext, completion := localwrite.Observe(sendContext, job.obsolete)', '''var completion *localwrite.Write
		if completionEnabled { sendContext, completion = localwrite.Observe(sendContext, job.obsolete) }''')
    replace(path, 'if err == nil {\n\t\t\terr = completion.Wait()', 'if err == nil && completionEnabled {\n\t\t\terr = completion.Wait()')
    replace(path, 'activeData := make(map[uint64]queuedFrame)', 'var activeData map[uint64]queuedFrame\n\tif completionEnabled { activeData = make(map[uint64]queuedFrame) }')
    replace(path, 'job.obsolete = make(chan struct{})\n\t\t\t\tactiveData[packet.seq] = job', 'if completionEnabled {\n\t\t\t\t\tjob.obsolete = make(chan struct{})\n\t\t\t\t\tactiveData[packet.seq] = job\n\t\t\t\t}')
    replace(path, 'if result.job.packet.kind == dataFrame {', 'if completionEnabled && result.job.packet.kind == dataFrame {')
    for name in ('local_write_test.go', 'local_deadline_test.go'):
        write(carrier / 'reliablestream' / name, (GATEWAY / 'candidate/reliablestream' / name).read_text())

