using System.Globalization;
namespace FamilyConnect;
internal sealed class MainForm:Form
{
    bool ru=CultureInfo.CurrentUICulture.TwoLetterISOLanguageName=="ru",busy;
    readonly bool saveLanguage;
    string state="unknown";
    bool tcpReady,awgReady,automatic,friendsReady;
    readonly ComboBox country=new ModernComboBox(){DropDownStyle=ComboBoxStyle.DropDownList,Dock=DockStyle.Fill};
    FriendsForm accessPage=null!;
    LiveNetworkPanel? telemetry;
    string Country=>country.SelectedIndex==1?"ru":"nl";string? transport,lastError;
    readonly ComboBox mode=new ModernComboBox(){DropDownStyle=ComboBoxStyle.DropDownList,Dock=DockStyle.Fill};
    bool TcpSelected=>mode.SelectedIndex==0;
    bool AwgSelected=>mode.SelectedIndex==1;
    bool AutoSelected=>false;
    bool polling,pollError;long revision;
    Func<Request,Task<Reply>> call=Wire.Call;
    readonly Label title=new(),status=new(),description=new(),detail=new(),notice=new();
    readonly Button enroll=new ModernButton();
    bool NeedsInvitation=>(state is "off" or "inactive")&&!friendsReady&&!(AwgSelected?awgReady:TcpSelected?tcpReady:false);
    readonly Button connect=new ModernButton(),request=new ModernButton(),activate=new ModernButton(),language=new ModernButton(),update=new ModernButton(),friends=new ModernButton();
    AppUpdate? availableUpdate;
    readonly System.Windows.Forms.Timer poll=new(){Interval=3000};
    readonly BufferedLayoutPanel content=new();
    readonly BufferedPanel viewport=new();
    readonly BufferedPanel shellHost=new(){Dock=DockStyle.Fill};
    readonly BufferedLayoutPanel shell=new();
    readonly TerminalHeader header=new();
    readonly BufferedLayoutPanel footer=new();
    readonly BufferedLayoutPanel card=new();
    bool fitting;
    string page="status";
    readonly RouteMap routeMap=new();
    readonly TerminalDial dial=new();
    readonly Label loadLabel=new(){AutoSize=true,Dock=DockStyle.Fill};readonly LoadBar loadBar=new();readonly ToolTip loadTip=new();
    readonly System.Windows.Forms.Timer loadTimer=new(){Interval=3000};
    LoadSample? loadSample;bool loadPending;DateTime loadNext=DateTime.MinValue;long loadRevision=-1;int loadMode=-1;
    readonly Label routeTitle=new(){AutoSize=true,Dock=DockStyle.Fill},messengerNote=new(){AutoSize=true,Dock=DockStyle.Fill};
    readonly Dictionary<string,Control[]> pages=new();
    readonly Dictionary<string,ModernButton> nav=new();
    readonly Color mint=Color.FromArgb(152,247,216);
    string T(string russian,string english)=>ru?russian:english;
    string pendingInvitation="";
    public MainForm(bool smoke,bool layoutTest=false)
    {
        SuspendLayout();
        saveLanguage=!smoke&&!layoutTest;
        if(saveLanguage)try{using var preferences=Microsoft.Win32.Registry.CurrentUser.OpenSubKey(@"Software\family_connect");var saved=preferences?.GetValue("Language") as string;if(saved is "ru" or "en")ru=saved=="ru";}catch(System.Security.SecurityException){}catch(UnauthorizedAccessException){}catch(IOException){}
        AutoScaleMode=AutoScaleMode.Dpi;AutoScaleDimensions=new SizeF(96,96);
        Text=$"family_connect · {Application.ProductVersion.Split('+')[0]}";ClientSize=new(560,800);MinimumSize=new(360,420);
        DoubleBuffered=true;
        BackColor=Color.FromArgb(3,17,14);ForeColor=Color.FromArgb(218,255,242);
        Icon=Icon.ExtractAssociatedIcon(Application.ExecutablePath);
        Font=new Font("Consolas",10);StartPosition=FormStartPosition.CenterScreen;
        shell.ColumnCount=1;shell.RowCount=3;shell.Margin=Padding.Empty;
        shell.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,100));
        shell.RowStyles.Add(new RowStyle(SizeType.Absolute,86));shell.RowStyles.Add(new RowStyle(SizeType.Percent,100));shell.RowStyles.Add(new RowStyle(SizeType.Absolute,76));
        Controls.Add(shellHost);shellHost.Controls.Add(shell);shellHost.SizeChanged+=(_,_)=>FitShell();
        viewport.Dock=DockStyle.Fill;viewport.AutoScroll=true;viewport.Margin=Padding.Empty;
        shell.Controls.Add(viewport,0,1);
        content.AutoSize=true;content.AutoSizeMode=AutoSizeMode.GrowAndShrink;
        content.ColumnCount=1;content.RowCount=15;content.Padding=new Padding(12,8,12,8);
        content.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,100));
        for(int i=0;i<15;i++)content.RowStyles.Add(new RowStyle(SizeType.AutoSize));
        viewport.Controls.Add(content);
        title.Text="family_connect";title.ForeColor=Color.FromArgb(218,255,242);title.Font=new Font(Font.FontFamily,14,FontStyle.Bold);
        using var brandStream=typeof(MainForm).Assembly.GetManifestResourceStream("FamilyConnect.Brand.png")!;
        using var brandSource=Image.FromStream(brandStream);
        var emblem=new PictureBox{Image=new Bitmap(brandSource),SizeMode=PictureBoxSizeMode.Zoom,Height=28,Dock=DockStyle.Fill,Margin=new Padding(0,0,10,0)};
        FormClosed+=(_,_)=>emblem.Image?.Dispose();
        status.Font=new Font(Font.FontFamily,14,FontStyle.Bold);
        foreach(var label in new[]{title,status,description,detail,notice}){
            label.AutoSize=true;label.Dock=DockStyle.Fill;label.TextAlign=ContentAlignment.MiddleLeft;
            label.Margin=new Padding(0,6,0,6);
        }
        foreach(var button in new[]{connect,request,activate,language,update,friends,enroll}){
            button.AutoSize=true;button.MinimumSize=new Size(0,46);button.Dock=DockStyle.Fill;
            button.BackColor=Color.FromArgb(7,32,24);button.FlatAppearance.BorderColor=Color.FromArgb(67,142,121);
            button.FlatAppearance.MouseOverBackColor=Color.FromArgb(16,61,46);button.FlatAppearance.MouseDownBackColor=Color.FromArgb(67,142,121);
            button.Cursor=Cursors.Hand;button.FlatStyle=FlatStyle.Flat;button.Margin=new Padding(0,4,0,4);
        }
        connect.FlatAppearance.MouseOverBackColor=Color.FromArgb(16,61,46);connect.FlatAppearance.MouseDownBackColor=Color.FromArgb(67,142,121);
        connect.BackColor=Color.FromArgb(7,32,24);connect.ForeColor=ForeColor;((ModernButton)connect).TerminalSwitch=true;connect.Font=new Font(Font.FontFamily,10,FontStyle.Bold);
        detail.ForeColor=Color.FromArgb(255,173,70);notice.ForeColor=Color.FromArgb(153,196,181);
        header.Dock=DockStyle.Fill;header.Margin=new Padding(0,0,0,8);
        shell.Controls.Add(header,0,0);
        var tagline=new Label{Text=T("Связь для вашей семьи","Connection for your family"),Name="tagline",AutoSize=true,Dock=DockStyle.Fill,ForeColor=Color.FromArgb(153,196,181),Margin=new Padding(0,0,0,16)};
        card.AutoSize=true;card.Dock=DockStyle.Fill;card.ColumnCount=1;card.RowCount=5;
        card.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,100));
        for(int i=0;i<5;i++)card.RowStyles.Add(new RowStyle(SizeType.AutoSize));
        card.Padding=new Padding(16,12,16,12);card.Margin=new Padding(0,0,0,12);
        card.BackColor=Color.FromArgb(7,32,24);
        card.Controls.Add(dial,0,0);card.Controls.Add(status,0,1);card.Controls.Add(description,0,2);
        card.Controls.Add(loadLabel,0,3);card.Controls.Add(loadBar,0,4);loadLabel.ForeColor=Color.FromArgb(153,196,181);
        dial.Click+=async(_,_)=>{if(connect.Enabled)await Execute(new(ConnectionAction()));};
        card.SizeChanged+=(_,_)=>{using var path=ModernButton.Cut(new RectangleF(0,0,card.Width,card.Height),12*DeviceDpi/96f);var old=card.Region;card.Region=new Region(path);old?.Dispose();};
        description.ForeColor=Color.FromArgb(153,196,181);
        foreach(var button in new[]{request,activate,language,update,friends})button.Font=new Font(Font.FontFamily,10,FontStyle.Bold);
        update.BackColor=BackColor;language.BackColor=BackColor;
        mode.Items.AddRange(new object[]{"TCP REALITY","AWG 3.1"});mode.SelectedIndex=1;
        mode.Margin=new Padding(0,4,0,8);mode.BackColor=Color.FromArgb(7,32,24);mode.ForeColor=ForeColor;
        country.Items.AddRange(new object[]{T("Нидерланды","Netherlands"),T("Россия","Russia")});country.SelectedIndex=0;
        country.BackColor=mode.BackColor;country.ForeColor=ForeColor;
        foreach(var picker in new[]{country,mode}){picker.ItemHeight=30;picker.Font=Font;}
        if(saveLanguage)try{using var p=Microsoft.Win32.Registry.CurrentUser.OpenSubKey(@"Software\family_connect");country.SelectedIndex=(p?.GetValue("Country") as string)=="ru"?1:0;mode.SelectedIndex=(p?.GetValue("Transport") as string)=="tcp"?0:1;}catch{}
        void SaveSelection(){revision++;loadNext=DateTime.MinValue;if(saveLanguage)try{using var p=Microsoft.Win32.Registry.CurrentUser.CreateSubKey(@"Software\family_connect");p.SetValue("Country",Country);p.SetValue("Transport",TcpSelected?"tcp":"awg");}catch{}PaintState();}
        country.SelectedIndexChanged+=(_,_)=>SaveSelection();mode.SelectedIndexChanged+=(_,_)=>SaveSelection();
        dial.Height=260;
        accessPage=new FriendsForm(ru,r=>call(r));accessPage.RegistrationChanged+=()=>{friendsReady=true;PaintState();};
        var selectors=new LiveNetworkPanel(country,mode,!smoke&&!layoutTest);telemetry=selectors;
        int row=0;
        foreach(Control child in new Control[]{card,enroll,selectors,friends,request,activate,detail,notice,update,accessPage})
            content.Controls.Add(child,0,row++);
        var version=new Label{Text="v"+Application.ProductVersion.Split('+')[0],AutoSize=true,Dock=DockStyle.Fill,ForeColor=Color.FromArgb(153,196,181)};
        language.MinimumSize=new Size(0,36);language.Dock=DockStyle.Fill;
        foreach(var child in new Control[]{language,version,routeTitle,routeMap,messengerNote})content.Controls.Add(child,0,row++);
        pages["status"]=new Control[]{card,enroll,selectors};
        pages["route"]=new Control[]{routeTitle,routeMap};
        pages["settings"]=new Control[]{friends,update,language,version};
        pages["access"]=new Control[]{accessPage};request.Visible=activate.Visible=false;
        pages["messenger"]=new Control[]{messengerNote};
        footer.Dock=DockStyle.Fill;footer.Height=64;footer.Padding=new Padding(12,2,12,8);footer.Margin=Padding.Empty;footer.ColumnCount=4;footer.RowCount=1;footer.RowStyles.Add(new RowStyle(SizeType.Percent,100));
        int column=0;
        foreach(string name in new[]{"status","messenger","route","settings"}){
            footer.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,25));
            var button=new ModernButton{NavigationButton=true,Tag=name,Dock=DockStyle.Fill,BackColor=BackColor,ForeColor=ForeColor,Font=new Font("Segoe UI",8,FontStyle.Regular),Margin=new Padding(2)};
            button.Click+=(_,_)=>{page=name;PaintState();FitContent();};nav[name]=button;footer.Controls.Add(button,column++,0);
        }
        shell.Controls.Add(footer,0,2);
        viewport.SizeChanged+=(_,_)=>FitContent();
        DpiChanged+=(_,_)=>BeginInvoke((Action)(()=>{ApplyDpiMetrics();FitWindow();}));
        update.Click+=async(_,_)=>{
            if(busy)return;revision++;busy=true;PaintState();
            try{
                if(availableUpdate is null){
                    availableUpdate=await Updates.Check(Application.ProductVersion.Split('+')[0]);
                    detail.Text=availableUpdate is null?T("Установлена последняя версия Windows: ","Windows is up to date: ")+Application.ProductVersion.Split('+')[0]:T("Доступна версия ","Version available: ")+availableUpdate.Version;
                }else{
                    string installer=await Updates.Download(availableUpdate);Updates.LaunchInstaller(installer,availableUpdate);
                    busy=false;state="off";Close();
                }
            }catch(Exception){detail.Text=T("Обновление недоступно или не прошло проверку. Текущая версия сохранена.","Update unavailable or verification failed. The current version is preserved.");}
            finally{busy=false;if(!IsDisposed)PaintState();}
        };
        connect.Click+=async(_,_)=>await Execute(new(ConnectionAction()));
        friends.Click+=(_,_)=>{page="access";PaintState();};
        enroll.Click+=(_,_)=>{page="access";PaintState();};
        language.Click+=(_,_)=>{ru=!ru;country.Items[0]=T("Нидерланды","Netherlands");country.Items[1]=T("Россия","Russia");if(saveLanguage)try{using var preferences=Microsoft.Win32.Registry.CurrentUser.CreateSubKey(@"Software\family_connect");preferences.SetValue("Language",ru?"ru":"en");}catch(Exception){detail.Text=T("Не удалось сохранить язык.","Could not save language.");}PaintState();FitWindow();};
        poll.Tick+=async(_,_)=>{if(pendingInvitation.Length>0&&!busy)await AcceptInvitation();else await PollStatus();};
        FormClosing+=(_,e)=>{if(busy){e.Cancel=true;return;}};
        FormClosed+=(_,_)=>{poll.Dispose();loadTimer.Dispose();loadTip.Dispose();connect.Dispose();};
        loadTimer.Tick+=async(_,_)=>await RefreshLoad();
        PaintState();
        Shown+=async(_,_)=>{
            ApplyDpiMetrics();FitWindow();
            if(layoutTest)return;
            if(smoke){Close();return;}
            await Execute(new("status"));if(state is "off" or "inactive")await EnsureIdentity();if(pendingInvitation.Length>0)await AcceptInvitation();else if(friendsReady&&(state is "off" or "inactive"))await Execute(new("friends-register"));poll.Start();loadTimer.Start();await RefreshLoad();
        };
        AutoScaleDimensions=new SizeF(96,96);
        ResumeLayout(true);
    }
    internal void Invite(string uri){
        if(!System.Text.RegularExpressions.Regex.IsMatch(uri,@"\Afamilyconnect://invite/[0-9a-f]{64}\z"))return;
        pendingInvitation=uri["familyconnect://invite/".Length..];page="status";
        if(WindowState==FormWindowState.Minimized)WindowState=FormWindowState.Normal;
        Activate();
    }
    async Task EnsureIdentity(){
        try{
            var reply=await call(new("friends-create"));
            if(!reply.Ok||reply.Code is null){detail.Text=FriendsForm.Error(reply.Error,ru);return;}
            using var identity=System.Text.Json.JsonDocument.Parse(reply.Code);
            var reference=identity.RootElement.GetProperty("device").GetString();
            if(reference is null||!System.Text.RegularExpressions.Regex.IsMatch(reference,@"\A[0-9a-f]{32}\z"))throw new IOException();
            accessPage.SetDevice(reference);
        }catch(Exception){detail.Text=T("Не удалось создать или открыть ключ устройства. Проверьте службу Family Connect в настройках доступа.","Could not create or open the device key. Check Family Connect service in access settings.");}
        finally{PaintState();}
    }
    async Task AcceptInvitation(){
        if(busy)return;
        string token=pendingInvitation;pendingInvitation="";
        var reply=await Execute(new("friends-register",token));
        if(reply?.Ok!=true){accessPage.PendingInvitation=token;page="access";PaintState();}
    }
    internal void CheckStartupLayout()
    {
        if(Application.HighDpiMode!=HighDpiMode.PerMonitorV2)throw new InvalidOperationException("Production startup changed DPI mode");
        state="off";awgReady=true;friendsReady=true;ru=true;PaintState();
        foreach(var size in new[]{new Size(560,800),new Size(1200,800),new Size(360,420),new Size(560,800)}){
            ClientSize=new Size(D(size.Width),D(size.Height));Application.DoEvents();FitContent();
            if(mode.Bottom>telemetry!.ClientSize.Height || country.Bounds.IntersectsWith(mode.Bounds))throw new InvalidOperationException("Startup selectors clipped");
            foreach(var button in nav.Values){
                if(button.Height<D(48)||button.Bottom>footer.ClientSize.Height)throw new InvalidOperationException("Startup navigation clipped");
            }
            viewport.AutoScrollPosition=Point.Empty;Application.DoEvents();
            if(size.Width>=560){
                using var image=new Bitmap(Width,Height);DrawToBitmap(image,new Rectangle(Point.Empty,Size));
                image.Save(Path.Combine(Path.GetTempPath(),size.Width==1200?"Windows-startup-wide.png":"Windows-startup.png"));
            }
        }
    }
    internal static void CheckLayouts()
    {
        TraceLayout("start");ServerLoad.Check();RouteMap.CheckPixels();TerminalHeader.CheckResizeInvalidation();
        TraceLayout("settings repaint");CheckSettingsRepaint();
        TraceLayout("polling");
        CheckPolling();TraceLayout("preview");
        using(var preview=new MainForm(true,true)){
            preview.ru=true;preview.state="off";preview.Show();preview.PaintState();preview.FitWindow();Application.DoEvents();
            using var bitmap=new Bitmap(preview.Width,preview.Height);preview.DrawToBitmap(bitmap,new Rectangle(Point.Empty,preview.Size));
            string path=Path.Combine(Path.GetTempPath(),"Windows-preview.png");
            Directory.CreateDirectory(Path.GetDirectoryName(path)!);bitmap.Save(path);
            preview.country.Focus();preview.country.DroppedDown=true;Application.DoEvents();
            if(!preview.country.DroppedDown)throw new InvalidOperationException("Country list did not open");
            preview.country.SelectedIndex=1;preview.country.DroppedDown=false;
            if(preview.Country!="ru")throw new InvalidOperationException("Country selection lost");
            preview.country.SelectedIndex=0;
            preview.mode.Focus();preview.mode.DroppedDown=true;Application.DoEvents();
            if(!preview.mode.DroppedDown)throw new InvalidOperationException("Transport list did not open");
            preview.mode.SelectedIndex=0;preview.mode.DroppedDown=false;
            if(!preview.TcpSelected)throw new InvalidOperationException("Transport selection lost");
            preview.mode.SelectedIndex=1;Application.DoEvents();
            foreach(var size in new[]{new Size(360,420),new Size(1200,800),new Size(800,700)}){
                preview.ClientSize=size;Application.DoEvents();preview.FitContent();
                if(preview.mode.Bottom>preview.telemetry!.ClientSize.Height || preview.country.Bounds.IntersectsWith(preview.mode.Bounds))
                    throw new InvalidOperationException("Resize clipped connection selectors");
                if(preview.nav.Values.Any(button=>button.Height<48*preview.DeviceDpi/96f))
                    throw new InvalidOperationException("Resize collapsed navigation");
            }
            preview.viewport.AutoScrollPosition=Point.Empty;Application.DoEvents();
            using(var wide=new Bitmap(preview.Width,preview.Height)){preview.DrawToBitmap(wide,new Rectangle(Point.Empty,preview.Size));wide.Save(Path.Combine(Path.GetTempPath(),"Windows-wide.png"));}
            preview.page="route";preview.PaintState();preview.FitWindow();Application.DoEvents();
            using var routeImage=new Bitmap(preview.Width,preview.Height);preview.DrawToBitmap(routeImage,new Rectangle(Point.Empty,preview.Size));
            routeImage.Save(Path.Combine(Path.GetTempPath(),"Windows-route.png"));
        }
        // No broker requests: test visible runtime layout.
        foreach(float scale in new[]{1f,1.5f,2f,2.5f})
        foreach(bool russian in new[]{true,false})
        foreach(int protocol in new[]{0,1})
        foreach(string selectedPage in new[]{"status","messenger","route","settings","access"})
        foreach(string connection in new[]{"inactive","off","pending","recovering","on","other-user","unknown"})
        foreach(Size size in new[]{new Size(360,420),new Size(480,620),new Size(800,700)}){
            if(selectedPage!="status"&&(protocol!=0||connection!="off"))continue;
            TraceLayout($"case {scale} {russian} {protocol} {selectedPage} {connection} {size}");
            using var form=new MainForm(true,true);
            form.page=selectedPage;form.ru=russian;form.state=connection=="recovering"?"pending":connection;form.lastError=connection=="recovering"?"tcp-reconnecting":null;form.tcpReady=protocol==0;form.awgReady=protocol==1;form.transport=protocol==1?"awg":"tcp";form.mode.SelectedIndex=protocol;form.automatic=false;
            form.Scale(new SizeF(scale,scale));
            form.ClientSize=new Size((int)(size.Width*scale),(int)(size.Height*scale));
            form.detail.Text=russian?"Служба Family Connect недоступна. Повторно запустите установщик приложения.":"Family Connect service is unavailable. Run the application installer again.";
            form.Show();Application.DoEvents();form.PaintState();
            form.ClientSize=new Size((int)(size.Width*scale),(int)(size.Height*scale));
            form.FitContent();form.PerformLayout();form.content.PerformLayout();
            if(form.nav.Values.Any(b=>!b.Visible))throw new Exception("Navigation disappeared");
            if(form.country.Visible && (form.mode.Bottom>form.telemetry!.ClientSize.Height || form.country.Bounds.IntersectsWith(form.mode.Bounds)))
                throw new InvalidOperationException("Connection selectors clipped or overlapping");
            if(form.header.Height<78*form.DeviceDpi/96f || form.dial.Height<150*form.DeviceDpi/96f)
                throw new InvalidOperationException("Custom painted control lost its logical height");
            int bottom=0;
            foreach(Control control in form.content.Controls.Cast<Control>().OrderBy(form.content.GetRow)){
                if(!control.Visible)continue;
                if(control.Left<0||control.Right>form.content.ClientSize.Width||control.Top<bottom)
                    throw new InvalidOperationException($"Clipped or overlapping content: page={selectedPage}, scale={scale}, ru={russian}, protocol={protocol}, state={connection}, requested={size}, client={form.ClientSize}, content={form.content.ClientSize}, row={form.content.GetRow(control)}, type={control.GetType().Name}, bounds={control.Bounds}, previousBottom={bottom}, text={control.Text}");
                bottom=control.Bottom;
                if(control is Label label && label.Height<label.GetPreferredSize(new Size(label.Width,0)).Height)
                    throw new InvalidOperationException("Clipped label");
                if(control is Button button && button.Width<button.GetPreferredSize(Size.Empty).Width)
                    throw new InvalidOperationException("Clipped button");
            }
            foreach(var label in new[]{form.status,form.description}){
                if(!label.Visible)continue;
                if(label.Right>form.card.ClientSize.Width-form.card.Padding.Right || label.Height<label.GetPreferredSize(new Size(label.Width,0)).Height)
                    throw new InvalidOperationException("Clipped status card");
            }
            if(form.content.Width>form.viewport.ClientSize.Width)
                throw new InvalidOperationException("Horizontal overflow");
            if(form.language.Visible && form.language.Bottom>form.language.Parent!.ClientSize.Height)
                throw new InvalidOperationException("Clipped settings language control");
            foreach(var button in form.nav.Values){
                var parent=button.Parent!;
                if(button.Left<0 || button.Top<0 || button.Right>parent.ClientSize.Width || button.Bottom>parent.ClientSize.Height)
                    throw new InvalidOperationException($"Clipped navigation: scale={scale}, page={selectedPage}, requested={size}, client={form.ClientSize}, footer={parent.ClientSize}, padding={parent.Padding}, button={button.Bounds}, text={button.Text}");
                var text=TextRenderer.MeasureText(button.Text,button.Font,Size.Empty,TextFormatFlags.NoPadding|TextFormatFlags.SingleLine);
                if(text.Width>button.Width-4 || text.Height>button.Height/2-4 || button.Height<48*form.DeviceDpi/96f)
                    throw new InvalidOperationException($"Clipped navigation text: {button.Text}, scale={scale}, client={form.ClientSize}, measured={text}, button={button.Size}");
            }
        }
    }
    static void TraceLayout(string value)=>File.WriteAllText(Path.Combine(Path.GetTempPath(),"fc-layout-progress.txt"),value);
    static void CheckSettingsRepaint(){
        using var form=new MainForm(true,true);form.state="off";form.awgReady=form.tcpReady=form.friendsReady=true;
        form.Show();form.PaintState();Application.DoEvents();
        int visibility=0,headerPaints=0;
        form.enroll.VisibleChanged+=(_,_)=>visibility++;
        form.header.Invalidated+=(_,_)=>headerPaints++;
        for(int i=0;i<8;i++){
            form.country.SelectedIndex=i%2;form.mode.SelectedIndex=i%2;Application.DoEvents();
        }
        if(visibility!=0||headerPaints!=0)throw new InvalidOperationException($"Settings repainted unrelated controls: activation={visibility}, header={headerPaints}");
        form.page="settings";form.PaintState();Application.DoEvents();
        foreach(Control child in form.content.Controls)child.VisibleChanged+=(_,_)=>visibility++;
        visibility=0;form.PaintState();Application.DoEvents();
        if(visibility!=0)throw new InvalidOperationException("Unchanged settings page toggled controls");
        form.language.PerformClick();Application.DoEvents();
        if(!form.language.Visible||!form.friends.Visible)throw new InvalidOperationException("Language change lost settings controls");
        form.Close();
    }
    static void CheckPolling()
    {
        TraceLayout("access page");FriendsForm.CheckUi();TraceLayout("polling state");
        using(var fresh=new MainForm(true,true)){
            fresh.state="inactive";fresh.Show();fresh.PaintState();
            var actions=new List<string>();
            fresh.call=r=>{actions.Add(r.Action);return Task.FromResult(new Reply(true,"inactive",Code:"{\"device\":\""+new string('a',32)+"\"}"));};
            Pump(fresh.EnsureIdentity());
            if(!fresh.enroll.Visible||fresh.dial.Enabled||actions.Count!=1||actions[0]!="friends-create")throw new Exception("Fresh device onboarding skipped invitation or local key creation");
            fresh.enroll.PerformClick();Application.DoEvents();
            if(fresh.page!="access"||!fresh.accessPage.Visible)throw new Exception("Activation entry is unreachable");
            fresh.Close();
        }
        using var form=new MainForm(true,true);form.state="off";form.awgReady=true;form.Show();form.PaintState();
        int changes=0;form.status.TextChanged+=(_,_)=>changes++;
        var response=new TaskCompletionSource<Reply>();int calls=0;
        form.call=_=>{calls++;return response.Task;};
        Task pending=form.PollStatus();
        if(form.busy||!form.connect.Enabled||changes!=0)throw new Exception("Poll changed visible state");
        form.PollStatus().GetAwaiter().GetResult();
        if(calls!=1)throw new Exception("Overlapping polls");
        response.SetResult(new(true,"off",AwgReady:true));
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
        form.state="inactive";form.tcpReady=true;form.mode.SelectedIndex=0;form.PaintState();
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
        form.automatic=false;form.state="inactive";form.awgReady=true;form.mode.SelectedIndex=1;form.PaintState();
        if(!form.connect.Enabled||form.ConnectionAction()!="connect-awg")throw new Exception("AWG-only profile unavailable");
        form.call=_=>Task.FromResult(new Reply(true,"pending",Transport:"awg",AwgReady:true));Pump(form.PollStatus());
        if(!form.connect.Enabled||form.mode.Enabled||form.ConnectionAction()!="disconnect"||form.mode.SelectedIndex!=1)throw new Exception("AWG cancellation unavailable");
        string? dialAction=null;
        form.call=r=>{dialAction=r.Action;return Task.FromResult(new Reply(true,"off"));};
        if(!form.dial.Enabled)throw new Exception("Dial differs from connection control");
        form.dial.PerformClick();Application.DoEvents();
        if(dialAction!="disconnect")throw new Exception("Dial did not dispatch existing connection action");
        form.busy=true;form.PaintState();dialAction=null;form.dial.PerformClick();
        if(dialAction is not null||form.dial.Enabled)throw new Exception("Busy dial accepted action");
        form.busy=false;
        static void Pump(Task task){
            var deadline=DateTime.UtcNow.AddSeconds(5);
            while(!task.IsCompleted&&DateTime.UtcNow<deadline)Application.DoEvents();
            if(!task.IsCompleted)throw new TimeoutException("UI test continuation");
            task.GetAwaiter().GetResult();
        }
    }
    int D(int value)=>(int)Math.Round(value*DeviceDpi/96f);
    void FitShell()
    {
        int width=Math.Min(shellHost.ClientSize.Width,D(720));
        shell.SetBounds(Math.Max(0,(shellHost.ClientSize.Width-width)/2),0,width,shellHost.ClientSize.Height);
        FitContent();
    }
    void ApplyDpiMetrics()
    {
        // Custom painting uses DeviceDpi. Its containing rows must use the same units,
        // including controls created after WinForms' first automatic scaling pass.
        shell.SuspendLayout();
        shell.RowStyles[0].Height=D(86);shell.RowStyles[2].Height=D(76);
        header.MinimumSize=new Size(D(240),D(78));header.Margin=new Padding(0,0,0,D(8));
        dial.MinimumSize=new Size(0,D(150));dial.Height=D(260);
        telemetry!.MinimumSize=new Size(0,D(174));telemetry.Height=D(174);
        card.Padding=new Padding(D(16),D(8),D(16),D(8));
        foreach(var label in new[]{status,description,loadLabel})label.Margin=new Padding(0,D(4),0,D(4));
        footer.Height=D(76);footer.Padding=new Padding(D(12),D(2),D(12),D(8));
        foreach(var picker in new[]{country,mode})picker.ItemHeight=D(30);
        shell.ResumeLayout(true);telemetry.PerformLayout();FitShell();
    }
    bool fittingContent;
    void FitContent()
    {
        if(fittingContent||viewport.ClientSize.Width<=0)return;
        fittingContent=true;
        try{
        int width=Math.Max(1,viewport.ClientSize.Width);
        content.SuspendLayout();
        content.MinimumSize=new Size(width,0);content.MaximumSize=new Size(width,0);content.Width=width;
        int textWidth=Math.Max(1,width-content.Padding.Horizontal);
        foreach(var label in new[]{title,detail,notice,routeTitle,messengerNote})label.MaximumSize=new Size(textWidth,0);
        foreach(var label in new[]{status,description})label.MaximumSize=new Size(Math.Max(1,textWidth-card.Padding.Horizontal),0);
        content.ResumeLayout(true);
        if(page=="status" && telemetry is not null && card.Height>dial.Height){
            int other=card.Height-dial.Height+telemetry.Height+content.Padding.Vertical+card.Margin.Vertical+telemetry.Margin.Vertical;
            int height=Math.Clamp(viewport.ClientSize.Height-other,D(150),D(260));
            if(dial.Height!=height){dial.Height=height;content.PerformLayout();}
        }
        }finally{fittingContent=false;}
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
            ClientSize=new Size(ClientSize.Width,Math.Min(max,ClientSize.Height));
            FitContent();
        }finally{fitting=false;}
    }
    void PaintState()
    {
        content.SuspendLayout();
        try{
        if(country.Items.Count==2){
            if((country.Items[0] as string)!=T("Нидерланды","Netherlands"))country.Items[0]=T("Нидерланды","Netherlands");
            if((country.Items[1] as string)!=T("Россия","Russia"))country.Items[1]=T("Россия","Russia");
        }
        ((ModernButton)connect).SwitchOn=state=="on";connect.Invalidate();
        status.ForeColor=state=="on"?Color.FromArgb(152,247,216):Color.FromArgb(218,255,242);
        status.Text=NeedsInvitation?T("Нужно приглашение","Invitation required"):state switch{
            "on"=>T("Туннель включён","Tunnel is on"),"off"=>T("Готов к подключению","Ready to connect"),
            "inactive"=>friendsReady?T("Готов к подключению","Ready to connect"):T("Получить доступ","Get access"),"other-user"=>T("VPN занят другим пользователем","VPN used by another user"),
            "pending"=>lastError=="tcp-reconnecting"?T("Восстанавливаем подключение…","Reconnecting…"):T("Подключение меняется…","Connection changing…"),_=>T("Статус недоступен","Status unavailable")};
        enroll.Text=T("Активировать по приглашению","Activate with invitation");
        description.Text=(Country=="nl"?T("Нидерланды","Netherlands"):T("Россия","Russia"))+" · "+(TcpSelected?"TCP REALITY":"AWG 3.1");
        connect.Text=state=="on"?T("Отключить","Disconnect"):state=="pending"&&(automatic||transport is "tcp" or "awg")?T("Отменить подключение","Cancel connection"):T("Подключить","Connect");
        connect.Enabled=!busy&&(state=="on"||(state=="pending"&&(automatic||transport is "tcp" or "awg"))||((state is "off" or "inactive")&&(friendsReady||(AutoSelected?(awgReady||tcpReady||state=="off"):AwgSelected?awgReady:TcpSelected?tcpReady:state=="off"))));
        dial.UpdateState(state=="on",busy||state=="pending",ru,connect.Enabled);telemetry?.Connection(ru,status.Text);
        mode.Enabled=country.Enabled=!busy&&(state is "off" or "inactive");
        friends.Text=T("Устройство и доступ", "Device and access");friends.Enabled=!busy;
        request.Text=T("Получить код устройства","Get device code");request.Enabled=!busy;
        activate.Text=AwgSelected?T("Открыть AWG-активацию","Open AWG activation"):TcpSelected?T("Открыть TCP-активацию","Open TCP activation"):T("Открыть файл активации","Open activation file");activate.Enabled=!busy&&!AutoSelected&&(state=="off"||state=="inactive");
        notice.Text=T("На телефоне: Настройки → Пригласить друга. Откройте эту ссылку на компьютере или вставьте её в разделе активации. Ключ создаётся автоматически; доступ выдаётся по приглашению.","On your phone: Settings → Invite a friend. Open that link on this PC or paste it in activation. The key is created automatically; access requires an invitation.");
        update.Text=availableUpdate is null?T("Проверить обновления","Check for updates"):T("Установить обновление","Install update");update.Enabled=!busy;
        accessPage.SetLanguage(ru);
        language.Text=T("Язык: Русский → English","Language: English → Русский");

        detail.Visible=detail.Text.Length>0;PaintLoad();ApplyPage();
        }finally{content.ResumeLayout(true);}
        FitContent();
    }
    void PaintLoad(){
        var sample=loadSample;
        if(sample is not null&&(!sample.Fresh||loadRevision!=revision||loadMode!=mode.SelectedIndex))sample=null;
        if(loadBar.Percent!=sample?.Percent){loadBar.Percent=sample?.Percent;loadBar.Invalidate();}
        loadLabel.Text=T("Нагрузка сервера","Server load")+" · "+(sample?.Percent is double p?(sample.Estimated?"≈ ":"")+Math.Round(p)+"%":T("Нет данных","No data"));
        loadBar.AccessibleName=loadLabel.Text;
        loadTip.SetToolTip(loadLabel,sample is null?loadLabel.Text:$"CPU {sample.Cpu:F0}% · ↓ {sample.Rx:F1} / ↑ {sample.Tx:F1} Mbps"+(sample.Estimated?T(" · оценка по 200 Мбит/с исходящего канала"," · estimated using 200 Mbps egress"):""));
    }
    async Task RefreshLoad(){
        if(IsDisposed||Disposing)return;PaintLoad();
        if(loadPending||busy||page!="status")return;
        if(DateTime.UtcNow<loadNext&&loadRevision==revision&&loadMode==mode.SelectedIndex)return;
        loadPending=true;long started=revision;int selected=mode.SelectedIndex;
        try{
            var target=friendsReady?new Reply(true,"off",Code:Country):await call(new("load-country",AutoSelected?"auto":AwgSelected?"awg":TcpSelected?"tcp":"wg"));
            var sample=target.Ok&&target.Code is "ru" or "nl"?await ServerLoad.Fetch(target.Code):null;
            if(!IsDisposed&&!Disposing&&started==revision&&selected==mode.SelectedIndex){loadSample=sample;loadRevision=started;loadMode=selected;}
        }catch(Exception){if(started==revision)loadSample=null;}
        finally{loadPending=false;loadNext=DateTime.UtcNow.AddSeconds(15);if(!IsDisposed&&!Disposing)PaintLoad();}
    }
    void ApplyPage(){
        routeTitle.Text=T("Маршрут подключения","Connection route");
        messengerNote.Text=T("Мессенджер пока доступен в Android. Версия для компьютера в разработке.","Messaging is currently available on Android. Desktop messaging is in development.");
        foreach(var group in pages)foreach(var control in group.Value)
            control.Visible=group.Key==page&&(control!=enroll||NeedsInvitation);
        notice.Visible=page=="status"&&NeedsInvitation;
        foreach(var item in nav){
            item.Value.Text=item.Key switch{"status"=>T("СТАТУС","STATUS"),"messenger"=>T("МЕССЕНДЖЕР","MESSENGER"),"route"=>T("МАРШРУТ","ROUTE"),_=>T("НАСТРОЙКИ","SETTINGS")};
            item.Value.ForeColor=(item.Key==page||(page=="access"&&item.Key=="settings"))?Color.FromArgb(255,173,70):Color.FromArgb(153,196,181);
        }
    }
    string ConnectionAction()=>state=="on"||(state=="pending"&&(automatic||transport is "tcp" or "awg"))?"disconnect":friendsReady?"friends-connect-"+(TcpSelected?"tcp":"awg")+"-"+Country:AutoSelected?"connect-auto":AwgSelected?"connect-awg":TcpSelected?"connect-tcp":"connect";
    string ErrorText(string? error)=>error switch{
        "activation-invalid"=>T("Активация недействительна, истекла или выдана другому устройству.","Activation is invalid, expired or belongs to another device."),
        "activation-required"=>T("Откройте файл активации выбранного подключения.","Open the activation file for the selected connection."),
        "other-user"=>T("Сначала отключите VPN в другой учётной записи Windows.","Disconnect the VPN in the other Windows account first."),
        "disconnect-first" or "busy"=>T("Сначала отключите VPN.","Disconnect the VPN first."),
        "awg-engine-missing"=>T("Компонент AWG отсутствует. Повторно запустите установщик.","AWG component is missing. Run the installer again."),
        "tcp-engine-missing"=>T("Компонент TCP отсутствует. Повторно запустите установщик.","TCP component is missing. Run the installer again."),
        "auto-switching"=>T("Проверяем соединение и выбираем доступный транспорт…","Checking connectivity and selecting a transport…"),
        "auto-exhausted"=>T("Доступные транспорты исчерпаны. Проверьте сеть и подключитесь повторно.","No working transport remains. Check your network and connect again."),
        "auto-cleanup-required"=>T("Переключение остановлено: сеть не очищена. Перезапустите службу Family Connect.","Switching stopped: network cleanup failed. Restart the Family Connect service."),
        "auto-session-failed"=>T("Автоматическое подключение не удалось.","Automatic connection failed."),
        "tcp-reconnecting"=>T("VPN прервался. Повторяем подключение; можно отменить.","VPN was interrupted. Retrying; you can cancel."),
        "tcp-recovery-exhausted"=>T("VPN не удалось восстановить за три попытки. Проверьте сеть и подключитесь вручную.","VPN recovery stopped after three attempts. Check your network and connect manually."),
        "tcp-engine-exited"=>T("VPN остановился. Можно подключиться повторно.","VPN stopped. You can connect again."),
        "tcp-session-failed"=>T("Не удалось включить VPN. Проверьте настройки сети и повторите попытку.","Could not start VPN. Check network settings and try again."),
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
            if(next==state&&error==pollError&&tcpReady==reply.TcpReady&&awgReady==reply.AwgReady&&transport==reply.Transport&&lastError==reply.Error&&automatic==reply.Automatic&&friendsReady==reply.FriendsReady)return;
            state=next;tcpReady=reply.TcpReady;awgReady=reply.AwgReady;transport=reply.Transport;lastError=reply.Error;automatic=reply.Automatic;friendsReady=reply.FriendsReady;accessPage.SetDevice(reply.Device);
            if(state is "on" or "pending")mode.SelectedIndex=transport=="awg"?1:0;
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
                state=reply.State;transport=reply.Transport;lastError=reply.Error;automatic=reply.Automatic;friendsReady=reply.FriendsReady;accessPage.SetDevice(reply.Device);
                if(action.Action is "status" or "activate-tcp" or "connect-tcp")tcpReady=reply.TcpReady;
                if(action.Action is "status" or "activate-awg" or "connect-awg")awgReady=reply.AwgReady;
            }
            if(!reply.Ok||reply.Error is not null)detail.Text=action.Action.StartsWith("friends-")?FriendsForm.Error(reply.Error,ru):ErrorText(reply.Error);
            else if(!quiet)detail.Text=(action.Action is "activate" or "activate-tcp" or "activate-awg")?T("Устройство активировано. Нажмите «Подключить».","Device activated. Click Connect."):"";
            return reply;
        }catch(Exception){state="unknown";detail.Text=T("Служба Family Connect недоступна. Повторно запустите установщик приложения.","Family Connect service is unavailable. Run the application installer again.");return null;}
        finally{busy=false;PaintState();}
    }
}
