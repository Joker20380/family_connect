"""Common v3 teardown: explicit drain before abort, finite passive ACK settlement."""
import subprocess
from prepare import SOURCE,TOOLS,patch_file

path=SOURCE/'cmd/telemost-binary/capacity.go'
subprocess.run([TOOLS/'go/bin/gofmt','-w',path],check=True)
text=path.read_text()
if 'packing_pre_close' not in text:
    old='defer func() {\n\t\t\tdrainContext, drainCancel'
    assert text.count(old)==1
    text=text.replace(old,'defer func() {\n if config.Mode != "P" {\n\t\t\tdrainContext, drainCancel')
    text=text.replace('\n\t\t\tcloseErr := secured.Close()','\n }\n\t\t\tcloseErr := secured.Close()')
    old='defer func() {\n\t\t\tstopMux()'
    assert text.count(old)==1
    text=text.replace(old,'''defer func() {
 if !server {
  select {case <-time.After(2*time.Second):case <-ctx.Done():}
  drainContext, drainCancel := context.WithTimeout(context.Background(),5*time.Second)
  drainErr := data.(*familysession.Session).LabDrain(drainContext)
  drainCancel()
  _ = emit(map[string]any{"event":"packing_drain","error":fmt.Sprint(drainErr),"packing":data.(*familysession.Session).LabPackingStats()})
 }
 _ = emit(map[string]any{"event":"packing_pre_close","packing":data.(*familysession.Session).LabPackingStats(),"reliability":reliableStats(),"server":server})
 stopMux()''')
    patch_file(path,text)
