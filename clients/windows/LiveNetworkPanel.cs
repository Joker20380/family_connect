using System.Drawing.Drawing2D;
using System.Net.NetworkInformation;
namespace FamilyConnect;

// The connection selectors share the same information panel as Android.
internal sealed class LiveNetworkPanel : UserControl
{
    readonly ComboBox country,protocol;
    readonly System.Windows.Forms.Timer timer=new(){Interval=1000};
    readonly Queue<float> history=new();
    long previousTime,rx,tx;string? adapter;
    string network="—",battery="—",rate="—",state="—";bool ru;
    internal LiveNetworkPanel(ComboBox country,ComboBox protocol,bool sample){
        this.country=country;this.protocol=protocol;DoubleBuffered=true;ResizeRedraw=true;Height=174;Dock=DockStyle.Top;
        BackColor=Color.FromArgb(7,32,24);ForeColor=Color.FromArgb(152,247,216);
        Controls.Add(country);Controls.Add(protocol);country.Dock=protocol.Dock=DockStyle.None;
        timer.Tick+=(_,_)=>Sample();timer.Enabled=sample;
        SizeChanged+=(_,_)=>Place();Place();
    }
    protected override void OnLayout(LayoutEventArgs e){base.OnLayout(e);Place();}
    protected override void OnDpiChangedAfterParent(EventArgs e){base.OnDpiChangedAfterParent(e);Place();}
    int D(int n)=>(int)Math.Round(n*DeviceDpi/96f);
    void Place(){
        if(country is null||protocol is null)return;
        int x=Width/2+D(10),w=Math.Max(1,Width-x-D(12));
        country.SetBounds(x,D(78),w,country.Height);protocol.SetBounds(x,D(114),w,protocol.Height);
    }
    internal void Connection(bool russian,string status){ru=russian;state=status;Invalidate();}
    void Sample(){
        try{
            var power=SystemInformation.PowerStatus;
            battery=(power.BatteryChargeStatus&BatteryChargeStatus.NoSystemBattery)!=0||power.BatteryLifePercent<0?"—":$"{power.BatteryLifePercent*100:F0}%";
            var interfaces=NetworkInterface.GetAllNetworkInterfaces().Where(n=>n.OperationalStatus==OperationalStatus.Up&&n.NetworkInterfaceType!=NetworkInterfaceType.Loopback);
            var current=interfaces.OrderBy(n=>n.Name.StartsWith("fcawg")||n.Name.StartsWith("fctcp")?0:n.NetworkInterfaceType==NetworkInterfaceType.Wireless80211?1:2).FirstOrDefault();
            if(current is null){network="—";adapter=null;previousTime=0;rate="—";history.Clear();Invalidate();return;}
            network=current.Name.StartsWith("fcawg")||current.Name.StartsWith("fctcp")?"VPN":current.NetworkInterfaceType==NetworkInterfaceType.Wireless80211?"Wi-Fi":"Ethernet";
            var counters=current.GetIPStatistics();long now=Environment.TickCount64;
            if(adapter==current.Id&&previousTime>0&&now>previousTime&&counters.BytesReceived>=rx&&counters.BytesSent>=tx){
                float down=(counters.BytesReceived-rx)*1000f/(now-previousTime)/1024,up=(counters.BytesSent-tx)*1000f/(now-previousTime)/1024;
                rate=$"↓ {down:F1} ↑ {up:F1} KiB/s";history.Enqueue(down+up);while(history.Count>48)history.Dequeue();
            }else{rate="—";history.Clear();}
            adapter=current.Id;previousTime=now;rx=counters.BytesReceived;tx=counters.BytesSent;
        }catch(NetworkInformationException){rate="—";previousTime=0;history.Clear();}
        Invalidate();
    }
    protected override void OnPaint(PaintEventArgs e){
        base.OnPaint(e);var g=e.Graphics;g.SmoothingMode=SmoothingMode.AntiAlias;
        float scale=DeviceDpi/96f;
        using var outline=new Pen(Color.FromArgb(67,142,121),scale);
        using var frame=ModernButton.Cut(new RectangleF(1,1,Width-3,Height-3),10*scale);g.DrawPath(outline,frame);
        using var small=new Font("Consolas",9*scale,FontStyle.Regular,GraphicsUnit.Pixel);
        using var normal=new Font("Consolas",14*scale,FontStyle.Regular,GraphicsUnit.Pixel);
        void Text(string value,int x,int y,int width,Font font,Color color)=>TextRenderer.DrawText(g,value,font,new Rectangle(x,D(y),width,D(24)),color,TextFormatFlags.EndEllipsis|TextFormatFlags.NoPadding);
        int split=Width/2,left=D(12);var muted=Color.FromArgb(153,196,181);
        Text(ru?"СЕТЬ":"NETWORK",left,12,split-D(20),small,muted);Text(ru?"БАТАРЕЯ":"BATTERY",split+D(10),12,split-D(22),small,muted);
        Text(network,left,32,split-D(20),normal,ForeColor);Text(battery,split+D(10),32,split-D(22),normal,Color.FromArgb(255,173,70));
        Text(ru?"СЕТЕВОЙ ТРАФИК":"NETWORK TRAFFIC",left,64,split-D(20),small,muted);
        Text(ru?"СОЕДИНЕНИЕ":"CONNECTION",split+D(10),64,split-D(22),small,muted);Text(rate,left,84,split-D(20),small,ForeColor);
        Text(state,split+D(10),151,split-D(22),small,muted);
        g.DrawLine(outline,split,D(61),split,Height-D(10));
        float top=D(110),bottom=Height-D(12),right=split-D(12);
        for(int i=0;i<4;i++){float y=top+(bottom-top)*i/3;g.DrawLine(outline,left,y,right,y);}
        var values=history.ToArray();float max=values.Length>0?Math.Max(1,values.Max()):1;
        using var graph=new Pen(ForeColor,1.5f);
        if(values.Length>1)g.DrawLines(graph,values.Select((v,i)=>new PointF(right-(values.Length-1-i)*(right-left)/47,bottom-v/max*(bottom-top))).ToArray());
    }
    protected override void Dispose(bool disposing){if(disposing)timer.Dispose();base.Dispose(disposing);}
}
