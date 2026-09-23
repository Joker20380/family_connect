using System.Drawing.Drawing2D;
using System.Runtime.InteropServices;
namespace FamilyConnect;

internal sealed class TerminalDial : Button
{
    readonly System.Windows.Forms.Timer motion=new(){Interval=50};
    bool connected,pending,russian;float phase;
    static readonly Color Mint=Color.FromArgb(112,244,198),Amber=Color.FromArgb(255,173,70);
    [DllImport("user32.dll")]static extern bool SystemParametersInfo(uint action,uint parameter,out int value,uint flags);
    static bool AnimationsEnabled()=>SystemParametersInfo(0x1042,0,out int value,0)&&value!=0;
    internal TerminalDial()
    {
        SetStyle(ControlStyles.UserPaint|ControlStyles.AllPaintingInWmPaint|ControlStyles.OptimizedDoubleBuffer,true);
        Height=230;Dock=DockStyle.Top;FlatStyle=FlatStyle.Flat;FlatAppearance.BorderSize=0;Cursor=Cursors.Hand;
        BackColor=Color.FromArgb(7,32,24);
        motion.Tick+=(_,_)=>{if(!AnimationsEnabled()){motion.Stop();return;}phase=(float)(Environment.TickCount64%9000)/9000*360;Invalidate();};
    }
    internal void UpdateState(bool on,bool working,bool ru,bool enabled)
    {
        bool changed=connected!=on||pending!=working||russian!=ru||Enabled!=enabled;
        connected=on;pending=working;russian=ru;Enabled=enabled;
        AccessibleName=ru?(on?"Отключить":"Подключить"):(on?"Disconnect":"Connect");
        motion.Enabled=Visible&&(connected||pending)&&AnimationsEnabled();if(changed)Invalidate();
    }
    protected override void OnVisibleChanged(EventArgs e){base.OnVisibleChanged(e);if(!Disposing)motion.Enabled=Visible&&(connected||pending)&&AnimationsEnabled();}
    protected override void Dispose(bool disposing){if(disposing)motion.Dispose();base.Dispose(disposing);}
    protected override void OnSizeChanged(EventArgs e)
    {
        base.OnSizeChanged(e);float size=Math.Min(Width,Height)*.96f;
        using var circle=new GraphicsPath();circle.AddEllipse((Width-size)/2,(Height-size)/2,size,size);
        var old=Region;Region=new Region(circle);old?.Dispose();
    }
    protected override void OnPaint(PaintEventArgs e)
    {
        var g=e.Graphics;g.Clear(BackColor);g.SmoothingMode=SmoothingMode.AntiAlias;
        float d=DeviceDpi/96f,x=Width/2f,y=Height/2f,r=Math.Min(Width,Height)*.385f,p=connected||pending?phase:0;
        if(r<4)return;Color accent=connected?Mint:Amber;
        Color Ink(Color color,int alpha=255)=>Color.FromArgb(Enabled?alpha:alpha/2,color);
        void Arc(float radius,float start,float sweep,float width,Color color,int alpha=255)
        {using var pen=new Pen(Ink(color,alpha),width);g.DrawArc(pen,x-radius,y-radius,radius*2,radius*2,start,sweep);}
        foreach(var (ratio,width,alpha) in new[]{(1.18f,.6f,85),(1.08f,.5f,110),(.72f,.65f,170),(.67f,.4f,55)})Arc(r*ratio,0,360,width*d,accent,alpha);
        for(int i=0;i<120;i++)
        {
            float a=i*MathF.Tau/120,outer=i%5==0?.86f:.825f;
            using var pen=new Pen(Ink(accent,i%5==0?175:85),.6f*d);
            g.DrawLine(pen,x+MathF.Sin(a)*r*.78f,y-MathF.Cos(a)*r*.78f,x+MathF.Sin(a)*r*outer,y-MathF.Cos(a)*r*outer);
        }
        for(int i=0;i<4;i++)
        {
            var saved=g.Save();g.TranslateTransform(x,y);g.RotateTransform(i*90);
            using var pen=new Pen(Ink(accent,160),.6f*d);g.DrawLine(pen,-r*1.25f,0,-r*1.02f,0);g.DrawLine(pen,-r*.76f,0,-r*.64f,0);g.Restore(saved);
        }
        for(int i=0;i<64;i++)
        {
            bool lit=connected||(pending&&(i-(int)(p/5.625f)+64)%64<19);var color=accent;
            if(lit)Arc(r,-90+i*5.625f,4.3f,r*.15f,color,20);
            Arc(r,-90+i*5.625f,4.3f,r*.105f,color,lit?230:pending?40:65);
        }
        for(int i=0;i<3;i++)Arc(r*1.18f,p+i*119+14,1.8f,2*d,accent,connected||pending?240:100);
        Arc(r*.72f,-90-p*.4f,94,.85f*d,accent,160);
        if(Focused||Capture)Arc(r*1.11f,0,360,1.4f*d,accent);
        float ly=y-r*.30f,lw=r*.19f;
        using(var pen=new Pen(Ink(accent),Math.Max(d,r*.026f)))
        {
            g.DrawArc(pen,x-lw*.63f,ly-lw*1.15f,lw*1.26f,lw*1.35f,180,180);
            g.DrawLine(pen,x+lw*.63f,ly-lw*.475f,x+lw*.63f,ly+lw*.08f);
            g.DrawLine(pen,x-lw*.63f,ly-lw*.475f,x-lw*.63f,connected?ly+lw*.08f:ly-lw*.25f);
        }
        using(var ink=new SolidBrush(Ink(accent)))g.FillRectangle(ink,x-lw,ly,lw*2,lw*1.15f);
        using(var dark=new SolidBrush(BackColor)){g.FillEllipse(dark,x-r*.033f,ly+lw*.43f-r*.033f,r*.066f,r*.066f);g.FillRectangle(dark,x-r*.016f,ly+lw*.43f,r*.032f,lw*.41f);}
        void TextAt(string text,float size,float baseline,Color color,bool bold=false)
        {
            using var font=new Font("Consolas",size,bold?FontStyle.Bold:FontStyle.Regular,GraphicsUnit.Pixel);
            using var brush=new SolidBrush(Ink(color));using var format=new StringFormat{Alignment=StringAlignment.Center};
            g.DrawString(text,font,brush,new PointF(x,baseline-size),format);
        }
        TextAt(connected?"ON":pending?"…":"OFF",Math.Min(30*d,r*.29f),y+r*.20f,accent,true);
        TextAt(russian?(connected?"ОТКЛЮЧИТЬ":"ПОДКЛЮЧИТЬ"):(connected?"DISCONNECT":"CONNECT"),Math.Min(11*d,r*.115f),y+r*.39f,accent);
    }
}
