"""Regenerate the rotated dodecahedron SVG, PNG, ICO and embedded Tk icon (Pillow)."""
from pathlib import Path
import math,itertools,base64,io
from PIL import Image,ImageDraw
p=Path(__file__).resolve().parents[1]
# Convex hull of a regular dodecahedron, rotated around all three axes.
phi=(1+math.sqrt(5))/2
vertices=list(itertools.product((-1,1),repeat=3))
for a,b in itertools.product((-1,1),repeat=2):vertices.extend([(0,a/phi,b*phi),(a/phi,b*phi,0),(b*phi,0,a/phi)])
def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return(a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def norm(a):return tuple(x/math.sqrt(dot(a,a)) for x in a)
def rotate(v):
 x,y,z=v
 for axis,angle in [(0,.55),(1,.77),(2,.19)]:
  c,t=math.cos(angle),math.sin(angle)
  if axis==0:y,z=y*c-z*t,y*t+z*c
  elif axis==1:x,z=x*c+z*t,-x*t+z*c
  else:x,y=x*c-y*t,x*t+y*c
 return(x,y,z)
faces={}
for ids in itertools.combinations(range(20),3):
 a,b,c=[vertices[i] for i in ids];n=cross(sub(b,a),sub(c,a))
 if dot(n,n)<1e-9:continue
 n=norm(n);ds=[dot(n,sub(v,a)) for v in vertices]
 if min(ds)<-1e-6 and max(ds)>1e-6:continue
 face=tuple(i for i,d in enumerate(ds) if abs(d)<1e-6)
 if len(face)!=5:continue
 center=tuple(sum(vertices[i][k] for i in face)/5 for k in range(3))
 if dot(n,center)<0:n=tuple(-x for x in n)
 u=norm(sub(vertices[face[0]],center));v=cross(n,u)
 face=tuple(sorted(face,key=lambda i:math.atan2(dot(sub(vertices[i],center),v),dot(sub(vertices[i],center),u))))
 faces[frozenset(face)]=(face,n)
assert len(faces)==12
im=Image.new('RGBA',(1024,1024));d=ImageDraw.Draw(im);d.rounded_rectangle((0,0,1023,1023),232,fill='#111827')
svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256"><rect width="256" height="256" rx="58" fill="#111827"/>'
for face,n in sorted(faces.values(),key=lambda f:rotate(f[1])[2]):
 normal=rotate(n)
 if normal[2]<=0:continue
 assert normal[2]<.90 # No visible face is front-on.
 points=[(128+rotate(vertices[i])[0]*57,128-rotate(vertices[i])[1]*57) for i in face]
 light=max(0,dot(normal,norm((-.6,.8,1))));color=tuple(round(a+(b-a)*light) for a,b in zip((61,49,155),(190,200,255)))
 hexcolor='#'+''.join(f'{x:02x}' for x in color)
 svg+='<polygon points="'+' '.join(f'{x:.2f},{y:.2f}' for x,y in points)+'" fill="'+hexcolor+'" stroke="#e0e7ff" stroke-width="1.7" stroke-linejoin="round"/>'
 coords=[(round(x*4),round(y*4)) for x,y in points];d.polygon(coords,fill=color);d.line(coords+[coords[0]],fill='#e0e7ff',width=7,joint='curve')
(p/'clients/assets/dodecahedron.svg').write_text(svg+'</svg>\n');im=im.resize((256,256),Image.Resampling.LANCZOS);im.save(p/'clients/assets/dodecahedron.png');im.save(p/'clients/windows/app.ico',sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
b=io.BytesIO();im.resize((80,80),Image.Resampling.LANCZOS).save(b,format='PNG')

f=p/'clients/desktop/app.py';s=f.read_text();start=s.index("ICON_PNG='");end=s.index("'",start+10)
s=s[:start]+"ICON_PNG='"+base64.b64encode(b.getvalue()).decode()+s[end:];f.write_text(s)
