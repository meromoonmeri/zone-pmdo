# Beach/Sky étendue — lot `beachsky_v1`

Plage étendue type « Beach » (Sky) construite depuis la **composition validée par l'utilisateur** (1264×848 = 158×106 cellules de 8 px,
aucun rééchantillonnage), en **12 calques (+ 9 frames vagues + 17 frames rivage)** × 3 modes (jour / crépuscule / nuit), eau animée par cycle de rampe.

- `valides/` : sable plein cadre + composition (validées, SHA dans `manifest.json`) · `bruts/` : éléments régénérés à l'identique sur magenta
- `couches/` : `BEACHSKY_V1_<JOUR|CREPUSCULE|NUIT>_NN_*.png` + `BEACHSKY_V1_NUAGES_BANDE_1440x136.png` (bande bouclable, −4 px/s)
- `scene/` : jour, crepuscule, nuit, `apercu_eau_animee.gif` · `apercu_beachsky_v1.html` : aperçu animé autonome
- `SPECIFICATION.md`, `build.py`, `verify.py` (13 contrôles PASS), `package.py`, `manifest.json`, `verification.json`

**Eau (canon Beach, mesuré sur `references/beach_ref.png`)** : ce n'est PAS du palette cycling. Base d'eau unie fixe (24,192,248) ;
calque 03 = **9 frames dessinées** : crête cyan + écume qui naît au large, descend vers la plage, s'efface, la mer respire, puis une
houle bleu foncé (16,88,216) renaît en haut ; calque 04b = **17 frames de rivage** posées sur le sable : l'écume monte (film d'eau,
sable mouillé) puis se retire. Frames explicites (MANUEL §13), cadence 10 ticks par défaut (cadence officielle non connue), les
deux cycles tournent indépendamment (9 et 17). Les versions antérieures (rotation de rampe, cycling V2) sont retirées.
Voir `COMMENT_JE_FAIS_LES_MAPS.md` §6 pour la mesure.
**Crépuscule** : 55 % jour + 45 % filtre Abyss exact + voile chaud (+12, +2, −10) ; ciel = mélange 50/50 des ciels natifs jour/nuit.
**Nuit** : filtre Abyss exact (blob 438383f4), ciel nuit + astres natifs.

Limites : pas de test moteur (code 139) ; pixels générés ≠ tuiles canoniques ; aucune collision/script fournis ; l'ouverture est vers la
grotte NW (seuil (120,192)) — pas de sortie est définie ; le calque 01 est un instantané de la bande (utiliser la bande pour le défilement).
