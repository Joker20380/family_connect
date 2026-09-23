package com.familyconnect.app;

/** Convert a neutral light exterior matte into a soft dark transparent contour.
 * Decisions use the original frame, so removal never propagates into eyes/teeth.
 */
final class ChatGifContour {
    static void clean(int[] pixels,int width,int height,boolean[] edge){
        if(width<1||height<1||pixels.length!=width*height||edge.length!=pixels.length)throw new IllegalArgumentException("Invalid frame");
        for(int y=0;y<height;y++)for(int x=0;x<width;x++){
            int index=y*width+x,color=pixels[index],r=(color>>16)&255,g=(color>>8)&255,b=color&255;
            edge[index]=false;
            if((color>>>24)==0||Math.min(r,Math.min(g,b))<170||Math.max(r,Math.max(g,b))-Math.min(r,Math.min(g,b))>55)continue;
            for(int dy=-1;dy<=1&&!edge[index];dy++)for(int dx=-1;dx<=1;dx++){
                int nx=x+dx,ny=y+dy;
                if(nx<0||ny<0||nx>=width||ny>=height||(pixels[ny*width+nx]>>>24)==0){edge[index]=true;break;}
            }
        }
        for(int i=0;i<pixels.length;i++)if(edge[i]){
            int color=pixels[i],light=Math.min((color>>16)&255,Math.min((color>>8)&255,color&255));
            // Neutral antialiasing originally composited on white: retain coverage,
            // render a transparent dark edge instead of deleting its geometry.
            int alpha=(color>>>24)*(255-light)/255;pixels[i]=alpha<<24;
        }
    }
}
