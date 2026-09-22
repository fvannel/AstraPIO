# Notes des essais — archives documentaires

La version retenue est **ABI 5**, source
`1b1c91183a4a9a5ea3516699845336175ffe6d96`, soumission **PR149**.
Le [bilan final](../validation-finale.md) fait foi pour son statut.

Les notes ci-dessous sont conservées comme historique des mesures et décisions.
Elles peuvent contenir des statuts périmés, des chemins désormais retirés et
des propositions abandonnées : ce ne sont ni des instructions actives ni des
autorisations de contourner un contrôle. Aucun résultat d'une ancienne variante
ne qualifie automatiquement la version finale.

| Étude | Notes conservées | Conclusion |
|---|---|---|
| SRAM / Magic / Ciel / precheck | `historique/sram-*.md`, `diagnostic-ci-summary.md`, `essenceia-ihp-sram-notes.md` | Voie abandonnée ; pas de macro SRAM dans le circuit final |
| PIO initial, compact et double contexte | `historique/architecture.md`, `isa-*.md`, `compact-*.md`, `verification.md` | Historique des capacités et limites, pas l'architecture finale |
| Moteur temporel et passage à un PIO | `historique/timed-pio-v4.md`, `single-pio-*.md` | Moteur conservé ; anciens résultats physiques distincts |
| WS2812 avec l'ancien PIO seul | `historique/ws2812-faisabilite-pio-seul.md` | Limites démontrées ; ne pas confondre caractérisation réussie et solution complète |
| ABI 5 et densités de placement | `historique/dense-pio-v5-before-cleanup.md` | Densité 91 retenue ; densité 90 échoue à l'audit hold explicite |
| Mémoire flip-flop | `historique/dense-flop-experiment.md`, `flipflop-experiment.md`, `registres/status-flipflop-experiment.json` | Simulations réussies, placement physique échoué ; latches conservés |
| OUTMSB / ABI 6 et micro-adaptations | `micro-adaptations/`, `registres/*qualification.json`, `registres/*diagnostic.json` | Non approuvées : tous les critères physiques ne passent pas |
| Décision finale | `registres/release-decision.json`, `status-micro-studies.json` | Garder ABI 5 ; arrêter les études et le suivi périodique |
| Revues de projets externes | `revues/` | Comparaisons documentaires, aucun code externe intégré |

Les bilans WS2812 de `micro-adaptations/` concernent **l'étude ABI 6 rejetée**.
Le test WS2812 de la version réellement soumise est dans `test/ws2812/` ;
ses résultats ABI 5 sont dans `release/validation/ws2812/`.
Les résumés des prechecks intermédiaires sont conservés dans
`historique/prechecks/`, y compris les échecs ; ce ne sont pas des waivers.

Les sources expérimentales restent accessibles dans l'historique Git et les
branches conservées, notamment `codex/pio-outmsb-candidate` (`c06acbf`) et
`codex/dense-pio10-flop-memory` (`9853aaa`). Les grandes copies de travail,
PDK complets, traces et sorties intermédiaires ont été déplacés vers la Corbeille
puis supprimés définitivement après accord de l'utilisateur, sans être intégrés
au dossier final. Les registres JSON conservent
les identifiants des builds et les raisons de refus sans conserver leurs gigaoctets.

La branche `main` est désormais alignée sur le circuit final ; les branches
d'études ne sont pas des candidats à soumettre. Le SHA accepté dans le shuttle
reste `1b1c9118`, même si la documentation et l'organisation du dépôt évoluent.
Le nettoyage initial était local ; sa publication ultérieure dans `main`
ne crée aucune nouvelle révision Tiny Tapeout.
