using System.Drawing.Drawing2D;
using System.Drawing.Imaging;
using System.Text.Json;
using System.Runtime.InteropServices;
namespace FamilyConnect;

// Same offline geography and physical-pixel stippling as Android beta25.
internal sealed class RouteMap : Control
{
    static readonly float[][][] land=LoadLand();
    readonly System.Windows.Forms.Timer animation=new(){Interval=50};
    Bitmap? dots;
    (int,int,int) cache;
    float phase;
    internal RouteMap()
    {
        DoubleBuffered=true;Height=200;Dock=DockStyle.Top;
        AccessibleName="World map";BackColor=Color.FromArgb(3,17,14);
        animation.Tick+=(_,_)=>{phase=(float)(Environment.TickCount64%5200)/5200;Invalidate();};
    }
    [DllImport("user32.dll", SetLastError=true)]
    static extern bool SystemParametersInfo(uint action,uint parameter,out int value,uint flags);
    static bool AnimationsEnabled()=>SystemParametersInfo(0x1042,0,out int enabled,0)&&enabled!=0;
    static float[][][] LoadLand()
    {
        using var stream=typeof(RouteMap).Assembly.GetManifestResourceStream("FamilyConnect.Land.json")!;
        return JsonSerializer.Deserialize<float[][][]>(stream)!;
    }
    protected override void OnVisibleChanged(EventArgs e)
    {
        base.OnVisibleChanged(e);
        animation.Enabled=Visible&&AnimationsEnabled();
        if(!animation.Enabled)phase=0;
    }
    protected override void Dispose(bool disposing)
    {
        if(disposing){animation.Dispose();dots?.Dispose();}base.Dispose(disposing);
    }
    Bitmap CreateDots(int w,int h,float scale)
    {
        using var path=new GraphicsPath(FillMode.Alternate);
        foreach(var ring in land)
            if(ring.Length>=3)path.AddPolygon(ring.Select(p=>new PointF((p[0]+180)/360*w,(85-p[1])/145*h)).ToArray());
        var layer=new Bitmap(w,h,PixelFormat.Format32bppArgb);
        using var g=Graphics.FromImage(layer);g.SmoothingMode=SmoothingMode.AntiAlias;g.PixelOffsetMode=PixelOffsetMode.Half;
        using var ink=new SolidBrush(Color.FromArgb(152,247,216));
        float diameter=Math.Max(1,(int)MathF.Floor(.65f*scale+.5f));
        float offset=(int)diameter%2==1?.5f:0,spacing=2.3f*scale,rowSpacing=spacing*.8660254f;
        for(int row=0;row*rowSpacing<h;row++)for(int col=0;col*spacing<w;col++)
        {
            float x=MathF.Floor((col+.5f*(row&1))*spacing-offset+.5f)+offset;
            float y=MathF.Floor(row*rowSpacing-offset+.5f)+offset;
            if(x>=0&&y>=0&&x<w&&y<h&&path.IsVisible(x,y))g.FillEllipse(ink,x-diameter/2,y-diameter/2,diameter,diameter);
        }
        return layer;
    }
    internal static void CheckPixels()
    {
        using var view=new RouteMap();
        foreach(int scale in new[]{1,2,3})
        {
            using var dots=view.CreateDots(360*scale,200*scale,scale);
            int peak=0;
            for(int y=0;y<dots.Height;y++)for(int x=0;x<dots.Width;x++)peak=Math.Max(peak,dots.GetPixel(x,y).A);
            if(peak<180)throw new Exception("Map dots blurred across physical pixels");
        }
    }
    protected override void OnPaint(PaintEventArgs e)
    {
        base.OnPaint(e);if(Width<1||Height<1)return;
        float scale=DeviceDpi/96f;var key=(Width,Height,DeviceDpi);
        if(dots is null||cache!=key){dots?.Dispose();dots=CreateDots(Width,Height,scale);cache=key;}
        var g=e.Graphics;var state=g.Save();g.SetClip(ClientRectangle);g.Clear(BackColor);
        g.SmoothingMode=SmoothingMode.AntiAlias;
        using var grid=new Pen(Color.FromArgb(45,70,139,117),.4f*scale);
        for(float x=0;x<Width;x+=16*scale)g.DrawLine(grid,x,0,x,Height);
        for(float y=0;y<Height;y+=16*scale)g.DrawLine(grid,0,y,Width,y);
        using var attributes=new ImageAttributes();
        var matrix=new ColorMatrix{Matrix33=(120+6*MathF.Sin(2*MathF.PI*phase))/255};attributes.SetColorMatrix(matrix);
        g.DrawImage(dots,ClientRectangle,0,0,Width,Height,GraphicsUnit.Pixel,attributes);
        using var border=new Pen(Color.FromArgb(70,139,117),scale);
        g.DrawRectangle(border,scale/2,scale/2,Math.Max(0,Width-scale),Math.Max(0,Height-scale));g.Restore(state);
    }
}
