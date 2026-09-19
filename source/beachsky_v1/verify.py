"""Audit Beach/Sky v1 — contrôles de fichiers (pas de test moteur)."""
from pathlib import Path
import hashlib, json, sys
import numpy as np
from PIL import Image
from scipy import ndimage as nd
HERE=Path(__file__).resolve().parent; sys.path.insert(0,str(HERE/'outils')); from night import night
man=json.loads((HERE/'manifest.json').read_text()); W,H=man['taille']; res=[]; ok=True
def check(n,c,d=''):
    global ok; ok&=bool(c); res.append({'test':n,'pass':bool(c),'detail':d}); print('PASS' if c else 'FAIL',n,d)
def L(f): return np.array(Image.open(HERE/'couches'/f).convert('RGBA'))
modes=list(man['modes']); names={m:man['modes'][m]['calques'] for m in modes}
lay={m:[L(f) for f in names[m]] for m in modes}
check('1. dimensions 1264x848 (÷8)',all(a.shape[:2]==(H,W) for m in modes for a in lay[m]) and W%8==0 and H%8==0,f'{len(names["jour"])} calques × {len(modes)} modes')
check('2a. alpha 0/255 sauf OMBRES',all(set(np.unique(a[...,3]).tolist())<={0,255} for m in modes for a,f in zip(lay[m],names[m]) if 'OMBRES' not in f))
def mag(a):
    r,g,b=(a[...,i].astype(int) for i in range(3)); return int(((r>70)&(b>70)&(r>g*1.45)&(b>g*1.45)&(a[...,3]>0)).sum())
check('2b. zéro magenta résiduel',sum(mag(a) for m in modes for a in lay[m])==0)
for m in modes:
    sc=Image.new('RGBA',(W,H))
    for a,f in zip(lay[m],names[m]):
        if '_03_' in f and not f.endswith('PHASE00.png'): continue
        sc.alpha_composite(Image.fromarray(a))
    check(f'3. recomposition = scène ({m})',np.array_equal(np.array(sc),np.array(Image.open(HERE/'scene'/f'{m}.png').convert('RGBA'))))
j={f.split('_',3)[3]:a for a,f in zip(lay['jour'],names['jour'])}; n_={f.split('_',3)[3]:a for a,f in zip(lay['nuit'],names['nuit'])}
check('3b. nuit = filtre Abyss exact (calques 02+)',all(np.array_equal(np.array(night(Image.fromarray(j[k]))),n_[k]) for k in j if not k.startswith(('00','01'))))
ph=[a for a,f in zip(lay['jour'],names['jour']) if '_03_' in f]
check('4. phases eau : même alpha, couleurs différentes',len(ph)==man['phases_eau'] and all(np.array_equal(ph[0][...,3],p[...,3]) for p in ph) and all(not np.array_equal(ph[0][...,:3],p[...,:3]) for p in ph[1:]),f'{len(ph)} phases')
solid=np.zeros((H,W),bool)
for k,a in j.items():
    if k[:2] in ('07','08','09','10','11'): solid|=a[...,3]>0
sand=j['04_SABLE.png'][...,3]==255
for key in ['entree','donjon_seuil']:
    x,y=man['points'][key]; check(f'5. dégagement 16x16 {key}',not solid[y:y+16,x:x+16].any() and (sand|(j['05_SENTIER_ROCHE.png'][...,3]==255))[y:y+16,x:x+16].all(),f'({x},{y})')
free=(sand|(j['05_SENTIER_ROCHE.png'][...,3]==255))&~solid
er=nd.binary_erosion(free,iterations=16); lab,_=nd.label(er)
ex,ey=man['points']['entree']; sx,sy=man['points']['donjon_seuil']
check('6. corridor ≥32 px arrivée → seuil (même composante après érosion 16)',lab[ey+8,ex+8]>0 and lab[ey+8,ex+8]==lab[sy+8,sx+8] if lab[sy+8,sx+8]>0 else False)
g=j['08_GROTTE_PROFONDEUR.png'][...,3]==255; bb=man['points']['grotte_bbox']
check('7. grotte connexe ≥ 40x40',nd.label(g)[1]==1 and bb[2]-bb[0]>=40 and bb[3]-bb[1]>=40,f'bbox {bb}')
check('8. noms uniques BEACHSKY_V1_',len({f for m in modes for f in names[m]})==sum(len(names[m]) for m in modes))
shas={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((HERE/'couches').glob('*.png'))}
check('9. SHA-256 calques = manifeste',shas==man['sha256_couches'])
band=Image.open(HERE/'couches'/man['nuages']['bande']); check('10. bande nuages bouclable 1440x136',band.size==(1440,136))
(HERE/'verification.json').write_text(json.dumps({'all_pass':ok,'engine_tested':False,'tests':res},ensure_ascii=False,indent=2))
print('RÉSULTAT :','TOUS PASS' if ok else 'ÉCHECS','| test moteur : NON'); sys.exit(0 if ok else 1)
