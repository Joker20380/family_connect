namespace FamilyConnect;

// First Friends onboarding screen; existing operator activation remains available.
internal sealed class FriendsForm : Form
{
    readonly bool ru;
    readonly Func<Request, Task<Reply>> call;
    readonly TextBox invitation = new(), link = new();
    readonly ComboBox region = new() { DropDownStyle = ComboBoxStyle.DropDownList };
    readonly Label status = new();
    readonly Button activate = new ModernButton(), connect = new ModernButton(), share = new ModernButton(), copy = new ModernButton();
    bool busy;
    string T(string r, string e) => ru ? r : e;
    internal FriendsForm(bool russian, Func<Request,Task<Reply>>? caller = null)
    {
        ru = russian; call = caller ?? Wire.Call;
        AutoScaleMode=AutoScaleMode.Dpi;AutoScaleDimensions=new SizeF(96,96);
        Text=T("Доступ по приглашению", "Invitation access");StartPosition=FormStartPosition.CenterParent;
        ClientSize=new(440,570);MinimumSize=new(340,360);Font=new Font("Segoe UI",10);
        BackColor=Color.FromArgb(4,24,21);ForeColor=Color.FromArgb(205,242,229);
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
        region.Items.AddRange(new object[]{T("Нидерланды", "Netherlands"),T("Россия", "Russia")});region.SelectedIndex=0;Add(region);
        Add(new Label { Text=T("Подключение через TCP. AWG 3.1 для этого экрана ещё не готов.","TCP connection. AWG 3.1 is not available on this screen yet."),AutoSize=true });
        connect.Text=T("Подключиться", "Connect");Add(connect);
        share.Text=T("Получить ссылку для друга", "Get invitation link");Add(share);
        link.ReadOnly=true;link.Multiline=true;link.Height=76;link.ScrollBars=ScrollBars.Vertical;Add(link);
        copy.Text=T("Скопировать ссылку", "Copy link");copy.Enabled=false;Add(copy);
        status.AutoSize=true;Add(status);
        foreach(var button in new[]{activate,connect,share,copy})
        {
            button.AutoSize=true;button.MinimumSize=new(0,42);button.FlatStyle=FlatStyle.Flat;
            button.BackColor=Color.FromArgb(12,48,40);button.ForeColor=ForeColor;
        }
        activate.Click+=async(_,_)=>await Run(new("friends-activate",invitation.Text.Trim()),T("Доступ активирован. Можно подключаться.","Access activated. You can connect."));
        connect.Click+=async(_,_)=>await Run(new(region.SelectedIndex==1?"friends-connect-tcp-ru":"friends-connect-tcp-nl"),T("Подключение запущено. Состояние видно в главном окне.","Connection started. Check its status in the main window."));
        share.Click+=async(_,_)=>await Run(new("friends-referral"),T("Ссылка готова. Отправьте её другу.","Link ready. Send it to your friend."));
        copy.Click+=(_,_)=>{if(link.Text.Length>0){Clipboard.SetText(link.Text);status.Text=T("Ссылка скопирована.","Link copied.");}};
        FormClosing+=(_,e)=>{if(busy)e.Cancel=true;};
    }
    async Task Run(Request request,string success)
    {
        if(busy)return;busy=true;
        foreach(var b in new[]{activate,connect,share,copy})b.Enabled=false;
        invitation.Enabled=region.Enabled=false;status.Text=T("Подождите…", "Please wait…");
        try
        {
            var reply=await call(request);
            if(!reply.Ok)
            {
                status.Text=reply.Error switch {
                    "disconnect-first" or "busy"=>T("Сначала отключите VPN в главном окне.","Disconnect VPN in the main window first."),
                    "invalid_invitation"=>T("Проверьте формат кода приглашения.","Check the invitation code format."),
                    "access_rejected"=>T("Сервер отклонил доступ. Проверьте приглашение.","The server rejected access. Check the invitation."),
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
        catch(Exception){status.Text=T("Служба недоступна или ответ некорректен. Повторите попытку.","The service is unavailable or its response is invalid. Retry.");}
        finally
        {
            busy=false;activate.Enabled=connect.Enabled=share.Enabled=true;
            copy.Enabled=link.Text.Length>0;invitation.Enabled=region.Enabled=true;
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
            Pump(form.Run(new("friends-activate",form.invitation.Text),"ok"));
            if(form.invitation.Text.Length!=0)throw new Exception("Invitation retained after success");
            Pump(form.Run(new("friends-referral"),"ok"));
            if(!form.copy.Enabled||!form.link.ReadOnly||!form.link.Text.EndsWith(new string('a',64)))throw new Exception("Invitation sharing UI failed");
            Pump(form.Run(new("friends-connect-tcp-ru"),"ok"));
            if(requests.Count!=3||requests[2].Action!="friends-connect-tcp-ru")throw new Exception("Wrong Friends action");
            form.Close();
        }
        using var denied=new FriendsForm(true,_=>Task.FromResult(new Reply(false,"off",Error:"access_rejected")));
        denied.Show();Application.DoEvents();denied.invitation.Text="keep-for-correction";
        var failure=denied.Run(new("friends-activate",denied.invitation.Text),"wrong-success");
        while(!failure.IsCompleted){Application.DoEvents();Thread.Sleep(5);}failure.GetAwaiter().GetResult();
        if(denied.invitation.Text.Length==0||denied.status.Text=="wrong-success"||!denied.activate.Enabled)throw new Exception("Failed activation UI state");
        denied.Close();
    }

}
