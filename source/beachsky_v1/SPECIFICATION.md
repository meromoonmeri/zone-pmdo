# Spécification — Beach/Sky étendue (lot `beachsky_v1`)

Écrite avant la génération des calques (20 septembre 2026). Cible PMDO 0.8.12, import PNG to Tileset 8 px.

## Base validée par l'utilisateur
- `renders/beachsky_v1/valides/beachsky_02_composition_plage_validee.png` — **layout retenu**, 1264×848.
- `renders/beachsky_v1/valides/beachsky_01_sable_texture_plein_cadre.png` — plaque de sable plein cadre.
- 1264 = 158 × 8 et 848 = 106 × 8 : **taille native conservée, aucun rééchantillonnage** des calques.

## Fonction
Plage étendue de type « Beach » (Sky) : zone de promenade / événements, avec une **grotte au nord-ouest**
(entrée de donjon secondaire), la mer au sud, un sentier de roche menant à la grotte.

## Composition (lecture de la composition validée)
| Zone | Contenu |
|---|---|
| Nord (y ≈ 0–250) | bande de ciel, falaises rouges continues (style Sharpedo/Beach) |
| Nord-ouest | bouche de grotte sombre + sol de roche brune (sentier) |
| Centre | plage de sable jaune pâle à vaguelettes ; palmiers (2 bosquets), touffes d'herbe, rochers épars |
| Sud (y ≈ 560–848) | mer bleue : écume au rivage, eau proche claire, eau profonde plus foncée ; pointes rocheuses rouges à l'ouest, au centre-ouest et à l'est entrant dans l'eau |
| Est | falaise/rebord ocre plus clair descendant vers la mer |

## Bords
| Côté | État |
|---|---|
| Nord | fermé (falaises) sauf la grotte NW (seuil de donjon) |
| Sud | mer (non praticable) |
| Ouest | fermé (falaises + pointes rocheuses) |
| Est | fermé (falaise ocre + rochers) — une ouverture praticable pourra être définie en x ≈ 1180–1264, y ≈ 230–330 selon la découpe |

## Points clés (grille 8 px, à confirmer après découpe)
- `donjon_seuil` : devant la bouche NW, ≈ (120, 200), 16 × 16 libre.
- `entree` (arrivée) : centre de la plage ≈ (640, 440), 16 × 16 libre.
- Corridor libre ≥ 32 px : arrivée → seuil, par la plage puis le sentier de roche.
- Ligne de rivage : limite sable/écume, praticable jusqu'à l'écume exclue.

## Calques (arrière → avant), tous 1264 × 848, noms `BEACHSKY_V1_<MODE>_NN_*`
| NN | Calque | Origine |
|---|---|---|
| 00 | CIEL | natif (fond des lots côtiers, mosaïque sans lune) |
| 01 | NUAGES | natif, calque propre, bande bouclable défilante |
| 02 | MER_PROFONDE | eau régénérée sur magenta, zone au large |
| 03 | MER_RIVAGE_ECUME | eau proche + écume ; **phases d'animation** (voir eau) |
| 04 | SABLE | plaque validée, masquée à la terre ferme |
| 05 | SENTIER_ROCHE | sol de roche NW + rebord ocre est |
| 06 | OMBRES | calculées au pied des falaises, palmiers, rochers |
| 07 | FALAISES_NORD | falaises rouges + grotte (le vide de la grotte sur 08) |
| 08 | GROTTE_PROFONDEUR | vide sombre de la bouche |
| 09 | POINTES_ROCHEUSES | éperons entrant dans la mer + rochers dans l'eau |
| 10 | HERBES | touffes vertes (feuille sur magenta, instances) |
| 11 | PALMIERS | bosquets (feuille sur magenta, instances) |
| 12 | ROCHERS_EPARS | petits rochers sur le sable |

## Eau animée (canonique)
Dans Explorers, les fonds de maps ground (BPL/BPC/BPA) animent l'eau par **cycle de palette** (indices de
couleur qui tournent) et parfois par tuiles animées. PMDO n'a pas de palettes indexées : l'équivalent
livrable est **N phases** du calque eau (03, et 02 si nécessaire), obtenues par **rotation des teintes de
la rampe d'eau** (permutation circulaire des couleurs quantifiées de la rampe, sans nouveau dessin),
à jouer en boucle (≈ 8 phases, 120–150 ms). Les phases doivent être cohérentes entre elles (même
géométrie, seules les couleurs de la rampe tournent) — exigence AGENTS.md sur les eaux multi-phases.

## Modes
Jour (tel quel) · Nuit (filtre Abyss exact, calques 02–12 ; ciel nuit + astres natifs) ·
**Crépuscule** (nouveau) : interpolation 45 % vers le résultat du filtre nuit + voile chaud
(+12 R, +2 G, −10 B) ; ciel : dégradé dérivé du ciel jour/nuit natifs (mélange 50/50), sans régénération.

## Contrôles
Dimensions, alpha 0/255 (sauf ombres), zéro magenta, recomposition = scène, nuit = filtre exact,
corridor/dégagements, cohérence des phases d'eau (même alpha pour toutes), noms uniques, SHA-256.
Pas de test moteur (code 139).
