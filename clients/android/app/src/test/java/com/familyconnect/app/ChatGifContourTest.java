package com.familyconnect.app;
import org.junit.Test;
import static org.junit.Assert.*;
public class ChatGifContourTest {
    @Test public void removesLightExteriorButPreservesEnclosedWhite(){
        int[] p={0,0xfff2f2ee,0,0,0, 0,0xff111111,0xff111111,0xff111111,0, 0,0xff111111,0xffffffff,0xff111111,0, 0,0xff111111,0xff111111,0xff111111,0, 0,0,0,0,0};
        ChatGifContour.clean(p,5,5,new boolean[25]);assertTrue((p[1]>>>24)>0&&(p[1]>>>24)<32);assertEquals(0,p[1]&0xffffff);assertEquals(0xffffffff,p[12]);assertEquals(0xff111111,p[11]);
    }
    @Test public void doesNotErodeWhiteInteriorOrYellow(){
        int[] p=new int[25];java.util.Arrays.fill(p,0xffffffff);p[0]=0xffffd020;
        ChatGifContour.clean(p,5,5,new boolean[25]);assertEquals(0,p[2]);assertEquals(0xffffffff,p[12]);assertEquals(0xffffd020,p[0]);
    }
}
