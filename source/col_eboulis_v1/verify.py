"""Audit avant livraison — Le col des Éboulis (contrôles de fichiers, pas de test moteur)."""
from pathlib import Path
import hashlib, json, sys
import numpy as np
from PIL import Image
from scipy import ndimage as nd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'outils'))
from night import night
man = json.loads((HERE / 'manifest.json').read_text())
S = man['taille'][0]; results = []; ok_all = True


def check(name, cond, detail=''):
    global ok_all
    ok_all &= bool(cond); results.append({'test': name, 'pass': bool(cond), 'detail': detail})
    print(('PASS' if cond else 'FAIL'), name, detail)


def load(fname): return np.array(Image.open(HERE / 'couches' / fname).convert('RGBA'))


layers = {m: [load(f) for f in man['variantes'][m]['calques']] for m in ['jour', 'nuit']}
names = man['variantes']['jour']['calques']
# 1. dimensions
check('1. dimensions 640x640 divisibles par 8', all(a.shape[:2] == (S, S) and S % 8 == 0 for m in layers for a in layers[m]), f'{len(names)} calques × 2 variantes')
# 2. alpha strict et magenta
strict = [i for i, n in enumerate(names) if 'OMBRES' not in n]
check('2a. alpha strictement 0/255 (sauf OMBRES)', all(set(np.unique(layers[m][i][..., 3]).tolist()) <= {0, 255} for m in layers for i in strict))
def magenta(a):
    r, g, b = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
    return ((r > 70) & (b > 70) & (r > g * 1.45) & (b > g * 1.45) & (a[..., 3] > 0)).sum()
check('2b. zéro pixel magenta résiduel', sum(magenta(a) for m in layers for a in layers[m]) == 0)
# 3. recomposition = scène
for m in layers:
    sc = Image.new('RGBA', (S, S))
    for a in layers[m]: sc.alpha_composite(Image.fromarray(a))
    ref = np.array(Image.open(HERE / 'scene' / f'{m}.png').convert('RGBA'))
    check(f'3. recomposition des calques = scène ({m})', np.array_equal(np.array(sc), ref))
# 3b. nuit = filtre exact appliqué au jour (calques 02–09)
same = all(np.array_equal(np.array(night(Image.fromarray(layers['jour'][i]))), layers['nuit'][i]) for i, n in enumerate(names) if n.split('_')[3] not in ('00', '01'))
check('3b. calques nuit = filtre Abyss exact des calques jour (02–09)', same)
# 4. corridor et dégagements
solid = np.zeros((S, S), bool)
for i, n in enumerate(names):
    if n.split('_')[3] in ('06', '07', '08', '09'): solid |= layers['jour'][i][..., 3] > 0
ground = layers['jour'][[i for i, n in enumerate(names) if '04_SOL' in n][0]][..., 3] == 255
x0, x1 = man['points']['corridor']['x']; y0, y1 = man['points']['corridor']['y']
corr = solid[y0:y1, x0:x1]
check('4a. corridor 32 px libre du seuil au bord sud', not corr.any() and ground[y0:y1, x0:x1].all(), f'x {x0}-{x1}, y {y0}-{y1}')
for key in ['donjon_seuil', 'entree']:
    x, y = man['points'][key]
    check(f'4b. dégagement 16x16 {key}', not solid[y:y + 16, x:x + 16].any() and ground[y:y + 16, x:x + 16].all(), f'({x},{y})')
# 5. bouche
mouth = layers['jour'][[i for i, n in enumerate(names) if '07_ENTREE' in n][0]][..., 3] == 255
lab, k = nd.label(mouth); bb = man['points']['bouche_bbox']
check('5. bouche connexe ≥ 40x40 autour de (320,130)', k == 1 and (bb[2] - bb[0]) >= 40 and (bb[3] - bb[1]) >= 40 and bb[0] < 320 < bb[2] and bb[1] < 130 < bb[3], f'bbox {bb}')
# 6. sud ouvert, rebords hors du chemin
bottom = solid[-1]; opening = ~bottom[272:368]
ledge = layers['jour'][[i for i, n in enumerate(names) if '09_REBORDS' in n][0]][..., 3] > 0
check('6a. bord sud ouvert sur ≥ 96 px centrés', opening.all() and ground[-1, 272:368].all())
check('6b. rebords uniquement dans les coins bas', not ledge[:, 248:392].any() and np.where(ledge)[0].min() >= S * .70)
# 7. noms uniques et SHA
check('7a. noms de fichiers uniques préfixés COLEBOULIS_V1_', len(set(names)) == len(names) and all(n.startswith('COLEBOULIS_V1_') for n in names))
shas = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((HERE / 'couches').glob('*.png'))}
check('7b. SHA-256 des calques identiques au manifeste', shas == man['sha256_couches'])
bruts_ok = all(hashlib.sha256((HERE / 'bruts' / n).read_bytes()).hexdigest() == v['sha256'] for n, v in man['bruts'].items())
check('7c. SHA-256 des bruts identiques au manifeste', bruts_ok, f'{len(man["bruts"])} bruts')
# 8. rochers hors corridor et sur le sol
rocks = layers['jour'][[i for i, n in enumerate(names) if '08_ROCHERS' in n][0]][..., 3] > 0
check('8. rochers épars sur le plateau, hors corridor', (rocks & ~ground).sum() == 0 and not rocks[:, 248:392].any(), f'{nd.label(rocks)[1]} instances')

(HERE / 'verification.json').write_text(json.dumps({'all_pass': ok_all, 'engine_tested': False, 'tests': results}, ensure_ascii=False, indent=2))
print('\nRÉSULTAT :', 'TOUS PASS' if ok_all else 'ÉCHECS', '| test moteur PMDO : NON effectué')
sys.exit(0 if ok_all else 1)
