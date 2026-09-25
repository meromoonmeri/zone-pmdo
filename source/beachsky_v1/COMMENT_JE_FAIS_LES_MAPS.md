# Comment je fabrique une map PMDO en calques — guide pour une autre IA

Ce document explique **exactement** la chaîne que j'utilise, dans l'ordre, avec ce qu'il ne faut pas faire.
Il complète `MANUEL_METHODE_PMDO.md` (règles du dépôt) et `AGENTS.md` (historique des décisions).

## 0. Les trois idées à comprendre avant de commencer

1. **Le générateur d'images n'est PAS un générateur de tuiles.** Il sert à deux choses : proposer une
   composition (le layout) et produire des *éléments* isolés sur fond magenta. Ses pixels ne sont jamais
   présentés comme des tuiles canoniques. On ne découpe jamais une image générée en tuiles de 8 px.
2. **Une map livrable = des calques PNG séparés à taille native**, tous de la même dimension (divisible par 8),
   avec alpha propre (0 ou 255), noms de fichiers uniques (PNG-to-Tileset nomme le tileset d'après le fichier).
   Jamais une image aplatie.
3. **La spécification s'écrit AVANT de générer** : fonction, bords fermés/ouverts, point d'arrivée, seuil de
   donjon, corridor libre ≥ 32 px, ordre des calques. Sinon on refait tout trois fois.

## 1. Références (jamais de copie de pixels)
- Choisir 1 à 3 captures canoniques (Mt. Horn, Beach, Steam Cave…) pour la **caméra, l'échelle, la construction**.
- Mesurer : taille de la carte, taille d'un sprite (32 px), largeur d'une bouche de donjon (48–72 px), largeur
  d'un chemin (≥ 96 px).
- Si la zone a une animation canonique (eau, aurore), **la mesurer sur le rip** avant d'inventer quoi que ce soit
  (cf. §6 : la mer de Beach n'est pas du palette cycling, ce sont des frames dessinées).

## 2. Spécification (`SPECIFICATION.md`)
Tableau des zones, tableau des bords (N/S/E/O ouvert ou fermé), points clés sur la grille 8 px
(`entree`, `donjon_seuil`, corridor), liste ordonnée des calques (arrière → avant), interdits transmis au
générateur (pas de Pokémon, texte, maisons, arbres, torches, ombres peintes…), modes (jour/crépuscule/nuit),
contrôles prévus. Si l'utilisateur corrige, on **amende** la spec (on ne l'écrase pas) et on garde la trace.

## 3. Composition (layout) avec le générateur
- Prompt = description du layout en texte + **une seule** référence image de *texture*.
  Piège appris : si on donne aussi une référence de *layout* en image, le générateur copie sa texture.
- Produire 2 à 3 propositions, **choisir à la main** (ou faire choisir l'utilisateur). Celle retenue devient
  la « composition validée » : on ne la régénère plus jamais pour la découper.
- Interdits explicites dans chaque prompt (liste du §2).

## 4. Éléments en calques : « même scène, tout le reste en magenta »
C'est le cœur de la méthode. Pour chaque calque voulu, on redonne **la composition validée** au générateur avec
la consigne : « reproduis exactement la même scène, garde uniquement X, remplace tout le reste par un magenta
plat #FF00FF, bords nets, pas d'ombre ». Exemples de X : « les roches rouges », « la végétation », « la mer »,
« le sentier de roche ». Pour le sol : « plaque de sol plein cadre, sans rien d'autre » (elle reconstitue aussi le
sol caché sous les objets).
- Les éléments sortent à la même taille et à la même place que la composition → ils se superposent sans réglage.
- Si la sortie est mauvaise (scène entière rendue, ou élément manquant) : on **regénère avec un prompt plus
  court**, on ne retouche pas à la main par chaînes de générations.

## 5. Détourage et assemblage (`build.py`, Pillow + numpy + scipy)
1. `key()` : magenta → alpha 0 (`R>70, B>70, R>1.45G, B>1.45G`), puis retrait des franges roses sur 3 px de bord,
   suppression des poussières < 12 px, alpha forcé à 0/255, RGB mis à 0 sous alpha 0.
2. Séparation sémantique par **composantes connexes** : ex. roches touchant le bord nord = falaises, les autres =
   pointes ; composante sombre dans la fenêtre de l'entrée = vide de la grotte ; végétation > 2500 px = palmiers,
   sinon herbes.
3. Le sol (plaque plein cadre) est **masqué** à la terre ferme lue dans la composition (couleur du sable), avec
   ouverture du bord sud conservée.
4. Les **ombres sont calculées** (décalage + dilatation des silhouettes, flou, alpha ≈ 0,3), jamais peintes.
5. Les petits objets répétés (rochers) viennent d'une feuille générée sur magenta, découpée en sprites par
   composantes, puis **instanciés** sur la grille 8 px hors corridor.
6. Taille : si le brut n'est pas à la taille cible, réduction **nearest** (jamais bilinéaire), jamais pour des
   tuiles natives.
7. Fonds natifs (ciel, nuages, astres) : repris des ressources du dépôt, mosaïque sans lune, bande de nuages
   1440 px bouclable à −4 px/s sur **son propre calque**.

## 6. Animations
- **Manuel §13** : une animation de palette s'implémente en **frames explicites** (PMDO n'a pas de palettes
  indexées), `FrameLength=10` ticks par frame ≈ 1,33 s pour 8 frames ; vérifier le raccord de fin de boucle.
- **Toujours mesurer le canon avant.** Mer de Beach (rip `beach_ref.png`, mesuré) : base d'eau unie fixe
  `(24,192,248)` ; **9 frames dessinées** où une crête cyan + écume blanche naît en haut de la bande, descend vers
  la plage, s'efface, puis une houle bleu foncé `(16,88,216)` renaît en haut ; **17 frames** pour le rivage où
  l'écume monte sur le sable (sable mouillé ocre) puis se retire. Ce **n'est pas** du palette cycling.
- Règle AGENTS.md : toute eau a plusieurs phases cohérentes ; alpha identique entre phases ; pas de fond d'eau
  statique présenté comme animé.

## 7. Modes
- Jour : pixels tels quels. Nuit : **filtre Abyss exact** (`night.py`, blob 438383f4) sur les calques terrain,
  ciel nuit + astres natifs. Crépuscule : 55 % jour + 45 % nuit + voile chaud (+12,+2,−10), ciel = mélange 50/50.
  Jamais de régénération pour changer d'heure.

## 8. Audit (`verify.py`) — obligatoire, sinon rien n'est livré
Dimensions ÷ 8 ; alpha 0/255 sauf ombres ; zéro magenta ; **recomposition des calques = scène pixel pour pixel** ;
nuit = filtre exact du jour ; corridor ≥ 32 px et dégagements 16×16 libres ; bouche/grotte connexe ≥ 40×40 ;
bords conformes à la spec ; phases d'eau à alpha identique ; noms uniques ; SHA-256 des bruts et des calques
dans `manifest.json`. Résultat dans `verification.json` avec `engine_tested: false`.

## 9. Livraison
`source/<lot>/` (spec, build, verify, package, outils, références natives) + `renders/<lot>/` (bruts, couches,
scene, manifest, verification) + `apercu_<lot>.html` autonome (calques togglables, modes, animation, grille,
marqueurs). Commit sur le dépôt, **sans écraser les lots précédents**. Ajouter un paragraphe à `AGENTS.md`.

## 10. Ce qu'il ne faut jamais dire
« Testé en jeu » (pas de test moteur ici, code 139) ; « tuiles canoniques » pour des pixels générés ;
« animation officielle récupérée » quand le rythme est choisi ; « N layouts » quand ce sont des variantes de
palette. Dire précisément ce qui a été vérifié et comment.
