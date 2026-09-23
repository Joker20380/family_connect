using Microsoft.VisualBasic.ApplicationServices;
namespace FamilyConnect;
internal sealed class SingleWindowApplication : WindowsFormsApplicationBase
{
    internal SingleWindowApplication(){IsSingleInstance=true;EnableVisualStyles=true;ShutdownStyle=ShutdownMode.AfterMainFormCloses;}
    protected override void OnCreateMainForm(){
        var form=new FamilyConnect.MainForm(false);MainForm=form;
        if(CommandLineArgs.Count==1)form.Invite(CommandLineArgs[0]);
    }
    protected override void OnStartupNextInstance(StartupNextInstanceEventArgs e){
        base.OnStartupNextInstance(e);e.BringToForeground=true;
        if(e.CommandLine.Count==1&&MainForm is FamilyConnect.MainForm form)form.Invite(e.CommandLine[0]);
    }
}
