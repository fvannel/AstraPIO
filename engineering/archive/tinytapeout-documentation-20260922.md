# Correction documentaire Tiny Tapeout — 22 septembre 2026

À la demande de l'utilisateur, une correction documentaire a été proposée dans
le dépôt du shuttle TTIHP26b, selon la procédure officielle :
https://www.tinytapeout.com/guides/documentation/

- PR : https://github.com/TinyTapeout/tinytapeout-ihp-26b/pull/252
- État au dépôt : ouverte ; revue et fusion par un mainteneur nécessaires.
- Commit documentaire : `f9723e25a3a739daefb91ca84791525ecec7ee6e`.
- Base du shuttle : `6e6087f766f57d527526acb024a333beb8137569`.
- Branche du fork : `fvannel/tinytapeout-ihp-26b:codex/docs-astrapio-abi5`.

Le texte soumis en PR149 conservait « not ready for tapeout » dans sa description
et des avertissements de développement dans sa notice, malgré l'acceptation
ultérieure du circuit. La PR252 corrige ces textes et lie les preuves existantes
ainsi que la datasheet publiée. Elle conserve les limites pré-silicium et carte.

Deux fichiers seulement sont modifiés :

- `projects/tt_um_fabien_pio/info.yaml` : description et commentaires uniquement.
- `projects/tt_um_fabien_pio/docs/info.md` : notice ABI 5 et état de validation.

Le brochage, la fréquence déclarée, le module, les sources et le nombre de tiles
sont inchangés. Aucun OAS, GDS, LEF, fichier Verilog, métrique, workflow ou
`commit_id.json` n'est modifié. Aucune nouvelle révision matérielle n'est soumise.
La source acceptée reste `1b1c91183a4a9a5ea3516699845336175ffe6d96`, PR149.

Le `info.yaml` local reste intentionnellement celui du circuit figé pour ne pas
invalider son manifeste : sa description historique n'est pas l'état de référence.
Les 50 empreintes locales ont été revérifiées après préparation de la correction.
La proposition est consultable dans la PR ; elle ne doit pas être présentée
comme déjà fusionnée ou déjà déployée sur le site avant confirmation.
