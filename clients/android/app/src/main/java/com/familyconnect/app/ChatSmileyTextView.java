package com.familyconnect.app;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.ColorFilter;
import android.graphics.Movie;
import android.graphics.PixelFormat;
import android.graphics.Rect;
import android.graphics.RectF;
import android.graphics.drawable.Drawable;
import android.os.SystemClock;
import android.text.SpannableString;
import android.text.Spanned;
import android.text.style.ImageSpan;
import android.util.AttributeSet;
import android.widget.TextView;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.List;

/** Display-only prototype. Pass original plain text to Store/transport, not this View.
 * Built-in verified assets only; no GIF attachments, remote URLs or writable packs.
 */
@SuppressWarnings("deprecation") // Movie supports minSdk26; native runtime validation pending.
public final class ChatSmileyTextView extends TextView {
    private final List<Gif> images=new ArrayList<>();
    private final Rect visible=new Rect();
    private boolean foreground,queued;
    private long time,previous;
    private final Runnable frame=()->{
        queued=false;
        if(eligible())invalidate();
        else previous=0;
    };
    public ChatSmileyTextView(Context context){super(context);}
    public ChatSmileyTextView(Context context,AttributeSet attrs){super(context,attrs);}

    /** Must be called on UI thread when binding/recycling a message. */
    public void setMessage(String original) {
        // Validate before replacing the previous visible message.
        List<ChatSmileys.Match> matches=ChatSmileys.find(original);
        stopFrames();images.clear();time=0;
        SpannableString text=new SpannableString(original);
        int height=Math.max(16,Math.min(96,Math.round(getTextSize()*1.4f)));
        for(ChatSmileys.Match match:matches) {
            if(images.size()==8)break; // Remaining tokens remain readable plain text.
            try {
                byte[] bytes=readAsset(ChatSmileys.FACES.get(match.index).asset);
                Movie movie=Movie.decodeByteArray(bytes,0,bytes.length);
                if(movie==null||movie.width()<1||movie.height()<1||movie.width()>64||movie.height()>64)continue;
                Gif gif=new Gif(movie);
                gif.setBounds(0,0,Math.max(1,height*movie.width()/movie.height()),height);
                images.add(gif);
                text.setSpan(new ImageSpan(gif,ImageSpan.ALIGN_BASELINE),match.start,match.end,Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
            } catch(java.io.IOException|IllegalArgumentException failure) {
                // Keep signed text visible; no asset path or message content logging.
            }
        }
        setText(text,BufferType.SPANNABLE);
        // Screen readers retain the literal message, including fallback tokens.
        setContentDescription(original);
        invalidate();
    }
    private byte[] readAsset(String name) throws java.io.IOException {
        try(InputStream in=getContext().getAssets().open("chat/icq-classic/"+name);
                ByteArrayOutputStream out=new ByteArrayOutputStream()) {
            byte[] buffer=new byte[1024];int count;
            while((count=in.read(buffer))!=-1) {
                if(out.size()+count>32768)throw new java.io.IOException("Invalid built-in smiley");
                out.write(buffer,0,count);
            }
            return out.toByteArray();
        }
    }
    /** Owner forwards Activity foreground state; default false means static frame. */
    public void setForegroundActive(boolean active) {
        foreground=active;
        if(!active)stopFrames();
        invalidate();
    }
    /** Explicit release for a recycled/offscreen message. */
    public void clearMessage(){stopFrames();images.clear();time=0;setText("");setContentDescription(null);}
    private boolean eligible() {
        return foreground&&!images.isEmpty()&&isAttachedToWindow()&&hasWindowFocus()
            &&getWindowVisibility()==VISIBLE&&isShown()&&getGlobalVisibleRect(visible);
    }
    private void stopFrames(){removeCallbacks(frame);queued=false;previous=0;}
    @Override protected void onDraw(Canvas canvas) {
        boolean animate=eligible();
        if(animate) {
            long now=SystemClock.uptimeMillis();
            if(previous!=0)time+=Math.min(100,Math.max(0,now-previous));
            previous=now;
        } else previous=0;
        super.onDraw(canvas);
        if(animate&&!queued){queued=true;postDelayed(frame,40);}
        else if(!animate)stopFrames();
    }
    @Override protected void onVisibilityChanged(android.view.View changed,int visibility) {
        super.onVisibilityChanged(changed,visibility);
        if(visibility!=VISIBLE&&frame!=null)stopFrames();
    }
    @Override protected void onDetachedFromWindow(){stopFrames();super.onDetachedFromWindow();}
    @Override public void onWindowFocusChanged(boolean focus){super.onWindowFocusChanged(focus);if(!focus)stopFrames();else invalidate();}
    @Override protected void onWindowVisibilityChanged(int visibility){super.onWindowVisibilityChanged(visibility);if(visibility!=VISIBLE&&frame!=null)stopFrames();}
    private final class Gif extends Drawable {
        final Movie movie;int opacity=255;
        Gif(Movie movie){this.movie=movie;}
        @Override public void draw(Canvas canvas) {
            Rect bounds=getBounds();int save=canvas.saveLayerAlpha(new RectF(bounds),opacity);
            canvas.translate(bounds.left,bounds.top);
            canvas.scale(bounds.width()/(float)movie.width(),bounds.height()/(float)movie.height());
            movie.setTime((int)(time%Math.max(1,movie.duration())));movie.draw(canvas,0,0);
            canvas.restoreToCount(save);
        }
        @Override public void setAlpha(int alpha){opacity=Math.max(0,Math.min(255,alpha));invalidateSelf();}
        @Override public void setColorFilter(ColorFilter filter){} // Original GIF palette.
        @Override public int getOpacity(){return PixelFormat.TRANSLUCENT;}
    }
}
