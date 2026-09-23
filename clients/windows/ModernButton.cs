using System.Drawing.Drawing2D;
namespace FamilyConnect;
// Retains native Button keyboard, accessibility, sizing and click behavior.
internal sealed class ModernButton : Button
{
    bool hovered,pressed;
    [System.ComponentModel.DesignerSerializationVisibility(System.ComponentModel.DesignerSerializationVisibility.Hidden)]
    internal bool TerminalSwitch { get; set; }
    [System.ComponentModel.DesignerSerializationVisibility(System.ComponentModel.DesignerSerializationVisibility.Hidden)]
    internal bool SwitchOn { get; set; }
    [System.ComponentModel.DesignerSerializationVisibility(System.ComponentModel.DesignerSerializationVisibility.Hidden)]
    internal bool NavigationButton { get; set; }
    public ModernButton(){UseVisualStyleBackColor=false;DoubleBuffered=true;FlatStyle=FlatStyle.Flat;FlatAppearance.BorderSize=0;
        FlatAppearance.MouseOverBackColor=Color.FromArgb(16,61,46);FlatAppearance.MouseDownBackColor=Color.FromArgb(37,94,78);Cursor=Cursors.Hand;}
    internal static GraphicsPath Rounded(RectangleF rect,float radius){
        float diameter=Math.Min(radius*2,Math.Min(rect.Width,rect.Height));
        var path=new GraphicsPath();
        if(diameter<=0)return path;
        path.AddArc(rect.Left,rect.Top,diameter,diameter,180,90);
        path.AddArc(rect.Right-diameter,rect.Top,diameter,diameter,270,90);
        path.AddArc(rect.Right-diameter,rect.Bottom-diameter,diameter,diameter,0,90);
        path.AddArc(rect.Left,rect.Bottom-diameter,diameter,diameter,90,90);path.CloseFigure();return path;
    }
    internal static GraphicsPath Cut(RectangleF rect,float corner){
        float c=Math.Min(corner,Math.Min(rect.Width,rect.Height)/4);var path=new GraphicsPath();
        path.AddPolygon(new PointF[]{new(rect.Left+c,rect.Top),new(rect.Right-c,rect.Top),new(rect.Right,rect.Top+c),new(rect.Right,rect.Bottom-c),new(rect.Right-c,rect.Bottom),new(rect.Left+c,rect.Bottom),new(rect.Left,rect.Bottom-c),new(rect.Left,rect.Top+c)});return path;
    }
    protected override void OnMouseEnter(EventArgs e){hovered=true;Invalidate();base.OnMouseEnter(e);}
    protected override void OnMouseLeave(EventArgs e){hovered=false;pressed=false;Invalidate();base.OnMouseLeave(e);}
    protected override void OnMouseDown(MouseEventArgs e){pressed=true;Invalidate();base.OnMouseDown(e);}
    protected override void OnMouseUp(MouseEventArgs e){pressed=false;Invalidate();base.OnMouseUp(e);}
    protected override void OnKeyDown(KeyEventArgs e){if(e.KeyCode==Keys.Space){pressed=true;Invalidate();}base.OnKeyDown(e);}
    protected override void OnKeyUp(KeyEventArgs e){if(e.KeyCode==Keys.Space){pressed=false;Invalidate();}base.OnKeyUp(e);}
    protected override void OnLostFocus(EventArgs e){pressed=false;Invalidate();base.OnLostFocus(e);}
    protected override void OnPaint(PaintEventArgs e)
    {
        e.Graphics.Clear(Parent?.BackColor??BackColor);
        e.Graphics.SmoothingMode=SmoothingMode.AntiAlias;
        float inset=2,diameter=Math.Min(24*DeviceDpi/96f,Math.Min(Width,Height)-4);
        var rect=new RectangleF(inset,inset,Width-2*inset-1,Height-2*inset-1);
        if(rect.Width<=diameter||rect.Height<=diameter)return;
        using var path=Cut(rect,10*DeviceDpi/96f);
        Color fill=!Enabled?Color.FromArgb(12,37,29):pressed?FlatAppearance.MouseDownBackColor:hovered?FlatAppearance.MouseOverBackColor:BackColor;
        using var brush=new SolidBrush(fill);e.Graphics.FillPath(brush,path);
        using(var frame=new Pen(ForeColor==Color.FromArgb(255,173,70)?ForeColor:Color.FromArgb(67,142,121),1)){e.Graphics.DrawPath(frame,path);}
        if(Focused&&ShowFocusCues){using var pen=new Pen(Color.FromArgb(152,247,216),2);e.Graphics.DrawPath(pen,path);}
        var label=Rectangle.Inflate(ClientRectangle,NavigationButton?-2:-14,-4);
        if(NavigationButton){
            float scale=DeviceDpi/96f;var saved=e.Graphics.Save();
            e.Graphics.TranslateTransform(Width/2f-10*scale,8*scale);e.Graphics.ScaleTransform(scale,scale);
            using var icon=new Pen(ForeColor,1.1f);
            switch(Tag as string){
                case "status":e.Graphics.DrawLines(icon,new PointF[]{new(0,10),new(5,10),new(8,2),new(12,19),new(15,7),new(17,10),new(21,10)});break;
                case "messenger":e.Graphics.DrawLines(icon,new PointF[]{new(2,2),new(19,2),new(19,15),new(11,15),new(5,20),new(5,15),new(2,15),new(2,2)});break;
                case "route":
                    e.Graphics.DrawLine(icon,10,5,3,16);e.Graphics.DrawLine(icon,10,5,18,16);
                    foreach(var point in new[]{new Point(10,3),new Point(3,18),new Point(18,18)})e.Graphics.DrawEllipse(icon,point.X-2,point.Y-2,4,4);break;
                default:
                    e.Graphics.DrawEllipse(icon,5,5,11,11);e.Graphics.DrawEllipse(icon,8,8,5,5);
                    for(int i=0;i<8;i++){double a=i*Math.PI/4;e.Graphics.DrawLine(icon,10.5f+(float)Math.Cos(a)*7,10.5f+(float)Math.Sin(a)*7,10.5f+(float)Math.Cos(a)*10,10.5f+(float)Math.Sin(a)*10);}break;
            }
            e.Graphics.Restore(saved);label=new Rectangle(2,Height/2,Width-4,Height/2-4);
        }
        if(TerminalSwitch){
            float scale=DeviceDpi/96f;var pill=new RectangleF(Width-78*scale,Height/2f-13*scale,62*scale,26*scale);
            Color tint=!Enabled?Color.FromArgb(117,152,138):SwitchOn?Color.FromArgb(152,247,216):Color.FromArgb(255,173,70);
            using var outline=Rounded(pill,13*scale);using var pen=new Pen(tint,scale);using var knob=new SolidBrush(tint);
            e.Graphics.DrawPath(pen,outline);e.Graphics.FillEllipse(knob,pill.Left+(SwitchOn?38:4)*scale,pill.Top+3*scale,20*scale,20*scale);
            label.Width=Math.Max(1,label.Width-(int)(82*scale));
        }
        TextRenderer.DrawText(e.Graphics,Text,Font,label,Enabled?ForeColor:Color.FromArgb(117,152,138),(TerminalSwitch?TextFormatFlags.Left:TextFormatFlags.HorizontalCenter)|TextFormatFlags.VerticalCenter|TextFormatFlags.WordBreak|TextFormatFlags.NoPadding);

    }
}
