import json
import os
from pathlib import Path
import selectors
import socket
import subprocess
import sys
import time


def test_real_two_process_direct_delivery(tmp_path):
    root=Path(__file__).resolve().parents[2]
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    processes=[]
    def read(process):
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout,selectors.EVENT_READ)
            assert selector.select(15), 'Synthetic peer response timed out'
            line=process.stdout.readline()
            assert line, 'Synthetic peer exited'
            return json.loads(line)
    def command(process,**request):
        process.stdin.write(json.dumps(request)+'\n');process.stdin.flush()
        return read(process)
    try:
        peers=[]
        for role in ('server','client'):
            process=subprocess.Popen([sys.executable,str(root/'messenger/tests/wire_peer.py'),role,str(tmp_path/role),str(port)],
                stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,
                env={**os.environ,'PYTHONPATH':str(root)+os.pathsep+os.environ.get('PYTHONPATH','')})
            processes.append(process);peers.append(read(process)['public'])
        from messenger.codec import address
        for index,process in enumerate(processes):
            command(process,op='trust',public=peers[1-index])
        for _ in range(3):
            for process in processes:command(process,op='announce')
            time.sleep(.25)
        texts=['synthetic short text', 'Ж'*2000]
        for index,process in enumerate(processes):
            command(process,op='send',peer=address(bytes.fromhex(peers[1-index])).hex(),text=texts[index])
        deadline=time.monotonic()+30
        while time.monotonic()<deadline:
            histories=[command(process,op='messages') for process in processes]
            if all(len(history)==2 and {m['status'] for m in history}=={'received','delivered'} for history in histories):break
            time.sleep(.2)
        else:raise AssertionError('DIRECT delivery/receipt did not complete within 30s')
        assert all({m['text'] for m in history}==set(texts) for history in histories)
    finally:
        for process in processes:process.terminate()
        for process in processes:
            try:process.wait(timeout=5)
            except subprocess.TimeoutExpired:process.kill();process.wait(timeout=5)
            process.stdin.close();process.stdout.close()
