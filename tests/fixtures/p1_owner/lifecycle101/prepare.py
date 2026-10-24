"""Fresh exact100/f631 observation capsule; no network or installation."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[4]
FIXTURE = Path(__file__).resolve().parent
BASE = ROOT / 'state-client-build/p1-owner-acceptance-20261021'
WORK = ROOT / 'state-client-build/p1-lifecycle-101-20261021'


def patch(path, old, new):
    text=path.read_text()
    assert text.count(old) == 1, (path, old)
    position=text.index(old)
    start=text.rfind('\n',0,position)+1
    end=text.find('\n',position+len(old))
    if end<0:end=len(text)
    original=text[start:end]
    new=original.replace(old,new)
    old=original
    subprocess.run(['apply_patch', '*** Begin Patch\n*** Update File: '+str(path)+'\n@@\n'+
                    ''.join('-'+line+'\n' for line in old.splitlines())+
                    ''.join('+'+line+'\n' for line in new.splitlines())+'*** End Patch\n'], check=True)


def replace_file(path, template):
    patch(path, path.read_text().rstrip('\n'), template.read_text().rstrip('\n'))


def instrument(carrier):
    replace_file(carrier/'tcpforward/mux_lifecycle.go', FIXTURE/'mux_lifecycle.go')
    path=carrier/'tcpforward/mux.go'
    patch(path, 'mux.lifeLocked("unknown", frame.id, frame.kind, "missing")',
          'mux.lifeLocked("unknown", frame.id, frame.kind, "missing")\n mux.lifeFrameLocked(frame, false)')
    patch(path, 'if stream.terminal != nil {\n\t\treturn\n\t}\n\tinvalid := false',
          'if stream.terminal != nil {\n mux.lifeFrameLocked(frame, false)\n return\n }\n invalid := false')
    patch(path, 'if invalid {', 'if invalid {\n mux.lifeFrameLocked(frame, true)')
    patch(path, 'case resetFrame:\n\t\tmux.stats.Resets++',
          'case resetFrame:\n stream.life.PeerTerminal = true\n mux.stats.Resets++')
    patch(path, 'stream.creditPending = 0\n\t\t\treturn muxFrame{muxWindowUpdate, id, credit}, true',
          'stream.creditPending = 0\n mux.lifeLocked("enqueue", id, muxWindowUpdate, "control")\n return muxFrame{muxWindowUpdate, id, credit}, true')
    path=carrier/'tcpforward/mux_stream.go'
    patch(path, 'stream.finishLocked(err)\n\tstream.send = []muxFrame{{resetFrame, stream.id, nil}}',
          'stream.life.LocalAbort = true\n stream.finishLocked(err)\n stream.send = []muxFrame{{resetFrame, stream.id, nil}}\n stream.mux.lifeLocked("enqueue", stream.id, resetFrame, "control")')
    patch(path, 'stream.send = append(stream.send, muxFrame{finFrame, stream.id, nil})',
          'stream.send = append(stream.send, muxFrame{finFrame, stream.id, nil})\n mux.lifeLocked("enqueue", stream.id, finFrame, "control")')
    patch(path, 'stream.send = append(stream.send, muxFrame{closeFrame, stream.id, nil})',
          'stream.send = append(stream.send, muxFrame{closeFrame, stream.id, nil})\n mux.lifeLocked("enqueue", stream.id, closeFrame, "control")')


def main():
    os.umask(0o077)
    inventory=json.loads((BASE/'build/source-inventory.json').read_text())
    assert all(hashlib.sha256((BASE/'android-source'/name).read_bytes()).hexdigest()==digest for name,digest in inventory.items())
    assert not (WORK/'android-source').exists() and not (WORK/'gateway-source').exists()
    for name in ('android-source','gateway-source'):
        shutil.copytree(BASE/name,WORK/name,ignore=shutil.ignore_patterns('.git','.gradle','__pycache__','build'))
    for carrier in (WORK/'android-source/carrier',WORK/'gateway-source'):
        instrument(carrier)
        shutil.copy2(FIXTURE/'lifecycle101_test.go',carrier/'tcpforward/lifecycle101_test.go')
    java=WORK/'android-source/clients/android/app/src/main/java/com/familyconnect/app/MuxLifecycle.java'
    replace_file(java,FIXTURE/'MuxLifecycle.java')
    patch(WORK/'android-source/clients/android/app/build.gradle',
          "versionCodeOverride = 100; versionNameOverride = '0.1.18-beta100-lifecycle'",
          "versionCodeOverride = 101; versionNameOverride = '0.1.18-beta101-lifecycle'")
    print('PREPARED101_NOT_BUILT_INSTALLED_OR_DEPLOYED')


if __name__=='__main__': main()
