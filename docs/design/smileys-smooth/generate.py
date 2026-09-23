"""Generate original vector expression studies. No external art or dependencies."""
from pathlib import Path
import html

ROOT = Path(__file__).resolve().parent
INK = '#50351c'
FACES = [
    ('smile', 'Улыбка', ':)'),
    ('wink', 'Подмигивание', ';)'),
    ('laugh', 'Смех', ':D'),
    ('sad', 'Грусть', ':('),
    ('kiss', 'Поцелуй', ':-*'),
]


def svg(kind, label, animated=True):
    def motion(attr, values, times, duration='4s'):
        return (f'<animate attributeName="{attr}" values="{values}" keyTimes="{times}" dur="{duration}" repeatCount="indefinite"/>' if animated else '')

    blink = motion('ry', '6;6;1;6;6', '0;.43;.46;.49;1')
    eyes = f'<ellipse cx="36" cy="40" rx="3.4" ry="6">{blink}</ellipse><ellipse cx="60" cy="40" rx="3.4" ry="6">{blink}</ellipse>'
    extra = ''
    if kind == 'smile':
        mouth = '<path d="M31 56 Q48 76 65 56 Q49 64 31 56Z"/>'
    elif kind == 'wink':
        eyes = f'<ellipse cx="36" cy="40" rx="3.4" ry="6">{blink}</ellipse><path d="M55 42 Q60 36 66 40" fill="none" stroke-width="3.5"/>'
        mouth = '<path d="M33 58 Q48 73 64 54" fill="none" stroke-width="3.2"/>'
        extra = '<path d="M56 28 Q62 25 67 28" fill="none" stroke-width="2.4"/>'
    elif kind == 'laugh':
        eyes = '<path d="M30 41 Q36 31 42 41 M54 41 Q60 31 66 41" fill="none" stroke-width="3.6"/>'
        mouth = '<path d="M29 52 Q48 58 67 52 C66 80 31 80 29 52Z"/><path d="M32 54 Q48 59 64 54 L62 61 Q48 65 34 61Z" fill="#fff5df" stroke="none"/><path d="M37 70 Q48 62 59 70 Q48 78 37 70" fill="#ed8163" stroke="none"/>'
    elif kind == 'sad':
        mouth = '<path d="M35 64 Q48 52 61 64" fill="none" stroke-width="3"/>'
        extra = '<path d="M30 29 L41 25 M55 25 L66 29" fill="none" stroke-width="2.7"/>'
    else:
        eyes = '<path d="M30 41 Q36 46 42 40 M54 40 Q60 46 66 41" fill="none" stroke-width="3"/>'
        mouth = '<path d="M46 54 Q59 55 49 60 Q59 65 46 66" fill="none" stroke-width="3"/>'
        extra = '<g fill="#ee785c" stroke="none"><path d="M76 48 C66 39 69 32 75 33 Q79 33 80 37 Q84 31 88 36 C94 42 82 48 76 48Z">' + motion('opacity', '0;0;1;1;0', '0;.25;.4;.7;1', '3s') + '</path></g>'
    bob = ''
    if animated:
        amounts = '0 0;0 -2;0 0;0 -1;0 0' if kind == 'laugh' else '0 0;0 -1;0 0'
        bob = f'<animateTransform attributeName="transform" type="translate" values="{amounts}" dur="{1.2 if kind == "laugh" else 3}s" repeatCount="indefinite"/>'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 96 96" role="img" aria-label="{label}">
<defs><radialGradient id="face" cx="36%" cy="25%" r="78%"><stop stop-color="#ffe995"/><stop offset=".55" stop-color="#ffd457"/><stop offset="1" stop-color="#efa92e"/></radialGradient></defs>
<g>{bob}<circle cx="48" cy="48" r="35" fill="url(#face)" stroke="#b77b27" stroke-width="1.5"/>
<path d="M24 31 Q34 15 53 18" fill="none" stroke="#fff3b4" stroke-width="2" stroke-linecap="round" opacity=".6"/>
<ellipse cx="26" cy="53" rx="6" ry="3.5" fill="#eb9353" opacity=".28"/><ellipse cx="70" cy="53" rx="6" ry="3.5" fill="#eb9353" opacity=".28"/>
<g fill="{INK}" stroke="{INK}" stroke-width="1" stroke-linejoin="round" stroke-linecap="round">{eyes}{mouth}{extra}</g></g></svg>'''


cards = []
for kind, label, token in FACES:
    for animated in (True, False):
        (ROOT / f'{kind}{"" if animated else "-still"}.svg').write_text(svg(kind, label, animated))
    cards.append(f'''<article><div class="large"><img src="{kind}.svg" alt="{label}"></div><h2>{label}</h2><code>{html.escape(token)}</code><div class="sizes"><img width="24" src="{kind}.svg" alt="24 px"><img width="32" src="{kind}.svg" alt="32 px"><img width="48" src="{kind}.svg" alt="48 px"></div></article>''')
page = '''<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Family Connect — образцы смайликов</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#101b1c;color:#e0e6d8;font-family:system-ui,sans-serif}main{max-width:1100px;margin:auto;padding:44px 40px}.eyebrow{color:#df9c51;font-size:12px;letter-spacing:3px}h1{font-size:32px;font-weight:550;margin:12px 0}p{color:#9caeaa;line-height:1.6;font-size:15px}.grid{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin:30px 0}article{border:1px solid #334545;background:#162425;text-align:center;padding:18px 8px 14px;border-radius:16px}.large img{width:132px;height:132px}h2{font-size:16px;font-weight:500;margin:8px}code{color:#a3b1a6}.sizes{display:flex;align-items:center;justify-content:center;gap:12px;height:64px;margin-top:16px;border-top:1px solid #30403d}.conversation{display:flex;gap:12px;flex-wrap:wrap;margin-top:20px}.bubble{display:flex;align-items:center;gap:5px;padding:12px 18px;border-radius:16px 16px 16px 4px;background:#253e36;font-size:17px}.bubble img{width:32px;height:32px}.light{background:#e8ebe0;color:#26362d}.foot{border-top:1px solid #334545;margin-top:26px;padding-top:16px;font-size:13px}button{background:#253e36;border:1px solid #516758;border-radius:8px;padding:10px 18px;color:#e0e6d8;cursor:pointer}button:focus-visible{outline:2px solid #df9c51}@media(max-width:700px){main{padding:25px 18px}.grid{grid-template-columns:repeat(2,1fr)}h1{font-size:26px}}
</style><main><div class="eyebrow">FAMILY CONNECT / EXPRESSION STUDY 01</div><h1>Знакомые эмоции. Чистый контур.</h1><p>Пять новых векторных смайликов с лёгкой анимацией.<br>Жёлтые лица, мягкий свет и тёплая мимика в духе старого мессенджера.</p><button id="motion" aria-pressed="false">Остановить анимацию</button><section class="grid">CARDS</section><p>В сообщении · размер 32 px</p><section class="conversation"><div class="bubble">Привет! <img src="smile.svg" alt="Улыбка"><img src="wink.svg" alt="Подмигивание"></div><div class="bubble">Ну ты даёшь <img src="laugh.svg" alt="Смех"></div><div class="bubble light">Скучаю <img src="sad.svg" alt="Грусть"><img src="kiss.svg" alt="Поцелуй"></div></section><p class="foot">Образцы для оценки, ещё не установлены в приложение. Ниже каждого лица — 24 / 32 / 48 px.<br>Прозрачный фон. Без GIF-палитры, белой подложки и растрового вырезания.</p></main>
<script>const button=document.querySelector('button');let paused=matchMedia('(prefers-reduced-motion: reduce)').matches;function render(){document.querySelectorAll('img').forEach(img=>{img.src=img.getAttribute('src').replace(/(-still)?\\.svg$/,paused?'-still.svg':'.svg')});button.textContent=paused?'Включить анимацию':'Остановить анимацию';button.setAttribute('aria-pressed',String(paused))}button.onclick=()=>{paused=!paused;render()};render();</script></html>'''
(ROOT / 'index.html').write_text(page.replace('CARDS', ''.join(cards)))
print('Generated 5 animated SVGs, 5 still SVGs and preview HTML.')
