package com.familyconnect.app;

import android.app.AlertDialog;
import android.content.Context;
import android.graphics.Typeface;
import android.view.Gravity;
import android.view.View;
import android.widget.*;
import com.google.gson.*;
import java.text.DateFormat;
import java.util.Date;
import java.util.function.Consumer;

/** Conversation viewport: updates never replace the composer or steal its selection. */
final class ChatThreadView extends LinearLayout {
    final EditText composer;
    final ScrollView history;
    private final LinearLayout messages;
    private boolean foreground=true;
    private AlertDialog smileyDialog;
    private String rendered="";
    private android.view.ViewTreeObserver.OnGlobalLayoutListener pendingScroll;
    private boolean revealLatest;
    Consumer<JsonObject> editMessage,playAudio;
    final VoiceHoldButton voice;
    private final Button faces,submit,cancelVoice;
    private final TextView recordingInfo;
    private long recordingMillis;
    ChatAudio audio;
    ChatThreadView(Context c,String draft,Consumer<String> changed,Consumer<String> send){
        super(c);setOrientation(VERTICAL);
        history=new ScrollView(c);history.setFillViewport(true);
        messages=new LinearLayout(c);messages.setOrientation(VERTICAL);messages.setPadding(0,TerminalUi.dp(c,8),0,TerminalUi.dp(c,8));
        history.addView(messages,new ScrollView.LayoutParams(-1,-2));addView(history,new LayoutParams(-1,0,1));
        LinearLayout row=new LinearLayout(c);row.setGravity(Gravity.BOTTOM);row.setPadding(0,TerminalUi.dp(c,6),0,TerminalUi.dp(c,6));
        faces=small(c,"☺",c.getString(R.string.chat_smileys));row.addView(faces,new LayoutParams(TerminalUi.dp(c,48),TerminalUi.dp(c,52)));
        cancelVoice=small(c,"×",c.getString(R.string.chat_voice_cancel));cancelVoice.setVisibility(GONE);row.addView(cancelVoice,new LayoutParams(TerminalUi.dp(c,48),TerminalUi.dp(c,52)));
        composer=new EditText(c);TerminalUi.textStyle(composer,16,TerminalUi.TEXT);composer.setTypeface(Typeface.create("sans-serif",Typeface.NORMAL));
        composer.setHint(R.string.chat_message_hint);composer.setHintTextColor(TerminalUi.MUTED);composer.setMinLines(1);composer.setMaxLines(4);
        composer.setInputType(android.text.InputType.TYPE_CLASS_TEXT|android.text.InputType.TYPE_TEXT_FLAG_MULTI_LINE|android.text.InputType.TYPE_TEXT_FLAG_CAP_SENTENCES);
        composer.setSaveEnabled(false);composer.setImportantForAutofill(View.IMPORTANT_FOR_AUTOFILL_NO);composer.setMinHeight(TerminalUi.dp(c,52));
        composer.setText(draft);composer.setSelection(composer.length());row.addView(composer,new LayoutParams(0,-2,1));
        recordingInfo=new TextView(c);TerminalUi.textStyle(recordingInfo,12,TerminalUi.MINT);recordingInfo.setGravity(Gravity.CENTER_VERTICAL);recordingInfo.setMinHeight(TerminalUi.dp(c,52));recordingInfo.setMaxLines(2);recordingInfo.setVisibility(GONE);row.addView(recordingInfo,new LayoutParams(0,-2,1));
        voice=new VoiceHoldButton(c);
        submit=small(c,"➤",c.getString(R.string.chat_send));row.addView(submit,new LayoutParams(TerminalUi.dp(c,52),TerminalUi.dp(c,52)));
        submit.setVisibility(VISIBLE);voice.setVisibility(VISIBLE);submit.setEnabled(!draft.trim().isEmpty());submit.setOnClickListener(v->send.accept(composer.getText().toString()));
        composer.addTextChangedListener(new android.text.TextWatcher(){
            public void beforeTextChanged(CharSequence s,int start,int count,int after){}
            public void onTextChanged(CharSequence s,int start,int before,int count){changed.accept(s.toString());submit.setEnabled(!s.toString().trim().isEmpty());}
            public void afterTextChanged(android.text.Editable s){}
        });
        faces.setOnClickListener(v->showSmileys());addView(row,new LayoutParams(-1,-2));
        row.addView(voice,new LayoutParams(TerminalUi.dp(c,52),TerminalUi.dp(c,52)));
        cancelVoice.setOnClickListener(v->{if(voice.listener!=null)voice.listener.cancel();});
    }
    void recordingState(int state){
        voice.setState(state);boolean idle=state==VoiceHoldButton.IDLE;
        faces.setVisibility(idle?VISIBLE:GONE);composer.setVisibility(idle?VISIBLE:GONE);
        recordingInfo.setVisibility(idle?GONE:VISIBLE);
        cancelVoice.setVisibility(state==VoiceHoldButton.LOCKED||state==VoiceHoldButton.READY?VISIBLE:GONE);
        submit.setVisibility(idle?VISIBLE:GONE);
        voice.setVisibility(VISIBLE);
        if(!idle)recordingElapsed(recordingMillis);
    }
    void recordingElapsed(long millis){
        recordingMillis=millis;String time=String.format(java.util.Locale.ROOT,"%d:%02d",millis/60000,(millis/1000)%60);
        int state=voice.state();
        int text=state==VoiceHoldButton.HOLDING?R.string.chat_voice_hold_status:state==VoiceHoldButton.LOCKED?R.string.chat_voice_locked_status:state==VoiceHoldButton.SENDING?R.string.chat_voice_sending:R.string.chat_voice_ready_status;
        recordingInfo.setText(getContext().getString(text,time));
    }
    static Button small(Context c,String text,String description){Button b=new Button(c);TerminalUi.actionStyle(b);b.setText(text);b.setContentDescription(description);b.setMinWidth(0);b.setMinimumWidth(0);b.setPadding(0,0,0,0);return b;}
    void insertSmiley(String token){int start=Math.max(0,composer.getSelectionStart()),end=Math.max(start,composer.getSelectionEnd());String before=start>0&&!Character.isWhitespace(composer.getText().charAt(start-1))?" ":"";String after=end<composer.length()&&!Character.isWhitespace(composer.getText().charAt(end))?" ":"";composer.getText().replace(start,end,before+token+after);composer.requestFocus();}
    private void showSmileys(){
        Context c=getContext();GridLayout grid=new GridLayout(c);grid.setColumnCount(5);int size=TerminalUi.dp(c,52);
        ScrollView scroll=new ScrollView(c);scroll.addView(grid);
        AlertDialog dialog=new AlertDialog.Builder(c).setView(scroll).setNegativeButton(android.R.string.cancel,null).create();
        for(ChatSmileys.Face face:ChatSmileys.FACES){
            ChatSmileyTextView item=new ChatSmileyTextView(c);TerminalUi.textStyle(item,22,TerminalUi.TEXT);item.setGravity(Gravity.CENTER);item.setMessage(face.token);item.setContentDescription(face.label+" "+face.token);
            item.setBackground(TerminalUi.frame(c,TerminalUi.SURFACE,TerminalUi.FRAME));item.setOnClickListener(v->{insertSmiley(face.token);dialog.dismiss();});grid.addView(item,new android.view.ViewGroup.LayoutParams(size,size));
        }
        smileyDialog=dialog;dialog.setOnDismissListener(d->{activate(grid,false);smileyDialog=null;});
        dialog.show();activate(grid,foreground);dialog.getWindow().setBackgroundDrawable(TerminalUi.frame(c,TerminalUi.BACKGROUND,TerminalUi.FRAME));
    }
    void setForeground(boolean active){active=active&&getContext().getSharedPreferences(FriendsActivity.class.getName(),Context.MODE_PRIVATE).getBoolean("motion",true)&&android.animation.ValueAnimator.areAnimatorsEnabled();foreground=active;if(smileyDialog!=null)activate(smileyDialog.getWindow().getDecorView(),active);for(int i=0;i<messages.getChildCount();i++)activate(messages.getChildAt(i),active);}
    @Override protected void onDetachedFromWindow(){if(smileyDialog!=null)smileyDialog.dismiss();clearPendingScroll();super.onDetachedFromWindow();}
    private void activate(View v,boolean active){if(v instanceof ChatSmileyTextView)((ChatSmileyTextView)v).setForegroundActive(active);if(v instanceof android.view.ViewGroup)for(int i=0;i<((android.view.ViewGroup)v).getChildCount();i++)activate(((android.view.ViewGroup)v).getChildAt(i),active);}
    void revealLatest(){revealLatest=true;}
    private void clearPendingScroll(){
        if(pendingScroll!=null&&history.getViewTreeObserver().isAlive())history.getViewTreeObserver().removeOnGlobalLayoutListener(pendingScroll);
        pendingScroll=null;
    }
    private void scrollAfterLayout(boolean bottom,int position){
        clearPendingScroll();
        pendingScroll=()->{clearPendingScroll();history.scrollTo(0,bottom?messages.getHeight():position);};
        history.getViewTreeObserver().addOnGlobalLayoutListener(pendingScroll);
        history.requestLayout();
    }
    void show(JsonObject data,Runnable previous,Runnable next){
        String signature=data.toString();if(signature.equals(rendered)){if(revealLatest){revealLatest=false;scrollAfterLayout(true,0);}return;}
        boolean bottom=revealLatest||rendered.isEmpty()||!history.canScrollVertically(1);revealLatest=false;int position=history.getScrollY();rendered=signature;
        boolean active=foreground;setForeground(false);messages.removeAllViews();foreground=active;
        if(data.get("offset").getAsInt()>0)TerminalUi.button(messages,R.string.chat_previous,previous);
        for(JsonElement entry:data.getAsJsonArray("messages")){
            JsonObject message=entry.getAsJsonObject();boolean outgoing=message.get("outgoing").getAsBoolean();
            LinearLayout bubble=new LinearLayout(getContext());bubble.setOrientation(VERTICAL);int pad=TerminalUi.dp(getContext(),10);bubble.setPadding(pad,pad,pad,pad);
            bubble.setBackground(TerminalUi.frame(getContext(),outgoing?0xff153d30:TerminalUi.SURFACE,outgoing?TerminalUi.FRAME:0xff285346));
            LayoutParams bp=new LayoutParams(-1,-2);bp.topMargin=TerminalUi.dp(getContext(),6);if(outgoing)bp.leftMargin=TerminalUi.dp(getContext(),38);else bp.rightMargin=TerminalUi.dp(getContext(),38);messages.addView(bubble,bp);
            if(message.has("kind")&&message.get("kind").getAsString().equals("audio")){
                bubble.addView(new ChatVoiceView(getContext(),message.get("id").getAsString(),message.get("duration_ms").getAsInt(),audio,
                    ()->{if(playAudio!=null)playAudio.accept(message);}),new LayoutParams(-1,-2));
            }else{
                ChatSmileyTextView text=new ChatSmileyTextView(getContext());TerminalUi.textStyle(text,17,TerminalUi.TEXT);text.setTypeface(Typeface.create("sans-serif",Typeface.NORMAL));text.setMessage(message.get("text").getAsString());text.setTextIsSelectable(true);text.setForegroundActive(foreground);bubble.addView(text,new LayoutParams(-1,-2));
                if(outgoing){
                    bubble.setOnLongClickListener(v->{if(editMessage!=null)editMessage.accept(message);return true;});
                    text.setOnLongClickListener(v->{if(editMessage!=null)editMessage.accept(message);return true;});
                }
            }
            String timestamp=DateFormat.getDateTimeInstance(DateFormat.SHORT,DateFormat.SHORT).format(new Date((long)(message.get("timestamp").getAsDouble()*1000)));
            TextView meta=new TextView(getContext());TerminalUi.textStyle(meta,10,TerminalUi.MUTED);meta.setGravity(Gravity.END);meta.setText(timestamp+(message.has("edited")?" · "+getContext().getString(R.string.notice_edited):"")+(outgoing?" · "+getContext().getString(ChatActivity.status(message.get("status").getAsString())):""));bubble.addView(meta);
        }
        if(data.getAsJsonArray("messages").isEmpty())TerminalUi.label(messages,getContext().getString(R.string.chat_no_messages),14,TerminalUi.MUTED);
        if(!data.get("next_offset").isJsonNull())TerminalUi.button(messages,R.string.chat_next,next);
        scrollAfterLayout(bottom,position);
    }
}
