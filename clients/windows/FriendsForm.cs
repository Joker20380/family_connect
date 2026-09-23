namespace FamilyConnect;

// Embedded access page. Registration and sharing never create a top-level window.
internal sealed class FriendsForm : UserControl
{
    bool ru;
    internal string PendingInvitation="";
    readonly Label hint=new(){AutoSize=true};
    readonly Func<Request,Task<Reply>> call;
    readonly Label status=new(){AutoSize=true},device=new(){AutoSize=true};
    internal void SetDevice(string? reference){device.Text=reference is null?"":"ID · "+reference;}
    readonly TextBox link=new(){ReadOnly=true,Multiline=true,Height=70};
    readonly Button register=new ModernButton(),share=new ModernButton(),copy=new ModernButton();
    bool busy;
    internal event Action? RegistrationChanged;
    string T(string r,string e)=>ru?r:e;
    internal FriendsForm(bool russian,Func<Request,Task<Reply>>? caller=null)
    {
        ru=russian;call=caller??Wire.Call;AutoScaleMode=AutoScaleMode.Dpi;
        AutoSize=true;AutoSizeMode=AutoSizeMode.GrowAndShrink;Dock=DockStyle.Top;
        BackColor=Color.FromArgb(3,17,14);ForeColor=Color.FromArgb(218,255,242);Font=new Font("Consolas",10);
        var panel=new TableLayoutPanel{AutoSize=true,Dock=DockStyle.Top,ColumnCount=1,Padding=new Padding(0,8,0,8)};
        panel.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,100));Controls.Add(panel);
        void Add(Control c){c.Dock=DockStyle.Top;c.Margin=new Padding(0,5,0,5);int row=panel.RowCount++;panel.RowStyles.Add(new RowStyle(SizeType.AutoSize));panel.Controls.Add(c,0,row);}
        SetLanguage(ru);Add(hint);Add(device);
        register.Text=T("Получить доступ","Get access");Add(register);Add(status);
        share.Text=T("Пригласить друга","Invite a friend");Add(share);Add(link);
        copy.Text=T("Скопировать ссылку","Copy link");copy.Enabled=false;Add(copy);
        foreach(var b in new[]{register,share,copy}){b.AutoSize=true;b.MinimumSize=new(0,44);b.BackColor=Color.FromArgb(7,32,24);b.ForeColor=ForeColor;}
        SizeChanged+=(_,_)=>{int width=Math.Max(1,Width-12);hint.MaximumSize=new(width,0);status.MaximumSize=new(width,0);};
        register.Click+=async(_,_)=>await Run("friends-register");
        share.Click+=async(_,_)=>await Run("friends-referral");
        copy.Click+=(_,_)=>{if(link.Text.Length>0)Clipboard.SetText(link.Text);};
    }
    internal void SetLanguage(bool russian){
        ru=russian;hint.Text=T("Откройте исходную ссылку приглашения и нажмите «Открыть приложение». Личный ключ сохранится автоматически.","Open your original invitation link and choose Open app. Your personal key is saved automatically.");
        register.Text=T("Повторить получение доступа","Retry activation");share.Text=T("Пригласить друга","Invite a friend");copy.Text=T("Скопировать ссылку","Copy link");
    }
    async Task Run(string action)
    {
        if(busy)return;busy=true;register.Enabled=share.Enabled=copy.Enabled=false;
        status.Text=T("Подождите…","Please wait…");
        try {
            var reply=await call(new(action,action=="friends-register"?PendingInvitation:null));
            if(!reply.Ok){status.Text=Error(reply.Error,ru);return;}
            if(action=="friends-register"){
                PendingInvitation="";status.Text=T("Доступ готов. Подключитесь на главном экране.","Access is ready. Connect on the main screen.");SetDevice(reply.Device);RegistrationChanged?.Invoke();
            }else{
                if(reply.Code is null||!System.Text.RegularExpressions.Regex.IsMatch(reply.Code,@"\Ahttps://185\.251\.89\.19:8443/invite/#[0-9a-f]{64}\z"))throw new IOException();
                link.Text=reply.Code;status.Text=T("Отправьте ссылку другу: на странице только загрузки приложения.","Send this link to a friend to download the app.");
            }
        }catch(OperationCanceledException){status.Text=Error("broker-timeout",ru);}
        catch(Exception){status.Text=Error("broker-unavailable",ru);}
        finally{busy=false;register.Enabled=share.Enabled=true;copy.Enabled=link.Text.Length>0;}
    }
    internal static string Error(string? code,bool ru)=>code switch{
        "access_rejected"=>ru?"Откройте ссылку приглашения и нажмите «Открыть приложение». Если доступ отозван — обратитесь к владельцу.":"Access for this device is disabled. Contact the service owner.",
        "tls_failed"=>ru?"Не удалось проверить защищённое соединение. Проверьте дату и время Windows.":"Could not verify the secure connection. Check Windows date and time.",
        "request_timeout"=>ru?"Сервер не ответил вовремя. Повторите попытку.":"The server did not respond in time. Retry.",
        "network_unavailable" or "service_unavailable"=>ru?"Сервер регистрации недоступен. Проверьте интернет и повторите попытку.":"Registration is unavailable. Check your connection and retry.",
        "rate_limited"=>ru?"Подождите минуту и повторите попытку.":"Wait a minute and retry.",
        "disconnect-first" or "busy"=>ru?"Сначала отключите VPN.":"Disconnect VPN first.",
        "invalid_response"=>ru?"Ответ сервера не прошёл проверку. Проверьте дату и версию приложения.":"The server response could not be verified. Check the date and app version.",
        "broker-timeout"=>ru?"Служба Windows не ответила. Перезапустите приложение.":"The Windows service did not respond. Restart the app.",
        "broker-unavailable"=>ru?"Нет связи со службой FamilyConnectBroker. Повторно запустите установщик.":"Cannot reach FamilyConnectBroker. Run the installer again.",
        _=>ru?"Действие не выполнено. Код: "+code:"Could not complete the action. Code: "+code
    };
    internal static void CheckUi()
    {
        foreach(bool ru in new[]{false,true}){
            var calls=new List<string>();
            using var host=new Form{ClientSize=new(400,540)};
            using var page=new FriendsForm(ru,r=>{calls.Add(r.Action);return Task.FromResult(new Reply(true,"inactive",Code:r.Action=="friends-referral"?"https://185.251.89.19:8443/invite/#"+new string('a',64):null,FriendsReady:true));});
            host.Controls.Add(page);host.Show();Application.DoEvents();
            page.register.PerformClick();Application.DoEvents();
            if(calls.Count!=1||calls[0]!="friends-register"||!page.register.Enabled)throw new Exception("Inline registration failed");
            page.share.PerformClick();Application.DoEvents();
            if(!page.copy.Enabled||!page.link.Text.EndsWith(new string('a',64)))throw new Exception("Inline sharing failed");
            if(ru){using var bitmap=new Bitmap(host.Width,host.Height);host.DrawToBitmap(bitmap,new Rectangle(Point.Empty,host.Size));bitmap.Save(Path.Combine(Path.GetTempPath(),"Windows-invitation.png"));}
            if(Application.OpenForms.Count!=1)throw new Exception("Access page opened another window");
            host.Close();
        }
    }
}
