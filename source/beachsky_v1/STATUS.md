# Beach/Sky étendue — lot `beachsky_v1` (en cours)

## Validé par l'utilisateur (20 septembre 2026)
Deux premières générations **validées** (déposées par l'utilisateur, 1264×848, RGB) :

| Fichier (`renders/beachsky_v1/valides/`) | SHA-256 | Rôle |
|---|---|---|
| `beachsky_01_sable_texture_plein_cadre.png` | `4cc20598…d586` | plaque de sable jaune pâle à vaguelettes (motif « Beach » de Sky), plein cadre → futur calque SOL |
| `beachsky_02_composition_plage_validee.png` | `66620b00…66ff` | composition de référence : falaises rouges (Sharpedo/Beach) au nord et en pointes vers la mer, plage étendue, palmiers, herbes, sentier vers une grotte au nord-ouest, mer au sud avec écume |

Règle : cette composition est le **layout retenu** ; elle ne sera pas régénérée pour découpe. Les calques seront
obtenus par régénération des éléments à l'identique sur magenta (méthode du col des Éboulis) + plaque de sol validée.

## À faire
1. Spécification (bords, arrivée, corridor, zones d'eau) — avant toute génération de calque.
2. Calques : ciel natif · mer profonde · mer proche + écume · sable (validé) · sentier/roche · ombres · falaises nord · pointes rocheuses · palmiers · herbes · rochers épars.
3. **Eau animée canonique** : dans EoS, l'eau des maps ground est animée par **palette cycling** (BPL, animations de palette) et
   par tuiles animées (BPA) — à confirmer/mesurer sur les GIF animés de Project Pokémon avant implémentation ; livrer les phases
   comme calques successifs cohérents (plusieurs phases, exigence AGENTS.md).
4. Jour / nuit (filtre Abyss exact) / crépuscule (nouveau mode demandé), nuages sur calque propre animé.
5. Audit + aperçu HTML + push.
