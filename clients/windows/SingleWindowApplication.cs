using Microsoft.VisualBasic.ApplicationServices;
namespace FamilyConnect;
internal sealed class SingleWindowApplication : WindowsFormsApplicationBase
{
    readonly bool layoutTest;
    internal int LayoutExitCode { get; private set; }
    internal SingleWindowApplication(bool layoutTest=false){
        this.layoutTest=layoutTest;IsSingleInstance=!layoutTest;EnableVisualStyles=true;
        HighDpiMode=System.Windows.Forms.HighDpiMode.PerMonitorV2;
        ShutdownStyle=ShutdownMode.AfterMainFormCloses;
    }
    protected override void OnCreateMainForm(){
        var form=new FamilyConnect.MainForm(layoutTest,layoutTest);MainForm=form;
        if(layoutTest)form.Shown+=(_,_)=>form.BeginInvoke((Action)(()=>{
            try{form.CheckStartupLayout();}
            catch(Exception e){LayoutExitCode=1;File.WriteAllText(Path.Combine(Path.GetTempPath(),"fc-layout-startup.txt"),e.ToString());}
            finally{form.Close();}
        }));
        if(CommandLineArgs.Count==1)form.Invite(CommandLineArgs[0]);
    }
    protected override void OnStartupNextInstance(StartupNextInstanceEventArgs e){
        base.OnStartupNextInstance(e);e.BringToForeground=true;
        if(e.CommandLine.Count==1&&MainForm is FamilyConnect.MainForm form)form.Invite(e.CommandLine[0]);
    }
}
