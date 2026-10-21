"""Restore ordinary trace-off client behavior with a forward91->92 update."""

import json
import os
import shutil
import subprocess
import sys

from preserve import ROOT, WORK, PARENT, digest

NORMAL=WORK/'normal92'


def load(path, expected, replacements):
    assert digest(path)==expected
    source=path.read_text()
    for old,new in replacements.items():
        assert old in source,old
        source=source.replace(old,new)
    namespace=dict(__name__='normal92_scoped',__file__=str(path))
    exec(compile(source,str(path),'exec'),namespace)
    namespace['WORK']=NORMAL
    return namespace


def main():
    os.umask(0o077)
    mode=sys.argv[1]
    if mode=='prepare':
        inventory=json.loads((PARENT/'android-build/source-inventory.json').read_text())
        assert all(digest(PARENT/'android-source'/name)==expected for name,expected in inventory.items())
        NORMAL.mkdir(mode=0o700,exist_ok=False)
        shutil.copytree(PARENT/'android-source',NORMAL/'android-source',
                        ignore=shutil.ignore_patterns('.gradle','__pycache__'))
        print('EXACT_BETA90_SOURCE_COPIED_NO_FUNCTIONAL_CANDIDATE')
        return
    if mode=='restore-build-metadata':
        assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=PARENT/'android-source',text=True).strip()=='f5240994869826c6a28f59e58e38256c688cf6eb'
        shutil.copytree(PARENT/'android-source/.git',NORMAL/'android-source/.git')
        print('ACCEPTED_BUILD_SOURCE_METADATA_RESTORED_VERIFIER_UNCHANGED')
        return
    if mode=='build':
        runner=load(ROOT/'tests/fixtures/tunnel_restart/build_android.py',
                    '6c47af0394134b7f926c30bb4066d230845d3df07cfba7444395527f717c8fa1',
                    {'version_code=90':'version_code=92'})
    elif mode=='sign':
        runner=load(ROOT/'tests/fixtures/tunnel_restart/sign90.py',
                    'bba6af9da371102306eedd2b3d620cd8c716863f7812518f83238bdc0a4c7a8e',{
            'state-client-build/mesh-throughput-trace-20261019/delivery/FamilyConnect-0.1.18-beta89-mesh-trace.apk':
                'state-client-build/mesh-receive-path-20261020/delivery/FamilyConnect-0.1.18-beta91-receive-trace.apk',
            'metadata(baseline, 89, True), metadata(unsigned, 90, False)':
                'metadata(baseline, 91, True), metadata(unsigned, 92, False)',
            'FamilyConnect-0.1.18-beta90-stability.apk':'FamilyConnect-0.1.18-beta92-stability.apk',
            'metadata(signed, 90, True)':'metadata(signed, 92, True)',
            'SIGNED_PRIVATE_TRACE_REMOVAL_NOT_CLIENT_RESTART_FIX':'SIGNED_PRIVATE_TRACE_REMOVAL_NOT_SPEED_FIX'})
    else:
        assert mode in ('check','install','identity-after')
        runner=load(ROOT/'tests/fixtures/mesh_throughput_trace/upgrade.py',
                    'cde4965c08308c14bf23175ad3af87cdcbdc72d5e3cfd03de1f4d2ffeb623301',{
            "current['code'] == 88":"current['code'] == 91",
            "after['code'] == 89":"after['code'] == 92",
            "version_code')=89":"version_code')=92",
            'beta89_readiness':'beta92_readiness',
            'FamilyConnect-0.1.18-beta89-mesh-trace.apk':'FamilyConnect-0.1.18-beta92-stability.apk',
            "current['native_sha256'] == 'dd722eada0da7c890a8d71a72099cba5d0bbac1ce73377bbdbc8e7b85d820c23'":
                "current['native_sha256'] == 'f257616827ad70cfaff8fbca3f080ce54e8c5abde973ebdec370c3a919d9fcab'"})
    runner['main']()


if __name__=='__main__':
    if sys.argv[1]=='sign':
        try:main()
        except Exception:
            print('SIGNING_STOPPED_NO_SECRET_OUTPUT')
            raise SystemExit(1) from None
    else:main()
