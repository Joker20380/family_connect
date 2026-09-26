"""Render the shared Android door vector into Windows launcher/installer icons."""
import base64
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ANDROID = '{http://schemas.android.com/apk/res/android}'
# Exported unchanged from Android res/drawable/ic_brand.xml.
source = ROOT/'clients/assets/linux-door.xml'
image = Image.new('RGBA', (1024, 1024))
draw = ImageDraw.Draw(image)
draw.rounded_rectangle((0, 0, 1023, 1023), radius=224, fill='#071511')
# Reuse the Android vector paths rather than maintaining a second logo geometry.
for path in ET.parse(source).getroot().iter('path'):
    data = path.attrib[ANDROID+'pathData']
    fill = path.attrib[ANDROID+'fillColor']
    for i, polygon in enumerate(data.split('Z')):
        if not polygon.strip():
            continue
        points = [tuple(map(float, pair)) for pair in re.findall(r'(-?[\d.]+),(-?[\d.]+)', polygon)]
        assert len(points) >= 3
        draw.polygon([(204.8+x*6.144, 204.8+y*6.144) for x,y in points],
                     fill='#071511' if i and path.attrib.get(ANDROID+'fillType')=='evenOdd' else fill)
image = image.resize((256,256), Image.Resampling.LANCZOS)
image.save(ROOT/'clients/assets/windows-door.png')
image.save(ROOT/'clients/windows/app.ico', sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
