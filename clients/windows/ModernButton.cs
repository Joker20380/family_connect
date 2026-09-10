using System.Drawing.Drawing2D;
namespace FamilyConnect;
// Retains native Button keyboard, accessibility, sizing and click behavior.
internal sealed class ModernButton : Button
{
    bool hovered,pressed;
    public ModernButton(){DoubleBuffered=true;FlatStyle=FlatStyle.Flat;FlatAppearance.BorderSize=0;
        FlatAppearance.MouseOverBackColor=Color.FromArgb(49,62,87);FlatAppearance.MouseDownBackColor=Color.FromArgb(59,73,98);Cursor=Cursors.Hand;}
    internal static GraphicsPath Rounded(RectangleF rect,float radius){
        float diameter=Math.Min(radius*2,Math.Min(rect.Width,rect.Height));
        var path=new GraphicsPath();
        if(diameter<=0)return path;
        path.AddArc(rect.Left,rect.Top,diameter,diameter,180,90);
        path.AddArc(rect.Right-diameter,rect.Top,diameter,diameter,270,90);
        path.AddArc(rect.Right-diameter,rect.Bottom-diameter,diameter,diameter,0,90);
        path.AddArc(rect.Left,rect.Bottom-diameter,diameter,diameter,90,90);path.CloseFigure();return path;
    }
    protected override void OnMouseEnter(EventArgs e){hovered=true;Invalidate();base.OnMouseEnter(e);}
    protected override void OnMouseLeave(EventArgs e){hovered=false;pressed=false;Invalidate();base.OnMouseLeave(e);}
    protected override void OnMouseDown(MouseEventArgs e){pressed=true;Invalidate();base.OnMouseDown(e);}
    protected override void OnMouseUp(MouseEventArgs e){pressed=false;Invalidate();base.OnMouseUp(e);}
    protected override void OnPaint(PaintEventArgs e)
    {
        e.Graphics.Clear(Parent?.BackColor??BackColor);
        e.Graphics.SmoothingMode=SmoothingMode.AntiAlias;
        float inset=2,diameter=Math.Min(24*DeviceDpi/96f,Math.Min(Width,Height)-4);
        var rect=new RectangleF(inset,inset,Width-2*inset-1,Height-2*inset-1);
        if(rect.Width<=diameter||rect.Height<=diameter)return;
        using var path=Rounded(rect,diameter/2);
        Color fill=!Enabled?Color.FromArgb(38,50,81):pressed?FlatAppearance.MouseDownBackColor:hovered?FlatAppearance.MouseOverBackColor:BackColor;
        using var brush=new SolidBrush(fill);e.Graphics.FillPath(brush,path);
        if(Focused&&ShowFocusCues){using var pen=new Pen(Color.FromArgb(199,210,254),2);e.Graphics.DrawPath(pen,path);}
        TextRenderer.DrawText(e.Graphics,Text,Font,Rectangle.Inflate(ClientRectangle,-8,-4),Enabled?ForeColor:Color.FromArgb(156,170,202),TextFormatFlags.HorizontalCenter|TextFormatFlags.VerticalCenter|TextFormatFlags.WordBreak);
    }
}
