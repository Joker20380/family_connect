namespace FamilyConnect;

// First Friends onboarding screen; existing operator activation remains available.
internal sealed class FriendsForm : Form
{
    readonly bool ru;
    readonly Func<Request, Task<Reply>> call;
    readonly TextBox invitation = new(), link = new();
    readonly ComboBox region = new() { DropDownStyle = ComboBoxStyle.DropDownList };
    readonly ComboBox transport = new() { DropDownStyle = ComboBoxStyle.DropDownList };
    readonly Label status = new();
    readonly Button activate = new ModernButton(), connect = new ModernButton(), share = new ModernButton(), copy = new ModernButton();
    bool busy;
    string T(string r, string e) => ru ? r : e;
    internal FriendsForm(bool russian, Func<Request,Task<Reply>>? caller = null)
    {
        ru = russian; call = caller ?? Wire.Call;
        AutoScaleMode=AutoScaleMode.Dpi;AutoScaleDimensions=new SizeF(96,96);
        Text=T("Доступ по приглашению", "Invitation access");StartPosition=FormStartPosition.CenterParent;
        ClientSize=new(440,570);MinimumSize=new(340,360);Font=new Font("Consolas",10);
        BackColor=Color.FromArgb(3,17,14);ForeColor=Color.FromArgb(218,255,242);
        var panel=new TableLayoutPanel { Dock=DockStyle.Fill,ColumnCount=1,AutoScroll=true,Padding=new Padding(20) };
        panel.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,100));Controls.Add(panel);
        void Add(Control control)
        {
            control.Dock=DockStyle.Top;control.Margin=new Padding(0,5,0,5);
            int row=panel.RowCount++;panel.RowStyles.Add(new RowStyle(SizeType.AutoSize));panel.Controls.Add(control,0,row);
        }
        Add(new Label { Text=T("Вставьте полученный код. При обычном обновлении повторная активация не нужна.","Paste your invitation code. An ordinary app update does not require activation again."),AutoSize=true });
        invitation.PlaceholderText="FC-…";invitation.MaxLength=128;Add(invitation);
        activate.Text=T("Активировать", "Activate");Add(activate);
        status.AutoSize=true;status.MinimumSize=new(0,44);Add(status);
        panel.SizeChanged+=(_,_)=>status.MaximumSize=new(Math.Max(1,panel.ClientSize.Width-panel.Padding.Horizontal-SystemInformation.VerticalScrollBarWidth),0);
        region.Items.AddRange(new object[]{T("Нидерланды", "Netherlands"),T("Россия", "Russia")});region.SelectedIndex=0;Add(region);
        transport.Items.AddRange(new object[]{"TCP REALITY","AWG 3.1"});transport.SelectedIndex=0;Add(transport);
        connect.Text=T("Подключиться", "Connect");Add(connect);
        share.Text=T("Получить ссылку для друга", "Get invitation link");Add(share);
        link.ReadOnly=true;link.Multiline=true;link.Height=76;link.ScrollBars=ScrollBars.Vertical;Add(link);
        copy.Text=T("Скопировать ссылку", "Copy link");copy.Enabled=false;Add(copy);
        foreach(var button in new[]{activate,connect,share,copy})
        {
            button.AutoSize=true;button.MinimumSize=new(0,42);button.FlatStyle=FlatStyle.Flat;
            button.BackColor=Color.FromArgb(7,32,24);button.ForeColor=ForeColor;
        }
        activate.Click+=async(_,_)=>await Run(new("friends-activate",invitation.Text.Trim()),T("Доступ активирован. Выберите страну и нажмите «Подключиться» ниже.","Access activated. Select a country and click Connect below."));
        connect.Click+=async(_,_)=>await Run(new("friends-connect-"+(transport.SelectedIndex==1?"awg":"tcp")+(region.SelectedIndex==1?"-ru":"-nl")),T("Подключение запущено. Состояние видно в главном окне.","Connection started. Check its status in the main window."));
        share.Click+=async(_,_)=>await Run(new("friends-referral"),T("Ссылка готова. Отправьте её другу.","Link ready. Send it to your friend."));
        copy.Click+=(_,_)=>{if(link.Text.Length>0){Clipboard.SetText(link.Text);status.Text=T("Ссылка скопирована.","Link copied.");}};
        FormClosing+=(_,e)=>{if(busy)e.Cancel=true;};
    }
    async Task Run(Request request,string success)
    {
        if(busy)return;busy=true;
        foreach(var b in new[]{activate,connect,share,copy})b.Enabled=false;
        invitation.Enabled=region.Enabled=transport.Enabled=false;status.Text=T("Подождите…", "Please wait…");
        try
        {
            var reply=await call(request);
            if(!reply.Ok)
            {
                status.Text=reply.Error switch {
                    "disconnect-first" or "busy"=>T("Сначала отключите VPN в главном окне.","Disconnect VPN in the main window first."),
                    "invalid_invitation"=>T("Проверьте формат кода приглашения.","Check the invitation code format."),
                    "access_rejected"=>T("Сервер отклонил доступ. Проверьте приглашение.","The server rejected access. Check the invitation."),
                    "network_unavailable"=>T("Нет связи с сервером активации. Проверьте интернет и попробуйте снова.","Cannot reach the activation server. Check your connection and retry."),
                    "request_timeout"=>T("Сервер не ответил вовремя. Повторите попытку с тем же кодом.","The server did not respond in time. Retry with the same code."),
                    "tls_failed"=>T("Не удалось проверить защищённое соединение. Проверьте дату и время Windows и обновления сертификатов.","Could not verify the secure connection. Check the Windows date, time and certificate updates."),
                    "rate_limited"=>T("Слишком много запросов. Подождите минуту и повторите попытку.","Too many requests. Wait a minute and retry."),
                    "service_unavailable"=>T("Сервер активации временно недоступен. Повторите попытку позже.","The activation server is temporarily unavailable. Retry later."),
                    "invalid_response"=>T("Ответ сервера не прошёл проверку. Проверьте дату и время Windows и версию приложения.","The server response could not be verified. Check the Windows date, time and app version."),
                    "system-failed"=>T("Локальная служба не смогла выполнить действие. Требуется диагностика службы и сохранённых данных.","The local service could not complete the action. Service and stored data diagnostics are required."),
                    "awg-engine-missing"=>T("Компонент AWG отсутствует. Нужен полный установщик.","The AWG component is missing. Use the complete installer."),
                    "tcp-engine-missing"=>T("Компонент TCP отсутствует. Нужен полный установщик.","The TCP component is missing. Use the complete installer."),
                    _=>T("Действие не выполнено. Проверьте сеть; если данные повреждены, требуется восстановление.","Could not complete the action. Check the network; damaged data requires recovery.") };
                return;
            }
            if(request.Action=="friends-referral")
            {
                if(reply.Code is null||!System.Text.RegularExpressions.Regex.IsMatch(reply.Code,@"\Ahttps://185\.251\.89\.19:8443/invite/#[0-9a-f]{64}\z"))throw new FormatException();
                link.Text=reply.Code;
            }
            if(request.Action=="friends-activate")invitation.Clear();
            status.Text=success;
        }
        catch(OperationCanceledException){status.Text=T("Служба Windows не ответила за 35 секунд. Повторите попытку; если ошибка повторяется, перезапустите приложение.","The Windows service did not respond within 35 seconds. Retry; if this persists, restart the app.");}
        catch(Exception){status.Text=T("Нет связи со службой FamilyConnectBroker. Повторно запустите установщик приложения.","Cannot communicate with FamilyConnectBroker. Run the app installer again.");}
        finally
        {
            busy=false;activate.Enabled=connect.Enabled=share.Enabled=true;
            copy.Enabled=link.Text.Length>0;invitation.Enabled=region.Enabled=transport.Enabled=true;
        }
    }
    internal static void CheckUi()
    {
        foreach(bool ru in new[]{false,true})
        {
            var requests=new List<Request>();
            using var form=new FriendsForm(ru, r=>{requests.Add(r);return Task.FromResult(new Reply(true,"off",Code:r.Action=="friends-referral"?"https://185.251.89.19:8443/invite/#"+new string('a',64):null));});
            form.Show();Application.DoEvents();
            void Pump(Task task) { var until=DateTime.UtcNow.AddSeconds(5);while(!task.IsCompleted&&DateTime.UtcNow<until){Application.DoEvents();Thread.Sleep(5);}task.GetAwaiter().GetResult(); }
            form.invitation.Text="FC-disposable-ui-test";
            form.activate.PerformClick();Application.DoEvents();
            if(requests.Count!=1||requests[0].Action!="friends-activate")throw new Exception("Activation click not dispatched");
            if(form.invitation.Text.Length!=0)throw new Exception("Invitation retained after success");
            if(form.status.Top<form.activate.Bottom||form.status.Bottom>form.region.Top||form.status.Width>form.ClientSize.Width)
                throw new Exception("Activation result not visible beside action");
            if(ru){using var bitmap=new Bitmap(form.Width,form.Height);form.DrawToBitmap(bitmap,new Rectangle(0,0,form.Width,form.Height));bitmap.Save(Path.Combine(Path.GetTempPath(),"Windows-invitation.png"));}
            Pump(form.Run(new("friends-referral"),"ok"));
            if(!form.copy.Enabled||!form.link.ReadOnly||!form.link.Text.EndsWith(new string('a',64)))throw new Exception("Invitation sharing UI failed");
            Pump(form.Run(new("friends-connect-tcp-ru"),"ok"));
            if(requests.Count!=3||requests[2].Action!="friends-connect-tcp-ru")throw new Exception("Wrong Friends action");
            form.transport.SelectedIndex=1;form.region.SelectedIndex=0;form.connect.PerformClick();Application.DoEvents();
            if(requests.Count!=4||requests[3].Action!="friends-connect-awg-nl")throw new Exception("Wrong AWG Friends action");
            form.Close();
        }
        using var denied=new FriendsForm(true,_=>Task.FromResult(new Reply(false,"off",Error:"access_rejected")));
        denied.Show();Application.DoEvents();denied.invitation.Text="keep-for-correction";
        var failure=denied.Run(new("friends-activate",denied.invitation.Text),"wrong-success");
        while(!failure.IsCompleted){Application.DoEvents();Thread.Sleep(5);}failure.GetAwaiter().GetResult();
        if(denied.invitation.Text.Length==0||denied.status.Text=="wrong-success"||!denied.activate.Enabled)throw new Exception("Failed activation UI state");
        denied.Close();
        using var unavailable=new FriendsForm(true,_=>Task.FromException<Reply>(new IOException()));
        unavailable.Show();Application.DoEvents();unavailable.invitation.Text="keep-for-retry";
        unavailable.activate.PerformClick();Application.DoEvents();
        if(!unavailable.status.Text.Contains("FamilyConnectBroker")||unavailable.invitation.Text!="keep-for-retry"||!unavailable.activate.Enabled)
            throw new Exception("Local broker failure not explained");
        unavailable.Close();
    }

}
