# Simple NPU — réanalyse du 19 septembre 2026

Commit : `ad804f87f964325e06132a3c2f75ca132b8e9706`.

RÉANALYSE APRÈS ACTUALISATION / RAPPORT 2

Simple NPU

19 septembre 2026. Le pull ne rapporte aucun nouveau commit. HEAD et la branche principale distante correspondent toujours à **ad804f87**. La réanalyse a été confiée à un second agent, puis intégrée à ce rapport.

**Verdict inchangé : corrections nécessaires avant de figer la conception.** Le calcul signé et le reset restent incorrects. Les contrôles physiques publiés sont favorables sous leurs hypothèses, mais ne compensent pas ces défauts fonctionnels.

| Nouveau passage local | Résultat |
| --- | --- |
| Produits signés, huit voies | 1 152 divergences sur 2 048 cas |
| Huit fonctions d’activation | 128/128 conformes aux formules et tables du RTL |
| Tests originaux | 3/3 réussis |
| Cinq scénarios complémentaires RTL | 1 succès ; 4 échecs identiques au premier audit |
| CI du commit exact | Tests, documentation, GDS et précontrôle toujours verts |

La conception comporte huit activations et poids sur quatre bits, huit neurones par couche et huit fonctions d’activation. Les instructions et poids proviennent d’une flash SPI. Le test positif sur deux couches continue de réussir.

### Comment lire les constats

N01/N02 sont des défauts certains et reproduits. N03/N04 sont des comportements d’interface démontrés dont l’acceptabilité dépend du protocole à documenter. Les réserves numériques et physiques ne sont pas présentées comme des pannes prouvées.

Les sources versionnées sont intactes. Les simulations netlist et les artefacts physiques du premier audit restent applicables au **même commit inchangé** ; ils n’ont pas été réexécutés pour cette actualisation.

[Version complète examinée : ad804f87f964325e06132a3c2f75ca132b8e9706](https://github.com/leonllrmc/ttihp26b_simple_NPU/tree/ad804f87f964325e06132a3c2f75ca132b8e9706/)

REPRODUITS À NOUVEAU / CORRECTIONS PRIORITAIRES

## 1. Deux défauts fonctionnels certains

### N01 | Les produits négatifs sont mal interprétés

PRIORITÉ ÉLEVÉE — 1 152 DIVERGENCES SUR 2 048

**Exemple.** Activation 0xF (−1), poids 0x1 (+1), biais nul : le produit vaut **+15 au lieu de −1**. Après la quantification existante, la sortie est +3 au lieu de 0xF (−1). Une inférence complète donne huit sorties égales à 3 au lieu de 15.

**Cause.** Les sélections de sous-vecteurs packed utilisées comme opérandes sont non signées. Le fait que le résultat soit déclaré signed ne transforme pas les opérandes.

**Portée du test.** Les 256 couples −8…7 sont testés sur chacune des huit voies. Le modèle conserve la troncature de chaque produit et le débordement du RTL ; il ne suppose aucune saturation nouvelle.

**Correction et acceptation.** Convertir explicitement chaque opérande avec $signed, ou employer des éléments réellement typés signés. Exiger zéro divergence et des inférences complètes comportant activations et poids négatifs.

[Source : src/neuron.sv, lignes 11–26](https://github.com/leonllrmc/ttihp26b_simple_NPU/blob/ad804f87f964325e06132a3c2f75ca132b8e9706/src/neuron.sv#L11-L26)

### N02 | Une sauvegarde survit au reset

PRIORITÉ MOYENNE — ÉCRITURE ET DÉMARRAGE FANTÔMES

**Preuve.** Créer une impulsion en attente, maintenir le reset trois cycles, garder save_activation=0, présenter adresse 7/donnée 5 puis relâcher le reset. Sans nouvelle sauvegarde, **activation[7]=5 et CS=0** : une écriture et une lecture flash démarrent.

**Cause et impact.** data_save_pulse et data_save_old ne sont pas réinitialisés. Une ancienne commande est consommée après reset avec le bus alors présent, ce qui peut démarrer un calcul avec des entrées incomplètes.

**Correction et acceptation.** Initialiser les deux registres et vérifier reset en attente de commande et depuis chaque état. Spécifier le comportement si la commande reste haute au relâchement.

[Source : src/project.sv, lignes 198–238](https://github.com/leonllrmc/ttihp26b_simple_NPU/blob/ad804f87f964325e06132a3c2f75ca132b8e9706/src/project.sv#L198-L238)

Ces deux comportements sont fraîchement reproduits en RTL. L’audit initial les avait également reproduits dans la netlist finale de ce même commit. Aucun nouveau test netlist n’est revendiqué ici.

COMPORTEMENTS OBSERVÉS / SPÉCIFICATION MANQUANTE

## 2. Contrats d’interface et formats à fixer

### N03 | Le premier chargement après une inférence est perdu

DÉPEND DU PROTOCOLE DE RÉARMEMENT VOULU

**Preuve.** Après une inférence sur huit valeurs 1, charger huit valeurs 2 sans reset donne **[1,2,2,2,2,2,2,2]**. La première sauvegarde quitte END sans enregistrer sa donnée ; ce test maintient les entrées plusieurs cycles.

**Action.** Enregistrer cette entrée en quittant END, ou documenter une impulsion distincte de réarmement. Le comportement est certain ; une commande de réarmement supplémentaire pourrait être un choix valide.

[Source : project.sv, lignes 343–346](https://github.com/leonllrmc/ttihp26b_simple_NPU/blob/ad804f87f964325e06132a3c2f75ca132b8e9706/src/project.sv#L343-L346)

### N04 | Adresse et donnée sont capturées après le strobe

DÉPEND DU TEMPS DE MAINTIEN PROMIS À L’UTILISATEUR

**Preuve.** Une impulsion d’un cycle sur adresse 2/donnée 5, suivie d’adresse 3/donnée 6, écrit **6 à l’adresse 3**. L’événement est mémorisé, mais le bus est lu au front suivant.

**Action.** Capturer événement, adresse et donnée ensemble, ou spécifier leur maintien jusqu’au front suivant. Les tests originaux maintiennent le bus plus longtemps et ne détectent pas ce cas.

[Source : project.sv, lignes 227–235](https://github.com/leonllrmc/ttihp26b_simple_NPU/blob/ad804f87f964325e06132a3c2f75ca132b8e9706/src/project.sv#L227-L235)

### Format numérique et documentation

Les 128 cas d’activation passent par rapport aux formules et tables actuelles. Cela ne valide pas un format numérique absent : position binaire, troncature avant somme, somme/biais modulo 16, cas abs(−8) et négation de −8 doivent être explicités.

Les deux sigmoid produisent des codes 4…11 et 2…14, alors que les opérations voisines utilisent −8…7 signé. La conversion entre couches doit être définie avant d’affirmer que ces choix sont cohérents.

Les sections How it works et How to test sont encore TODO. Documenter l’encodage flash, le chargement, la fin d’inférence, le redémarrage et le reset. Si l’entrée vient d’un bouton ou d’un contrôleur asynchrone, prévoir synchronisation et stabilité du bus ; aucune panne de métastabilité n’est déduite de la simulation.

[Documentation actuelle : docs/info.md](https://github.com/leonllrmc/ttihp26b_simple_NPU/blob/ad804f87f964325e06132a3c2f75ca132b8e9706/docs/info.md)

ARTEFACTS ANTÉRIEURS / COMMIT INCHANGÉ

## 3. Physique, preuves et revalidation

| Résultats publiés déjà audités | État pour ad804f87 |
| --- | --- |
| Timing à 50 MHz, trois coins RC nominal | Setup +9,607 ns ; hold +0,115 ns |
| DRC / LVS / antennes | 0 / 0 / 0 ; précontrôle 10/10 |
| Fanout d’horloge | Une violation : 16 charges pour une limite de 8 |
| Netlist, audit initial | Sans SDF ; même succès et quatre échecs que le RTL |

La CI exacte a été interrogée à nouveau : test, documentation, GDS et précontrôle restent réussis. Aucun nouveau placement/routage, extraction, STA, DRC, LVS ou téléchargement d’artefacts physiques n’a été réalisé : le commit est inchangé.

Le dépassement de fanout doit être corrigé ou accepté avec justification par le responsable physique. Les délais génériques d’I/O de 4 ns ne prouvent pas le trajet SCLK–flash–MISO à 25 MHz. Choisir une flash réelle et valider timing, démarrage, tensions/pads, reset et carte. Le chip complet et le silicium ne sont pas validés.

### Conditions de revalidation

**1.** Corriger N01/N02, conserver les tests négatifs et de reset. **2.** Décider et documenter N03/N04 et les formats numériques. **3.** Tester les deux inférences successives, toutes les activations et les limites avec des délais maximums réels. **4.** Relancer RTL, netlist et flux physique sur le commit corrigé, puis résoudre fanout et contraintes d’intégration.

La simulation par défaut avec Icarus reste un point de portabilité signalé dans le premier audit : référence à xfer_active avant déclaration. Les exécutions RTL de cette réanalyse utilisent Verilator. Ce point n’est pas une preuve d’échec de synthèse.

### Preuves fraîches et références

[MAC exhaustif : 1 152 divergences / 2 048](/Users/fabien/Documents/_projects/10_hepia/TinyTapeout/work/reviews-2026-09-18/simple_NPU/.review/recheck-2026-09-19/mac-exhaustive.log)

[Activations : 128 cas conformes](/Users/fabien/Documents/_projects/10_hepia/TinyTapeout/work/reviews-2026-09-18/simple_NPU/.review/recheck-2026-09-19/activation-exhaustive.log)

[Tests originaux : 3/3](/Users/fabien/Documents/_projects/10_hepia/TinyTapeout/work/reviews-2026-09-18/simple_NPU/.review/recheck-2026-09-19/baseline-tests.log)

[Cinq tests complémentaires RTL](/Users/fabien/Documents/_projects/10_hepia/TinyTapeout/work/reviews-2026-09-18/simple_NPU/.review/recheck-2026-09-19/rtl-tests.log)

[Synthèse détaillée du second agent](/Users/fabien/Documents/_projects/10_hepia/TinyTapeout/work/reviews-2026-09-19/reanalyse-NPU.md)

[Flux GDS du commit audité : 35253058716](https://github.com/leonllrmc/ttihp26b_simple_NPU/actions/runs/35253058716)

Nouvelles preuves : simple_NPU/.review/recheck-2026-09-19. Outils : Icarus 13.0 pour les bancs unitaires, Verilator 5.052 et cocotb 2.0.1/Python 3.12 pour le système. Les liens de journaux sont locaux.
