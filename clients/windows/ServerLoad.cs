using System.Net.Http;
using System.Text.Json;
namespace FamilyConnect;
internal sealed record LoadSample(string Country,double Observed,double Cpu,double Rx,double Tx,double? Percent,bool Estimated)
{
    internal bool Fresh=>FreshAt(DateTimeOffset.UtcNow.ToUnixTimeSeconds());
    internal bool FreshAt(double now)=>now-Observed is >=-15 and <=45;
}
internal static class ServerLoad
{
    static readonly HttpClient http=new(new HttpClientHandler{AllowAutoRedirect=false}){Timeout=TimeSpan.FromSeconds(5),MaxResponseContentBufferSize=8192};
    internal static string? Country(string? endpoint)=>endpoint switch{"185.251.89.19"=>"ru","186.246.45.246"=>"nl",_=>null};
    internal static LoadSample Parse(string raw,string country,double now)
    {
        if(raw.Length>8192||country is not ("ru" or "nl"))throw new FormatException();
        using var doc=JsonDocument.Parse(raw);var root=doc.RootElement;
        if(root.GetProperty("schema").GetInt32()!=1)throw new FormatException();
        var o=root.GetProperty("gateways").GetProperty(country);
        if(o.GetProperty("country").GetString()!=country)throw new FormatException();
        double Number(string name,double min=0,double max=1e12){var e=o.GetProperty(name);if(e.ValueKind!=JsonValueKind.Number)throw new FormatException();double n=e.GetDouble();if(!double.IsFinite(n)||n<min||n>max)throw new FormatException();return n;}
        double at=Number("observed_at"),cpu=Number("cpu_percent",0,100),rx=Number("rx_mbps"),tx=Number("tx_mbps");
        string? direction=o.TryGetProperty("capacity_direction",out var d)?d.GetString():"duplex";
        if(direction is not ("duplex" or "egress"))throw new FormatException();
        double? percent=null;if(o.TryGetProperty("capacity_mbps",out var cap)&&cap.ValueKind!=JsonValueKind.Null)
            percent=Math.Min(100,Math.Max(cpu,100*(direction=="egress"?tx:Math.Max(rx,tx))/Number("capacity_mbps",.001,1e9)));
        bool estimated=o.TryGetProperty("capacity_basis",out var b)&&b.GetString()=="provider-default-estimate";
        var result=new LoadSample(country,at,cpu,rx,tx,percent,estimated);if(!result.FreshAt(now))throw new FormatException();return result;
    }
    internal static async Task<LoadSample> Fetch(string country)=>Parse(await http.GetStringAsync("https://185.251.89.19:8443/status/server-load.json"),country,DateTimeOffset.UtcNow.ToUnixTimeSeconds());
    internal static async Task<Dictionary<string,LoadSample>> FetchAll()
    {
        var raw=await http.GetStringAsync("https://185.251.89.19:8443/status/server-load.json");
        var now=DateTimeOffset.UtcNow.ToUnixTimeSeconds();
        using var doc=JsonDocument.Parse(raw);var root=doc.RootElement;
        if(root.GetProperty("schema").GetInt32()!=1)throw new FormatException();
        var result=new Dictionary<string,LoadSample>();
        foreach(var country in new[]{"ru","nl"})
            if(root.GetProperty("gateways").TryGetProperty(country,out _))
                try{result[country]=Parse(raw,country,now);}catch(FormatException){}
        if(result.Count==0)throw new FormatException();
        return result;
    }
    internal static void Check()
    {
        const string json="""{"schema":1,"gateways":{"nl":{"country":"nl","observed_at":1000,"cpu_percent":30,"rx_mbps":900,"tx_mbps":100,"capacity_mbps":200,"capacity_direction":"egress","capacity_basis":"provider-default-estimate"}}}""";
        var s=Parse(json,"nl",1010);if(s.Percent!=50||!s.Estimated)throw new Exception("Load calculation");
        if(Parse(json.Replace("\"capacity_mbps\":200","\"capacity_mbps\":null"),"nl",1010).Percent is not null)throw new Exception("Unknown capacity");
        foreach(var now in new[]{1046d,980d}){bool rejected=false;try{Parse(json,"nl",now);}catch(FormatException){rejected=true;}if(!rejected)throw new Exception("Stale load accepted");}
        if(Country("127.0.0.1") is not null)throw new Exception("Unknown server mapped");
    }
}
internal sealed class LoadBar:Control
{
    internal double? Percent;
    public LoadBar(){DoubleBuffered=true;ResizeRedraw=true;Height=8;Dock=DockStyle.Fill;Margin=new Padding(0,4,0,8);AccessibleRole=AccessibleRole.ProgressBar;}
    protected override void OnPaint(PaintEventArgs e){base.OnPaint(e);using var border=new Pen(Color.FromArgb(67,142,121));e.Graphics.DrawRectangle(border,0,0,Math.Max(0,Width-1),Math.Max(0,Height-1));if(Percent is double p){using var fill=new SolidBrush(p>=90?Color.FromArgb(239,132,116):p>=70?Color.FromArgb(255,173,70):Color.FromArgb(152,247,216));e.Graphics.FillRectangle(fill,1,1,(int)((Width-2)*Math.Clamp(p,0,100)/100),Math.Max(0,Height-2));}}
}
