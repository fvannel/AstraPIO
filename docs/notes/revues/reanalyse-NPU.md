# Réanalyse NPU après actualisation — 19 septembre 2026

**Le dépôt n’a pas évolué depuis l’audit précédent. Les deux défauts fonctionnels confirmés restent présents : calcul des produits signés incorrect et sauvegarde en attente conservée pendant le reset. Le verdict est inchangé : corrections nécessaires avant de figer la conception pour fabrication.**

## Version vérifiée

Le `git pull --ff-only` réalisé pour cette réanalyse n’a apporté aucun changement. Une vérification indépendante de `HEAD` et de `refs/heads/main` sur GitHub retrouve le même commit : **`ad804f87f964325e06132a3c2f75ca132b8e9706`**. Aucun fichier versionné modifié ; `git diff --exit-code` réussit. [Preuve de révision](/Users/fabien/Documents/_projects/10_hepia/TinyTapeout/work/reviews-2026-09-18/simple_NPU/.review/recheck-2026-09-19/revision.json).

## Tests relancés

| Vérification locale | Résultat du nouveau passage |
|---|---|
| MAC signé exhaustif, 256 couples sur huit voies | **1 152 divergences / 2 048 cas** |
| Huit fonctions d’activation, seize entrées chacune | **128/128 conformes aux formules et LUT du RTL** |
| Trois tests originaux du dépôt | **3/3 réussis** |
| Cinq scénarios complémentaires par les broches, RTL | **1 réussi, 4 échecs identiques à l’audit initial** |

Le test positif sur deux couches réussit. Les quatre scénarios qui échouent reproduisent les mêmes comportements :

1. **Défaut certain — produit signé** : −1 × +1 donne un produit +15 ; après la quantification existante, les huit sorties valent +3 au lieu de `0xF` (−1). Le test conserve les règles de troncature et de débordement du code : il ne suppose pas une saturation nouvelle.
2. **Défaut certain — reset** : après une impulsion interrompue par le reset, sans nouvelle sauvegarde, `activation[7]=5` et `CS=0`. Une écriture et une inférence fantômes se produisent.
3. **Contrat d’interface à fixer — strobe court** : une impulsion d’un cycle à l’adresse 2/donnée 5, suivie d’adresse 3/donnée 6, écrit 6 à l’adresse 3. Il faut capturer ensemble événement/adresse/donnée, ou spécifier leur maintien jusqu’au front suivant.
4. **Contrat d’interface à fixer — réarmement** : après une première inférence sur `[1,1,1,1,1,1,1,1]`, charger `[2,2,2,2,2,2,2,2]` sans reset donne `[1,2,2,2,2,2,2,2]`. La première sauvegarde réarme le moteur sans enregistrer la donnée. Une impulsion dédiée au réarmement pourrait être un choix valide, mais elle doit être documentée.

Les deux derniers cas sont des comportements prouvés, pas deux bugs indépendants inconditionnels : leur acceptabilité dépend du protocole que l’auteur veut garantir. Les formats numériques, arrondis, débordements et conversions entre activations restent à spécifier ; aucun choix non spécifié n’est transformé en nouveau défaut.

Preuves fraîches, conservées séparément des anciennes : [MAC](/Users/fabien/Documents/_projects/10_hepia/TinyTapeout/work/reviews-2026-09-18/simple_NPU/.review/recheck-2026-09-19/mac-exhaustive.log), [activations](/Users/fabien/Documents/_projects/10_hepia/TinyTapeout/work/reviews-2026-09-18/simple_NPU/.review/recheck-2026-09-19/activation-exhaustive.log), [tests originaux](/Users/fabien/Documents/_projects/10_hepia/TinyTapeout/work/reviews-2026-09-18/simple_NPU/.review/recheck-2026-09-19/baseline-tests.log), [tests complémentaires RTL](/Users/fabien/Documents/_projects/10_hepia/TinyTapeout/work/reviews-2026-09-18/simple_NPU/.review/recheck-2026-09-19/rtl-tests.log), [résultats XML](/Users/fabien/Documents/_projects/10_hepia/TinyTapeout/work/reviews-2026-09-18/simple_NPU/.review/recheck-2026-09-19/results.xml). Outils : Icarus 13.0 pour les bancs unitaires, Verilator 5.052 et cocotb 2.0.1/Python 3.12 pour les simulations complètes.

## CI et portée physique

L’interrogation actuelle de GitHub pour ce commit confirme toujours les trois workflows du 17 septembre 2026 : [test réussi](https://github.com/leonllrmc/ttihp26b_simple_NPU/actions/runs/35253058500), [documentation réussie](https://github.com/leonllrmc/ttihp26b_simple_NPU/actions/runs/35253058697), [GDS réussi](https://github.com/leonllrmc/ttihp26b_simple_NPU/actions/runs/35253058716). Les jobs GDS, précontrôle et viewer de ce dernier run sont tous réussis. [Réponse CI archivée](/Users/fabien/Documents/_projects/10_hepia/TinyTapeout/work/reviews-2026-09-18/simple_NPU/.review/recheck-2026-09-19/github-actions.json), [état des jobs GDS](/Users/fabien/Documents/_projects/10_hepia/TinyTapeout/work/reviews-2026-09-18/simple_NPU/.review/recheck-2026-09-19/github-gds-jobs.json).

**Aucun nouveau placement/routage, extraction, STA, DRC, LVS, téléchargement d’artefacts physiques ou test de netlist n’a été relancé.** Le commit n’ayant pas changé, la réanalyse réutilise les conclusions physiques limitées de l’audit initial : DRC/LVS/antennes publiés sans erreur, timing positif sous les contraintes publiées, dépassement de fanout de la racine d’horloge **16 pour une limite 8** encore à examiner/justifier. Les simulations netlist sans SDF de l’audit initial restent des preuves sur ce même commit, pas des exécutions nouvelles.

Une CI verte n’invalide pas les contre-exemples fonctionnels et ne constitue pas une nouvelle validation de fabrication. Les corrections futures devront être suivies d’une nouvelle chaîne complète sur le commit corrigé ; il faudra également arrêter le protocole d’entrée et valider la flash réelle et son budget temporel.

Rapports de référence inchangés : [audit complet du 18 septembre](/Users/fabien/Documents/_projects/10_hepia/TinyTapeout/work/reviews-2026-09-18/rapport-simple-NPU.md), [complément conception/fabrication](/Users/fabien/Documents/_projects/10_hepia/TinyTapeout/work/reviews-2026-09-18/simple_NPU/.review/complement-conception-fabrication.md). Aucune exploration exhaustive nouvelle n’a été engagée pour cette version inchangée.
