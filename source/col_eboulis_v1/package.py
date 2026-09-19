"""Aperçu HTML autonome + pack ZIP prêt à déposer à la racine du dépôt guilde-treehouse-pmd."""
from pathlib import Path
import base64, json, zipfile, io
from PIL import Image

HERE = Path(__file__).resolve().parent
man = json.loads((HERE / 'manifest.json').read_text())
ver = json.loads((HERE / 'verification.json').read_text())
S = man['taille'][0]


def b64(p): return 'data:image/png;base64,' + base64.b64encode(Path(p).read_bytes()).decode()


layers = {m: [(f, b64(HERE / 'couches' / f)) for f in man['variantes'][m]['calques']] for m in ['jour', 'nuit']}
labels = {'00': 'Ciel natif', '01': 'Nuages natifs', '02': 'Chaîne lointaine', '03': 'Chaîne proche', '04': 'Sol / chemin',
          '05': 'Ombres (calculées)', '06': 'Massif + rochers de bord', '07': 'Profondeur de l’entrée', '08': 'Rochers épars', '09': 'Rebords premier plan (Top)'}
pts = man['points']
tests = ''.join(f"<li class='{'ok' if t['pass'] else 'ko'}'>{t['test']} <small>{t['detail']}</small></li>" for t in ver['tests'])
imgs = {m: ''.join(f"<img class='L' data-n='{f.split('_')[3]}' src='{d}' alt='{f}'>" for f, d in layers[m]) for m in layers}
checks = ''.join(f"<label><input type='checkbox' checked data-n='{k}'> {k} · {v}</label>" for k, v in labels.items())
html = f"""<!doctype html><html lang='fr'><head><meta charset='utf-8'><title>Le col des Éboulis — aperçu des calques</title>
<style>body{{font-family:system-ui,sans-serif;background:#1d1f24;color:#e8e8e8;margin:0;padding:16px}}h1{{font-size:20px;margin:0 0 4px}}
.wrap{{display:flex;gap:20px;align-items:flex-start;flex-wrap:wrap}}.stage{{position:relative;width:{S}px;height:{S}px;background:#000;image-rendering:pixelated;flex:none;overflow:hidden;transform-origin:0 0}}
.stage img,.stage canvas{{position:absolute;left:0;top:0;width:{S}px;height:{S}px;image-rendering:pixelated}}.panel{{max-width:420px;font-size:14px}}label{{display:block;margin:2px 0}}
.ok{{color:#8fd98f}}.ko{{color:#ff8a8a}}ul{{padding-left:18px}}small{{color:#9aa}}button{{margin:2px}}.hidden{{display:none}}
code{{background:#2b2e36;padding:1px 4px;border-radius:3px}}</style></head><body>
<h1>Le col des Éboulis — chemin sud → nord vers l’entrée canonique de Mont Horn</h1>
<p><small>Lot <code>col_eboulis_v1</code> · {S}×{S} px = {S // 8}×{S // 8} cellules de 8 px · calques générés (DA PMD) détourés, fonds natifs, nuit = filtre Abyss exact · <b>aperçu de fichiers, pas de test moteur PMDO</b>.</small></p>
<div class='wrap'><div><div>
<button onclick="mode('jour')">Jour</button><button onclick="mode('nuit')">Nuit</button>
<button onclick="zoom(1)">1×</button><button onclick="zoom(2)">2×</button>
<label style='display:inline'><input type='checkbox' id='grid' onchange='draw()'> grille 8 px</label>
<label style='display:inline'><input type='checkbox' id='marks' checked onchange='draw()'> marqueurs</label></div>
<div id='outer' style='width:{S}px;height:{S}px;overflow:hidden'><div class='stage' id='st'>
<div id='jour'>{imgs['jour']}</div><div id='nuit' class='hidden'>{imgs['nuit']}</div><canvas id='ov' width='{S}' height='{S}'></canvas></div></div></div>
<div class='panel'><h3>Calques (arrière → avant)</h3>{checks}
<h3>Points clés (grille 8 px)</h3><ul><li>Seuil <code>donjon_seuil</code> : {pts['donjon_seuil']} (16×16)</li><li>Arrivée <code>entree</code> : {pts['entree']} (16×16)</li>
<li>Corridor libre : x {pts['corridor']['x']}, y {pts['corridor']['y']}</li><li>Bouche : bbox {pts['bouche_bbox']}</li></ul>
<h3>Audit ({'tous PASS' if ver['all_pass'] else 'échecs'})</h3><ul>{tests}</ul>
<p><small>Import : PNG to Tileset, 8 px, un tileset par PNG (noms uniques <code>COLEBOULIS_V1_*</code>). Le calque 09 doit être placé devant le personnage (Top). Les nuages peuvent devenir un fond défilant. Aucune collision n’est fournie : bloquer hors du sol visible (calque 04) et sur les calques 06–09.</small></p></div></div>
<script>
const st=document.getElementById('st'),ov=document.getElementById('ov');let z=1;
function mode(m){{document.getElementById('jour').classList.toggle('hidden',m!=='jour');document.getElementById('nuit').classList.toggle('hidden',m!=='nuit');}}
function zoom(k){{z=k;st.style.transform='scale('+k+')';document.getElementById('outer').style.width=({S}*k)+'px';document.getElementById('outer').style.height=({S}*k)+'px';}}
document.querySelectorAll('input[data-n]').forEach(c=>c.onchange=()=>{{document.querySelectorAll('img.L[data-n="'+c.dataset.n+'"]').forEach(i=>i.style.visibility=c.checked?'visible':'hidden')}});
function draw(){{const g=ov.getContext('2d');g.clearRect(0,0,{S},{S});if(document.getElementById('grid').checked){{g.strokeStyle='rgba(255,255,255,.18)';g.beginPath();for(let x=0;x<={S};x+=8){{g.moveTo(x+.5,0);g.lineTo(x+.5,{S});}}for(let y=0;y<={S};y+=8){{g.moveTo(0,y+.5);g.lineTo({S},y+.5);}}g.stroke();}}
if(document.getElementById('marks').checked){{g.fillStyle='rgba(0,255,120,.25)';g.fillRect({pts['corridor']['x'][0]},{pts['corridor']['y'][0]},{pts['corridor']['x'][1] - pts['corridor']['x'][0]},{pts['corridor']['y'][1] - pts['corridor']['y'][0]});
g.strokeStyle='#ff4040';g.lineWidth=2;g.strokeRect({pts['donjon_seuil'][0]},{pts['donjon_seuil'][1]},16,16);g.strokeStyle='#40a0ff';g.strokeRect({pts['entree'][0]},{pts['entree'][1]},16,16);
g.strokeStyle='#ffd040';g.strokeRect({pts['bouche_bbox'][0]},{pts['bouche_bbox'][1]},{pts['bouche_bbox'][2] - pts['bouche_bbox'][0]},{pts['bouche_bbox'][3] - pts['bouche_bbox'][1]});}}}}
draw();</script></body></html>"""
(HERE / 'apercu_col_eboulis_v1.html').write_text(html, encoding='utf-8')

# planche de présentation jour/nuit côte à côte
j, n = Image.open(HERE / 'scene/jour.png'), Image.open(HERE / 'scene/nuit.png')
board = Image.new('RGB', (S * 2 + 8, S), (30, 30, 34)); board.paste(j, (0, 0)); board.paste(n, (S + 8, 0)); board.save(HERE / 'scene/planche_jour_nuit.png')

# pack ZIP : arborescence prête pour la racine du dépôt
out = HERE / 'col_eboulis_v1_pack.zip'
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
    for p in ['build.py', 'verify.py', 'package.py', 'SPECIFICATION.md', 'README.md', 'manifest.json', 'verification.json']:
        z.write(HERE / p, f'source/col_eboulis_v1/{p}')
    for p in sorted((HERE / 'outils').glob('*.py')): z.write(p, f'source/col_eboulis_v1/outils/{p.name}')
    for p in sorted((HERE / 'references').glob('fond_*.png')): z.write(p, f'source/col_eboulis_v1/references/{p.name}')
    for sub in ['bruts', 'couches', 'scene']:
        for p in sorted((HERE / sub).glob('*.png')): z.write(p, f'renders/col_eboulis_v1/{sub}/{p.name}')
    z.write(HERE / 'manifest.json', 'renders/col_eboulis_v1/manifest.json')
    z.write(HERE / 'verification.json', 'renders/col_eboulis_v1/verification.json')
    z.write(HERE / 'apercu_col_eboulis_v1.html', 'apercu_col_eboulis_v1.html')
    z.write(HERE / 'AGENTS_ajout.md', 'source/col_eboulis_v1/AGENTS_ajout.md')
print('aperçu + planche + zip écrits :', out.stat().st_size // 1024, 'Ko')
