using System.Drawing.Drawing2D;
namespace FamilyConnect;

internal sealed class TerminalHeader : Control
{
    internal TerminalHeader() { DoubleBuffered=true;Height=78;MinimumSize=new(240,78);BackColor=Color.FromArgb(3,17,14); }
    protected override void OnPaint(PaintEventArgs e)
    {
        var g=e.Graphics;g.Clear(BackColor);g.SmoothingMode=SmoothingMode.AntiAlias;
        float scale=DeviceDpi/96f;
        using var border=new Pen(Color.FromArgb(67,142,121),scale);
        using var frame=ModernButton.Cut(new RectangleF(1,1,Width-3,Height-3),12*scale);g.DrawPath(border,frame);
        var saved=g.Save();g.TranslateTransform(17*scale,15*scale);g.ScaleTransform(.48f*scale,.48f*scale);
        void Polygon(Color color,PointF[] points){using var brush=new SolidBrush(color);g.FillPolygon(brush,points);}
        using(var logo=new GraphicsPath(FillMode.Alternate))
        {
            logo.AddPolygon(new PointF[]{new(50,3),new(90,25),new(90,77),new(50,99),new(10,77),new(10,25)});
            logo.AddPolygon(new PointF[]{new(50,12),new(18,30),new(18,73),new(50,91),new(82,73),new(82,30)});
            using var brush=new SolidBrush(Color.FromArgb(152,247,216));g.FillPath(brush,logo);
        }
        Polygon(Color.FromArgb(141,235,205),new PointF[]{new(23,36),new(50,20),new(50,99),new(23,81)});
        Polygon(Color.FromArgb(193,255,233),new PointF[]{new(55,50),new(60,50),new(60,65),new(55,65)});
        Polygon(Color.FromArgb(37,94,78),new PointF[]{new(50,12),new(82,30),new(82,36),new(50,19)});g.Restore(saved);
        using var font=new Font("Consolas",(Width/scale>=350?19:16)*scale,FontStyle.Regular,GraphicsUnit.Pixel);
        using var small=new Font("Consolas",9*scale,FontStyle.Regular,GraphicsUnit.Pixel);
        using var text=new SolidBrush(Color.FromArgb(218,255,242));using var mint=new SolidBrush(Color.FromArgb(152,247,216));
        g.DrawString("family_connect",font,text,77*scale,17*scale);
        g.DrawString("SECURE NETWORK TERMINAL",small,mint,78*scale,44*scale);
        using var faint=new Pen(Color.FromArgb(55,67,142,121),scale);
        g.DrawLine(faint,78*scale,40*scale,205*scale,40*scale);g.DrawLine(faint,78*scale,60*scale,205*scale,60*scale);
        using var amber=new Pen(Color.FromArgb(255,173,70),3*scale);
        for(int y=28;y<=46;y+=9)g.DrawLine(amber,8*scale,y*scale,8*scale,(y+5)*scale);
    }
}
