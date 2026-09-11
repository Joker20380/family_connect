using System.Globalization;
namespace FamilyConnect;
internal sealed class MainForm:Form
{
    bool ru=CultureInfo.CurrentUICulture.TwoLetterISOLanguageName=="ru",busy;
    string state="unknown";
    bool tcpReady;string? transport,lastError;
    readonly ComboBox mode=new(){DropDownStyle=ComboBoxStyle.DropDownList,Dock=DockStyle.Fill};
    bool TcpSelected=>mode.SelectedIndex==1;
    bool polling,pollError;long revision;
    Func<Request,Task<Reply>> call=Wire.Call;
    readonly Label title=new(),status=new(),description=new(),detail=new(),notice=new();
    readonly Button connect=new ModernButton(),request=new ModernButton(),activate=new ModernButton(),language=new ModernButton(),update=new ModernButton();
    AppUpdate? availableUpdate;
    readonly System.Windows.Forms.Timer poll=new(){Interval=3000};
    readonly TableLayoutPanel content=new();
    readonly Panel viewport=new();
    readonly TableLayoutPanel card=new();
    bool fitting;
    readonly Color mint=Color.FromArgb(165,180,252);
    string T(string russian,string english)=>ru?russian:english;
    public MainForm(bool smoke,bool layoutTest=false)
    {
        AutoScaleMode=AutoScaleMode.Dpi;AutoScaleDimensions=new SizeF(96,96);
        Text=$"Family Connect · {Application.ProductVersion.Split('+')[0]}";ClientSize=new(390,548);MinimumSize=new(360,360);
        DoubleBuffered=true;
        BackColor=Color.FromArgb(14,20,35);ForeColor=Color.White;
        Icon=Icon.ExtractAssociatedIcon(Application.ExecutablePath);
        Font=new Font("Segoe UI",10);StartPosition=FormStartPosition.CenterScreen;
        var shell=new TableLayoutPanel{Dock=DockStyle.Fill,ColumnCount=1,RowCount=2,Margin=Padding.Empty};
        shell.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,100));
        shell.RowStyles.Add(new RowStyle(SizeType.Percent,100));shell.RowStyles.Add(new RowStyle(SizeType.AutoSize));
        Controls.Add(shell);
        viewport.Dock=DockStyle.Fill;viewport.AutoScroll=true;viewport.Margin=Padding.Empty;
        shell.Controls.Add(viewport,0,0);
        content.AutoSize=true;content.AutoSizeMode=AutoSizeMode.GrowAndShrink;
        content.ColumnCount=1;content.RowCount=10;content.Padding=new Padding(24,12,24,8);
        content.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,100));
        for(int i=0;i<10;i++)content.RowStyles.Add(new RowStyle(SizeType.AutoSize));
        viewport.Controls.Add(content);
        title.Text="Family Connect";title.ForeColor=Color.FromArgb(238,242,255);title.Font=new Font(Font.FontFamily,14,FontStyle.Bold);
        using var brandStream=typeof(MainForm).Assembly.GetManifestResourceStream("FamilyConnect.Brand.png")!;
        using var brandSource=Image.FromStream(brandStream);
        var emblem=new PictureBox{Image=new Bitmap(brandSource),SizeMode=PictureBoxSizeMode.Zoom,Height=28,Dock=DockStyle.Fill,Margin=new Padding(0,0,10,0)};
        FormClosed+=(_,_)=>emblem.Image?.Dispose();
        status.Font=new Font(Font.FontFamily,14,FontStyle.Bold);
        foreach(var label in new[]{title,status,description,detail,notice}){
            label.AutoSize=true;label.Dock=DockStyle.Fill;label.TextAlign=ContentAlignment.MiddleLeft;
            label.Margin=new Padding(0,6,0,6);
        }
        foreach(var button in new[]{connect,request,activate,language,update}){
            button.AutoSize=true;button.MinimumSize=new Size(0,46);button.Dock=DockStyle.Fill;
            button.BackColor=Color.FromArgb(32,43,65);button.FlatAppearance.BorderColor=Color.FromArgb(51,65,100);
            button.FlatAppearance.MouseOverBackColor=Color.FromArgb(41,55,92);button.FlatAppearance.MouseDownBackColor=Color.FromArgb(51,65,100);
            button.Cursor=Cursors.Hand;button.FlatStyle=FlatStyle.Flat;button.Margin=new Padding(0,4,0,4);
        }
        connect.FlatAppearance.MouseOverBackColor=Color.FromArgb(199,210,254);connect.FlatAppearance.MouseDownBackColor=Color.FromArgb(129,140,248);
        connect.BackColor=mint;connect.ForeColor=BackColor;connect.Font=new Font(Font.FontFamily,10,FontStyle.Bold);
        detail.ForeColor=Color.FromArgb(232,205,164);notice.ForeColor=Color.FromArgb(153,166,198);
        var header=new TableLayoutPanel{AutoSize=true,Dock=DockStyle.Fill,ColumnCount=2,RowCount=1,Margin=new Padding(0,0,0,8)};
        header.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute,38));header.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,100));
        header.Controls.Add(emblem,0,0);header.Controls.Add(title,1,0);
        var tagline=new Label{Text=T("Связь для вашей семьи","Connection for your family"),Name="tagline",AutoSize=true,Dock=DockStyle.Fill,ForeColor=Color.FromArgb(153,166,198),Margin=new Padding(0,0,0,16)};
        card.AutoSize=true;card.Dock=DockStyle.Fill;card.ColumnCount=1;card.RowCount=2;
        card.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,100));
        card.Padding=new Padding(16,12,16,12);card.Margin=new Padding(0,0,0,12);
        card.BackColor=Color.FromArgb(25,35,53);
        card.Controls.Add(status,0,0);card.Controls.Add(description,0,1);
        card.SizeChanged+=(_,_)=>{using var path=ModernButton.Rounded(new RectangleF(0,0,card.Width,card.Height),16*DeviceDpi/96f);var old=card.Region;card.Region=new Region(path);old?.Dispose();};
        description.ForeColor=Color.FromArgb(153,166,198);
        foreach(var button in new[]{request,activate,language,update})button.Font=new Font(Font.FontFamily,10,FontStyle.Bold);
        update.BackColor=BackColor;language.BackColor=BackColor;
        mode.Items.AddRange(new object[]{"WireGuard","TCP · preview"});mode.SelectedIndex=0;
        mode.Margin=new Padding(0,4,0,8);mode.BackColor=Color.FromArgb(32,43,65);mode.ForeColor=ForeColor;
        mode.SelectedIndexChanged+=(_,_)=>PaintState();
        int row=0;
        foreach(Control child in new Control[]{header,tagline,card,mode,connect,request,activate,detail,notice,update})
            content.Controls.Add(child,0,row++);
        var footer=new Panel{Dock=DockStyle.Fill,Height=48,Padding=new Padding(24,4,24,8),Margin=Padding.Empty};
        footer.Controls.Add(new Label{Text="v"+Application.ProductVersion.Split('+')[0],AutoSize=true,ForeColor=Color.FromArgb(153,166,198),Location=new Point(24,16)});
        language.MinimumSize=new Size(0,32);language.Dock=DockStyle.Right;language.Width=100;footer.Controls.Add(language);shell.Controls.Add(footer,0,1);
        viewport.SizeChanged+=(_,_)=>FitContent();
        DpiChanged+=(_,_)=>BeginInvoke((Action)FitContent);
        update.Click+=async(_,_)=>{
            if(busy)return;revision++;busy=true;PaintState();
            try{
                if(availableUpdate is null){
                    availableUpdate=await Updates.Check(Application.ProductVersion.Split('+')[0]);
                    detail.Text=availableUpdate is null?T("Установлена последняя версия.","You are up to date."):T("Доступна версия ","Version available: ")+availableUpdate.Version;
                }else if(Confirm(T("Скачать и установить обновление? VPN может кратко прерваться. Ключи и профили сохранятся.","Download and install the update? VPN may briefly disconnect. Keys and profiles will be preserved.")) ){
                    string installer=await Updates.Download(availableUpdate);Updates.LaunchInstaller(installer,availableUpdate);
                    busy=false;state="off";Close();
                }
            }catch(Exception){detail.Text=T("Обновление недоступно или не прошло проверку. Текущая версия сохранена.","Update unavailable or verification failed. The current version is preserved.");}
            finally{busy=false;if(!IsDisposed)PaintState();}
        };
        connect.Click+=async(_,_)=>await Execute(new(ConnectionAction()));
        request.Click+=async(_,_)=>{
            var reply=await Execute(new("request"));
            if(reply?.Code is not string code)return;
            using var dialog=new Form{Text=T("Код устройства","Device code"),BackColor=BackColor,ForeColor=ForeColor,Font=Font,Icon=Icon,ClientSize=new(500,230),MinimumSize=new(340,240),StartPosition=FormStartPosition.CenterParent,AutoScaleMode=AutoScaleMode.Dpi};
            dialog.HandleCreated+=(_,_)=>DarkFrame(dialog);
            var layout=new TableLayoutPanel{Dock=DockStyle.Fill,Padding=new Padding(16),ColumnCount=1,RowCount=3};
            layout.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,100));
            layout.RowStyles.Add(new RowStyle(SizeType.Percent,45));layout.RowStyles.Add(new RowStyle(SizeType.Percent,55));layout.RowStyles.Add(new RowStyle(SizeType.AutoSize));
            var text=new TextBox{BackColor=Color.FromArgb(25,35,53),ForeColor=ForeColor,BorderStyle=BorderStyle.None,Text=code,ReadOnly=true,Multiline=true,WordWrap=true,ScrollBars=ScrollBars.Vertical,Dock=DockStyle.Fill};
            var copy=new ModernButton{BackColor=mint,ForeColor=BackColor,Text=T("Скопировать код","Copy code"),Dock=DockStyle.Fill,AutoSize=true,MinimumSize=new(0,44)};
            copy.Click+=(_,_)=>{Clipboard.SetText(code);dialog.Close();};
            var help=new Label{Text=T("Передайте этот код оператору для активации. Закрытый ключ остаётся на устройстве.","Send this code to the operator for activation. Your private key stays on this device."),Dock=DockStyle.Fill};
            layout.Controls.Add(text,0,0);layout.Controls.Add(help,0,1);layout.Controls.Add(copy,0,2);
            dialog.Controls.Add(layout);dialog.ShowDialog(this);
        };
        activate.Click+=async(_,_)=>{
            using var dialog=new OpenFileDialog{Filter=TcpSelected?"Family Connect TCP activation|*.fctcpactivation":"Family Connect activation|*.fcactivation",CheckFileExists=true};
            if(dialog.ShowDialog(this)!=DialogResult.OK)return;
            try{
                using var stream=File.OpenRead(dialog.FileName);
                if(stream.Length>8192)throw new IOException();
                using var reader=new StreamReader(stream);await Execute(new(TcpSelected?"activate-tcp":"activate",await reader.ReadToEndAsync()));
            }catch(Exception){detail.Text=T("Не удалось прочитать файл активации.","Could not read the activation file.");}
        };
        language.Click+=(_,_)=>{ru=!ru;PaintState();FitWindow();};
        poll.Tick+=async(_,_)=>await PollStatus();
        FormClosing+=(_,e)=>{if(busy){e.Cancel=true;return;}if(!smoke&&(state is "on" or "pending")&&!Confirm(T("Закрыть окно? VPN продолжит работать.","Close this window? The VPN will keep running.")))e.Cancel=true;};
        FormClosed+=(_,_)=>poll.Dispose();
        PaintState();
        Shown+=async(_,_)=>{
            FitWindow();
            if(layoutTest)return;
            if(smoke){Close();return;}
            await Execute(new("status"));poll.Start();
        };
    }
    internal static void CheckLayouts()
    {
        CheckPolling();
        using(var preview=new MainForm(true,true)){
            preview.ru=true;preview.state="off";preview.Show();preview.PaintState();preview.FitWindow();Application.DoEvents();
            using var bitmap=new Bitmap(preview.Width,preview.Height);preview.DrawToBitmap(bitmap,new Rectangle(Point.Empty,preview.Size));
            string path=Path.Combine(Path.GetTempPath(),"Windows-preview.png");
            Directory.CreateDirectory(Path.GetDirectoryName(path)!);bitmap.Save(path);
        }
        // No broker requests: test visible runtime layout.
        foreach(float scale in new[]{1f,1.5f,2f,2.5f})
        foreach(bool russian in new[]{true,false})
        foreach(bool tcp in new[]{false,true})
        foreach(string connection in new[]{"inactive","off","pending","recovering","on","other-user","unknown"})
        foreach(Size size in new[]{new Size(360,420),new Size(480,620),new Size(800,700)}){
            using var form=new MainForm(true,true);
            form.ru=russian;form.state=connection=="recovering"?"pending":connection;form.lastError=connection=="recovering"?"tcp-reconnecting":null;form.tcpReady=tcp;form.transport=tcp?"tcp":"wg";form.mode.SelectedIndex=tcp?1:0;
            form.Scale(new SizeF(scale,scale));
            form.ClientSize=new Size((int)(size.Width*scale),(int)(size.Height*scale));
            form.detail.Text=russian?"Служба Family Connect недоступна. Повторно запустите установщик приложения.":"Family Connect service is unavailable. Run the application installer again.";
            form.Show();Application.DoEvents();form.PaintState();form.PerformLayout();form.content.PerformLayout();
            int bottom=0;
            foreach(Control control in form.content.Controls){
                if(!control.Visible)continue;
                if(control.Left<0||control.Right>form.content.ClientSize.Width||control.Top<bottom)
                    throw new InvalidOperationException("Clipped or overlapping content");
                bottom=control.Bottom;
                if(control is Label label && label.Height<label.GetPreferredSize(new Size(label.Width,0)).Height)
                    throw new InvalidOperationException("Clipped label");
                if(control is Button button && button.Width<button.GetPreferredSize(Size.Empty).Width)
                    throw new InvalidOperationException("Clipped button");
            }
            foreach(var label in new[]{form.status,form.description}){
                if(label.Right>form.card.ClientSize.Width-form.card.Padding.Right || label.Height<label.GetPreferredSize(new Size(label.Width,0)).Height)
                    throw new InvalidOperationException("Clipped status card");
            }
            if(form.content.Width>form.viewport.ClientSize.Width)
                throw new InvalidOperationException("Horizontal overflow");
            if(form.language.Bottom>form.language.Parent!.ClientSize.Height)
                throw new InvalidOperationException("Clipped footer");
        }
    }
    static void CheckPolling()
    {
        using var form=new MainForm(true,true);form.state="off";form.Show();form.PaintState();
        using(var cancel=new System.Windows.Forms.Timer{Interval=50}){
            cancel.Tick+=(_,_)=>{foreach(Form dialog in Application.OpenForms)if(dialog!=form){dialog.DialogResult=DialogResult.Cancel;break;}};
            cancel.Start();if(form.Confirm("Confirmation cancellation check"))throw new Exception("Cancelled confirmation accepted");cancel.Stop();
        }
        int changes=0;form.status.TextChanged+=(_,_)=>changes++;
        var response=new TaskCompletionSource<Reply>();int calls=0;
        form.call=_=>{calls++;return response.Task;};
        Task pending=form.PollStatus();
        if(form.busy||!form.connect.Enabled||changes!=0)throw new Exception("Poll changed visible state");
        form.PollStatus().GetAwaiter().GetResult();
        if(calls!=1)throw new Exception("Overlapping polls");
        response.SetResult(new(true,"off"));
        Pump(pending);if(changes!=0)throw new Exception("Unchanged poll repainted state");
        form.call=_=>Task.FromResult(new Reply(true,"on"));Pump(form.PollStatus());
        if(form.state!="on")throw new Exception("State change ignored");
        response=new TaskCompletionSource<Reply>();form.call=_=>response.Task;pending=form.PollStatus();
        form.call=_=>Task.FromResult(new Reply(true,"off"));Pump(form.Execute(new("disconnect")));
        response.SetResult(new(true,"on"));Pump(pending);
        if(form.state!="off")throw new Exception("Stale poll overwrote user action");
        form.call=_=>Task.FromException<Reply>(new IOException());Pump(form.PollStatus());
        if(form.state!="unknown")throw new Exception("Poll error hidden");
        form.call=_=>Task.FromResult(new Reply(true,"off"));Pump(form.PollStatus());
        if(form.state!="off"||form.detail.Text!="")throw new Exception("Poll recovery failed");
        form.state="inactive";form.tcpReady=true;form.mode.SelectedIndex=1;form.PaintState();
        if(!form.connect.Enabled||form.ConnectionAction()!="connect-tcp")throw new Exception("TCP-only activation unavailable");
        form.state="pending";form.transport="tcp";form.PaintState();
        if(!form.connect.Enabled||form.mode.Enabled||form.ConnectionAction()!="disconnect")throw new Exception("TCP cancellation unavailable");
        form.state="inactive";form.lastError=null;form.transport="wg";
        form.call=_=>Task.FromResult(new Reply(true,"inactive",Error:"tcp-engine-exited",TcpReady:true,Transport:"wg"));Pump(form.PollStatus());
        if(form.detail.Text!=form.ErrorText("tcp-engine-exited"))throw new Exception("Same-state TCP error hidden");
        form.call=_=>Task.FromResult(new Reply(true,"inactive",TcpReady:false,Transport:"wg"));Pump(form.PollStatus());
        if(form.connect.Enabled||form.detail.Text!="")throw new Exception("TCP readiness or recovery stale");
        form.call=_=>Task.FromResult(new Reply(true,"pending",Error:"tcp-reconnecting",TcpReady:true,Transport:"tcp"));Pump(form.PollStatus());
        if(!form.connect.Enabled||form.ConnectionAction()!="disconnect"||form.mode.Enabled||form.detail.Text!=form.ErrorText("tcp-reconnecting"))throw new Exception("Recovery cancellation UI broken");
        form.call=_=>Task.FromResult(new Reply(true,"on",TcpReady:true,Transport:"tcp"));Pump(form.PollStatus());
        if(form.detail.Text!=""||form.state!="on")throw new Exception("Recovery success UI stale");
        form.call=_=>Task.FromResult(new Reply(true,"inactive",Error:"tcp-recovery-exhausted",TcpReady:true,Transport:"wg"));Pump(form.PollStatus());
        if(!form.connect.Enabled||form.ConnectionAction()!="connect-tcp"||form.detail.Text!=form.ErrorText("tcp-recovery-exhausted"))throw new Exception("Manual retry unavailable");
        static void Pump(Task task){
            var deadline=DateTime.UtcNow.AddSeconds(5);
            while(!task.IsCompleted&&DateTime.UtcNow<deadline)Application.DoEvents();
            if(!task.IsCompleted)throw new TimeoutException("UI test continuation");
            task.GetAwaiter().GetResult();
        }
    }
    void FitContent()
    {
        if(viewport.ClientSize.Width<=0)return;
        int width=Math.Max(1,viewport.ClientSize.Width-(viewport.VerticalScroll.Visible?SystemInformation.VerticalScrollBarWidth:0));
        content.SuspendLayout();
        content.MinimumSize=new Size(width,0);content.MaximumSize=new Size(width,0);content.Width=width;
        int textWidth=Math.Max(1,width-content.Padding.Horizontal);
        foreach(var label in new[]{title,detail,notice})label.MaximumSize=new Size(textWidth,0);
        foreach(var label in new[]{status,description})label.MaximumSize=new Size(Math.Max(1,textWidth-card.Padding.Horizontal),0);
        content.ResumeLayout(true);
    }
    [System.Runtime.InteropServices.DllImport("dwmapi.dll")]
    static extern int DwmSetWindowAttribute(IntPtr window,int attribute,ref int value,int size);
    protected override void OnHandleCreated(EventArgs e)
    {
        base.OnHandleCreated(e);
        DarkFrame(this);
    }
    static void DarkFrame(Form form){int enabled=1;DwmSetWindowAttribute(form.Handle,20,ref enabled,sizeof(int));}
    void FitWindow()
    {
        if(fitting)return;fitting=true;
        try{
            FitContent();content.PerformLayout();
            int max=Screen.FromControl(this).WorkingArea.Height-(Height-ClientSize.Height)-40;
            ClientSize=new Size(ClientSize.Width,Math.Min(max,content.PreferredSize.Height+language.Parent!.Height));
            FitContent();
        }finally{fitting=false;}
    }
    bool Confirm(string message)
    {
        using var dialog=new Form{Text="Family Connect",BackColor=BackColor,ForeColor=ForeColor,Font=Font,Icon=Icon,
            AutoScaleMode=AutoScaleMode.Dpi,ClientSize=new Size(370,280),StartPosition=FormStartPosition.CenterParent,
            FormBorderStyle=FormBorderStyle.FixedDialog,MaximizeBox=false,MinimizeBox=false};
        dialog.HandleCreated+=(_,_)=>DarkFrame(dialog);
        var panel=new TableLayoutPanel{Dock=DockStyle.Fill,Padding=new Padding(24),ColumnCount=1,RowCount=3};
        panel.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,100));
        panel.RowStyles.Add(new RowStyle(SizeType.Percent,100));
        panel.RowStyles.Add(new RowStyle(SizeType.Absolute,46));panel.RowStyles.Add(new RowStyle(SizeType.Absolute,46));
        panel.Controls.Add(new Label{Text=message,Dock=DockStyle.Fill,AutoSize=true},0,0);
        var accept=new ModernButton{Text=T("Продолжить","Continue"),Dock=DockStyle.Fill,BackColor=mint,ForeColor=BackColor,DialogResult=DialogResult.OK};
        var cancel=new ModernButton{Text=T("Отмена","Cancel"),Dock=DockStyle.Fill,BackColor=Color.FromArgb(32,43,65),ForeColor=ForeColor,DialogResult=DialogResult.Cancel};
        panel.Controls.Add(accept,0,1);panel.Controls.Add(cancel,0,2);dialog.Controls.Add(panel);
        dialog.AcceptButton=cancel;dialog.CancelButton=cancel;
        return dialog.ShowDialog(this)==DialogResult.OK;
    }
    void PaintState()
    {
        status.ForeColor=state=="on"?Color.FromArgb(110,231,183):Color.FromArgb(238,242,255);
        status.Text=state switch{
            "on"=>T("Туннель включён","Tunnel is on"),"off"=>T("Готов к подключению","Ready to connect"),
            "inactive"=>T("Активируйте устройство","Activate your device"),"other-user"=>T("VPN занят другим пользователем","VPN used by another user"),
            "pending"=>lastError=="tcp-reconnecting"?T("Восстанавливаем подключение…","Reconnecting…"):T("Подключение меняется…","Connection changing…"),_=>T("Статус недоступен","Status unavailable")};
        description.Text=(state is "on" or "pending"?transport=="tcp":TcpSelected)?T("TCP · предварительная версия","TCP · preview"):T("Защищённое подключение · Россия","Private connection · Russia");
        connect.Text=state=="on"?T("Отключить","Disconnect"):state=="pending"&&transport=="tcp"?T("Отменить подключение","Cancel connection"):T("Подключить","Connect");
        connect.Enabled=!busy&&(state=="on"||(state=="pending"&&transport=="tcp")||((state is "off" or "inactive")&&(TcpSelected?tcpReady:state=="off")));
        mode.Enabled=!busy&&(state is "off" or "inactive");
        request.Text=T("Получить код устройства","Get device code");request.Enabled=!busy;
        activate.Text=TcpSelected?T("Открыть TCP-активацию","Open TCP activation"):T("Открыть файл активации","Open activation file");activate.Enabled=!busy&&(state=="off"||state=="inactive");
        notice.Text=T("Туннель не подтверждает доступность интернета. Активация пилота выполняется оператором.","Tunnel status does not verify Internet access. Pilot activation is handled by the operator.");
        update.Text=availableUpdate is null?T("Проверить обновления","Check for updates"):T("Установить обновление","Install update");update.Enabled=!busy;
        language.Text="RU / EN";
        content.Controls.Find("tagline",false)[0].Text=T("Связь для вашей семьи","Connection for your family");
        detail.Visible=detail.Text.Length>0;FitContent();
        if(Visible)FitWindow();
    }
    string ConnectionAction()=>state=="on"||(state=="pending"&&transport=="tcp")?"disconnect":TcpSelected?"connect-tcp":"connect";
    string ErrorText(string? error)=>error switch{
        "activation-invalid"=>T("Активация недействительна, истекла или выдана другому устройству.","Activation is invalid, expired or belongs to another device."),
        "activation-required"=>T("Откройте файл активации выбранного подключения.","Open the activation file for the selected connection."),
        "other-user"=>T("Сначала отключите VPN в другой учётной записи Windows.","Disconnect the VPN in the other Windows account first."),
        "disconnect-first" or "busy"=>T("Сначала отключите VPN.","Disconnect the VPN first."),
        "tcp-engine-missing"=>T("Компонент TCP отсутствует. Повторно запустите установщик.","TCP component is missing. Run the installer again."),
        "tcp-reconnecting"=>T("TCP прервался. Повторяем подключение; можно отменить.","TCP was interrupted. Retrying; you can cancel."),
        "tcp-recovery-exhausted"=>T("TCP не удалось восстановить за три попытки. Проверьте сеть и подключитесь вручную.","TCP recovery stopped after three attempts. Check your network and connect manually."),
        "tcp-engine-exited"=>T("TCP остановился. Можно подключиться повторно.","TCP stopped. You can connect again."),
        "tcp-session-failed"=>T("Не удалось включить TCP. Проверьте настройки сети и повторите попытку.","Could not start TCP. Check network settings and try again."),
        "tcp-cleanup-required"=>T("Не удалось восстановить настройки сети. Перезапустите службу Family Connect или Windows.","Could not restore network settings. Restart the Family Connect service or Windows."),
        _=>T("Не удалось выполнить действие. Код: ","Operation failed. Code: ")+error
    };
    async Task PollStatus()
    {
        if(busy||polling||IsDisposed)return;
        polling=true;long started=revision;
        try{
            Reply reply;
            try{reply=await call(new("status"));}
            catch(Exception){reply=new(false,"unknown");}
            if(IsDisposed||Disposing||busy||started!=revision)return;
            bool error=!reply.Ok;
            string next=error?"unknown":reply.State;
            if(next==state&&error==pollError&&tcpReady==reply.TcpReady&&transport==reply.Transport&&lastError==reply.Error)return;
            state=next;tcpReady=reply.TcpReady;transport=reply.Transport;lastError=reply.Error;
            if(state is "on" or "pending")mode.SelectedIndex=transport=="tcp"?1:0;
            if(error)detail.Text=T("Служба Family Connect недоступна. Повторно запустите установщик приложения.","Family Connect service is unavailable. Run the application installer again.");
            else detail.Text=reply.Error is null?"":ErrorText(reply.Error);
            pollError=error;PaintState();
        }finally{polling=false;}
    }
    async Task<Reply?> Execute(Request action,bool quiet=false)
    {
        if(busy)return null;revision++;busy=true;PaintState();
        try{
            var reply=await call(action);
            if(action.Action!="request"){
                state=reply.State;transport=reply.Transport;lastError=reply.Error;
                if(action.Action is "status" or "activate-tcp" or "connect-tcp")tcpReady=reply.TcpReady;
            }
            if(!reply.Ok||reply.Error is not null)detail.Text=ErrorText(reply.Error);
            else if(!quiet)detail.Text=(action.Action is "activate" or "activate-tcp")?T("Устройство активировано. Нажмите «Подключить».","Device activated. Click Connect."):"";
            return reply;
        }catch(Exception){state="unknown";detail.Text=T("Служба Family Connect недоступна. Повторно запустите установщик приложения.","Family Connect service is unavailable. Run the application installer again.");return null;}
        finally{busy=false;PaintState();}
    }
}
