"""Derive the existing operator with smaller caps and a two-end completion barrier."""
import subprocess
from interaction_prepare import FIX, SOURCE, WORK, TOOLS, write


def main():
    assert not (WORK/'run_phase.py').exists()
    def change(path,old,new):
        text=path.read_text()
        assert text.count(old)==1,(str(path),old)
        write(path,text.replace(old,new))
    host=SOURCE/'cmd/telemost-binary/host_compare.go'
    change(host,'index < 12;', 'index < 24;')
    change(host,'{{"small_idle", \'E\', 32}, {"control_echo", \'E\', 65536}}','{{"control_echo", \'E\', 65536}}')
    change(host,'\tsmallDone := make(chan error, 1)', '''
 for index:=0;index<6;index++ { if err:=request("small_idle_"+strconv.Itoa(index),'E',32);err!=nil{return err} }
 smallDone := make(chan error, 1)''')
    change(host,'go func() { time.Sleep(time.Second); smallDone <- request("small_loaded", \'E\', 32) }()', '''go func() {
 time.Sleep(time.Second)
 for index:=0;index<6;index++ {if err:=request("small_loaded_"+strconv.Itoa(index),'E',32);err!=nil{smallDone<-err;return};time.Sleep(100*time.Millisecond)}
 smallDone<-nil
 }()''')
    capacity=SOURCE/'cmd/telemost-binary/capacity.go'
    change(capacity,'ctx = familysession.WithLabPacking(ctx, config.Packing)', '''if config.Mode=="P" { var stopTransfer context.CancelFunc;ctx,stopTransfer=context.WithTimeout(ctx,180*time.Second);defer stopTransfer() }
 ctx = familysession.WithLabPacking(ctx, config.Packing)''')
    change(capacity,'"reliability": reliableStats(), "packing": packingStats()', '"pressure":interactionPressure(data.(*familysession.Session)), "packing":packingStats()')
    change(capacity,'"performance": mux.PerformanceSnapshot(), "pressure":', '"performance": interactionMuxPressure(mux), "pressure":')
    change(capacity,'"observation": mux.LabObservation()', '"observation": mux.LabObservation(), "performance":mux.PerformanceSnapshot()')
    old=capacity.read_text()
    start=old.index('\n\t\t\tif !server {',old.index('defer func() {\n\t\t\tif !server'))
    end=old.index('\n\t\t\t_ = emit(map[string]any{"event": "packing_pre_close"',start)
    write(capacity,old[:start]+old[end:])
    change(capacity,'''if server {
			return mux.Wait()
		}
		return muxHostCompare(ctx, mux, 18764, snapshot, emit)''','''if !server {
 if err:=muxHostCompare(ctx,mux,18764,snapshot,emit);err!=nil{return err}
 _=emit(map[string]any{"event":"p_workload_done"})
 }
 return interactionComplete(ctx,path,mux,data.(*familysession.Session),server,emit)''')
    write(SOURCE/'cmd/telemost-binary/lab_interaction_completion.go',(FIX/'interaction/completion.go').read_text())
    subprocess.run([TOOLS/'go/bin/gofmt','-w',host,capacity,SOURCE/'cmd/telemost-binary/lab_interaction_completion.go'],check=True)
    text=(FIX/'run.py').read_text()
    replacements=[
        ('from prepare import ROOT, WORK, FIX, digest','from interaction_prepare import ROOT, WORK, FIX, digest'),
        ('spec.loader.exec_module(host_operator)','spec.loader.exec_module(host_operator)\nhost_operator.WORK=WORK'),
        ("parser.add_argument('--media'", "parser.add_argument('--credit128',action='store_true')\n    parser.add_argument('--media'"),
        ('args=parser.parse_args()',"args=parser.parse_args()\n    assert args.mode=='P' and args.send==32 and args.receive==32 and not args.reverse"),
        ('Packing=args.packing,MediaPolicy','Packing=args.packing,MuxCredit128=args.credit128,MediaPolicy'),
        ("if args.mode=='P':app=8585273+1024","if args.mode=='P':app=8*1024**2+3*65536+12*64+4096"),
        ('app_used+app<=128*1024*1024','app_used+app<=64*1024*1024'),
        ('wire_used+server_limit+client_limit<=256*1024*1024','wire_used+server_limit+client_limit<=128*1024*1024'),
        ('packing-20261021-','pstack-20261021-'),
        ("FIX/'worker.py'","WORK/'worker.py'"),
        ('RuntimeMaxSec=510','RuntimeMaxSec=280'),
        ('runtime=510','runtime=280'),
        ('deadline=time.monotonic()+490','deadline=time.monotonic()+250\n        draining=False\n        finished=False'),
        ("time.sleep(5)\n            if args.mode=='P':", "time.sleep(2)\n            if args.mode=='P':"),
        ("current=production_state()",'''if any(row.get('event')=='p_workload_done' for row in rows(directory/'peer.jsonl')) and not draining:
                (directory/'drain.input').write_text(args.phase)
                ssh(HOST,"from pathlib import Path;Path("+repr(stage+'/drain.input')+").write_text("+repr(args.phase)+")")
                draining=True
            if draining and not finished:
                local_rows=rows(directory/'peer.jsonl')
                remote_rows=[json.loads(line) for line in remote_snapshot(HOST,stage).get('peer.jsonl','').splitlines() if line.strip()]
                proofs=[next((row for row in events if row.get('event')=='p_drained'),None) for events in [local_rows,remote_rows]]
                if all(proofs):
                    assert all(row['error']=='<nil>' and row['mux']['ActiveStreams']==0 and row['mux']['ProtocolErrors']==0 and row['reliability']['DataSent']==row['reliability']['Performance']['ReleasedBlocks'] for row in proofs),'TWO_END_DRAIN_FAILED'
                    for sender,receiver in [(proofs[0],proofs[1]),(proofs[1],proofs[0])]:
                        first,second=sender['packing'],receiver['packing']
                        assert first['Accepted']==first['Sent']==second['Received'] and first['InputSHA256']==first['OutputSHA256']==second['ReceiveSHA256'],'CIPHERTEXT_COMPLETION_FAILED'
                    assert len([row for row in remote_rows if row.get('event')=='host_fixture_result' and row.get('passed')])==17,'SERVER_BODY_COMPLETION_FAILED'
                    save(directory/'two-end-proof.json',dict(client=proofs[0],server=proofs[1]))
                    ssh(HOST,"from pathlib import Path;Path("+repr(stage+'/finish.input')+").write_text("+repr(args.phase)+")")
                    (directory/'finish.input').write_text(args.phase)
                    finished=True
            current=production_state()'''),
        ("assert local.poll() is not None,'LOCAL_DEADLINE'", "assert local.poll() is not None,'LOCAL_DEADLINE'\n        assert finished,'MISSING_TWO_END_COMPLETION'"),
    ]
    for old,new in replacements:
        assert old in text,old
        text=text.replace(old,new)
    text=text.replace('from interaction_prepare import ROOT, WORK, FIX, digest','from interaction_prepare import ROOT, WORK, FIX, digest\nfrom interaction_proof import validate')
    start=text.index("                    assert all(row['error']=='<nil>'")
    end=text.index("                    save(directory/'two-end-proof.json'",start)
    text=text[:start]+"                    validate(proofs,[row for row in local_rows if row.get('event')=='host_request'],131072 if args.credit128 else 65536)\n"+text[end:]
    write(WORK/'run_phase.py',text)
    worker=(FIX/'worker.py').read_text().replace("'8m' if config['Mode']=='P' else '210s'","'240s'").replace('time.monotonic()-started<490','time.monotonic()-started<250')
    write(WORK/'worker.py',worker)


if __name__=='__main__':
    main()
