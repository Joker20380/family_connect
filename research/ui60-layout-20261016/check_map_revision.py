import json
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw


root = Path(__file__).resolve().parent
previous = root / 'revisions/ui60-2/renders-candidate/ui60-fixtures'
current = root / 'renderer/renders-candidate/ui60-fixtures'
checks = []
for language in ['ru', 'en']:
    receipt = json.loads((current / f'receipt-candidate-392-780-{language}-1.json').read_text())
    scene = next(row for row in receipt if row.get('name') == f'candidate-{language}-392-780-1.0-home-off')
    bounds = next(view for view in scene['views'] if view.get('tag') == 'home_map')
    image_name = scene['name'] + '.png'
    before = Image.open(previous / image_name).convert('RGB')
    after = Image.open(current / image_name).convert('RGB')
    assert before.size == after.size
    difference = ImageChops.difference(before, after)
    assert difference.getbbox() is not None, 'Map revision did not change the rendered image'
    left, top = bounds['left'], bounds['top']
    right, bottom = left + bounds['width'], top + bounds['height']
    ImageDraw.Draw(difference).rectangle((left, top, right-1, bottom-1), fill=(0, 0, 0))
    assert difference.getbbox() is None, 'Unexpected change outside the map: ' + language
    checks.append(dict(language=language, viewport=[392, 780], map_bounds=[left, top, right, bottom], outside_map_pixel_identical_to_revision2=True))
(root / 'map-revision-check.json').write_text(json.dumps(dict(checks=checks, scope='Normal-size RU/EN OFF fixtures; synthetic data'), indent=2) + '\n')
print(json.dumps(dict(outside_map_pixel_identical=True, configurations=len(checks))))
