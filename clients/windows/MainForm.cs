using System.Globalization;
namespace FamilyConnect;
internal sealed class MainForm:Form
{
    bool ru=CultureInfo.CurrentUICulture.TwoLetterISOLanguageName=="ru",busy;
    string state="unknown";
    readonly Label title=new(),status=new(),description=new(),detail=new(),notice=new();
    readonly Button connect=new(),request=new(),activate=new(),language=new();
    readonly System.Windows.Forms.Timer poll=new(){Interval=3000};
    readonly Color mint=Color.FromArgb(102,219,192);
    string T(string russian,string english)=>ru?russian:english;
    public MainForm(bool smoke)
    {
        Text="Family Connect";Size=new(540,700);MinimumSize=new(480,650);
        BackColor=Color.FromArgb(16,25,35);ForeColor=Color.White;
        Font=new Font("Segoe UI",11);StartPosition=FormStartPosition.CenterScreen;
        var panel=new TableLayoutPanel{Dock=DockStyle.Fill,Padding=new Padding(28),ColumnCount=1,RowCount=9};
        Controls.Add(panel);
        title.Text="FAMILY CONNECT";title.ForeColor=mint;title.Font=new Font(Font.FontFamily,24,FontStyle.Bold);
        status.Font=new Font(Font.FontFamily,22,FontStyle.Bold);
        foreach(var label in new[]{title,status,description,detail,notice}){label.AutoSize=true;label.Dock=DockStyle.Fill;label.TextAlign=ContentAlignment.MiddleCenter;label.Margin=new Padding(0,12,0,12);}
        foreach(var button in new[]{connect,request,activate,language}){
            button.AutoSize=true;button.MinimumSize=new Size(0,46);button.Dock=DockStyle.Fill;
            button.FlatStyle=FlatStyle.Flat;button.Margin=new Padding(0,6,0,6);
        }
        connect.BackColor=mint;connect.ForeColor=BackColor;connect.Font=new Font(Font.FontFamily,14,FontStyle.Bold);
        detail.ForeColor=Color.FromArgb(232,205,164);notice.ForeColor=Color.LightSlateGray;
        panel.Controls.Add(title);panel.Controls.Add(status);panel.Controls.Add(description);panel.Controls.Add(connect);
        panel.Controls.Add(request);panel.Controls.Add(activate);panel.Controls.Add(detail);panel.Controls.Add(notice);panel.Controls.Add(language);
        connect.Click+=async(_,_)=>await Execute(new(state=="on"?"disconnect":"connect"));
        request.Click+=async(_,_)=>{
            var reply=await Execute(new("request"));
            if(reply?.Code is not string code)return;
            using var dialog=new Form{Text=T("Код устройства","Device code"),Size=new(580,230),StartPosition=FormStartPosition.CenterParent};
            var text=new TextBox{Text=code,ReadOnly=true,Multiline=true,Dock=DockStyle.Top,Height=65};
            var copy=new Button{Text=T("Скопировать код","Copy code"),Dock=DockStyle.Bottom,Height=45};
            copy.Click+=(_,_)=>{Clipboard.SetText(code);dialog.Close();};
            dialog.Controls.Add(new Label{Text=T("Передайте этот код оператору для активации. Закрытый ключ остаётся на устройстве.","Send this code to the operator for activation. Your private key stays on this device."),Dock=DockStyle.Fill});
            dialog.Controls.Add(text);dialog.Controls.Add(copy);dialog.ShowDialog(this);
        };
        activate.Click+=async(_,_)=>{
            using var dialog=new OpenFileDialog{Filter="Family Connect activation|*.fcactivation",CheckFileExists=true};
            if(dialog.ShowDialog(this)!=DialogResult.OK)return;
            try{
                using var stream=File.OpenRead(dialog.FileName);
                if(stream.Length>8192)throw new IOException();
                using var reader=new StreamReader(stream);await Execute(new("activate",await reader.ReadToEndAsync()));
            }catch(Exception){detail.Text=T("Не удалось прочитать файл активации.","Could not read the activation file.");}
        };
        language.Click+=(_,_)=>{ru=!ru;PaintState();};
        poll.Tick+=async(_,_)=>{if(!busy)await Execute(new("status"),true);};
        FormClosing+=(_,e)=>{if(busy){e.Cancel=true;return;}if(!smoke&&state=="on"&&MessageBox.Show(T("Закрыть окно? VPN продолжит работать.","Close this window? The VPN will keep running."),Text,MessageBoxButtons.OKCancel)!=DialogResult.OK)e.Cancel=true;};
        FormClosed+=(_,_)=>poll.Dispose();
        PaintState();
        Shown+=async(_,_)=>{
            if(smoke){Close();return;}
            await Execute(new("status"));poll.Start();
        };
    }
    void PaintState()
    {
        status.Text=busy?T("Выполняется…","Working…"):state switch{
            "on"=>T("Туннель включён","Tunnel is on"),"off"=>T("Готов к подключению","Ready to connect"),
            "inactive"=>T("Активируйте устройство","Activate your device"),"other-user"=>T("VPN занят другим пользователем","VPN used by another user"),
            "pending"=>T("Подключение меняется…","Connection changing…"),_=>T("Статус недоступен","Status unavailable")};
        description.Text=T("Защищённое подключение · Россия","Private connection · Russia");
        connect.Text=state=="on"?T("Отключить","Disconnect"):T("Подключить","Connect");
        connect.Enabled=!busy&&(state=="on"||state=="off");
        request.Text=T("1. Получить код устройства","1. Get device code");request.Enabled=!busy;
        activate.Text=T("2. Открыть файл активации","2. Open activation file");activate.Enabled=!busy&&(state=="off"||state=="inactive");
        notice.Text=T("Туннель не подтверждает доступность интернета. Активация пилота выполняется оператором.","Tunnel status does not verify Internet access. Pilot activation is handled by the operator.");
        language.Text="RU / EN";
    }
    async Task<Reply?> Execute(Request action,bool quiet=false)
    {
        if(busy)return null;busy=true;PaintState();
        try{
            var reply=await Wire.Call(action);
            if(action.Action!="request")state=reply.State;
            if(!reply.Ok)detail.Text=reply.Error switch{
                "activation-invalid"=>T("Активация недействительна, истекла или выдана другому устройству.","Activation is invalid, expired or belongs to another device."),
                "other-user"=>T("Сначала отключите VPN в другой учётной записи Windows.","Disconnect the VPN in the other Windows account first."),
                "disconnect-first"=>T("Сначала отключите VPN.","Disconnect the VPN first."),
                _=>T("Не удалось выполнить действие. Код: ","Operation failed. Code: ")+reply.Error};
            else if(!quiet)detail.Text=action.Action=="activate"?T("Устройство активировано. Нажмите «Подключить».","Device activated. Click Connect."):"";
            return reply;
        }catch(Exception){state="unknown";detail.Text=T("Служба Family Connect недоступна. Повторно запустите установщик приложения.","Family Connect service is unavailable. Run the application installer again.");return null;}
        finally{busy=false;PaintState();}
    }
}
