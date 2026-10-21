from lab import FIX, SOURCE, WORK, ROOT, replace, write


def main():
    write(SOURCE/'telemost/lab_fragment.go',(FIX/'fragment.go').read_text())
    write(SOURCE/'telemost/lab_fragment_test.go',(FIX/'fragment_test.go').read_text())
    replace(SOURCE/'telemost/head_loss_test.go','point.reassembler.ingest(fragment)','point.labIngest(fragment)')
    session=SOURCE/'telemost/session.go'
    replace(session,'reassembler *reassembler','reassembler *reassembler\n labFragments *labFragmentCodec')
    replace(session,'s.reassembler.trace = cfg.Trace','s.reassembler.trace = cfg.Trace\n if labFragmentSettings.Mode=="S" || labFragmentSettings.Mode=="SF" {s.labFragments=newLabFragmentCodec(labFragmentSettings)}')
    replace(session,'s.reassembler.prune()','s.reassembler.prune()\n if s.labFragments!=nil {s.labFragments.prune()}')
    replace(session,'encodeFragments(s.senderID, msgID, payload)','s.labEncode(ctx, msgID, payload)')
    replace(session,'s.reassembler.ingest(msg.Data)','s.labIngest(msg.Data)')
    replace(session,'var queuedAt time.Time\n\t\tif s.cfg.PacketPacing != nil {\n\t\t\tqueuedAt = time.Now()\n\t\t}', 'queuedAt := time.Now()')
    replace(session,'s.signalClosedAt(ErrClosed, source)','s.signalClosedAt(ErrClosed, source)\n if s.labFragments!=nil {s.labFragments.close()}')
    signaling=SOURCE/'telemost/signaling.go'
    replace(signaling,'s.reassembler.ingest(frag)','s.labIngest(frag)')
    replace(signaling,'written := s.writeVP8Sample(frame.data, frame.point)','if s.labFragments!=nil {s.labFragments.mutex.Lock();age:=uint64(time.Since(frame.queuedAt));s.labFragments.metrics.QueueAgeMaxNS=max(s.labFragments.metrics.QueueAgeMaxNS,age);s.labFragments.metrics.QueueAgeNS+=age;s.labFragments.metrics.QueueSamples++;s.labFragments.mutex.Unlock()}\n written := s.writeVP8Sample(frame.data, frame.point)')
    boundary=SOURCE/'telemost/boundary.go'
    replace(boundary,'point := sessiontrace.Boundary{}\n\tif len(data) < fragmentHeaderLen {','''point := sessiontrace.Boundary{}
 if len(data)>=labHeader && string(data[:4])=="FCF2" {
 point.Sender=binary.BigEndian.Uint32(data[24:]);point.Message=binary.BigEndian.Uint32(data[28:]);point.Fragment=uint32(binary.BigEndian.Uint16(data[40:]))*10+uint32(data[42]);point.Total=80;point.MessageKnown=true
 if point.Fragment==0 {point.DataSequence,point.DataKnown=reliablestream.DataSequencePrefix(data[labHeader:],binary.BigEndian.Uint32(data[32:]))};return point
 }
 if len(data) < fragmentHeaderLen {''')
    media=SOURCE/'telemost/lab_media.go'
    replace(media,'event.Kind = "data"\n\tevent.Sender', '''event.Kind = "data"
 if len(fragment)>=labHeader && string(fragment[:4])=="FCF2" {
 event.Sender=binary.BigEndian.Uint32(fragment[24:]);event.Message=binary.BigEndian.Uint32(fragment[28:]);event.Fragment=uint32(binary.BigEndian.Uint16(fragment[40:]))*10+uint32(fragment[42]);event.Total=uint32(fragment[43]);if fragment[42]>=fragment[43] {event.Kind="repair"};return
 }
 event.Sender''')
    wire=SOURCE/'telemost/lab_wire.go'
    replace(wire,'labWireRTP.Add(uint64(size))','labMediaRate(size+64,header.MarshalSize())\n labWireRTP.Add(uint64(size))')
    replace(wire,'labWireRTCP.Add(uint64(size))','labMediaRate(size+64,0)\n labWireRTCP.Add(uint64(size))')
    capacity=SOURCE/'cmd/telemost-binary/capacity.go'
    replace(capacity,'type capacityConfig struct {','type capacityConfig struct {\n FragmentMode string\n FragmentEpoch string')
    replace(capacity,'result["histograms"] = endpoint.snapshot()','result["histograms"] = endpoint.snapshot()\n result["lab_fragments"]=session.LabFragmentStats()\n result["lab_rate"]=telemost.LabRateStats()')
    write(SOURCE/'telemost/lab_fragment.go',(SOURCE/'telemost/lab_fragment.go').read_text().replace('func labRateStats()', 'func LabRateStats()'))
    configure=SOURCE/'cmd/telemost-binary/capacity_media.go'
    replace(configure,'func capacityMediaConfigure(path string)', 'func capacityMediaConfigure(path string, server bool)')
    replace(configure,'return telemost.ConfigureLabMedia', 'if err:=telemost.ConfigureLabFragments(config.FragmentMode,config.FragmentEpoch,server);err!=nil{return err}\n return telemost.ConfigureLabMedia')
    main_file=SOURCE/'cmd/telemost-binary/main.go'
    replace(main_file,'capacityMediaConfigure(*capacityFile)', 'capacityMediaConfigure(*capacityFile,*role=="echo")')
    operator=WORK/'run_phase.py'
    text=operator.read_text().replace('from interaction_prepare import ROOT, WORK, FIX, digest','from lab import ROOT, WORK, FIX, digest')
    text=text.replace('from interaction_proof import validate','from interaction_proof import validate\nimport secrets')
    text=text.replace("parser.add_argument('--credit128'", "parser.add_argument('--fragment',choices=['L','S','SF'],required=True)\n    parser.add_argument('--credit128'")
    text=text.replace("assert args.mode=='P' and args.send==32", "assert args.mode in ['P','R','C'] and args.packing=='A' and args.credit128 and args.send==32")
    text=text.replace('config=dict(Mode=args.mode,','config=dict(FragmentMode=args.fragment,FragmentEpoch=secrets.token_hex(16),Mode=args.mode,')
    text=text.replace('<=64*1024*1024','<=128*1024*1024').replace('<=128*1024*1024,\'WIRE_BUDGET\'', '<=256*1024*1024,\'WIRE_BUDGET\'')
    text=text.replace('pstack-20261021-','fec-20261021-').replace('runtime=510','runtime=280')
    text=text.replace("assert finished,'MISSING_TWO_END_COMPLETION'", "assert args.mode!='P' or finished,'MISSING_TWO_END_COMPLETION'")
    write(operator,text)
    for name in ['lab.py']:
        write(WORK/name,(FIX/name).read_text().replace("ROOT = Path(__file__).resolve().parents[3]",'ROOT = Path('+repr(str(ROOT))+')').replace('FIX = Path(__file__).resolve().parent','FIX = Path('+repr(str(FIX))+')'))
    import subprocess
    from lab import TOOLS
    subprocess.run([TOOLS/'go/bin/gofmt','-w',*[path for path in SOURCE.rglob('*.go')]],check=True)


if __name__=='__main__': main()
