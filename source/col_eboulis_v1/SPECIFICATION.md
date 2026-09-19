# Spécification — « Le col des Éboulis » : chemin vers l’entrée canonique de Mont Horn

Lot `col_eboulis_v1` · cible PMDO 0.8.12 · import utilisateur *PNG to Tileset*, tuile **8 px** ·
19 septembre 2026. Écrite **avant** les générations retenues (étape 2 de la méthode).

## Historique des consignes (résumé)
1. Choix initial : nouvelle entrée de donjon indépendante, biome montagne/pic, jour + nuit.
2. Propositions A/B (Mont Horn-like, ocre / portail gris) → correction : « ne pas changer les
   textures, seulement le layout : chemin sud → nord, montagnes de chaque côté, roche marron ».
3. Propositions C/D/E (cônes bruns type Steam Cave) → correction finale :
   > « Tu reprends Mont Horn et tu fais en plusieurs layers le chemin vers l’entrée canonique de
   > Mont Horn, de face, chemin sud vers nord, avec l’altitude : en contrebas, des chaînes de
   > montagne au loin. Élabore plusieurs layers. »
   Les propositions A–E sont écartées (leurs bruts ont été perdus dans la réinitialisation de la
   sandbox ; seule une trace réduite de A est conservée dans `references/`).

## Régime de textures
Nouvelle entrée indépendante (règle du 13 septembre 2026) : textures générées dans la DA PMD,
livrées en calques séparés. **Référence de texture et d’entrée : `Mt_Horn_entrance_Sky.png`**
(canonique, 552 × 360) : strates ocre empilées, bouche sombre surélevée avec marches, ligne de
rochers bas au bord du plateau, pics lointains. Aucune recoloration. Les pixels canoniques ne sont
pas copiés ; le générateur reproduit la matière et la construction.

## Fonction
Entrée de donjon vue **de face** : le héros arrive par le **bord sud**, monte le chemin vers le
**nord** jusqu’aux marches de la bouche, peut revenir en arrière. Sensation d’**altitude** : le
plateau domine des chaînes de montagnes lointaines situées **en contrebas**.

## Dimensions et grille
- Carte **640 × 640 px** = **80 × 80 cellules** de 8 px. Positions de la spec sur la grille 8 px.
- Bruts générés ramenés à 640 × 640 par recadrage sans étirement puis réduction *nearest*
  (pratique admise pour les générations — `applewoods_skygrass_v1` — jamais pour des tuiles natives).

## Composition
| Zone | Description |
|---|---|
| Haut-centre | massif porteur de la bouche (≈ 45–55 % de la largeur), bouche centrée x ≈ 320, ouverture 56–72 px, seuil y ≈ 152–208, trois marches vers le sud |
| Haut-gauche / haut-droite | vide : ciel, puis **chaîne lointaine** (pâle, brumeuse) et **chaîne proche** (plus contrastée), toutes deux sous la ligne du plateau |
| Côtés du plateau | lignes de rochers bas ocre (comme à gauche de Mont Horn) marquant le bord du vide |
| Centre | plateau de sable/roche beige, sentier usé du bord sud aux marches |
| Bas-gauche / bas-droite | rebords de falaise vus de face (comme le bas de Mont Horn), **interrompus au centre** pour laisser le chemin ouvert |

## Côtés
| Côté | État |
|---|---|
| Sud | **ouvert** : chemin ≥ 96 px de large centré (x ≈ 272…368) |
| Nord | massif au centre ; ciel/chaînes de part et d’autre (non praticable : bord du vide tenu par les rochers bas) |
| Ouest / Est | bord du vide tenu par les rochers bas puis les rebords de premier plan |

## Points clés (grille 8 px, confirmés sur la composition retenue dans `manifest.json`)
| Élément | Position visée | Contrôle |
|---|---|---|
| Seuil `donjon_seuil` | (312, y_seuil) 16 × 16 au pied des marches | libre de tout pixel opaque des calques 05–08 |
| Arrivée `entree` | (312, 608) 16 × 16, bord sud | idem |
| Corridor | polyligne arrivée → seuil, **largeur ≥ 32 px** | idem |
| Bouche | composante sombre connexe ≥ 40 × 40 px autour de (320, 130) | lisible à l’échelle d’un sprite de 32 px |

## Calques livrés (arrière → avant), tous 640 × 640, noms uniques `COLEBOULIS_V1_<JOUR|NUIT>_NN_*.png`
| NN | Calque | Origine |
|---|---|---|
| 00 | `CIEL` | fond natif Guilde/Sharpedo du pipeline (jour) ; ciel nuit + astres natifs (nuit) |
| 01 | `CHAINE_LOINTAINE` | générée sur magenta, détourée |
| 02 | `CHAINE_PROCHE` | générée sur magenta, détourée |
| 03 | `SOL_CHEMIN` | plein cadre généré (reconstitue aussi le sol caché) |
| 04 | `OMBRES` | **calculées** au pied des masses (alpha intermédiaire autorisé, cf. *Crooked Cavern Shadows*) |
| 05 | `MASSIF_ET_BORDS` | massif de l’entrée + lignes de rochers bas, générés sur magenta |
| 06 | `ENTREE_PROFONDEUR` | vide de la bouche extrait du massif |
| 07 | `ROCHERS_EPARS` | feuille générée sur magenta, instances hors corridor |
| 08 | `REBORDS_PREMIER_PLAN` | rebords bas-gauche / bas-droite ; couche **devant** le personnage (`Top`) |

## Variantes
Jour = couleurs générées détourées. Nuit = filtre nocturne **exact d’Abyss** (`outils/night.py`,
copie de `source/cote_v4_abyss/night.py`, blob `438383f4`) sur les calques 01–08 ; ciel nuit +
astres natifs ; nuages passés par la formule des fonds Guilde/Sharpedo. Aucune régénération.

## Interdits transmis au générateur
Pokémon, personnages, texte, interface, maisons, arbres, panneaux, ponts, torches, coffres ;
ombres portées peintes sur le sol.

## Contrôles avant livraison
1. 640 × 640 et divisible par 8 pour chaque calque ; 2. alpha 0/255 sauf `OMBRES`, zéro magenta
résiduel ; 3. recomposition des calques = scène (jour et nuit) ; 4. corridor 32 px + dégagements
16 × 16 ; 5. bouche connexe ≥ 40 × 40 ; 6. sud ouvert ≥ 96 px, rebords absents devant le chemin ;
7. noms uniques, SHA-256 des bruts et des calques dans `manifest.json`.

## Limites
Pas de test moteur PMDO ici (échec code 139 documenté au dépôt). Contrôles de fichiers, pas de
collisions en mouvement ni de rendu en jeu. Pixels générés ≠ tuiles canoniques ; pas d’attribution
à un artiste humain. Mont Horn © Pokémon / Nintendo / Creatures / GAME FREAK / Chunsoft.
