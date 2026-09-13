"""Validate built-in archive GIFs; Pillow needed in the development environment."""
from pathlib import Path
import hashlib
import json
from PIL import Image
root=Path(__file__).resolve().parents[1]/'app/src/main/assets/chat/icq-classic'
manifest=json.loads((root/'provenance.json').read_text())
assets=manifest['assets'];assert len(assets)==49
assert {p.name for p in root.glob('*.gif')}=={item['file'] for item in assets}
codes=set()
for item in assets:
    name=item['file'];assert len(name)==6 and name[:2].isalpha() and name.endswith('.gif')
    data=(root/name).read_bytes()
    assert len(data)==item['bytes']<=32768
    assert hashlib.sha256(data).hexdigest()==item['sha256']
    with Image.open(root/name) as im:
        assert im.format=='GIF' and 0<im.width<=64 and 0<im.height<=64
        assert (im.width,im.height,im.n_frames)==(item['width'],item['height'],item['frames'])
        assert im.n_frames<=512
        for frame in range(im.n_frames):im.seek(frame);im.load()
    for code in item['codes']:
        assert code not in codes and 0<len(code.encode('ascii'))<=12
        codes.add(code)
print(json.dumps(dict(gifs=len(assets),bytes=sum(item['bytes'] for item in assets),codes=len(codes),hashes_and_frames_verified=True)))
