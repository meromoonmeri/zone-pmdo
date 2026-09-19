# Le col des Éboulis — entrée « Mont Horn » en calques (lot `col_eboulis_v1`)

Chemin **sud → nord** vers l’entrée canonique de Mont Horn vue **de face**, plateau en **altitude**
dominant deux chaînes de montagnes en contrebas, livré en **10 calques** 640 × 640, **jour + nuit**.

## Arborescence (dans le dépôt)
```
source/col_eboulis_v1/      SPECIFICATION.md (écrite avant génération), build.py, verify.py, package.py,
                            outils/night.py (copie du filtre Abyss), outils/palette.py (détourage magenta),
                            references/fond_*.png (ciel/nuages/astres natifs des lots côtiers)
renders/col_eboulis_v1/     bruts/ (générations, SHA-256 dans manifest.json), couches/ (20 PNG), scene/ (jour, nuit, planche)
apercu_col_eboulis_v1.html  aperçu autonome : calques togglables, jour/nuit, zoom, grille 8 px, marqueurs, audit
```

## Méthode appliquée (les 7 étapes)
1. **Références** : `Mt_Horn_entrance_Sky.png` (texture + entrée), Steam Cave Peak, Mt. Bristle — construction et échelle seulement.
2. **Spécification** écrite avant génération, amendée deux fois sur consignes utilisateur (voir `SPECIFICATION.md`).
3. **Génération guidée** : compositions G/H avec Mont Horn en référence image ; **H retenue manuellement** (entrée de face avec terrasse
   et marches, deux chaînes distinctes, rebords cantonnés aux coins, sud ouvert) ; G écartée. Les propositions A–F antérieures
   sont écartées (bruts perdus lors d’une réinitialisation de la sandbox).
4. **Éléments régénérés à l’identique sur magenta** depuis H (massif + rochers de bord + rebords ; chaîne proche ; chaîne lointaine ;
   feuille de 16 rochers) et **plaque de sol plein cadre** ; détourage `key()` + retrait des franges ; réduction *nearest* 1024 → 640.
   Le vide de la bouche, les rebords et le massif sont séparés par analyse de composantes ; le sol est masqué au plateau ;
   les ombres sont **calculées** ; les rochers épars sont instanciés hors corridor sur la grille 8 px.
5. **Nuit** : filtre nocturne exact d’Abyss (`night.py`, blob `438383f4`) sur les calques 02–09 ; ciel nuit + astres natifs ;
   nuages par la formule des fonds Guilde/Sharpedo. Aucune régénération.
6. **Audit** `verify.py` : 16 contrôles PASS (dimensions, alpha 0/255, zéro magenta, recomposition exacte, nuit = filtre exact,
   corridor 32 px, dégagements 16 × 16, bouche connexe, sud ouvert, rebords aux coins, noms uniques, SHA-256 bruts/calques, rochers).
7. **Import** : PNG to Tileset, **8 px**, un tileset par PNG ; noms uniques `COLEBOULIS_V1_<JOUR|NUIT>_NN_*`.

## Ordre des calques (arrière → avant)
| NN | Calque | Rôle moteur suggéré |
|---|---|---|
| 00 | CIEL | fond fixe (ou `.dir`) |
| 01 | NUAGES | fond défilant possible (−4 px/s comme les lots côtiers) |
| 02 | CHAINE_LOINTAINE | fond |
| 03 | CHAINE_PROCHE | fond |
| 04 | SOL_CHEMIN | sol praticable (collisions : libre) |
| 05 | OMBRES | calque alpha intermédiaire (comme *Crooked Cavern Shadows*) |
| 06 | MASSIF_ET_BORDS | bloqué |
| 07 | ENTREE_PROFONDEUR | bloqué ; marqueur `donjon_seuil` devant |
| 08 | ROCHERS_EPARS | bloqué |
| 09 | REBORDS_PREMIER_PLAN | **devant le personnage** (`Top`) |

Points clés : seuil (312, 248), arrivée (312, 608), corridor x 304–336 / y 248–640 — cf. `manifest.json`.

## Limites (à ne pas surestimer)
- Aucun test moteur PMDO ici (échec code 139 documenté). Les contrôles valident des fichiers, pas les collisions en mouvement ni le rendu en jeu.
- Pixels **générés** (réduits *nearest*), pas des tuiles canoniques ; non attribués à un artiste humain. Mont Horn © Pokémon / Nintendo / Creatures / GAME FREAK / Chunsoft.
- Aucune collision, aucun script, aucune destination de donjon fournis : `donjon_seuil` est une position, pas un téléporteur.
- La chaîne proche est prolongée vers le bas par répétition de sa dernière ligne opaque (zone presque entièrement masquée).

Rebuild : `python3 build.py && python3 verify.py && python3 package.py` (Pillow, numpy, scipy).
