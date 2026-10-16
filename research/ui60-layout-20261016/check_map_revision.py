import json
import math
from pathlib import Path


root = Path(__file__).resolve().parent
previous = root / 'revisions/ui60-3/renders-candidate/ui60-fixtures'
current = root / 'renderer/renders-candidate/ui60-fixtures'
checks = []
for language in ['ru', 'en']:
    name = f'receipt-candidate-392-780-{language}-1.json'
    before = json.loads((previous / name).read_text())
    after = json.loads((current / name).read_text())
    scene_name = f'candidate-{language}-392-780-1.0-home-off'
    before_scene = next(row for row in before if row.get('name') == scene_name)
    after_scene = next(row for row in after if row.get('name') == scene_name)
    bounds = {}
    for tag in ['home_map', 'home_connection', 'home_workspace']:
        old = next(view for view in before_scene['views'] if view.get('tag') == tag)
        new = next(view for view in after_scene['views'] if view.get('tag') == tag)
        assert new['width'] == old['width'], tag
        if tag == 'home_map':
            assert new['height'] == math.ceil((new['width'] - 12) * 145 / 360) + 12
            assert new['height'] > old['height']
            assert new['top'] + new['height'] <= 714
        else:
            assert new['height'] < old['height'], tag
        bounds[tag] = {'before_height': old['height'], 'after_height': new['height'], 'width': new['width']}
    assert all(view.get('ellipsizedCharacters', 0) == 0 for view in after_scene['views'] if view.get('parent') == 'LiveNetworkPanel')
    checks.append({'language': language, 'viewport': [392, 780], 'bounds': bounds})
(root / 'map-revision-check.json').write_text(json.dumps({'checks': checks, 'scope': 'Revision4 normal RU/EN OFF real-code fixtures; compact middle panel, proportional full-width map'}, indent=2) + '\n')
print(json.dumps({'full_width_proportional_map': True, 'both_other_panels_compacted': True, 'configurations': len(checks)}))
