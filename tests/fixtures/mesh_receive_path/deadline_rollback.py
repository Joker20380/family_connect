"""Prepare a forward-only ordinary94 fallback, exact92 native and Java."""

import os
import shutil
import subprocess
import sys

from deadline import WORK
from late_arrival import ROOT, SAVED, digest


def main():
    os.umask(0o077)
    normal = WORK / 'normal94'
    if sys.argv[1] == 'prepare':
        normal.mkdir(mode=0o700, exist_ok=False)
        shutil.copytree(SAVED / 'normal92/android-source', normal / 'android-source', ignore=shutil.ignore_patterns('.gradle', '__pycache__'))
        gradle = normal / 'android-source/clients/android/app/build.gradle'
        subprocess.run(['apply_patch', '*** Begin Patch\n*** Update File: '+str(gradle)+
            "\n@@\n-            variant.outputs.all { versionCodeOverride = 92; versionNameOverride = '0.1.18-beta92-stability' }\n"+
            "+            variant.outputs.all { versionCodeOverride = 94; versionNameOverride = '0.1.18-beta94-stability' }\n*** End Patch\n"], check=True)
        return
    original = ROOT / 'tests/fixtures/tunnel_restart/build_android.py'
    assert digest(original) == '6c47af0394134b7f926c30bb4066d230845d3df07cfba7444395527f717c8fa1'
    source = original.read_text().replace('version_code=90', 'version_code=94')
    namespace = dict(__name__='deadline_forward_fallback', __file__=str(original))
    exec(compile(source, str(original), 'exec'), namespace)
    namespace['WORK'] = normal
    namespace['main']()


if __name__ == '__main__':
    main()
