namespace FamilyConnect;

// Buffer the layout surfaces themselves: a buffered Form does not buffer its
// separate child windows. Paint background and contents in the same frame.
internal sealed class BufferedPanel : Panel
{
    internal BufferedPanel(){
        SetStyle(ControlStyles.UserPaint|ControlStyles.AllPaintingInWmPaint|ControlStyles.OptimizedDoubleBuffer,true);
        BackColor=Color.FromArgb(3,17,14);
    }
}
internal sealed class BufferedLayoutPanel : TableLayoutPanel
{
    internal BufferedLayoutPanel(){
        SetStyle(ControlStyles.UserPaint|ControlStyles.AllPaintingInWmPaint|ControlStyles.OptimizedDoubleBuffer,true);
        BackColor=Color.FromArgb(3,17,14);
    }
}
