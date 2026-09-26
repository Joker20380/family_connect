using System.Drawing.Drawing2D;
using System.Runtime.InteropServices;
namespace FamilyConnect;

// Keep native list navigation, keyboard selection and accessibility, paint the
// closed selector and every list row with the application's terminal palette.
internal sealed class ModernComboBox : ComboBox
{
    bool hovered;
    public ModernComboBox(){
        DropDownStyle=ComboBoxStyle.DropDownList;DrawMode=DrawMode.OwnerDrawFixed;
        FlatStyle=FlatStyle.Flat;ItemHeight=30;Cursor=Cursors.Hand;
        BackColor=Color.FromArgb(7,32,24);ForeColor=Color.FromArgb(218,255,242);
    }
    protected override void OnMouseEnter(EventArgs e){hovered=true;Invalidate();base.OnMouseEnter(e);}
    protected override void OnMouseLeave(EventArgs e){hovered=false;Invalidate();base.OnMouseLeave(e);}
    protected override void OnGotFocus(EventArgs e){base.OnGotFocus(e);Invalidate();}
    protected override void OnLostFocus(EventArgs e){base.OnLostFocus(e);Invalidate();}
    protected override void OnDropDown(EventArgs e){base.OnDropDown(e);Invalidate();}
    protected override void OnDropDownClosed(EventArgs e){base.OnDropDownClosed(e);Invalidate();}
    protected override void OnDrawItem(DrawItemEventArgs e){
        if(e.Index<0)return;
        bool selected=(e.State&DrawItemState.Selected)!=0;
        var tint=Color.FromArgb(152,247,216);
        using var fill=new SolidBrush(selected?Color.FromArgb(25,75,61):BackColor);
        e.Graphics.FillRectangle(fill,e.Bounds);
        int pad=(int)Math.Round(10*DeviceDpi/96f);
        var label=Rectangle.Inflate(e.Bounds,-pad,0);
        TextRenderer.DrawText(e.Graphics,GetItemText(Items[e.Index]),Font,label,Enabled?(selected?tint:ForeColor):Color.FromArgb(117,152,138),TextFormatFlags.Left|TextFormatFlags.VerticalCenter|TextFormatFlags.EndEllipsis|TextFormatFlags.NoPrefix);
        if(selected){using var marker=new SolidBrush(tint);e.Graphics.FillRectangle(marker,e.Bounds.Left,e.Bounds.Top,Math.Max(2,pad/3),e.Bounds.Height);}
        base.OnDrawItem(e);
    }
    [StructLayout(LayoutKind.Sequential)]
    struct PaintStruct {
        internal IntPtr Hdc;internal int Erase,Left,Top,Right,Bottom,Restore,IncUpdate;
        [MarshalAs(UnmanagedType.ByValArray,SizeConst=32)]internal byte[] Reserved;
    }
    [DllImport("user32.dll")]static extern IntPtr BeginPaint(IntPtr hwnd,out PaintStruct paint);
    [DllImport("user32.dll")]static extern bool EndPaint(IntPtr hwnd,ref PaintStruct paint);
    protected override void WndProc(ref Message m){
        if(m.Msg==0x0014){m.Result=(IntPtr)1;return;} // Background is part of the buffered frame.
        if(m.Msg==0x000F && IsHandleCreated){
            IntPtr dc=BeginPaint(Handle,out var paint);
            try{if(dc!=IntPtr.Zero && Width>0 && Height>0){
                using var target=Graphics.FromHdc(dc);
                using var buffer=BufferedGraphicsManager.Current.Allocate(target,ClientRectangle);
                PaintSelector(buffer.Graphics);buffer.Render(target);
            }}finally{EndPaint(Handle,ref paint);}
            m.Result=IntPtr.Zero;return;
        }
        if(m.Msg is 0x0317 or 0x0318 && m.WParam!=IntPtr.Zero){
            using var target=Graphics.FromHdc(m.WParam);PaintSelector(target);m.Result=IntPtr.Zero;return;
        }
        base.WndProc(ref m);
    }
    void PaintSelector(Graphics g){
        if(Width<4||Height<4)return;
        g.SmoothingMode=SmoothingMode.AntiAlias;
        // WM_PRINT may share a parent bitmap HDC: never clear outside this control.
        using(var background=new SolidBrush(Parent?.BackColor??BackColor))g.FillRectangle(background,ClientRectangle);
        float scale=DeviceDpi/96f;
        var tint=!Enabled?Color.FromArgb(117,152,138):Focused||hovered||DroppedDown?Color.FromArgb(152,247,216):Color.FromArgb(67,142,121);
        using var path=ModernButton.Cut(new RectangleF(1,1,Width-3,Height-3),6*scale);
        using var fill=new SolidBrush(DroppedDown||hovered?Color.FromArgb(16,61,46):BackColor);
        using var pen=new Pen(tint,scale);g.FillPath(fill,path);g.DrawPath(pen,path);
        int pad=(int)Math.Round(10*scale),arrow=(int)Math.Round(30*scale);
        TextRenderer.DrawText(g,Text,Font,new Rectangle(pad,1,Math.Max(1,Width-arrow-pad),Height-2),Enabled?ForeColor:Color.FromArgb(117,152,138),TextFormatFlags.Left|TextFormatFlags.VerticalCenter|TextFormatFlags.EndEllipsis|TextFormatFlags.NoPrefix);
        float x=Width-16*scale,y=Height/2f;float direction=DroppedDown?-1:1;
        g.DrawLines(pen,new PointF[]{new(x-4*scale,y-direction*2*scale),new(x,y+direction*2*scale),new(x+4*scale,y-direction*2*scale)});
    }
}
