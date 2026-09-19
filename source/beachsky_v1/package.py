"""Aperçu HTML autonome (3 modes, calques togglables, eau cyclée, nuages défilants) — pas un test moteur."""
from pathlib import Path
import base64, json
HERE=Path(__file__).resolve().parent; man=json.loads((HERE/'manifest.json').read_text()); ver=json.loads((HERE/'verification.json').read_text())
W,H=man['taille']; b64=lambda p:'data:image/png;base64,'+base64.b64encode(Path(p).read_bytes()).decode()
def imgs(m):
    out=[]
    for f in man['modes'][m]['calques']:
        k=f.split('_',3)[3][:2]; ph=f.split('PHASE')[1][:2] if 'PHASE' in f else ''
        cls='L'+(' ph' if ph else '')+(' cl' if k=='01' else ''); out.append(f"<img class='{cls}' data-n='{k}' data-ph='{ph}' src='{b64(HERE/'couches'/f)}'>")
    return ''.join(out)
labels={'00':'Ciel natif','01':'Nuages (bande défilante)','02':'Mer profonde','03':f"Mer rivage + écume ({man['phases_eau']} phases cyclées)",'04':'Sable (plaque validée)','05':'Sentier roche / rebord ocre','06':'Ombres calculées','07':'Falaises nord','08':'Profondeur grotte','09':'Pointes rocheuses','10':'Herbes','11':'Palmiers'}
checks=''.join(f"<label><input type='checkbox' checked data-n='{k}'> {k} · {v}</label>" for k,v in labels.items())
tests=''.join(f"<li class='{'ok' if t['pass'] else 'ko'}'>{t['test']} <small>{t['detail']}</small></li>" for t in ver['tests'])
modes=''.join(f"<div id='m_{m}' class='{'hidden' if m!='jour' else ''}'>{imgs(m)}</div>" for m in man['modes'])
html=f"""<!doctype html><html lang='fr'><head><meta charset='utf-8'><title>Beach/Sky étendue — aperçu</title><style>
body{{font-family:system-ui;background:#1d1f24;color:#eee;margin:0;padding:14px}}.wrap{{display:flex;gap:18px;flex-wrap:wrap;align-items:flex-start}}
#st{{position:relative;width:{W}px;height:{H}px;background:#000;overflow:hidden;transform-origin:0 0}}#st img{{position:absolute;left:0;top:0;width:{W}px;height:{H}px;image-rendering:pixelated}}
.hidden{{display:none}}.panel{{max-width:400px;font-size:14px}}label{{display:block}}.ok{{color:#8fd98f}}.ko{{color:#f88}}small{{color:#9aa}}button{{margin:2px}}</style></head><body>
<h2 style='margin:0 0 6px'>Beach/Sky étendue — lot beachsky_v1 ({W}×{H}, {W//8}×{H//8} cellules)</h2>
<p><small>Composition validée par l'utilisateur, calques régénérés sur magenta ; eau = {man['phases_eau']} phases par cycle de rampe (équivalent palette cycling EoS) ; nuages = bande 1440 px à −4 px/s ; nuit = filtre Abyss exact ; crépuscule = interpolation 45 % + voile chaud. <b>Aperçu de fichiers, pas de test moteur.</b></small></p>
<div class='wrap'><div><div><button onclick="mode('jour')">Jour</button><button onclick="mode('crepuscule')">Crépuscule</button><button onclick="mode('nuit')">Nuit</button>
<button onclick="zoom(.5)">½×</button><button onclick="zoom(1)">1×</button> <label style='display:inline'><input type='checkbox' id='anim' checked> animation</label></div>
<div id='outer' style='width:{W}px;height:{H}px;overflow:hidden'><div id='st'>{modes}</div></div></div>
<div class='panel'><h3>Calques</h3>{checks}<h3>Points</h3><ul><li>Arrivée {man['points']['entree']}</li><li>Seuil grotte {man['points']['donjon_seuil']}</li></ul>
<h3>Audit ({'tous PASS' if ver['all_pass'] else 'échecs'})</h3><ul>{tests}</ul></div></div>
<script>
const N={man['phases_eau']};let ph=0,cx=0;
function mode(m){{for(const k of ['jour','crepuscule','nuit'])document.getElementById('m_'+k).classList.toggle('hidden',k!==m)}}
function zoom(k){{const st=document.getElementById('st');st.style.transform='scale('+k+')';document.getElementById('outer').style.width=({W}*k)+'px';document.getElementById('outer').style.height=({H}*k)+'px'}}
document.querySelectorAll('input[data-n]').forEach(c=>c.onchange=()=>document.querySelectorAll('img.L[data-n="'+c.dataset.n+'"]').forEach(i=>i.dataset.off=c.checked?'':'1'));
function tick(){{const a=document.getElementById('anim').checked;if(a)ph=(ph+1)%N;document.querySelectorAll('img.ph').forEach(i=>i.style.visibility=(i.dataset.off||(+i.dataset.ph!==ph))?'hidden':'visible');
document.querySelectorAll('img.L:not(.ph)').forEach(i=>i.style.visibility=i.dataset.off?'hidden':'visible');}}
setInterval(tick,130);
function cloud(){{if(document.getElementById('anim').checked){{cx=(cx-0.13)%1440;document.querySelectorAll('img.cl').forEach(i=>i.style.transform='translateX('+cx+'px)')}}requestAnimationFrame(cloud)}}cloud();
</script></body></html>"""
(HERE/'apercu_beachsky_v1.html').write_text(html,encoding='utf-8'); print('html', (HERE/'apercu_beachsky_v1.html').stat().st_size//1024,'Ko')
