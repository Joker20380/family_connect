package com.familyconnect.app;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.location.Location;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import org.junit.runner.RunWith;
import java.lang.reflect.Field;
import java.io.File;
import java.io.FileOutputStream;
import static org.junit.Assert.*;

/** Real Canvas checks using synthetic coordinates, no permissions/network/VPN. */
@RunWith(AndroidJUnit4.class)
public class RouteMapRuntimeTest {
    private void number(RouteMapView view,String name,float value){
        try{Field field=RouteMapView.class.getDeclaredField(name);field.setAccessible(true);field.setFloat(view,value);}
        catch(Exception e){throw new AssertionError(e);}
    }
    private Bitmap render(RouteMapView view,int w,int h){
        view.layout(0,0,w,h);Bitmap image=Bitmap.createBitmap(w,h,Bitmap.Config.ARGB_8888);view.draw(new Canvas(image));return image;
    }
    @Test public void zoomedRouteAndDeviceStayInsideMap(){
        InstrumentationRegistry.getInstrumentation().runOnMainSync(()->{
            Context context=InstrumentationRegistry.getInstrumentation().getTargetContext();
            for(int width:new int[]{320,720,1080})for(float zoom:new float[]{1,2,3}){
                int height=width*2/3;
                for(float pan:new float[]{0,.5f,1}){
                    RouteMapView view=new RouteMapView(context,code->{});
                    Location location=new Location("synthetic");location.setLatitude(31);location.setLongitude(20);
                    view.locate(location);view.update("nl","on","ok",false);view.layout(0,0,width,height);
                    number(view,"zoom",zoom);number(view,"panX",width*(1-zoom)*pan);number(view,"panY",height*.78f*(1-zoom)*pan);
                    Bitmap image=render(view,width,height);
                    try{
                        for(int y=(int)Math.ceil(height*.78)+2;y<height;y++)for(int x=0;x<width;x++)
                            assertEquals("Route escaped map at zoom="+zoom,TerminalUi.BACKGROUND,image.getPixel(x,y));
                    }finally{image.recycle();}
                }
            }
        });
    }
    @Test public void landShimmersWithoutLocationAndReducedMotionIsStable(){
        InstrumentationRegistry.getInstrumentation().runOnMainSync(()->{
            Context context=InstrumentationRegistry.getInstrumentation().getTargetContext();
            RouteMapView view=new RouteMapView(context,code->{});view.update("nl","off","off",true);
            number(view,"phase",0);Bitmap first=render(view,1080,750);
            number(view,"phase",.25f);Bitmap next=render(view,1080,750);
            assertFalse("Land should shimmer without requesting location",first.sameAs(next));first.recycle();next.recycle();
            view.update("nl","off","off",false);number(view,"phase",0);first=render(view,1080,750);
            number(view,"phase",.5f);next=render(view,1080,750);
            assertTrue("Reduced motion must remain static",first.sameAs(next));
            File folder=context.getExternalFilesDir("ui-acceptance");assertNotNull(folder);
            try(FileOutputStream output=new FileOutputStream(new File(folder,"route-map-dots.png"))){assertTrue(first.compress(Bitmap.CompressFormat.PNG,100,output));}
            catch(Exception e){throw new AssertionError(e);}
            finally{first.recycle();next.recycle();}
        });
    }
}
