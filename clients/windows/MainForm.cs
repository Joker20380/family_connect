using System.Globalization;
namespace FamilyConnect;
internal sealed class MainForm:Form
{
    bool ru=CultureInfo.CurrentUICulture.TwoLetterISOLanguageName=="ru",busy;
    string state="unknown";
    readonly Label title=new(),status=new(),description=new(),detail=new(),notice=new();
    readonly Button connect=new ModernButton(),request=new ModernButton(),activate=new ModernButton(),language=new ModernButton(),update=new ModernButton();
    AppUpdate? availableUpdate;
    readonly System.Windows.Forms.Timer poll=new(){Interval=3000};
    readonly TableLayoutPanel content=new();
    readonly Panel viewport=new();
    readonly Color mint=Color.FromArgb(165,180,252);
    string T(string russian,string english)=>ru?russian:english;
    public MainForm(bool smoke,bool layoutTest=false)
    {
        AutoScaleMode=AutoScaleMode.Dpi;AutoScaleDimensions=new SizeF(96,96);
        Text=$"Family Connect · {Application.ProductVersion.Split('+')[0]}";ClientSize=new(480,680);MinimumSize=new(360,420);
        BackColor=Color.FromArgb(11,16,32);ForeColor=Color.White;
        Icon=Icon.ExtractAssociatedIcon(Application.ExecutablePath);
        Font=new Font("Segoe UI",11);StartPosition=FormStartPosition.CenterScreen;
        var shell=new TableLayoutPanel{Dock=DockStyle.Fill,ColumnCount=1,RowCount=2,Margin=Padding.Empty};
        shell.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,100));
        shell.RowStyles.Add(new RowStyle(SizeType.Percent,100));shell.RowStyles.Add(new RowStyle(SizeType.AutoSize));
        Controls.Add(shell);
        viewport.Dock=DockStyle.Fill;viewport.AutoScroll=true;viewport.Margin=Padding.Empty;
        shell.Controls.Add(viewport,0,0);
        content.AutoSize=true;content.AutoSizeMode=AutoSizeMode.GrowAndShrink;
        content.ColumnCount=1;content.RowCount=10;content.Padding=new Padding(24,18,24,12);
        content.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,100));
        for(int i=0;i<10;i++)content.RowStyles.Add(new RowStyle(SizeType.AutoSize));
        viewport.Controls.Add(content);
        title.Text="Family Connect";title.ForeColor=Color.FromArgb(238,242,255);title.Font=new Font(Font.FontFamily,24,FontStyle.Bold);
        using var brandStream=typeof(MainForm).Assembly.GetManifestResourceStream("FamilyConnect.Brand.png")!;
        using var brandSource=Image.FromStream(brandStream);
        var emblem=new PictureBox{Image=new Bitmap(brandSource),SizeMode=PictureBoxSizeMode.Zoom,Height=88,Dock=DockStyle.Fill,Margin=new Padding(0,18,0,14)};
        FormClosed+=(_,_)=>emblem.Image?.Dispose();
        status.Font=new Font(Font.FontFamily,20,FontStyle.Bold);
        foreach(var label in new[]{title,status,description,detail,notice}){
            label.AutoSize=true;label.Dock=DockStyle.Fill;label.TextAlign=ContentAlignment.MiddleCenter;
            label.Margin=new Padding(0,8,0,8);
        }
        foreach(var button in new[]{connect,request,activate,language,update}){
            button.AutoSize=true;button.MinimumSize=new Size(0,48);button.Dock=DockStyle.Fill;
            button.BackColor=Color.FromArgb(27,36,64);button.FlatAppearance.BorderColor=Color.FromArgb(51,65,100);
            button.FlatAppearance.MouseOverBackColor=Color.FromArgb(41,55,92);button.FlatAppearance.MouseDownBackColor=Color.FromArgb(51,65,100);
            button.Cursor=Cursors.Hand;button.FlatStyle=FlatStyle.Flat;button.Margin=new Padding(0,4,0,4);
        }
        connect.FlatAppearance.MouseOverBackColor=Color.FromArgb(199,210,254);connect.FlatAppearance.MouseDownBackColor=Color.FromArgb(129,140,248);
        connect.BackColor=mint;connect.ForeColor=BackColor;connect.Font=new Font(Font.FontFamily,14,FontStyle.Bold);
        detail.ForeColor=Color.FromArgb(232,205,164);notice.ForeColor=Color.FromArgb(153,166,198);
        int row=0;
        foreach(Control child in new Control[]{title,emblem,status,description,connect,request,activate,detail,notice,update})
            content.Controls.Add(child,0,row++);
        var footer=new Panel{Dock=DockStyle.Fill,Height=60,Padding=new Padding(24,4,24,8),Margin=Padding.Empty};
        footer.Controls.Add(new Label{Text="v"+Application.ProductVersion.Split('+')[0],AutoSize=true,ForeColor=Color.FromArgb(153,166,198),Location=new Point(24,18)});
        language.Dock=DockStyle.Right;language.Width=100;footer.Controls.Add(language);shell.Controls.Add(footer,0,1);
        viewport.SizeChanged+=(_,_)=>FitContent();
        DpiChanged+=(_,_)=>BeginInvoke((Action)FitContent);
        update.Click+=async(_,_)=>{
            if(busy)return;busy=true;PaintState();
            try{
                if(availableUpdate is null){
                    availableUpdate=await Updates.Check(Application.ProductVersion.Split('+')[0]);
                    detail.Text=availableUpdate is null?T("Установлена последняя версия.","You are up to date."):T("Доступна версия ","Version available: ")+availableUpdate.Version;
                }else if(MessageBox.Show(T("Скачать и установить обновление? VPN может кратко прерваться. Ключи и профили сохранятся.","Download and install the update? VPN may briefly disconnect. Keys and profiles will be preserved."),Text,MessageBoxButtons.OKCancel)==DialogResult.OK){
                    string installer=await Updates.Download(availableUpdate);Updates.LaunchInstaller(installer,availableUpdate);
                    busy=false;state="off";Close();
                }
            }catch(Exception){detail.Text=T("Обновление недоступно или не прошло проверку. Текущая версия сохранена.","Update unavailable or verification failed. The current version is preserved.");}
            finally{busy=false;if(!IsDisposed)PaintState();}
        };
        connect.Click+=async(_,_)=>await Execute(new(state=="on"?"disconnect":"connect"));
        request.Click+=async(_,_)=>{
            var reply=await Execute(new("request"));
            if(reply?.Code is not string code)return;
            using var dialog=new Form{Text=T("Код устройства","Device code"),BackColor=BackColor,ForeColor=ForeColor,Font=Font,Icon=Icon,ClientSize=new(500,230),MinimumSize=new(340,240),StartPosition=FormStartPosition.CenterParent,AutoScaleMode=AutoScaleMode.Dpi};
            var layout=new TableLayoutPanel{Dock=DockStyle.Fill,Padding=new Padding(16),ColumnCount=1,RowCount=3};
            layout.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,100));
            layout.RowStyles.Add(new RowStyle(SizeType.Percent,45));layout.RowStyles.Add(new RowStyle(SizeType.Percent,55));layout.RowStyles.Add(new RowStyle(SizeType.AutoSize));
            var text=new TextBox{Text=code,ReadOnly=true,Multiline=true,WordWrap=true,ScrollBars=ScrollBars.Vertical,Dock=DockStyle.Fill};
            var copy=new ModernButton{Text=T("Скопировать код","Copy code"),Dock=DockStyle.Fill,AutoSize=true,MinimumSize=new(0,44)};
            copy.Click+=(_,_)=>{Clipboard.SetText(code);dialog.Close();};
            var help=new Label{Text=T("Передайте этот код оператору для активации. Закрытый ключ остаётся на устройстве.","Send this code to the operator for activation. Your private key stays on this device."),Dock=DockStyle.Fill};
            layout.Controls.Add(text,0,0);layout.Controls.Add(help,0,1);layout.Controls.Add(copy,0,2);
            dialog.Controls.Add(layout);dialog.ShowDialog(this);
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
            if(layoutTest)return;
            if(smoke){Close();return;}
            await Execute(new("status"));poll.Start();
        };
    }
    internal static void CheckLayouts()
    {
        // No broker requests: test real layout while the form remains unshown.
        foreach(float scale in new[]{1f,1.5f,2f})
        foreach(bool russian in new[]{true,false})
        foreach(string connection in new[]{"inactive","on","other-user","unknown"})
        foreach(Size size in new[]{new Size(360,420),new Size(480,620),new Size(800,700)}){
            using var form=new MainForm(true,true);
            form.ru=russian;form.state=connection;
            form.Scale(new SizeF(scale,scale));
            form.ClientSize=new Size((int)(size.Width*scale),(int)(size.Height*scale));
            form.detail.Text=russian?"Служба Family Connect недоступна. Повторно запустите установщик приложения.":"Family Connect service is unavailable. Run the application installer again.";
            form.Show();Application.DoEvents();form.PaintState();form.PerformLayout();form.content.PerformLayout();
            int bottom=0;
            foreach(Control control in form.content.Controls){
                if(control.Left<0||control.Right>form.content.ClientSize.Width||control.Top<bottom)
                    throw new InvalidOperationException("Clipped or overlapping content");
                bottom=control.Bottom;
                if(control is Label label && label.Height<label.GetPreferredSize(new Size(label.Width,0)).Height)
                    throw new InvalidOperationException("Clipped label");
                if(control is Button button && button.Width<button.GetPreferredSize(Size.Empty).Width)
                    throw new InvalidOperationException("Clipped button");
            }
            if(form.content.Width>form.viewport.ClientSize.Width)
                throw new InvalidOperationException("Horizontal overflow");
            if(form.language.Bottom>form.language.Parent!.ClientSize.Height)
                throw new InvalidOperationException("Clipped footer");
        }
    }
    void FitContent()
    {
        if(viewport.ClientSize.Width<=0)return;
        int width=Math.Max(1,viewport.ClientSize.Width-SystemInformation.VerticalScrollBarWidth);
        content.SuspendLayout();
        content.MinimumSize=new Size(width,0);content.MaximumSize=new Size(width,0);content.Width=width;
        int textWidth=Math.Max(1,width-content.Padding.Horizontal);
        foreach(var label in new[]{title,status,description,detail,notice})label.MaximumSize=new Size(textWidth,0);
        content.ResumeLayout(true);
    }
    void PaintState()
    {
        status.ForeColor=state=="on"?Color.FromArgb(110,231,183):Color.FromArgb(238,242,255);
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
        update.Text=availableUpdate is null?T("Проверить обновления","Check for updates"):T("Установить обновление","Install update");update.Enabled=!busy;
        language.Text="RU / EN";FitContent();
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
