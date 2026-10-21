"""Keep exact accepted-source deltas and replayable apply_patch input, no commits."""

import difflib
import json
import shutil
import subprocess
from prepare import ROOT, WORK, FIXTURE, ANDROID, GATEWAY, digest, write


def inventory(source):
    return {str(path.relative_to(source)): digest(path) for path in source.rglob('*') if path.is_file() and not any(part in ('.git','.gradle','__pycache__','build') for part in path.relative_to(source).parts)}


def delta(name, before, after):
    previous, current = inventory(before), inventory(after)
    changes={}; unified=[]; applicable=['*** Begin Patch\n']
    for relative in sorted(set(previous)|set(current)):
        if previous.get(relative)==current.get(relative):continue
        assert relative in current, 'unexpected deletion'
        old=(before/relative).read_text().splitlines(True) if relative in previous else []
        new=(after/relative).read_text().splitlines(True)
        lines=list(difflib.unified_diff(old,new,fromfile='a/'+relative if old else '/dev/null',tofile='b/'+relative))
        unified.extend(lines)
        if not old:
            applicable.append('*** Add File: '+relative+'\n')
            applicable.extend('+'+line.rstrip('\n')+'\n' for line in new)
        else:
            applicable.append('*** Update File: '+relative+'\n')
            applicable.extend('@@\n' if line.startswith('@@') else line for line in lines[2:])
        changes[relative]=dict(before=previous.get(relative),after=current[relative])
    applicable.append('*** End Patch\n')
    write(FIXTURE/(name+'.patch'),''.join(unified))
    write(FIXTURE/(name+'.apply_patch'),''.join(applicable))
    (WORK/(name+'-inventory.json')).write_text(json.dumps(current,indent=2,sort_keys=True))
    replay=WORK/('replay-'+name)
    assert not replay.exists()
    shutil.copytree(before,replay,ignore=shutil.ignore_patterns('.git','.gradle','__pycache__','build'))
    subprocess.run(['apply_patch'],input=''.join(applicable),cwd=replay,text=True,check=True,stdout=subprocess.DEVNULL)
    assert inventory(replay)==current
    return dict(changes=changes,patch_sha256=digest(FIXTURE/(name+'.patch')),apply_patch_sha256=digest(FIXTURE/(name+'.apply_patch')),inventory_sha256=digest(WORK/(name+'-inventory.json')),replay='EXACT_ALL_SOURCE_FILES')


def main():
    assert not (WORK/'source-seal.json').exists()
    from q1_core import q1_android
    q1=WORK/'q1-only'
    shutil.copytree(ANDROID/'android-source/carrier',q1)
    q1_android(q1)
    result={
        'android-q1-core':delta('android-q1-core',ANDROID/'android-source/carrier',q1),
        'android96-to97':delta('android96-to97',ANDROID/'android-source',WORK/'android-source'),
        'gateway734-to-speed':delta('gateway734-to-speed',GATEWAY/'candidate',WORK/'gateway-source'),
    }
    protected=['go.mod','go.sum','telemost/msg.go','telemost/rtp.go','telemost/vp8.go','reliablestream/protocol.go','tcpforward/mux.go','tcpforward/mux_stream.go','roombroker/lease_control.go','roombroker/lease.go','bootstrap/seed.go']
    for name,source,before in [('android',WORK/'android-source/carrier',ANDROID/'android-source/carrier'),('gateway',WORK/'gateway-source',GATEWAY/'candidate')]:
        result[name+'-protected']={relative:digest(source/relative) for relative in protected if (source/relative).exists()}
        assert all(digest(before/relative)==value for relative,value in result[name+'-protected'].items())
    for relative in ['cmd/bootstrap-broker/seed_recovery.go','cmd/bootstrap-broker/seed_recovery_test.go']:
        assert digest(WORK/'gateway-source'/relative)==digest(GATEWAY/'candidate'/relative)
    result['build']=json.loads((WORK/'build/receipt.json').read_text())
    result['gateway_build']=json.loads((WORK/'gateway-build.json').read_text())
    result['runtime_changed']=False
    (WORK/'source-seal.json').write_text(json.dumps(result,indent=2))
    print(json.dumps({name:len(value['changes']) for name,value in result.items() if isinstance(value,dict) and 'changes' in value}))


if __name__=='__main__':main()
