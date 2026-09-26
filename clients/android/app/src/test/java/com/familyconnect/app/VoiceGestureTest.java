package com.familyconnect.app;

import org.junit.Test;
import static org.junit.Assert.*;

public class VoiceGestureTest {
    @Test public void releaseSendsOnlyOnce(){VoiceGesture g=new VoiceGesture();g.start();assertEquals(VoiceGesture.Action.SEND,g.release());assertEquals(VoiceGesture.Action.NONE,g.release());}
    @Test public void upwardLockSurvivesReleaseAndTouchCancellation(){VoiceGesture g=new VoiceGesture();g.start();assertEquals(VoiceGesture.Action.LOCK,g.move(-10,-64));assertEquals(VoiceGesture.Action.NONE,g.release());assertEquals(VoiceGesture.Action.NONE,g.cancel());assertEquals(VoiceGesture.Action.NONE,g.move(-100,0));}
    @Test public void leftSwipeCancelsWithoutSending(){VoiceGesture g=new VoiceGesture();g.start();assertEquals(VoiceGesture.Action.CANCEL,g.move(-80,-20));assertEquals(VoiceGesture.Action.NONE,g.release());}
    @Test public void diagonalUsesDominantDirection(){VoiceGesture g=new VoiceGesture();g.start();assertEquals(VoiceGesture.Action.CANCEL,g.move(-90,-90));g.start();assertEquals(VoiceGesture.Action.LOCK,g.move(-80,-100));}
    @Test public void jitterDoesNotLockOrCancel(){VoiceGesture g=new VoiceGesture();g.start();assertEquals(VoiceGesture.Action.NONE,g.move(-20,-30));assertEquals(VoiceGesture.Action.SEND,g.release());}
    @Test public void cancelledOrResetGestureCannotSend(){VoiceGesture g=new VoiceGesture();assertEquals(VoiceGesture.Action.NONE,g.release());g.start();assertEquals(VoiceGesture.Action.CANCEL,g.cancel());assertEquals(VoiceGesture.Action.NONE,g.release());g.start();g.reset();assertEquals(VoiceGesture.Action.NONE,g.release());}
}
