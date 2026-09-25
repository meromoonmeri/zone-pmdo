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
N_PHASES = 8


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

# --- mer : géométrie = composition validée (eau + écume) ; texture = brut à bandes de vagues (mer_bandes_magenta),
# indexée comme la mer V2 du dépôt : base fixe + 8 indices de vagues qui tournent (palette cycling), écume fixe.
sea_geo = nd.binary_closing(sea_c | foam_c, iterations=2)
sea_geo = nd.binary_fill_holes(sea_geo) & ~nd.binary_dilation(sky_c, iterations=2)
labS, nS = nd.label(sea_geo); sS = np.bincount(labS.ravel()); sS[0] = 0; sea_geo = labS == sS.argmax()
bands = clean(key(load(BR / 'mer_bandes_magenta.png')), min_px=1)
ba = arr(bands); bm = ba[..., 3] == 255
# plaque pleine : chaque colonne prolongée vers le haut/bas à partir de ses pixels d'eau
full = ba.copy()
for x in range(W):
    ys = np.where(bm[:, x])[0]
    if len(ys):
        full[:ys.min(), x] = ba[ys.min(), x]; full[ys.max() + 1:, x] = ba[ys.max(), x]
        gaps = np.where(~bm[:, x])[0]; gaps = gaps[(gaps > ys.min()) & (gaps < ys.max())]
        for gy in gaps: full[gy, x] = ba[ys[ys < gy].max(), x]
full[..., 3] = 255
sea = Image.fromarray(full)
foam_geo = sea_geo & nd.binary_dilation(foam_c, iterations=1)
M = sea_geo
dist_shore = nd.distance_transform_edt(M)                                       # distance au bord de l'eau
deep = M & (dist_shore > 96)
near = M & ~deep
L_mer_prof = Image.fromarray(np.zeros((H, W, 4), 'uint8'))                        # réservé : base statique (vide, tout le plan cycle sur 03)

# ---------------------------------------------------------------------------------------------------------
# EAU CANONIQUE BEACH (mesurée sur references/beach_ref.png, rip Beach & Path to Beach) :
#  - base d'eau UNIE et FIXE (24,192,248) ; 19 couleurs en tout ;
#  - 9 frames DESSINÉES (pas de palette cycling) : une crête cyan + écume blanche naît en haut de la bande,
#    descend vers la plage en s'affaiblissant, la mer respire (petits traits), puis une houle bleu foncé
#    (16,88,216) renaît en haut avec écume et grossit → boucle ;
#  - rivage : 17 frames où l'écume monte sur le sable (sable mouillé ocre) puis se retire.
# Ici : mêmes principes, reconstruits sur la géométrie de la composition validée. Frames explicites (MANUEL §13).
# ---------------------------------------------------------------------------------------------------------
BASE = np.array([24, 192, 248]); WHITE = np.array([248, 248, 248])
CREST_LIGHT = np.array([144, 224, 232]); CREST_MID = np.array([72, 232, 248]); CREST_CYAN = np.array([112, 208, 248])
SWELL_DARK = np.array([16, 88, 216]); SWELL_MID = np.array([16, 112, 224]); SWELL_LIGHT = np.array([40, 152, 240])
RIPPLE = np.array([64, 208, 248])
WET_SAND = np.array([214, 168, 74]); WET_SAND2 = np.array([232, 196, 110])
N_WAVE, N_SHORE = 9, 17

yy, xx = np.mgrid[:H, :W]
# rivage principal = pour chaque colonne, première ligne d'eau (bord plage/mer) ; les vagues sont des lignes
# horizontales ondulées mesurées en y depuis ce rivage (comme le rip : bandes horizontales, pas concentriques)
shore_y = np.full(W, -1)
for x in range(W):
    ys = np.where(M[:, x])[0]
    if len(ys): shore_y[x] = ys.min()
shore_y = nd.uniform_filter1d(nd.median_filter(np.where(shore_y < 0, np.nanmedian(shore_y[shore_y >= 0]), shore_y), 41).astype(float), 25)
dist_in = np.where(M, yy - shore_y[None, :], -1).astype(float)                    # profondeur (px sous le rivage)
land_ring = land & ~M & (yy >= shore_y[None, :] - 20) & (yy < shore_y[None, :] + 2)
dist_sand = np.clip(shore_y[None, :] - yy, 0, None).astype(float)                 # hauteur sur le sable
wob = (3 * np.sin(xx / 31.0) + 1.5 * np.sin(xx / 13.0 + 0.9))


def band(center, thick, region):
    d = dist_in + wob
    return region & (d >= center - thick / 2) & (d < center + thick / 2)


def wave_frames():
    """9 frames : trajet d'une crête du large (d≈70) vers le rivage (d≈8), puis renaissance en houle sombre."""
    out = []
    # position de la crête principale par frame (distance au rivage) et intensité (0..1)
    path = [(30, 1.0), (24, .8), (18, .55), (12, .3), (8, .12), (0, 0), (0, 0), (60, .7), (48, 1.0)]
    for f in range(N_WAVE):
        a = np.zeros((H, W, 4), 'uint8'); a[M, :3] = BASE; a[M, 3] = 255
        # respiration : traits clairs épars, décalés à chaque frame (frames 3..6 surtout)
        rip = M & (((yy + f * 2) % 23 < 2) & ((xx // 6 + f) % 7 < 2)) & (dist_in > 14)
        a[rip, :3] = RIPPLE
        c, k = path[f]
        if k > 0 and f < 7:                                                      # crête cyan qui descend
            a[band(c, 5, M), :3] = CREST_CYAN
            a[band(c + 1, 2, M), :3] = CREST_MID
            if k >= .8: a[band(c + 2, 2, M) & ((xx // 9) % 3 != 0), :3] = WHITE
            elif k >= .5: a[band(c + 2, 1.5, M) & ((xx // 6) % 4 == 0), :3] = CREST_LIGHT
        if f >= 7:                                                               # houle sombre qui naît au large
            a[band(c, 9 if f == 8 else 6, M), :3] = SWELL_MID
            a[band(c + 2, 3, M), :3] = SWELL_DARK
            a[band(c - 3, 2, M), :3] = SWELL_LIGHT
            a[band(c - 4, 2 if f == 7 else 3, M) & ((xx // 7) % 5 != 0), :3] = WHITE
        # écume permanente au contact sable/eau (fine), plus forte quand la crête arrive (frames 3-5)
        foamw = 2 + (2 if f in (3, 4, 5) else 0)
        a[M & (dist_in <= foamw) & ((xx // 4 + f) % 5 != 0), :3] = WHITE
        a[~M] = 0
        out.append(Image.fromarray(a))
    return out


def shore_frames():
    """17 frames de rivage sur le SABLE : l'eau monte (sable mouillé + écume) puis se retire. Calque au-dessus du sable."""
    out = []
    reach = [0, 2, 6, 9, 11, 12, 12, 11, 10, 9, 8, 6, 4, 2, 1, 0, 0]              # avancée max en px sur le sable
    for f in range(N_SHORE):
        a = np.zeros((H, W, 4), 'uint8')
        r = reach[f]
        if r > 0:
            d = dist_sand + wob * .6
            wet = land_ring & (d <= r + 6)                                       # sable mouillé (reste après le retrait)
            a[wet, :3] = WET_SAND2; a[wet, 3] = 255
            wet2 = land_ring & (d <= r + 2)
            a[wet2, :3] = WET_SAND; a[wet2, 3] = 255
            film = land_ring & (d <= r)                                          # film d'eau
            a[film, :3] = (BASE * .55 + WHITE * .45).astype('uint8'); a[film, 3] = 255
            edge = land_ring & (d > r - 2) & (d <= r)                            # ligne d'écume
            a[edge, :3] = WHITE; a[edge, 3] = 255
        else:
            # sable humide résiduel très léger en fin de cycle (frames 15,16 : rien / frame 0 : rien)
            pass
        a[~land_ring] = 0
        out.append(Image.fromarray(a))
    return out


phases = wave_frames(); N_PHASES = len(phases); shore_phases = shore_frames()
L_mer_prof = Image.fromarray(np.zeros((H, W, 4), 'uint8'))                        # réservé (base incluse dans les frames)

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
man = {'lot': 'beachsky_v1', 'taille': [W, H], 'grille_px': 8, 'cellules': [W // 8, H // 8], 'phases_eau': N_PHASES, 'phases_rivage': N_SHORE,
       'eau': 'canon Beach (rip beach_ref.png mesuré) : base unie fixe (24,192,248) + 9 frames dessinées de vagues (crête cyan/écume qui naît au large, descend, s\'efface, houle sombre renaît) sur le calque 03 ; 17 frames de rivage sur le sable (écume monte, sable mouillé, retrait) sur le calque 04b ; frames explicites, FrameLength=10 ticks par défaut (cadence officielle non connue)',
       'nuages': {'bande': f'{PREFIX}_NUAGES_BANDE_1440x136.png', 'vitesse_px_s': -4, 'boucle': True},
       'modes': {}, 'bruts': {p.name: {'sha256': sha(p), 'taille': list(Image.open(p).size)} for p in sorted(list(BR.glob('*.png')) + list(VA.glob('*.png')))}}
for mode in ['jour', 'crepuscule', 'nuit']:
    f = mode_fn(mode)
    layers = [('00_CIEL', SKY[mode]), ('01_NUAGES', CLOUDS[mode])]
    layers += [(n, f(im)) for n, im in TERRAIN if n < '03']
    layers += [(f'03_MER_VAGUES_PHASE{p:02}', f(ph)) for p, ph in enumerate(phases)]
    layers += [(n, f(im)) for n, im in TERRAIN if n > '03' and n < '04z']
    layers += [(f'04b_RIVAGE_SABLE_PHASE{p:02}', f(ph)) for p, ph in enumerate(shore_phases)]
    layers += [(n, f(im)) for n, im in TERRAIN if n > '04z']
    names = []
    for n, im in layers:
        assert im.size == (W, H), n
        fn = f'{PREFIX}_{mode.upper()}_{n}.png'; im.save(COU / fn, optimize=True); names.append(fn)
    scene = Image.new('RGBA', (W, H))
    for n, im in layers:
        if ('PHASE' in n) and not n.endswith('PHASE00'): continue
        scene.alpha_composite(im)
    scene.save(SC / f'{mode}.png', optimize=True)
    man['modes'][mode] = {'calques': names, 'scene': f'scene/{mode}.png'}
    if mode == 'jour':                                                          # GIF d'aperçu (vagues 9 + rivage 17, boucle 153 frames)
        under = Image.new('RGBA', (W, H)); mid = Image.new('RGBA', (W, H)); over = Image.new('RGBA', (W, H))
        for n, im in layers:
            if 'PHASE' in n: continue
            if n < '03': under.alpha_composite(im)
            elif n < '04b': mid.alpha_composite(im)
            else: over.alpha_composite(im)
        frames = []
        for t in range(N_WAVE * 2):
            fr = under.copy(); fr.alpha_composite(phases[t % N_WAVE]); fr.alpha_composite(mid); fr.alpha_composite(shore_phases[t % N_SHORE]); fr.alpha_composite(over)
            frames.append(fr.crop((300, 480, 900, 848)).convert('P', palette=Image.ADAPTIVE, colors=128))
        frames[0].save(SC / 'apercu_eau_animee.gif', save_all=True, append_images=frames[1:], duration=167, loop=0)
# points clés
free = land & ~nd.binary_dilation(solid | cave, iterations=2)
man['points'] = {'entree': [640, 440], 'donjon_seuil': None}
cy, cx = (np.where(cave)[0].max() if cave.any() else 200), (int(np.where(cave)[1].mean()) if cave.any() else 120)
sx, sy = (cx // 8) * 8 + 24, (int(cy) // 8 + 1) * 8 + 8
man['points']['donjon_seuil'] = [int(sx), int(sy)]
man['points']['grotte_bbox'] = [int(v) for v in (np.where(cave)[1].min(), np.where(cave)[0].min(), np.where(cave)[1].max() + 1, np.where(cave)[0].max() + 1)] if cave.any() else None
man['sha256_couches'] = {p.name: sha(p) for p in sorted(COU.glob('*.png'))}
(HERE / 'manifest.json').write_text(json.dumps(man, ensure_ascii=False, indent=2))
print('grotte', man['points']['grotte_bbox'], 'seuil', man['points']['donjon_seuil'], '| frames vagues', N_WAVE, 'rivage', N_SHORE, '| calques/mode', len(man['modes']['jour']['calques']))
