import hashlib
import json
from pathlib import Path
import shutil
from PIL import Image, ImageDraw, ImageFont

root=Path(__file__).resolve().parent
review=root.parent/'owner-cumulative-client-acceptance-1-resume/review-publication'
publication=review/'research/ui60-layout-20261016'
publication.mkdir(parents=True,exist_ok=True)
for name in ['ui-only.patch','boundary.json','artifact-check.json','verify_boundary.py','check_artifact.py','build_ui.py','prepare.py','publish_evidence.py']:
    shutil.copy2(root/name,publication/name)
for name in ['receipt.json','cumulative-source.json']:
    shutil.copy2(root/'build'/name,publication/('build-'+name))
renderer=publication/'renderer';renderer.mkdir(exist_ok=True)
for name in ['AndroidManifest.xml','build_fixture.py','run.py']:
    shutil.copy2(root/'renderer'/name,renderer/name)
shutil.copytree(root/'renderer/java',renderer/'java',dirs_exist_ok=True)
images=publication/'screenshots';images.mkdir(exist_ok=True)
records=[]
for label in ['beta60','current','candidate']:
    origin=root/'renderer'/('renders-'+label)/'ui60-fixtures'
    for path in sorted(origin.glob(label+'-*.png')):
        if label!='candidate' and not any(marker in path.name for marker in ['-ru-392-780-1.0-','-en-392-780-1.0-']):continue
        if label!='candidate' and '-home-' in path.name and not path.name.endswith('-home-off.png'):continue
        shutil.copy2(path,images/path.name)
        records.append(dict(name=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),fixture=True))
receipts={}
for label in ['beta60','current','candidate']:
    receipts[label]=json.loads((root/'renderer'/label/'receipt.json').read_bytes())
(publication/'render-inputs.json').write_text(json.dumps(receipts,indent=2)+'\n')
(publication/'screenshots.json').write_text(json.dumps(records,indent=2)+'\n')
comparisons=publication/'comparisons';comparisons.mkdir(exist_ok=True)
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',16)
for screen in ['home-off','chat-empty','chat-list','chat-conversation','route','settings']:
    canvas=Image.new('RGB',(1176,816),'#071211');draw=ImageDraw.Draw(canvas)
    for column,label in enumerate(['beta60','current','candidate']):
        draw.text((column*392+12,9),label+' | RU | fixture',font=font,fill='#e2eee8')
        canvas.paste(Image.open(images/(label+'-ru-392-780-1.0-'+screen+'.png')).convert('RGB'),(column*392,36))
    canvas.save(comparisons/(screen+'.png'))
tests=[]
for path in sorted((root/'renderer/renders-candidate').glob('*.log')):
    text=path.read_text();prefix='INSTRUMENTATION_RESULT: result='
    assert 'INSTRUMENTATION_CODE: -1' in text and 'INSTRUMENTATION_RESULT: error=' not in text,path
    rows=json.loads(text.split(prefix,1)[1].split('\nINSTRUMENTATION_CODE:',1)[0])
    scenes=[{key:value for key,value in row.items() if key!='views'} for row in rows if 'name' in row]
    assert len(scenes) in [13,14] and all(scene['secure'] and scene['serviceRequests']==0 for scene in scenes)
    navigation=[row for row in rows if 'navigationCycles' in row]
    assert len(navigation)==1 and navigation[0]['liveControlsPreserved'] and navigation[0]['sessionPreserved']
    for row in rows:
        panels=[view for view in row.get('views',[]) if view['kind']=='LiveNetworkPanel']
        for view in row.get('views',[]):
            if view['kind']=='Button':assert min(view['width'],view['height'])>=48,view
            if view['kind']=='InlineLabel':assert view.get('ellipsizedCharacters',0)==0 and view.get('lineCount',0)<=3,view
            if view.get('parent')=='LiveNetworkPanel':
                assert len(panels)==1
                panel=panels[0]
                assert panel['left']<=view['left'] and view['left']+view['width']<=panel['left']+panel['width'],view
                assert panel['top']<=view['top'] and view['top']+view['height']<=panel['top']+panel['height'],view
    presentation=[row for row in rows if 'beta60TelemetryGrouping' in row]
    assert len(presentation)==1 and all(presentation[0].values())
    tests.append(dict(configuration=path.stem,scenes=scenes,navigation=navigation,presentation=presentation))
keyboard=(root/'renderer/keyboard.log').read_text()
keyboard_pass='INSTRUMENTATION_CODE: -1' in keyboard and 'INSTRUMENTATION_RESULT: error=' not in keyboard
keyboard_rows=json.loads(keyboard.split('INSTRUMENTATION_RESULT: result=',1)[1].split('\nINSTRUMENTATION_CODE:',1)[0]) if keyboard_pass else []
(publication/'ui-tests.json').write_text(json.dumps(dict(api=31,isolated_canvas_configurations=tests,real_ime_component=keyboard_pass,keyboard=[{key:value for key,value in row.items() if key!='views'} for row in keyboard_rows],api35_runtime='NOT_RUN',live_actions=0),indent=2)+'\n')
print(json.dumps(dict(published_screenshots=len(records),real_ime_component=keyboard_pass,product_apk_published=False)))
