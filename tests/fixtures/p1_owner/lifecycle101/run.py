"""Reuse owner automation; same cumulative ledger, <=24MiB additional traffic."""
import hashlib
import json
import runpy
import sys
from pathlib import Path
from prepare import ROOT, BASE, WORK


def main():
    action=sys.argv.pop(1)
    fixture=ROOT/'tests/fixtures/p1_owner'
    sys.path.insert(0,str(fixture));sys.path.insert(0,str(ROOT))
    import observe
    observe.WORK=WORK
    if action=='readback':
        module=runpy.run_path(str(ROOT/'tests/fixtures/speed_candidate/readback.py'))
        module['main'].__globals__['WORK']=WORK
        module['main']();return
    assert action in ('gate','observe','control','traffic')
    source=(fixture/(action+'.py')).read_text()
    source=source.replace("WORK=ROOT/'state-client-build/p1-owner-acceptance-20261021'",'WORK=Path('+repr(str(WORK))+')')
    if action=='gate':source=source.replace("phone['version_code']==100","phone['version_code']==101")
    if action=='control':
        sys.modules.pop('prepare',None)
        source=source.replace("(WORK/'p0-observed-gateway.json')",'(Path('+repr(str(BASE/'p0-observed-gateway.json'))+'))')
    if action=='traffic':
        source=source.replace("ledger=WORK/'traffic-ledger'",'ledger=Path('+repr(str(BASE/'traffic-ledger'))+')')
        source=source.replace("'active':(4<<20)+31*1024","'active':(1<<20)+31*1024")
        source=source.replace("'periodic-bulk-'+str(index),1<<20","'periodic-bulk-'+str(index),1<<18")
        source=source.replace('assert used+amount<=64<<20','assert used+amount<=64<<20\n    assert used+amount-37832704<=24<<20')
        assert "ledger=Path(" in source and '37832704' in source
    namespace=dict(__name__='__main__',__file__=str(fixture/(action+'.py')),Path=Path)
    exec(compile(source,str(fixture/(action+'.py')),'exec'),namespace)


if __name__=='__main__':main()
