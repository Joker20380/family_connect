"""Small, replayable harness delta applied only to the new capsule."""
from prepare import SOURCE, patch_file

def once(name,old,new):
    path=SOURCE/name;text=path.read_text()
    if new in text:return
    for needle,marker in [('closeErr := secured.Close()','"packing_drain"'),('completed := make(chan error, 2)','"small_loaded"'),('expected := payload[:size]','err = stream.CloseWrite()'),('ended := time.Now()','"missing FIN after exact body"')]:
        if old==needle and marker in text:return
    assert text.count(old)==1,(name,old)
    patch_file(path,text.replace(old,new))

once('familysession/session.go','endpoint.SendContext(ctx, buffer[:count])','connection.lab.baselineSend(ctx, buffer[:count])')
once('cmd/telemost-binary/capacity.go','closeErr := secured.Close()', 'drainContext, drainCancel := context.WithTimeout(context.Background(), 5*time.Second)\n drainErr := secured.LabDrain(drainContext); drainCancel()\n _ = emit(map[string]any{"event":"packing_drain", "error":fmt.Sprint(drainErr),"packing":secured.LabPackingStats()})\n closeErr := secured.Close()')
once('cmd/telemost-binary/host_compare.go','index < 8;', 'index < 12;')
once('cmd/telemost-binary/host_compare.go','if size != 65536 && size != 2<<20 && size != 4<<20 {','if size != 32 && size != 65536 && size != 2<<20 && size != 4<<20 {')
once('cmd/telemost-binary/host_compare.go','if size != 65536 {',"if size != 65536 && !(header[0] == 'E' && size == 32) {")
once('cmd/telemost-binary/host_compare.go','expected := payload[:size]', 'if err==nil {err=stream.CloseWrite()}\n expected := payload[:size]')
once('cmd/telemost-binary/host_compare.go','ended := time.Now()', 'if err==nil {var tail [1]byte; _,tailErr:=stream.Read(tail[:]);if tailErr!=io.EOF {err=errors.New("missing FIN after exact body")}}\n if err==nil {err=stream.Close()}\n ended := time.Now()')
once('cmd/telemost-binary/host_compare.go','{{"control_echo", \'E\', 65536}, {"single", \'D\', 4 << 20}}', '{{"small_idle", \'E\', 32}, {"control_echo", \'E\', 65536}}')
once('cmd/telemost-binary/host_compare.go','completed := make(chan error, 2)', '''smallDone:=make(chan error,1)
 go func(){time.Sleep(time.Second);smallDone<-request("small_loaded", 'E',32)}()
 singleErr:=request("single",'D',4<<20)
 smallErr:=<-smallDone
 if singleErr!=nil {return singleErr};if smallErr!=nil {return smallErr}
 completed := make(chan error, 2)''')
