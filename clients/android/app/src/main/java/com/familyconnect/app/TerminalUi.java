package com.familyconnect.app;

import android.app.Activity;
import android.content.Context;
import android.content.res.ColorStateList;
import android.graphics.*;
import android.graphics.drawable.*;
import android.view.*;
import android.widget.*;

/** Terminal presentation; animation follows view visibility and real connection state. */
final class TerminalUi {
    static final int BACKGROUND = 0xff071211, SURFACE = 0xff102321, FRAME = 0xff416861;
    static final int SWITCH_ON = 0xffa8dfce, SWITCH_OFF = 0xffdbb674;
    static final int TEXT = 0xffe2eee8, MUTED = 0xffa4bab2, MINT = 0xffa8dfce, AMBER = 0xffdbb674;
    static final float STROKE_FINE=.5f, STROKE_DETAIL=.65f, STROKE_FRAME=1f;
    static float stroke(Context context,float width){return Math.max(.5f,width*context.getResources().getDisplayMetrics().density);}

    static int dp(Context context, int value) { return Math.round(value * context.getResources().getDisplayMetrics().density); }

    static String version(Context context) {
        try { return context.getPackageManager().getPackageInfo(context.getPackageName(),0).versionName; }
        catch (android.content.pm.PackageManager.NameNotFoundException impossible) { return ""; }
    }

    /** Shared viewport with independently scrollable workspaces. */
    static LinearLayout dashboard(Activity activity) {
        activity.getWindow().setStatusBarColor(BACKGROUND);activity.getWindow().setNavigationBarColor(BACKGROUND);
        activity.getWindow().getDecorView().setSystemUiVisibility(0);
        LinearLayout root=new DashboardLayout(activity);root.setOrientation(LinearLayout.VERTICAL);root.setBackground(new Grid(activity));
        int p=dp(activity,12);root.setPadding(p,dp(activity,8),p,dp(activity,8));
        install(activity,root);return root;
    }

    static void install(Activity activity,View root){
        int left=root.getPaddingLeft(),top=root.getPaddingTop(),right=root.getPaddingRight(),bottom=root.getPaddingBottom();
        if(android.os.Build.VERSION.SDK_INT>=35)root.setOnApplyWindowInsetsListener((view,insets)->{
            Insets bars=insets.getInsets(WindowInsets.Type.systemBars()|WindowInsets.Type.displayCutout()|WindowInsets.Type.ime());
            View navigation=root.findViewWithTag("exit_navigation");if(navigation!=null&&activity instanceof ChatActivity)navigation.setVisibility(insets.isVisible(WindowInsets.Type.ime())?View.GONE:View.VISIBLE);
            root.setPadding(left+bars.left,top+bars.top,right+bars.right,bottom+bars.bottom);return insets;
        });
        root.addOnLayoutChangeListener((view,newLeft,newTop,newRight,newBottom,oldLeft,oldTop,oldRight,oldBottom)->{
            if(root instanceof ViewGroup){ViewGroup group=(ViewGroup)root;if(group.getChildCount()>0&&group.getChildAt(0) instanceof BrandHeader){View header=group.getChildAt(0);int available=root.getHeight()-root.getPaddingTop()-root.getPaddingBottom();boolean compact=available<dp(activity,420)||(activity.getResources().getConfiguration().fontScale>=1.3f&&available<dp(activity,560));int visibility=compact?View.GONE:View.VISIBLE;if(header.getVisibility()!=visibility)root.post(()->header.setVisibility(visibility));}}
        });
        activity.setContentView(root);root.requestApplyInsets();enter(root);
    }

    static void enter(View view) {
        if (!android.animation.ValueAnimator.areAnimatorsEnabled() || !view.getContext().getSharedPreferences(FriendsActivity.class.getName(),Context.MODE_PRIVATE).getBoolean("motion",true)) return;
        view.setAlpha(.72f);view.setTranslationY(dp(view.getContext(),3));
        view.animate().alpha(1).translationY(0).setDuration(140).start();
        view.addOnAttachStateChangeListener(new View.OnAttachStateChangeListener(){
            public void onViewAttachedToWindow(View target){}
            public void onViewDetachedFromWindow(View target){target.animate().cancel();target.setAlpha(1);target.setTranslationY(0);}
        });
    }

    /** Keep navigation reachable while the workspace adapts to actual viewport pixels. */
    private static final class DashboardLayout extends LinearLayout {
        private LinearLayout panel,body;
        private Dial dial;
        private View workspace,map;
        private ScrollView scroll;
        DashboardLayout(Context context){super(context);}
        void compact(LinearLayout panel,Dial dial,View workspace,View map){
            this.panel=panel;this.dial=dial;this.workspace=workspace;this.map=map;
            View header=getChildAt(0),footer=getChildAt(getChildCount()-1);
            removeAllViews();addView(header);
            body=new LinearLayout(getContext());body.setOrientation(VERTICAL);body.setTag("ui60_body");
            panel.setTag("home_connection");dial.setTag("ui60_dial");workspace.setTag("home_workspace");map.setTag("home_map");
            body.addView(panel,new LayoutParams(-1,-2));
            LayoutParams network=new LayoutParams(-1,LiveNetworkPanel.minimumHeight(getContext()));network.topMargin=dp(getContext(),8);body.addView(workspace,network);
            LayoutParams preview=new LayoutParams(-1,0);preview.topMargin=dp(getContext(),8);body.addView(map,preview);
            scroll=new ScrollView(getContext());scroll.setFillViewport(false);scroll.addView(body,new ScrollView.LayoutParams(-1,-2));
            addView(scroll,new LayoutParams(-1,0,1));addView(footer);
        }
        @Override protected void onMeasure(int widthSpec,int heightSpec){
            if(dial==null){super.onMeasure(widthSpec,heightSpec);return;}
            int width=MeasureSpec.getSize(widthSpec)-getPaddingLeft()-getPaddingRight();
            LiveNetworkPanel network=(LiveNetworkPanel)((ViewGroup)workspace).getChildAt(0);
            LayoutParams networkParams=(LayoutParams)workspace.getLayoutParams();networkParams.height=network.requiredHeight(width,0);
            LayoutParams dialParams=(LayoutParams)dial.getLayoutParams();dialParams.weight=0;dialParams.height=Ui60Presentation.dialHeight(width-panel.getPaddingLeft()-panel.getPaddingRight(),MeasureSpec.getSize(heightSpec),dp(getContext(),120));
            LayoutParams mapParams=(LayoutParams)map.getLayoutParams();mapParams.height=0;map.setVisibility(GONE);
            panel.forceLayout();dial.forceLayout();body.forceLayout();scroll.forceLayout();
            super.onMeasure(widthSpec,heightSpec);
            int free=scroll.getMeasuredHeight()-panel.getMeasuredHeight()-workspace.getMeasuredHeight()-dp(getContext(),16);
            int preview=((RouteMapView)map).compactHeight(width),deficit=Math.max(0,preview-free);
            int compactNetwork=network.requiredHeight(width,deficit);
            deficit=Math.max(0,deficit-(networkParams.height-compactNetwork));networkParams.height=compactNetwork;
            dialParams.height=Ui60Presentation.compactDialHeight(dialParams.height,dp(getContext(),120),deficit);
            mapParams.height=preview;map.setVisibility(VISIBLE);
            panel.forceLayout();dial.forceLayout();workspace.forceLayout();body.forceLayout();scroll.forceLayout();super.onMeasure(widthSpec,heightSpec);
        }
    }
    static void compactDashboardDial(LinearLayout root,LinearLayout panel,Dial dial,View workspace,View map){((DashboardLayout)root).compact(panel,dial,workspace,map);}

    static void dashboardHeader(LinearLayout root) {
        root.addView(new BrandHeader(root.getContext()),new LinearLayout.LayoutParams(-1,dp(root.getContext(),72)));
    }

    private static final class BrandHeader extends View {
        private final Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG);
        private final Drawable mark;
        BrandHeader(Context context){super(context);mark=context.getDrawable(R.drawable.ic_brand);setBackground(frame(context,BACKGROUND,FRAME));setContentDescription("EXIT · Personal communications");}
        @Override protected void onDraw(Canvas canvas){
            float d=getResources().getDisplayMetrics().density,w=getWidth(),h=getHeight();
            if(w<220*d){paint.setTypeface(Typeface.MONOSPACE);paint.setColor(TEXT);paint.setTextSize(18*getResources().getDisplayMetrics().scaledDensity);canvas.drawText("EXIT",(w-paint.measureText("EXIT"))/2,(h-paint.ascent()-paint.descent())/2,paint);return;}
            if(h<60*d){
                int size=dp(getContext(),30);mark.setBounds(dp(getContext(),12),(getHeight()-size)/2,dp(getContext(),12)+size,(getHeight()+size)/2);mark.draw(canvas);
                paint.setTypeface(Typeface.MONOSPACE);paint.setColor(TEXT);paint.setTextSize(23*getResources().getDisplayMetrics().scaledDensity);
                canvas.drawText("EXIT",54*d,(h-paint.ascent()-paint.descent())/2,paint);return;
            }
            int logo=dp(getContext(),46);int x=dp(getContext(),19),y=(getHeight()-logo)/2;
            mark.setBounds(x,y,x+logo,y+logo);mark.draw(canvas);
            paint.setColor(AMBER);for(int i=0;i<3;i++)canvas.drawRect(7*d,h/2-10*d+i*7*d,11*d,h/2-6*d+i*7*d,paint);
            float left=76*d,available=w-left-14*d;
            paint.setTypeface(Typeface.create(Typeface.MONOSPACE,Typeface.NORMAL));paint.setTextSize(27*d);paint.setTextScaleX(1);
            paint.setTextSize(32*d);paint.setColor(TEXT);
            canvas.drawText("EXIT",left,h*.49f,paint);
            paint.setTypeface(Typeface.MONOSPACE);paint.setTextScaleX(1);paint.setTextSize(9*d);paint.setColor(MINT);
            String sub="PERSONAL COMMUNICATIONS";paint.setTextSize(Math.min(9*d,paint.getTextSize()*available/paint.measureText(sub)));
            canvas.drawText(sub,left,h*.73f,paint);
            float ruleWidth=paint.measureText(sub);paint.setStrokeWidth(stroke(getContext(),STROKE_FINE));paint.setColor(0x38438e79);
            canvas.drawLine(left,h*.55f,left+ruleWidth,h*.55f,paint);canvas.drawLine(left,h*.81f,left+ruleWidth,h*.81f,paint);
        }
    }

    static TextView compactLabel(LinearLayout root,String value,int size,int color) {
        TextView text=new TextView(root.getContext());textStyle(text,size,color);text.setIncludeFontPadding(false);text.setText(value);
        text.setPadding(0,dp(root.getContext(),5),0,dp(root.getContext(),5));
        root.addView(text,new LinearLayout.LayoutParams(-1,-2));return text;
    }

    static LinearLayout dashboardPanel(LinearLayout root,float weight) {
        Context c=root.getContext();LinearLayout panel=new LinearLayout(c);panel.setOrientation(LinearLayout.VERTICAL);
        panel.setPadding(dp(c,10),dp(c,6),dp(c,10),dp(c,10));panel.setBackground(frame(c,SURFACE,FRAME));
        root.addView(panel,new LinearLayout.LayoutParams(-1,0,weight));return panel;
    }

    static Button dashboardButton(LinearLayout root,int title,Runnable action) {
        Context c=root.getContext();Button button=new Button(c);textStyle(button,14,TEXT);button.setAllCaps(false);button.setText(title);
        button.setMaxLines(2);button.setIncludeFontPadding(false);button.setMinHeight(0);button.setMinimumHeight(0);
        button.setPadding(dp(c,10),0,dp(c,10),0);
        button.setBackground(new RippleDrawable(ColorStateList.valueOf(0x4470f4c6),frame(c,SURFACE,FRAME),null));
        button.setOnClickListener(v->action.run());LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(-1,dp(c,52));p.topMargin=dp(c,7);root.addView(button,p);return button;
    }

    static void navigation(LinearLayout root,Runnable status,Runnable chats,Runnable route,Runnable settings) { navigation(root,0,status,chats,route,settings); }
    static void navigation(LinearLayout root,int selected,Runnable status,Runnable chats,Runnable route,Runnable settings) {
        Context c=root.getContext();LinearLayout row=new LinearLayout(c);row.setTag("exit_navigation");
        int[] names={R.string.dashboard_status,R.string.dashboard_chats,R.string.dashboard_route_short,R.string.dashboard_settings_short};
        Runnable[] actions={status,chats,route,settings};
        for(int i=0;i<4;i++) {
            final Runnable action=actions[i];Button button=new Button(c);textStyle(button,10,i==selected?AMBER:MUTED);
            button.setText(names[i]);button.setSelected(i==selected);button.setAllCaps(false);button.setMaxLines(2);button.setMinHeight(dp(c,58));button.setIncludeFontPadding(false);
            button.setPadding(dp(c,2),dp(c,5),dp(c,2),dp(c,4));button.setMinWidth(0);button.setMinimumWidth(0);
            button.setBackground(new RippleDrawable(ColorStateList.valueOf(0x4470f4c6),frame(c,i==selected?SURFACE:BACKGROUND,i==selected?AMBER:FRAME),null));
            Drawable icon=new NavIcon(c,i,i==selected?AMBER:MINT);icon.setBounds(0,0,dp(c,21),dp(c,21));button.setCompoundDrawables(null,icon,null,null);
            button.setOnClickListener(v->action.run());row.addView(button,new LinearLayout.LayoutParams(0,-1,1));
        }
        root.addView(row,new LinearLayout.LayoutParams(-1,-2));
    }

    static void actionStyle(Button button) {
        Context c=button.getContext();textStyle(button,14,MINT);button.setAllCaps(false);button.setMinHeight(dp(c,48));
        button.setTextColor(new ColorStateList(new int[][]{new int[]{-android.R.attr.state_enabled},new int[]{}},new int[]{MUTED,MINT}));
        button.setBackground(new RippleDrawable(ColorStateList.valueOf(0x4470f4c6),frame(c,SURFACE,FRAME),null));
        button.setPadding(dp(c,12),dp(c,6),dp(c,12),dp(c,6));
    }

    static void dialog(Activity activity,int title,View content) {
        TextView heading=new TextView(activity);textStyle(heading,19,AMBER);heading.setText(title);
        int p=dp(activity,18);heading.setPadding(p,p,p,dp(activity,10));
        android.app.AlertDialog dialog=new android.app.AlertDialog.Builder(activity)
            .setCustomTitle(heading).setView(content).setPositiveButton(android.R.string.ok,null).create();
        dialog.show();dialog.getWindow().setBackgroundDrawable(frame(activity,BACKGROUND,FRAME));
        textStyle(dialog.getButton(android.content.DialogInterface.BUTTON_POSITIVE),14,AMBER);
    }

    private static final class NavIcon extends Drawable {
        private final Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG);private final Path path=new Path();private final int kind,color;
        NavIcon(Context c,int kind,int color){this.kind=kind;this.color=color;}
        @Override public void draw(Canvas c){
            c.save();Rect b=getBounds();c.translate(b.left,b.top);c.scale(b.width()/24f,b.height()/24f);
            paint.setColor(color);paint.setStrokeWidth(1.3f);paint.setStyle(Paint.Style.STROKE);
            if(kind==0){path.reset();path.moveTo(1,13);path.lineTo(6,13);path.lineTo(9,4);path.lineTo(13,21);path.lineTo(16,10);path.lineTo(19,13);path.lineTo(23,13);c.drawPath(path,paint);}
            else if(kind==1){c.drawRoundRect(2,3,22,18,2,2,paint);c.drawLine(6,18,6,23,paint);c.drawLine(6,23,12,18,paint);}
            else if(kind==2){c.drawCircle(12,4,3,paint);c.drawCircle(4,20,3,paint);c.drawCircle(20,20,3,paint);c.drawLine(12,7,4,17,paint);c.drawLine(12,7,20,17,paint);}
            else {c.drawCircle(12,12,6,paint);c.drawCircle(12,12,2,paint);for(int i=0;i<8;i++){c.save();c.rotate(i*45,12,12);c.drawLine(12,2,12,6,paint);c.restore();}}
            c.restore();
        }
        @Override public void setAlpha(int alpha){} @Override public void setColorFilter(ColorFilter filter){} @Override public int getOpacity(){return PixelFormat.TRANSLUCENT;}
    }

    static void goTab(Activity activity,int tab) {
        if(activity instanceof FriendsActivity){((FriendsActivity)activity).navigate(tab);return;}
        if(tab==1&&activity instanceof ChatActivity)return;
        android.content.Intent intent=new android.content.Intent(activity,tab==1?ChatActivity.class:FriendsActivity.class);
        intent.addFlags(android.content.Intent.FLAG_ACTIVITY_REORDER_TO_FRONT|android.content.Intent.FLAG_ACTIVITY_SINGLE_TOP);intent.putExtra("tab",tab);activity.startActivity(intent);
    }
    static void tabs(LinearLayout root,Activity activity,int selected){navigation(root,selected,()->goTab(activity,0),()->goTab(activity,1),()->goTab(activity,2),()->goTab(activity,3));}

    static LinearLayout screen(Activity activity, String subtitle) {
        LinearLayout root=dashboard(activity);dashboardHeader(root);
        ScrollView scroll=new ScrollView(activity);scroll.setFillViewport(true);
        LinearLayout column=new LinearLayout(activity);column.setOrientation(LinearLayout.VERTICAL);
        int p=dp(activity,4);column.setPadding(p,dp(activity,10),p,dp(activity,12));scroll.addView(column,new ScrollView.LayoutParams(-1,-2));
        root.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
        TextView title=label(column,subtitle,14,MINT);title.setGravity(Gravity.START);
        // The managed technical launcher has no Friends activity in its manifest.
        if(activity.getPackageName().endsWith(".friends"))tabs(root,activity,activity instanceof ChatActivity?1:3);
        return column;
    }

    static LinearLayout section(LinearLayout parent, String title) {
        Context context = parent.getContext();
        LinearLayout panel = new LinearLayout(context); panel.setOrientation(LinearLayout.VERTICAL);
        panel.setPadding(dp(context, 16), dp(context, 12), dp(context, 16), dp(context, 16));
        panel.setBackground(frame(context, SURFACE, FRAME));
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(-1, -2); params.bottomMargin = dp(context, 12);
        parent.addView(panel, params);
        if (title != null) {
            TextView label = label(panel, title, 13, MINT);
            label.setTypeface(Typeface.MONOSPACE);label.setGravity(Gravity.START); label.setLetterSpacing(.04f);
        }
        return panel;
    }

    static void textStyle(TextView view, int size, int color) {
        view.setTextSize(size); view.setTextColor(color); view.setTypeface(Typeface.create("sans-serif",Typeface.NORMAL));
        view.setIncludeFontPadding(true);
    }

    static TextView label(LinearLayout parent, String text, int size, int color) {
        TextView view = new TextView(parent.getContext()); textStyle(view, size, color);
        view.setText(text); view.setGravity(Gravity.START); view.setLineSpacing(dp(view.getContext(), 3), 1);
        view.setPadding(0, dp(view.getContext(), 7), 0, dp(view.getContext(), 7));
        parent.addView(view, new LinearLayout.LayoutParams(-1, -2)); return view;
    }

    static Button button(LinearLayout parent, int resource, Runnable action) {
        Button button = new Button(parent.getContext()); button.setText(resource); button.setAllCaps(false);
        textStyle(button, 15, MINT); button.setLetterSpacing(.03f);
        ColorStateList text = new ColorStateList(new int[][]{new int[]{-android.R.attr.state_enabled}, new int[]{}}, new int[]{0xff66867a, MINT});
        button.setTextColor(text);
        StateListDrawable surfaces = new StateListDrawable();
        surfaces.addState(new int[]{-android.R.attr.state_enabled}, frame(parent.getContext(), BACKGROUND, 0xff25483d));
        surfaces.addState(new int[]{}, frame(parent.getContext(), 0xff102e24, MINT));
        button.setBackground(new RippleDrawable(ColorStateList.valueOf(0x4470f4c6), surfaces, null));
        button.setMinHeight(dp(parent.getContext(), 54));
        button.setPadding(dp(parent.getContext(), 12), dp(parent.getContext(), 12), dp(parent.getContext(), 12), dp(parent.getContext(), 12));
        button.setOnClickListener(v -> action.run());
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(-1, -2); params.topMargin = dp(parent.getContext(), 10);
        parent.addView(button, params); return button;
    }

    static final class InlineLabel extends TextView {
        InlineLabel(Context context){super(context);setMaxLines(3);setHorizontallyScrolling(false);}
        void label(CharSequence value){setText(value);setContentDescription(value);}
    }
    static void inlinePicker(Spinner spinner,String[] items){
        Context c=spinner.getContext();
        spinner.setAdapter(new ArrayAdapter<String>(c,android.R.layout.simple_spinner_dropdown_item,items){
            @Override public View getView(int position,View recycled,ViewGroup parent){
                InlineLabel text=new InlineLabel(c);
                textStyle(text,12,MINT);text.label(items[position]+" ▾");
                text.setEllipsize(android.text.TextUtils.TruncateAt.END);text.setMinHeight(Math.max(dp(c,48),(int)Math.ceil(text.getPaint().getFontMetrics().bottom-text.getPaint().getFontMetrics().top)));text.setPadding(0,0,0,0);text.setGravity(Gravity.CENTER_VERTICAL);text.setBackgroundColor(Color.TRANSPARENT);return text;
            }
            @Override public View getDropDownView(int position,View recycled,ViewGroup parent){
                TextView text=(TextView)super.getDropDownView(position,recycled instanceof InlineLabel?null:recycled,parent);textStyle(text,14,TEXT);
                text.setMinHeight(dp(c,48));text.setPadding(dp(c,12),dp(c,8),dp(c,12),dp(c,8));text.setGravity(Gravity.CENTER_VERTICAL);return text;
            }
        });
        spinner.setBackgroundColor(Color.TRANSPARENT);spinner.setPadding(0,0,0,0);
        spinner.setPopupBackgroundDrawable(frame(c,SURFACE,FRAME));
    }

    static void picker(Spinner spinner, String[] items) {
        Context context = spinner.getContext();
        spinner.setAdapter(new ArrayAdapter<String>(context, android.R.layout.simple_spinner_dropdown_item, items) {
            private View style(View view) {
                TextView text = (TextView) view; textStyle(text, 15, TEXT);
                text.setSingleLine(false); text.setMaxLines(3); text.setBackgroundColor(Color.TRANSPARENT);
                text.setMinHeight(dp(context, 52)); text.setGravity(Gravity.CENTER_VERTICAL);
                text.setPadding(dp(context, 12), dp(context, 10), dp(context, 12), dp(context, 10));
                return text;
            }
            @Override public View getView(int position, View view, ViewGroup parent) {
                TextView selected = (TextView) style(super.getView(position, view, parent));
                selected.append("  ▾"); return selected;
            }
            @Override public View getDropDownView(int position, View view, ViewGroup parent) { return style(super.getDropDownView(position, view, parent)); }
        });
        spinner.setBackground(frame(context, SURFACE, FRAME));
        spinner.setPopupBackgroundDrawable(frame(context, SURFACE, FRAME));
    }

    static Drawable frame(Context context, int fill, int stroke) { return new TerminalFrame(context,fill,stroke); }
    static Drawable backdrop(Context context){return new Grid(context);}

    private static final class TerminalFrame extends Drawable {
        private final Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG);private final Path border=new Path();
        private final float d;private final int fill,stroke;
        TerminalFrame(Context c,int fill,int stroke){d=c.getResources().getDisplayMetrics().density;this.fill=fill;this.stroke=stroke;}
        @Override protected void onBoundsChange(Rect bounds){
            float left=bounds.left+d/2,top=bounds.top+d/2,right=bounds.right-d/2,bottom=bounds.bottom-d/2;
            border.reset();border.addRect(left,top,right,bottom,Path.Direction.CW);
        }
        @Override public void draw(Canvas canvas){
            Rect b=getBounds();canvas.save();canvas.clipPath(border);paint.setStyle(Paint.Style.FILL);paint.setColor(fill);canvas.drawRect(b,paint);
            canvas.restore();paint.setStyle(Paint.Style.STROKE);paint.setColor(stroke);paint.setStrokeWidth(Math.max(.5f,STROKE_FRAME*d));canvas.drawPath(border,paint);

        }
        @Override public void setAlpha(int alpha){paint.setAlpha(alpha);invalidateSelf();}
        @Override public void setColorFilter(ColorFilter filter){paint.setColorFilter(filter);invalidateSelf();}
        @Override public int getOpacity(){return PixelFormat.TRANSLUCENT;}
    }

    private static final class Grid extends Drawable {
        private final Paint paint = new Paint(); private final int step;
        Grid(Context context) { step = dp(context, 12); }
        @Override public void draw(Canvas canvas) {
            canvas.drawColor(BACKGROUND);
        }
        @Override public void setAlpha(int alpha) {}
        @Override public void setColorFilter(ColorFilter filter) {}
        @Override public int getOpacity() { return PixelFormat.OPAQUE; }
    }

    static final class Dial extends View {
        private final Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG);
        private final RectF oval=new RectF();
        private android.animation.ValueAnimator sweep;
        private float phase;
        private boolean motion=true;
        private String state="off",health="";
        Dial(Context context){super(context);setClickable(true);setFocusable(true);describe();}
        @Override public CharSequence getAccessibilityClassName(){return Button.class.getName();}
        private void describe(){setContentDescription(getContext().getString(state.equals("off")||state.equals("failed")?R.string.connect:state.equals("on")?R.string.disconnect:android.R.string.cancel));}
        void setMotion(boolean enabled){motion=enabled;animateState();invalidate();}
        private void animateState(){
            boolean run=motion&&android.animation.ValueAnimator.areAnimatorsEnabled()&&isAttachedToWindow()&&getWindowVisibility()==VISIBLE&&isShown()&&hasWindowFocus()&&!state.equals("off");
            if(run&&sweep==null){sweep=android.animation.ValueAnimator.ofFloat(0,360);sweep.setDuration(9000);sweep.setRepeatCount(-1);sweep.setInterpolator(new android.view.animation.LinearInterpolator());sweep.addUpdateListener(a->{phase=(float)a.getAnimatedValue();invalidate();});sweep.start();}
            else if(!run&&sweep!=null){sweep.cancel();sweep=null;phase=0;}
        }
        @Override protected void onAttachedToWindow(){super.onAttachedToWindow();animateState();}
        @Override protected void onDetachedFromWindow(){if(sweep!=null){sweep.cancel();sweep=null;}super.onDetachedFromWindow();}
        @Override protected void onWindowVisibilityChanged(int visibility){super.onWindowVisibilityChanged(visibility);animateState();}
        @Override protected void onVisibilityChanged(View view,int visibility){super.onVisibilityChanged(view,visibility);animateState();}
        @Override public void onWindowFocusChanged(boolean focus){super.onWindowFocusChanged(focus);animateState();}
        @Override protected void drawableStateChanged(){super.drawableStateChanged();invalidate();}
        @android.annotation.SuppressLint("ClickableViewAccessibility") // View dispatches native click/accessibility actions.
        @Override public boolean onTouchEvent(MotionEvent event){
            if(!"home_action".equals(getTag())&&event.getActionMasked()==MotionEvent.ACTION_DOWN&&Math.hypot(event.getX()-getWidth()/2f,event.getY()-getHeight()/2f)>Math.min(getWidth(),getHeight())*.47f)return false;
            return super.onTouchEvent(event);
        }
        @Override public boolean performClick(){return super.performClick();}
        void update(String state,String health){
            if(this.state.equals(state)&&this.health.equals(health))return;
            this.state=state;this.health=health;describe();animateState();invalidate();
        }
        private void ring(Canvas c,float x,float y,float r,float width,int color,int alpha){
            paint.setStyle(Paint.Style.STROKE);paint.setStrokeWidth(width);paint.setColor(color);paint.setAlpha(alpha);c.drawCircle(x,y,r,paint);
        }
        private void arc(Canvas c,float x,float y,float r,float from,float span,float width,int color,int alpha){
            oval.set(x-r,y-r,x+r,y+r);paint.setStyle(Paint.Style.STROKE);paint.setStrokeWidth(width);paint.setColor(color);paint.setAlpha(alpha);c.drawArc(oval,from,span,false,paint);
        }
        @Override protected void onDraw(Canvas canvas){
            super.onDraw(canvas);
            boolean home="home_action".equals(getTag());
            float captionSpace=home?17*getResources().getDisplayMetrics().scaledDensity+dp(getContext(),4):0;
            float x=getWidth()/2f,y=(getHeight()-captionSpace)/2f,r=Math.min(getWidth(),getHeight()-captionSpace)*.385f,d=getResources().getDisplayMetrics().density;
            if(r<4)return;
            boolean off=state.equals("off"),ready=state.equals("on")&&health.equals("ok");
            int accent=ready?SWITCH_ON:SWITCH_OFF;
            paint.setStyle(Paint.Style.FILL);paint.setShader(new RadialGradient(x,y,r*1.23f,new int[]{(accent&0x00ffffff)|(isPressed()?0x30000000:0x12000000),accent&0x00ffffff},null,Shader.TileMode.CLAMP));canvas.drawCircle(x,y,r*1.23f,paint);paint.setShader(null);
            ring(canvas,x,y,r*1.18f,.6f*d,accent,85);
            ring(canvas,x,y,r*1.08f,.5f*d,accent,110);
            ring(canvas,x,y,r*.72f,.65f*d,accent,170);
            ring(canvas,x,y,r*.67f,.4f*d,accent,55);
            paint.setStrokeCap(Paint.Cap.BUTT);
            // Fine inner ticks and crosshairs echo the reference, not a progress scale.
            for(int i=0;i<120;i++){
                canvas.save();canvas.rotate(i*3,x,y);paint.setColor(accent);paint.setAlpha(i%5==0?175:85);paint.setStrokeWidth(.6f*d);
                canvas.drawLine(x,y-r*.78f,x,y-r*(i%5==0?.86f:.825f),paint);canvas.restore();
            }
            for(int i=0;i<4;i++){
                canvas.save();canvas.rotate(i*90,x,y);paint.setColor(accent);paint.setAlpha(160);paint.setStrokeWidth(.6f*d);
                canvas.drawLine(x-r*1.25f,y,x-r*1.02f,y,paint);canvas.drawLine(x-r*.76f,y,x-r*.64f,y,paint);canvas.restore();
            }
            for(int i=0;i<64;i++){
                float start=-90+i*5.625f;
                boolean lit=ready||(!off&&((i-(int)(phase/5.625f)+64)%64)<19);
                int color=accent;
                int alpha=lit?230:off?65:40;
                if(lit)arc(canvas,x,y,r,start,4.3f,r*.15f,color,20);
                arc(canvas,x,y,r,start,4.3f,r*.105f,color,alpha);
            }
            // Sparse markers move slowly while connected/negotiating; no invented %.
            for(int i=0;i<3;i++){
                float angle=phase+i*119+14;
                arc(canvas,x,y,r*1.18f,angle,1.8f,2*d,accent,off?100:240);
            }
            arc(canvas,x,y,r*.72f,-90-phase*.4f,94,.85f*d,accent,160);
            if(isPressed()||isFocused())ring(canvas,x,y,r*1.11f,1.4f*d,accent,240);
            // Lock icon: the closed state is only shown for verified Internet health.
            float lockY=y-r*.30f,lockW=r*.19f;
            paint.setColor(accent);paint.setAlpha(isEnabled()?255:100);paint.setStyle(Paint.Style.STROKE);paint.setStrokeWidth(Math.max(d,r*.026f));
            oval.set(x-lockW*.63f,lockY-lockW*1.15f,x+lockW*.63f,lockY+lockW*.2f);
            canvas.drawArc(oval,180,180,false,paint);
            // The open shackle stays attached on the right; only the left leg lifts.
            canvas.drawLine(x+lockW*.63f,lockY-lockW*.475f,x+lockW*.63f,lockY+lockW*.08f,paint);
            canvas.drawLine(x-lockW*.63f,lockY-lockW*.475f,x-lockW*.63f,ready?lockY+lockW*.08f:lockY-lockW*.25f,paint);
            paint.setStyle(Paint.Style.FILL);canvas.drawRoundRect(x-lockW,lockY,x+lockW,lockY+lockW*1.15f,r*.025f,r*.025f,paint);
            paint.setColor(BACKGROUND);canvas.drawCircle(x,lockY+lockW*.43f,r*.033f,paint);canvas.drawRect(x-r*.016f,lockY+lockW*.43f,x+r*.016f,lockY+lockW*.84f,paint);
            paint.setStyle(Paint.Style.FILL);paint.setTypeface(Typeface.create(Typeface.MONOSPACE,Typeface.BOLD));paint.setTextAlign(Paint.Align.CENTER);paint.setColor(accent);paint.setAlpha(isEnabled()?255:110);
            paint.setTextSize(Math.min(30*d,r*.29f));canvas.drawText(off?"OFF":ready?"ON":"…",x,y+r*.20f,paint);
            String label=getContentDescription().toString().toUpperCase(java.util.Locale.ROOT);
            paint.setTypeface(Typeface.MONOSPACE);paint.setTextSize(home?14*getResources().getDisplayMetrics().scaledDensity:Math.min(11*d,r*.115f));
            if(!home)paint.setTextSize(Math.min(paint.getTextSize(),paint.getTextSize()*r*1.13f/Math.max(1,paint.measureText(label))));paint.setColor(accent);
            canvas.drawText(label,x,home?getHeight()-dp(getContext(),2)-paint.descent():y+r*.39f,paint);paint.setAlpha(255);
        }
    }
}
