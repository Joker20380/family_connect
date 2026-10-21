"""Finite authorized continuation; each phase closes before the next reservation."""
import json
import subprocess
import sys
from prepare import FIX,WORK
from analyze import analyze

def clean(name,result):
    phase=result['phases'][name]
    assert phase['result'].get('completed') and not phase['result'].get('error'),(name,'phase failed')
    assert not any(phase['protocol_errors'].values()),(name,'protocol error')
    assert all(value['accepted_equals_ordered_peer'] and value['accepted_equals_submitted'] for value in phase['packing'].values()),(name,'ciphertext boundary incomplete')
    if phase['config']['Mode']=='T':
        assert phase['delivery_fraction']==1 and phase['received']['corrupt']==0,(name,'T integrity')
    else:
        assert len(phase['requests'])==7 and all(value['passed'] for value in phase['requests']),(name,'P integrity')

def main():
    assert not (WORK/'verification.json').exists()
    result=analyze()
    for name in ['T8A','T8B']:clean(name,result)
    assert result['phases']['T8B']['packing']['server']['bytes_per_slot']>result['phases']['T8A']['packing']['server']['bytes_per_slot']*1.5
    phases=[('T32A1','T','A',32),('T32B1','T','B2',32),('T32B2','T','B2',32),('T32A2','T','A',32),('P32A1r','P','A',32),('P32B1','P','B2',32),('P32B2','P','B2',32),('P32A2','P','A',32),('P8Ar','P','A',8),('P8B','P','B2',8)]
    for name,mode,packing,window in phases:
        if (WORK/name/'reservation.json').exists():
            clean(name,result)
            continue
        command=[sys.executable,str(FIX/'run.py'),name,'--mode',mode,'--packing',packing,'--send',str(window),'--receive',str(16 if window==8 else 32),'--count','256']
        subprocess.run(command,check=True,timeout=550)
        result=analyze();clean(name,result)
        if name=='T32B1':
            assert result['phases'][name]['received_mbit_s_to_last']>=result['phases']['T32A1']['received_mbit_s_to_last']*.5,'severe T regression; stop'
        if name=='P32B1':
            def single(phase):return next(row['goodput_mbit_s'] for row in phase['requests'] if row['name']=='single')
            assert single(result['phases'][name])>=single(result['phases']['P32A1r'])*.5,'severe P regression; stop'
    print('FINITE MATRIX COMPLETE; no more load scheduled',flush=True)

if __name__=='__main__':main()
