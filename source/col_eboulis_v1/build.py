"""Le col des Éboulis — assemblage en calques d'une entrée « Mont Horn » (chemin sud → nord).

Méthode : composition générée (H) → éléments régénérés à l'identique sur magenta → détourage →
calques séparés 640×640 → jour / nuit (filtre Abyss exact) → scène → manifeste.
Les bruts sont ramenés de 1024 px à 640 px par réduction *nearest* (pas d'étirement) ; la chaîne
lointaine (1376×768) est réduite à la largeur 640 par le même procédé.
"""
from pathlib import Path
import hashlib, json, sys
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage as nd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'outils'))
from night import night            # filtre nocturne exact d'Abyss (blob 438383f4)
from palette import key            # détourage magenta déjà utilisé par les lots magenta

S = 640                            # carte 640×640 = 80×80 cellules de 8 px
NN = Image.Resampling.NEAREST
BRUTS, COUCHES, SCENE = HERE / 'bruts', HERE / 'couches', HERE / 'scene'
for d in (COUCHES, SCENE): d.mkdir(exist_ok=True)
PREFIX = 'COLEBOULIS_V1'
rng = np.random.default_rng(20260919)


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(name): return Image.open(BRUTS / name).convert('RGBA')
def arr(im): return np.array(im)
def to_640(im): return im.resize((S, S), NN)


def clean_alpha(im, min_px=10):
    """Alpha strict 0/255, retrait des franges magenta résiduelles et des poussières isolées."""
    a = arr(im).copy()
    r, g, b = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
    opaque = a[..., 3] > 0
    pinkish = (r > g * 1.08) & (b > g * 1.08) & (r > 60) & (b > 60)
    edge = opaque & ~nd.binary_erosion(opaque, iterations=3)
    opaque &= ~(pinkish & edge)
    lab, n = nd.label(opaque, np.ones((3, 3)))
    if n:
        sizes = np.bincount(lab.ravel()); sizes[0] = 0
        opaque &= sizes[lab] >= min_px
    a[..., 3] = np.where(opaque, 255, 0).astype('uint8'); a[~opaque] = 0
    return Image.fromarray(a)


def keyed(name):
    return clean_alpha(key(to_640(load(name))))


def grade_clouds(im):
    """Formule des fonds Guilde/Sharpedo (nuages de nuit), identique aux lots côtiers."""
    a = arr(im).copy(); v = a[..., :3].astype(float)
    lum = (v @ np.array([.2126, .7152, .0722]))[..., None]
    a[..., :3] = np.rint((lum * .20 + v * .80) * np.array([.40, .42, .58]) + np.array([4, 8, 15])).clip(0, 255).astype('uint8')
    a[a[..., 3] == 0] = 0
    return Image.fromarray(a)


# ---------------------------------------------------------------- 1. composition de référence
H = to_640(load('composition_H.png'))
Hr = arr(H).astype(int); r, g, b = Hr[..., 0], Hr[..., 1], Hr[..., 2]
sand_H = (r > g) & (g > b) & (r - b > 40) & (r > 150)

# ---------------------------------------------------------------- 2. massif / rebords / entrée
massif_all = keyed('massif_magenta.png')
M = arr(massif_all)[..., 3] == 255
lab, n = nd.label(M, np.ones((3, 3)))
ledge = np.zeros_like(M)
for k, sl in enumerate(nd.find_objects(lab), 1):
    comp = lab == k
    if comp[-1].any() and sl[0].start >= int(S * .70):
        ledge |= comp
massif = M & ~ledge
# vide de la bouche : composante sombre la plus grande dans la fenêtre de l'entrée
rgb = arr(massif_all)[..., :3].astype(int)
dark = massif & (rgb.max(axis=2) < 64)
win = np.zeros_like(M); win[40:220, 232:408] = True
lab2, n2 = nd.label(dark & win, np.ones((3, 3)))
sizes = np.bincount(lab2.ravel()); sizes[0] = 0
mouth = nd.binary_fill_holes(nd.binary_opening(lab2 == sizes.argmax(), iterations=2))
mouth &= massif
massif_only = massif & ~mouth


def part(src, mask):
    a = arr(src).copy(); a[~mask] = 0; a[mask, 3] = 255
    return Image.fromarray(a)


L_massif = part(massif_all, massif_only)
L_mouth = part(massif_all, mouth)
L_ledge = part(massif_all, ledge)

# ---------------------------------------------------------------- 3. plateau (sol visible)
ground_mask = nd.binary_fill_holes(nd.binary_closing(sand_H | M, iterations=3))
ground_mask |= nd.binary_dilation(M, iterations=2)          # le sol continue sous les masses
ground_mask[-4:, :] |= sand_H[-4:, :]                        # bord sud ouvert conservé
labg, ng = nd.label(ground_mask); szg = np.bincount(labg.ravel()); szg[0] = 0
ground_mask = labg == szg.argmax()                            # plateau = composante principale seule
sol = to_640(load('sol_chemin.png'))
L_sol = part(sol, ground_mask)

# ---------------------------------------------------------------- 4. chaînes de montagnes
near = keyed('chaine_proche_magenta.png')
na = arr(near).copy()
for x in range(S):                                           # prolonger la base vers le bas
    ys = np.where(na[:, x, 3] == 255)[0]
    if len(ys) and ys.max() < S - 1:
        na[ys.max() + 1:, x] = na[ys.max(), x]
L_near = Image.fromarray(na)
far_src = load('chaine_lointaine_magenta.png')
fw, fh = far_src.size
far = clean_alpha(key(far_src.resize((S, round(fh * S / fw)), NN)))
canvas = Image.new('RGBA', (S, S)); canvas.alpha_composite(far, (0, 0))
L_far = canvas

# ---------------------------------------------------------------- 5. rochers épars
sheet = keyed('rochers_magenta.png')
sa = arr(sheet); lab3, n3 = nd.label(sa[..., 3] == 255, np.ones((3, 3)))
sprites = []
for k, sl in enumerate(nd.find_objects(lab3), 1):
    if sl is None: continue
    comp = (lab3 == k)
    if comp.sum() < 120: continue
    crop = sa[sl].copy(); crop[~comp[sl]] = 0
    sprites.append(Image.fromarray(crop))
sprites.sort(key=lambda im: -im.width)
sprites = sprites[:16]
free = ground_mask & ~nd.binary_dilation(M | ledge, iterations=14)
corridor_band = np.zeros_like(M); corridor_band[:, 248:392] = True
free &= ~corridor_band
free[:, :24] = free[:, -24:] = False; free[:180] = free[600:] = False
rocks = Image.new('RGBA', (S, S)); placed = []
ys, xs = np.where(free)
order = rng.permutation(len(ys))
for idx in order:
    if len(placed) >= 10: break
    y, x = int(ys[idx]), int(xs[idx])
    if any(abs(x - px) < 56 and abs(y - py) < 40 for px, py, *_ in placed): continue
    spr = sprites[len(placed) % len(sprites)]
    w = int(rng.integers(22, 38)); h = max(8, round(spr.height * w / spr.width))
    sp = spr.resize((w, h), NN)
    x0, y0 = (x - w // 2) // 8 * 8, (y - h) // 8 * 8            # ancrage grille 8 px
    if x0 < 0 or y0 < 0 or x0 + w > S or y0 + h > S: continue
    foot = np.zeros_like(M); foot[y0:y0 + h, x0:x0 + w] = arr(sp)[..., 3] == 255
    if (foot & ~free).any(): continue
    placed.append((x, y, x0, y0, w, h, len(placed) % len(sprites)))
placed.sort(key=lambda p: p[3] + p[5])
for x, y, x0, y0, w, h, k in placed:
    rocks.alpha_composite(sprites[k].resize((w, h), NN), (x0, y0))
L_rocks = clean_alpha(rocks, min_px=1)

# ---------------------------------------------------------------- 6. ombres calculées
solid = massif_only | ledge | (arr(L_rocks)[..., 3] == 255)
shifted = np.roll(np.roll(solid, 4, axis=0), 2, axis=1)
shadow = nd.binary_dilation(shifted, iterations=3) & ~solid & ~mouth & ground_mask
sh = Image.fromarray((shadow * 255).astype('uint8')).filter(ImageFilter.GaussianBlur(1.2))
sha_ = np.zeros((S, S, 4), dtype='uint8'); sha_[..., :3] = (62, 40, 18)
sha_[..., 3] = (np.array(sh) * .34).astype('uint8'); sha_[sha_[..., 3] == 0] = 0
sha_[..., 3][solid | mouth] = 0
L_shadow = Image.fromarray(sha_)

# ---------------------------------------------------------------- 7. fonds natifs (ciel, nuages, astres)
def tiled_sky(name):
    src = arr(Image.open(HERE / 'references' / name).convert('RGBA'))
    xs = np.arange(S) % 480; xs = np.where(xs < 240, xs, 479 - xs)      # moitié sans lune, en miroir
    rows = np.minimum(np.arange(S), src.shape[0] - 1)
    return Image.fromarray(src[rows[:, None], xs[None, :]])


clouds_src = Image.open(HERE / 'references' / 'fond_nuages_native.png').convert('RGBA')
crops = [(16, 24, 168, 72), (176, 8, 272, 72), (272, 16, 368, 64), (72, 80, 168, 128), (176, 72, 296, 128), (320, 64, 472, 128)]
dests = [(32, 40), (272, 16), (504, 72), (728, 32), (920, 80), (1160, 24)]
strip = Image.new('RGBA', (1440, 208))
for rect, dest in zip(crops, dests): strip.paste(clouds_src.crop(rect), dest)
clouds = Image.new('RGBA', (S, S)); clouds.alpha_composite(strip.crop((0, 0, S, 208)), (0, 0))
stars_src = Image.open(HERE / 'references' / 'fond_astres_nuit_native.png').convert('RGBA')
stars = Image.new('RGBA', (S, S)); stars.paste(stars_src, (S - 480, 0)); stars.paste(stars_src.crop((0, 0, 160, 184)), (0, 0))

SKY = {'jour': tiled_sky('fond_ciel_jour_native.png'), 'nuit': Image.alpha_composite(tiled_sky('fond_ciel_nuit_native.png'), stars)}
CLOUDS = {'jour': clouds, 'nuit': grade_clouds(clouds)}

# ---------------------------------------------------------------- 8. export des calques et scènes
TERRAIN = [('02_CHAINE_LOINTAINE', L_far), ('03_CHAINE_PROCHE', L_near), ('04_SOL_CHEMIN', L_sol),
           ('05_OMBRES', L_shadow), ('06_MASSIF_ET_BORDS', L_massif), ('07_ENTREE_PROFONDEUR', L_mouth),
           ('08_ROCHERS_EPARS', L_rocks), ('09_REBORDS_PREMIER_PLAN', L_ledge)]
manifest = {'lot': 'col_eboulis_v1', 'titre': 'Le col des Éboulis — chemin vers l’entrée de Mont Horn',
            'taille': [S, S], 'grille_px': 8, 'cellules': [S // 8, S // 8], 'cible': 'PMDO 0.8.12, import PNG to Tileset 8 px',
            'filtre_nuit': 'Abyss V4 tools/tile_night.py (blob 438383f4) via outils/night.py, calques 02–09 ; nuages : formule des fonds Guilde/Sharpedo',
            'bruts': {p.name: {'sha256': sha(p), 'taille': list(Image.open(p).size)} for p in sorted(BRUTS.glob('*.png'))},
            'composition_retenue': 'composition_H.png', 'compositions_ecartees': ['composition_G.png'],
            'reduction': 'nearest 1024→640 (facteur 0,625) ; chaîne lointaine 1376→640', 'variantes': {}, 'rochers': placed}
for mode in ['jour', 'nuit']:
    layers = [('00_CIEL', SKY[mode]), ('01_NUAGES', CLOUDS[mode])] + [(n, night(im) if mode == 'nuit' else im) for n, im in TERRAIN]
    scene = Image.new('RGBA', (S, S)); names = []
    for n, im in layers:
        assert im.size == (S, S), (n, im.size)
        fname = f'{PREFIX}_{mode.upper()}_{n}.png'; im.save(COUCHES / fname, optimize=True); names.append(fname)
        scene.alpha_composite(im)
    scene.save(SCENE / f'{mode}.png', optimize=True)
    manifest['variantes'][mode] = {'calques': names, 'scene': f'scene/{mode}.png'}

# points clés dérivés (grille 8 px)
col = massif_only[:, 312:328].any(axis=1)
steps_bottom = int(np.where(col[:320])[0].max())                 # dernière ligne de massif au-dessus du chemin
threshold = [312, (steps_bottom // 8 + 1) * 8]
manifest['points'] = {'donjon_seuil': threshold, 'entree': [312, 608], 'bouche_bbox': [int(v) for v in (np.where(mouth)[1].min(), np.where(mouth)[0].min(), np.where(mouth)[1].max() + 1, np.where(mouth)[0].max() + 1)],
                      'corridor': {'x': [304, 336], 'y': [threshold[1], S]}}
manifest['calques_ordre'] = ['00_CIEL', '01_NUAGES'] + [n for n, _ in TERRAIN]
manifest['couche_devant_personnage'] = ['09_REBORDS_PREMIER_PLAN']
manifest['sha256_couches'] = {p.name: sha(p) for p in sorted(COUCHES.glob('*.png'))}
(HERE / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
print('composantes massif:', n, '| rebords px:', int(ledge.sum()), '| bouche bbox:', manifest['points']['bouche_bbox'],
      '| seuil:', threshold, '| rochers placés:', len(placed), '| sprites:', len(sprites))
