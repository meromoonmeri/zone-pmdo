"""Beach/Sky étendue — calques 1264×848 depuis la composition validée + éléments régénérés sur magenta.
Modes : jour, crepuscule, nuit. Eau : 8 phases par rotation de la rampe de couleurs (équivalent palette cycling).
Aucun rééchantillonnage : tous les bruts sont déjà à la taille native 1264×848 (158×106 cellules de 8 px)."""
from pathlib import Path
import hashlib, json, sys
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage as nd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'outils'))
from night import night
from palette import key
W, H = 1264, 848
assert W % 8 == 0 and H % 8 == 0
BR, VA, COU, SC = HERE / 'bruts', HERE / 'valides', HERE / 'couches', HERE / 'scene'
for d in (COU, SC): d.mkdir(exist_ok=True)
PREFIX = 'BEACHSKY_V1'
N_PHASES = 12


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p): return Image.open(p).convert('RGBA')
def arr(im): return np.array(im)


def clean(im, min_px=12):
    a = arr(im).copy(); r, g, b = (a[..., i].astype(int) for i in range(3))
    op = a[..., 3] > 0
    pink = (r > g * 1.08) & (b > g * 1.08) & (r > 60) & (b > 60)
    edge = op & ~nd.binary_erosion(op, iterations=3)
    op &= ~(pink & edge)
    lab, n = nd.label(op, np.ones((3, 3)))
    if n:
        s = np.bincount(lab.ravel()); s[0] = 0; op &= s[lab] >= min_px
    a[..., 3] = np.where(op, 255, 0).astype('uint8'); a[~op] = 0
    return Image.fromarray(a)


def part(src, mask):
    a = arr(src).copy(); a[~mask] = 0; a[mask, 3] = 255
    return Image.fromarray(a)


comp = load(VA / 'beachsky_02_composition_plage_validee.png')
C = arr(comp)[..., :3].astype(int); r, g, b = C[..., 0], C[..., 1], C[..., 2]
sand_c = (r > 200) & (g > 190) & (b > 110) & (b < 200) & (r - b > 30)          # sable jaune pâle
sea_c = (b > r + 40) & (b > 120)                                                 # eau
foam_c = (r > 225) & (g > 235) & (b > 235)
sky_c = (b > r + 20) & (b > 150) & (g > 150) & (np.arange(H)[:, None] < 130)      # ciel pâle en bande nord
sea_c &= ~sky_c

# --- roches rouges : falaises nord / éperons & rochers / vide de la grotte
rocks = clean(key(load(BR / 'roches_rouges_magenta.png')))
R = arr(rocks)[..., 3] == 255
rgb = arr(rocks)[..., :3].astype(int)
dark = R & (rgb.max(axis=2) < 70)
win = np.zeros_like(R); win[100:260, 40:240] = True
lab, n = nd.label(dark & win, np.ones((3, 3)))
s = np.bincount(lab.ravel()); s[0] = 0
cave = nd.binary_fill_holes(nd.binary_closing(lab == s.argmax(), iterations=2)) if n else np.zeros_like(R)
cave &= R
labR, nR = nd.label(R, np.ones((3, 3)))
north = np.zeros_like(R)
for k, sl in enumerate(nd.find_objects(labR), 1):
    if sl[0].start < 40: north |= labR == k                                    # touche la bande nord
spurs = R & ~north
L_falaises = part(rocks, north & ~cave); L_grotte = part(rocks, cave); L_pointes = part(rocks, spurs)

# --- végétation : palmiers vs herbes (par taille de composante)
veg = clean(key(load(BR / 'vegetation_magenta.png')))
V = arr(veg)[..., 3] == 255
labV, nV = nd.label(nd.binary_dilation(V, iterations=2), np.ones((3, 3)))
palms = np.zeros_like(V)
for k, sl in enumerate(nd.find_objects(labV), 1):
    if (labV == k).sum() > 2500: palms |= (labV == k) & V
L_palmiers = part(veg, palms); L_herbes = part(veg, V & ~palms)

# --- sentier de roche + rebord ocre
L_sentier = clean(key(load(BR / 'sentier_roche_magenta.png')))
S_ = arr(L_sentier)[..., 3] == 255

# --- sable : plaque validée masquée à la terre ferme (composition : non-mer, non-ciel)
sable_plate = load(VA / 'beachsky_01_sable_texture_plein_cadre.png')
water = nd.binary_closing(sea_c | foam_c, iterations=2)
land = ~water & ~sky_c
land = nd.binary_opening(land, iterations=2) | (nd.binary_dilation(R | V | S_, iterations=2) & ~water)
above_rock = np.cumsum(R, axis=0) == 0                                          # rien de rocheux au-dessus = ciel
land &= ~(above_rock & (np.arange(H)[:, None] < 140))
land &= ~nd.binary_dilation(water & ~R, iterations=1)
labL, nL = nd.label(land); sL = np.bincount(labL.ravel()); sL[0] = 0; land = labL == sL.argmax()
L_sable = part(sable_plate, land)

# --- mer : plaque continue ; rivage/écume vs large ; phases par rotation de rampe
sea = clean(key(load(BR / 'mer_magenta.png')))
M = arr(sea)[..., 3] == 255
for x in range(W):                                                                # prolonger vers le haut sous le sable
    ys = np.where(M[:, x])[0]
    if len(ys):
        top = ys.min(); a_ = arr(sea); a_[:top, x] = a_[top, x]; sea = Image.fromarray(a_); M[:top, x] = True
sea_a = arr(sea)
sea_rgb = sea_a[..., :3].astype(int)
lum = sea_rgb.sum(axis=2)
deep = M & (lum < 430); near = M & ~deep
L_mer_prof = part(sea, deep)


def water_phases(img, mask, n):
    """Cycle de palette : l'eau est quantifiée sur une rampe courte de n teintes (comme une palette EoS),
    puis chaque phase décale les indices d'un cran ; l'écume (blancs) reste fixe. Géométrie et alpha inchangés."""
    a = arr(img); rgb = a[..., :3].astype(int)
    foam = mask & (rgb.min(axis=2) > 215)
    cyc = mask & ~foam
    lum = (rgb[..., 0] * .3 + rgb[..., 1] * .59 + rgb[..., 2] * .11)
    lo, hi = np.percentile(lum[cyc], [1, 99])
    idx = np.clip(((lum - lo) / max(hi - lo, 1) * n).astype(int), 0, n - 1)
    ramp = np.array([rgb[cyc & (idx == i)].mean(axis=0) if (cyc & (idx == i)).any() else [0, 0, 0] for i in range(n)])
    out = []
    for p in range(n):
        b_ = a.copy(); b_[~mask] = 0; b_[mask, 3] = 255
        # seules les teintes claires (crêtes) tournent ; la base sombre reste fixe (cycle EoS partiel)
        k = n // 2; hi_ = cyc & (idx >= n - k)
        b_[hi_, :3] = np.rint(ramp[n - k + ((idx[hi_] - (n - k) + p) % k)]).astype('uint8')
        out.append(Image.fromarray(b_))
    return out, n


phases, ncols = water_phases(sea, near, N_PHASES)
phases = phases[:N_PHASES // 2]                                                  # k = n/2 phases distinctes
N_PHASES = len(phases)

# --- ombres calculées
solid = north | spurs | palms | S_
shift = np.roll(np.roll(solid, 5, 0), 3, 1)
shadow = nd.binary_dilation(shift, iterations=2) & ~solid & ~cave & land
sh = Image.fromarray((shadow * 255).astype('uint8')).filter(ImageFilter.GaussianBlur(1.2))
sa = np.zeros((H, W, 4), 'uint8'); sa[..., :3] = (70, 45, 30); sa[..., 3] = (np.array(sh) * .32).astype('uint8')
sa[..., 3][solid | cave] = 0; sa[sa[..., 3] == 0] = 0
L_ombres = Image.fromarray(sa)

# --- fonds natifs
def tiled_sky(name):
    src = arr(Image.open(HERE / 'references' / name).convert('RGBA'))
    xs = np.arange(W) % 480; xs = np.where(xs < 240, xs, 479 - xs)
    rows = np.minimum(np.arange(H), src.shape[0] - 1)
    return Image.fromarray(src[rows[:, None], xs[None, :]])


cl = Image.open(HERE / 'references/fond_nuages_native.png').convert('RGBA')
crops = [(16, 24, 168, 72), (176, 8, 272, 72), (272, 16, 368, 64), (72, 80, 168, 128), (176, 72, 296, 128), (320, 64, 472, 128)]
dests = [(32, 40), (272, 16), (504, 72), (728, 32), (920, 80), (1160, 24)]
strip = Image.new('RGBA', (1440, 208))
for rect, d in zip(crops, dests): strip.paste(cl.crop(rect), d)
strip = strip.crop((0, 0, 1440, 136))                                            # bande bouclable
strip.save(COU / f'{PREFIX}_NUAGES_BANDE_1440x136.png')
clouds = Image.new('RGBA', (W, H)); clouds.alpha_composite(strip.crop((0, 0, W, 136)), (0, 0))
stars_src = Image.open(HERE / 'references/fond_astres_nuit_native.png').convert('RGBA')
stars = Image.new('RGBA', (W, H))
for x in range(0, W, 480): stars.paste(stars_src.crop((0, 0, 240, 184)) if x + 480 < W else stars_src, (x, 0))
sky_j, sky_n = tiled_sky('fond_ciel_jour_native.png'), tiled_sky('fond_ciel_nuit_native.png')


def grade_clouds(im):
    a = arr(im).copy(); v = a[..., :3].astype(float); l = (v @ [.2126, .7152, .0722])[..., None]
    a[..., :3] = np.rint((l * .2 + v * .8) * [.40, .42, .58] + [4, 8, 15]).clip(0, 255).astype('uint8'); a[a[..., 3] == 0] = 0
    return Image.fromarray(a)


def dusk(im):
    """Crépuscule : 45 % vers le filtre nuit exact + voile chaud ; alpha inchangé."""
    a = arr(im).copy(); n_ = arr(night(im)).astype(float); d = a[..., :3].astype(float)
    mix = d * .55 + n_[..., :3] * .45 + np.array([12, 2, -10])
    a[..., :3] = mix.clip(0, 255).astype('uint8'); a[a[..., 3] == 0] = 0
    return Image.fromarray(a)


def mode_fn(mode): return {'jour': lambda im: im, 'nuit': night, 'crepuscule': dusk}[mode]


SKY = {'jour': sky_j, 'nuit': Image.alpha_composite(sky_n, stars),
       'crepuscule': Image.blend(sky_j, sky_n, .5)}
CLOUDS = {'jour': clouds, 'nuit': grade_clouds(clouds), 'crepuscule': Image.blend(clouds, grade_clouds(clouds), .5)}

TERRAIN = [('02_MER_PROFONDE', L_mer_prof), ('04_SABLE', L_sable), ('05_SENTIER_ROCHE', L_sentier), ('06_OMBRES', L_ombres),
           ('07_FALAISES_NORD', L_falaises), ('08_GROTTE_PROFONDEUR', L_grotte), ('09_POINTES_ROCHEUSES', L_pointes),
           ('10_HERBES', L_herbes), ('11_PALMIERS', L_palmiers)]
man = {'lot': 'beachsky_v1', 'taille': [W, H], 'grille_px': 8, 'cellules': [W // 8, H // 8], 'phases_eau': N_PHASES,
       'eau': f'calque 03 en {N_PHASES} phases : rotation circulaire de la rampe de {ncols} teintes quantifiées (équivalent palette cycling EoS), géométrie et alpha identiques ; cadence suggérée 130 ms',
       'nuages': {'bande': f'{PREFIX}_NUAGES_BANDE_1440x136.png', 'vitesse_px_s': -4, 'boucle': True},
       'modes': {}, 'bruts': {p.name: {'sha256': sha(p), 'taille': list(Image.open(p).size)} for p in sorted(list(BR.glob('*.png')) + list(VA.glob('*.png')))}}
for mode in ['jour', 'crepuscule', 'nuit']:
    f = mode_fn(mode)
    layers = [('00_CIEL', SKY[mode]), ('01_NUAGES', CLOUDS[mode])]
    layers += [(n, f(im)) for n, im in TERRAIN if n < '03']
    layers += [(f'03_MER_RIVAGE_PHASE{p:02}', f(ph)) for p, ph in enumerate(phases)]
    layers += [(n, f(im)) for n, im in TERRAIN if n > '03']
    names = []
    for n, im in layers:
        assert im.size == (W, H), n
        fn = f'{PREFIX}_{mode.upper()}_{n}.png'; im.save(COU / fn, optimize=True); names.append(fn)
    scene = Image.new('RGBA', (W, H))
    for n, im in layers:
        if n.startswith('03_') and not n.endswith('PHASE00'): continue
        scene.alpha_composite(im)
    scene.save(SC / f'{mode}.png', optimize=True)
    man['modes'][mode] = {'calques': names, 'scene': f'scene/{mode}.png'}
    if mode == 'jour':                                                          # GIF d'aperçu de l'animation de l'eau
        frames = []
        base = Image.new('RGBA', (W, H))
        for n, im in layers:
            if n < '03': base.alpha_composite(im)
        over = Image.new('RGBA', (W, H))
        for n, im in layers:
            if n > '03' and not n.startswith('03'): over.alpha_composite(im)
        for p, ph in enumerate(phases):
            fr = base.copy(); fr.alpha_composite(ph); fr.alpha_composite(over)
            frames.append(fr.crop((300, 480, 900, 848)).convert('P', palette=Image.ADAPTIVE, colors=128))
        frames[0].save(SC / 'apercu_eau_animee.gif', save_all=True, append_images=frames[1:], duration=130, loop=0)
# points clés
free = land & ~nd.binary_dilation(solid | cave, iterations=2)
man['points'] = {'entree': [640, 440], 'donjon_seuil': None}
cy, cx = (np.where(cave)[0].max() if cave.any() else 200), (int(np.where(cave)[1].mean()) if cave.any() else 120)
sx, sy = (cx // 8) * 8 + 24, (int(cy) // 8 + 1) * 8 + 8
man['points']['donjon_seuil'] = [int(sx), int(sy)]
man['points']['grotte_bbox'] = [int(v) for v in (np.where(cave)[1].min(), np.where(cave)[0].min(), np.where(cave)[1].max() + 1, np.where(cave)[0].max() + 1)] if cave.any() else None
man['sha256_couches'] = {p.name: sha(p) for p in sorted(COU.glob('*.png'))}
(HERE / 'manifest.json').write_text(json.dumps(man, ensure_ascii=False, indent=2))
print('grotte', man['points']['grotte_bbox'], 'seuil', man['points']['donjon_seuil'], '| teintes eau', ncols, '| calques/mode', len(man['modes']['jour']['calques']))
