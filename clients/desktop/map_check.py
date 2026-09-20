"""Native Cairo checks for the shared Android beta25 map style."""
import base64,json,math,zlib
from pathlib import Path
import cairo
from app import RouteMap,LAND_ZLIB_BASE64,Adw,TerminalGauge


def check():
    root=Path(__file__).resolve().parents[1]
    assert zlib.decompress(base64.b64decode(LAND_ZLIB_BASE64))==(root/'assets/land.json').read_bytes()
    Adw.init()
    for scale in (1,2,3):
        layer=RouteMap.land_layer(360,200,scale)
        # Ocean remains empty; central Sahara contains land dots.
        data=layer.get_data();stride=layer.get_stride()
        def count(left,top,right,bottom):
            return sum(data[y*stride+x*4+3]>0 for y in range(int(top*scale),int(bottom*scale)) for x in range(int(left*scale),int(right*scale)))
        assert count(40,110,60,130)==0,'Pacific ocean contains dots'
        assert count(190,75,200,85)>0,'Sahara land missing'
        # Every dot uses the same raster alignment/coverage at this scale.
        spacing=2.3*scale;step=spacing*.8660254;diameter=max(1,math.floor(.65*scale+.5));offset=.5 if diameter%2 else 0
        values=set()
        for row in range(math.ceil(200*scale/step)):
            y=math.floor(row*step-offset+.5)+offset
            for col in range(math.ceil(360*scale/spacing)):
                x=math.floor((col+.5*(row%2))*spacing-offset+.5)+offset
                if 3<x<357*scale and 3<y<197*scale:
                    a=data[int(y)*stride+int(x)*4+3]
                    if a:values.add(a)
        assert len(values)<=2,('Unequal dot coverage',scale,values)
    view=RouteMap();view.phase=0
    def render(phase):
        view.phase=phase;image=cairo.ImageSurface(cairo.FORMAT_ARGB32,720,400);view.draw_map(view,cairo.Context(image),720,400);return image
    first=render(0);assert bytes(first.get_data())!=bytes(render(.25).get_data())
    assert bytes(first.get_data())==bytes(render(0).get_data())
    first.write_to_png('/tmp/fc-desktop-map.png')
    dial=TerminalGauge();dial.update(False,False,True,True)
    clicks=[];dial.connect('clicked',lambda *_:clicks.append(True));dial.emit('clicked');assert len(clicks)==1
    images=[]
    for on in (False,True):
        dial.update(on,False,True,True)
        image=cairo.ImageSurface(cairo.FORMAT_ARGB32,360,360);cr=cairo.Context(image);cr.set_source_rgb(3/255,17/255,14/255);cr.paint()
        dial.draw(dial.area,cr,360,360);image.write_to_png('/tmp/fc-desktop-dial-'+('on' if on else 'off')+'.png');images.append(bytes(image.get_data()))
    assert images[0]!=images[1]
    dial.update(True,True,True,False);assert not dial.get_sensitive()
    print('Dial: native button callback, enabled state and ON/OFF renders passed')
    print('Map: shared geography, 3 scales, equal dot coverage, ocean/land and shimmer passed')

if __name__=='__main__':
    try:check()
    except Exception:
        import os,traceback
        if os.environ.get('GITHUB_ACTIONS'):
            detail=traceback.format_exc().replace('%','%25').replace('\r','%0D').replace('\n','%0A')
            print('::error title=Native map check::'+detail,flush=True)
        raise
