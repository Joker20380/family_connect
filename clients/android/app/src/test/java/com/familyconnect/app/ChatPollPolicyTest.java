package com.familyconnect.app;
import org.junit.Test;
import static org.junit.Assert.*;
public class ChatPollPolicyTest {
    @Test public void discoversIncomingWithoutTypingAndLimitsFrequency(){
        ChatPollPolicy policy=new ChatPollPolicy();
        assertTrue(policy.poll(0,true,true,false,false,true));
        assertFalse(policy.poll(2000,true,true,false,false,true));
        assertFalse(policy.poll(5999,true,true,false,false,true));
        assertTrue(policy.poll(6000,true,true,false,false,true));
    }
    @Test public void respectsLifecycleOutstandingWorkAndRetryFailures(){
        ChatPollPolicy policy=new ChatPollPolicy();
        assertFalse(policy.poll(0,false,true,false,false,true));
        assertFalse(policy.poll(0,true,false,false,false,true));
        assertFalse(policy.poll(0,true,true,true,false,true));
        assertFalse(policy.poll(0,true,true,false,true,true));
        assertFalse(policy.poll(0,true,true,false,false,false));
        assertTrue(policy.poll(0,true,true,false,false,true));
    }
}
