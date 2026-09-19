# Beach/Sky étendue — lot `beachsky_v1`

Plage étendue type « Beach » (Sky) construite depuis la **composition validée par l'utilisateur** (1264×848 = 158×106 cellules de 8 px,
aucun rééchantillonnage), en **12 calques** × 3 modes (jour / crépuscule / nuit), eau animée par cycle de rampe.

- `valides/` : sable plein cadre + composition (validées, SHA dans `manifest.json`) · `bruts/` : éléments régénérés à l'identique sur magenta
- `couches/` : `BEACHSKY_V1_<JOUR|CREPUSCULE|NUIT>_NN_*.png` + `BEACHSKY_V1_NUAGES_BANDE_1440x136.png` (bande bouclable, −4 px/s)
- `scene/` : jour, crepuscule, nuit, `apercu_eau_animee.gif` · `apercu_beachsky_v1.html` : aperçu animé autonome
- `SPECIFICATION.md`, `build.py`, `verify.py` (13 contrôles PASS), `package.py`, `manifest.json`, `verification.json`

**Eau** : dans EoS l'eau des fonds est animée par cycle de palette (BPL) ; ici équivalent en 6 phases du calque 03 — quantification de
la rampe d'eau sur 12 teintes, rotation des 6 teintes claires (crêtes/écume tournent, masse stable), alpha identique entre phases.
**Crépuscule** : 55 % jour + 45 % filtre Abyss exact + voile chaud (+12, +2, −10) ; ciel = mélange 50/50 des ciels natifs jour/nuit.
**Nuit** : filtre Abyss exact (blob 438383f4), ciel nuit + astres natifs.

Limites : pas de test moteur (code 139) ; pixels générés ≠ tuiles canoniques ; aucune collision/script fournis ; l'ouverture est vers la
grotte NW (seuil (120,192)) — pas de sortie est définie ; le calque 01 est un instantané de la bande (utiliser la bande pour le défilement).
