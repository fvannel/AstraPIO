# HEPIARISC — réanalyse du 19 septembre 2026

Commit : `0ab411f183bfb27c6413beb2892b547374577f4b`.

RÉANALYSE APRÈS ACTUALISATION / RAPPORT 1

HEPIARISC

19 septembre 2026. Mise à jour de **b7ca0d6 vers 0ab411f**. Un nouveau commit, cinq fichiers modifiés. La branche locale correspond à la branche principale distante au moment du contrôle.

**Verdict : corrections encore nécessaires avant validation pour fabrication.** Trois points du premier audit sont corrigés. Les erreurs ADD, de comparaison non signée et d’IRQ restent présentes ; le nouveau commit introduit aussi une erreur de débordement SUB et modifie incorrectement le retour d’interruption.

| Point du premier audit | État après actualisation |
| --- | --- |
| H01 — Overflow ADD | Toujours incorrect : 32 768 cas sur 65 536. |
| H02 — Carry SUB / comparaisons | Toujours incohérent avec les branches non signées. |
| H03 — Demandes IRQ perdues | Toujours reproduit malgré le registre ajouté. |
| H04 — Retour et priorité IRQ | Non résolu ; nouvelle erreur de retour et incohérences de banque. |
| H05 / H06 / H07 | Reset I²C, donnée SPI et test RAM : corrections vérifiées. |
| H08 / H09 / H10 | Documentation et intégration à compléter ; fanout : 73 dépassements, contre 72 auparavant. |
| Nouveau H11 — Overflow SUB | Régression : 32 768 cas incorrects sur 65 536. |

Les tests originaux et les workflows test, documentation et GDS sont maintenant verts. Les contre-exemples complémentaires échouent encore, y compris sur la nouvelle netlist finale. Une CI verte ne suffit donc pas à valider le comportement.

### Périmètre

Relecture du changement et de ses interactions avec le CPU, tests arithmétiques exhaustifs, scénarios IRQ/périphériques, simulation RTL et netlist, contrôle des nouveaux artefacts physiques du même commit. Les sources versionnées sont intactes.

[Version complète examinée : 0ab411f183bfb27c6413beb2892b547374577f4b](https://github.com/leonllrmc/ttihp26b_llr_hepiarisc/tree/0ab411f183bfb27c6413beb2892b547374577f4b/)

CONFIRMÉ / PRIORITÉ ÉLEVÉE

## 1. Arithmétique : deux défauts persistants, une régression

### H01 | ADD conserve la mauvaise formule de débordement

PERSISTANT — RTL EXHAUSTIF ET NETLIST

**Exemple.** `0x7F + 1 = 0x80`, mais V vaut 0 au lieu de 1. Sur les 65 536 couples d’octets : **32 768 divergences** pour V.

**Cause et impact.** La formule attachée à ADD est une formule de soustraction. BVS/BVC et toute logique utilisant V peuvent prendre le mauvais chemin. Un programme test produit GPO=1 au lieu de 10, en RTL et netlist.

[Source : hepiarisc_alu.sv, lignes 43–46](https://github.com/leonllrmc/ttihp26b_llr_hepiarisc/blob/0ab411f183bfb27c6413beb2892b547374577f4b/src/hepiarisc_alu.sv#L43-L46)

### H11 | Le débordement de SUB est maintenant incorrect

NOUVEAU — RÉGRESSION INTRODUITE PAR 0ab411f

**Exemple.** `0x80 - 1 = 0x7F` représente −128 − 1 : V doit valoir 1, mais vaut 0. Le programme BVS produit GPO=1 au lieu de 10 dans les deux simulations.

**Preuve du changement.** La formule d’addition a été placée dans le cas SUB. L’ancien audit trouvait zéro erreur de V pour SUB ; le nouveau retrouve **32 768 erreurs sur 65 536**.

[Ligne modifiée : hepiarisc_alu.sv, ligne 45](https://github.com/leonllrmc/ttihp26b_llr_hepiarisc/blob/0ab411f183bfb27c6413beb2892b547374577f4b/src/hepiarisc_alu.sv#L45)

### H02 | Le carry SUB contredit les branches non signées

PERSISTANT — RTL EXHAUSTIF ET NETLIST

**Exemple et preuve.** `3 - 2` produit C=0 ; BGEU n’est pas pris alors que 3 ≥ 2. Le RTL produit un emprunt, mais les branches attendent une absence d’emprunt : **65 536 désaccords sur 65 536**. Le programme test donne GPO=1 au lieu de 10.

**Action.** Rendre cohérents carry et décodage de BGEU/BLTU/BGTU/BLEU, puis tester égalité, limites et couples exhaustifs.

[Sources : ALU 34–45 ; décodage CPU 172–185](https://github.com/leonllrmc/ttihp26b_llr_hepiarisc/blob/0ab411f183bfb27c6413beb2892b547374577f4b/src/hepiarisc.sv#L172-L185)

**Formules attendues**, avec A/B opérandes et R résultat : ADD V = `~(A[7]^B[7]) & (A[7]^R[7])` ; SUB V = `(A[7]^B[7]) & (A[7]^R[7])`. Pour les branches actuelles, SUB C = absence d’emprunt.

Contrôles positifs : zéro écart de résultat numérique ou N/Z sur 524 288 combinaisons ALU ; carry ADD correct. Le sens de V après ASR reste à spécifier séparément.

CONFIRMÉ / PRIORITÉ ÉLEVÉE

## 2. Interruptions : la correction reste incomplète

### H03 | La demande mémorisée est effacée trop tôt

PERSISTANT — REPRODUIT AU NIVEAU DU SYSTÈME

**Séquence fautive.** Au front de STATE_CPU_EXEC, le contrôleur programme `enable=1` et efface l’IRQ mémorisée si l’impulsion source est retombée. Le CPU voit encore l’ancien enable=0. Au front suivant, il voit enable=1, mais l’IRQ vaut déjà 0.

**Preuve.** 103 instructions exécutées et 14 impulsions systick : **aucune entrée dans le gestionnaire**. Une impulsion externe de huit cycles pendant le chargement flash est aussi perdue. Le défaut systick est reproduit dans la nouvelle netlist.

**Correction attendue.** Conserver la demande jusqu’à son acceptation réelle par le CPU ; définir la priorité si une nouvelle demande arrive pendant l’acquittement. Initialiser aussi le nouveau registre au reset, ce que le code ne fait pas.

[Source : project.sv 262–300 et 369–375](https://github.com/leonllrmc/ttihp26b_llr_hepiarisc/blob/0ab411f183bfb27c6413beb2892b547374577f4b/src/project.sv#L369-L375)

### H04 | Le retour IRQ peut renvoyer vers le gestionnaire

RÉGRESSION DU RETOUR — CPU RTL

**Preuve.** Une IRQ pendant ADD à PC=17 donne PC=1 et sauvegarde **IRL=1 au lieu de 18**. BIR revient donc à 1. La valeur sauvegardée est maintenant `next_PC`, mais ce signal inclut déjà la redirection IRQ vers le vecteur 1.

**Interprétation.** L’ancien défaut de réexécution de l’instruction n’est pas corrigé proprement : il est remplacé par une continuation incorrecte vers le gestionnaire.

[Sources : hepiarisc.sv 232 et 299–311](https://github.com/leonllrmc/ttihp26b_llr_hepiarisc/blob/0ab411f183bfb27c6413beb2892b547374577f4b/src/hepiarisc.sv#L299-L311)

### H04 suite | PC, banque et pile ne changent pas de façon cohérente

PRIORITÉ ENCORE FAUSSE ET NOUVELLES INTERACTIONS DE BANQUE

**Branche interrompue.** Depuis banque 1/PC=32, B +5 avec IRQ donne **banque 0/PC=37**, au lieu de banque 0/PC=1. La banque suit la priorité IRQ, mais le PC suit la branche : l’exécution part au mauvais endroit.

**Appel / retour de banque.** Un appel interrompu vers banque 2/PC=48 sauvegarde banque 2 mais PC=1 ; la pile reste à 0 au lieu de 1. Après BIR : banque 2/PC=1. Un retour de banque interrompu laisse de même la pile à 1 au lieu de 0.

**Correction attendue.** Définir une continuation sans IRQ, puis appliquer une seule décision d’entrée IRQ au PC, à la banque et aux effets de pile. Tester chaque type de branche, appel/retour et instruction mémoire.

[Sources : hepiarisc.sv 213–265 et 275–311](https://github.com/leonllrmc/ttihp26b_llr_hepiarisc/blob/0ab411f183bfb27c6413beb2892b547374577f4b/src/hepiarisc.sv#L252-L311)

PÉRIPHÉRIQUES / UTILISATION

## 3. Corrections validées et documentation restante

| Point corrigé | Vérification sur la nouvelle version |
| --- | --- |
| H05 — Commandes I²C au reset | Les six impulsions sont mises à zéro. Le scénario START en attente, cinq cycles de reset puis relâchement donne START=0 et busy=0 : aucune reprise fantôme. Vérifié en RTL. |
| H06 — Octet SPI utilisateur | L’écriture de 0xA5 à 0x98 transmet maintenant 0xA5 sur huit fronts SPI. Vérifié dans le système RTL et dans la nouvelle netlist. |
| H07 — Test RAM | Les deux constantes 0x8850 deviennent 0x8840 ; l’accès testé retombe dans les 80 octets. La suite originale complète passe localement, comme en CI. |

[Corrections I²C et SPI : project.sv 285–290 et 423–428](https://github.com/leonllrmc/ttihp26b_llr_hepiarisc/blob/0ab411f183bfb27c6413beb2892b547374577f4b/src/project.sv#L285-L290)

[Tests actualisés : test/test.py](https://github.com/leonllrmc/ttihp26b_llr_hepiarisc/blob/0ab411f183bfb27c6413beb2892b547374577f4b/test/test.py)

### Portée de ces succès

Ces essais ferment les trois contre-exemples précis du premier audit. Ils ne constituent pas une validation exhaustive de tous les états I²C, du partage de bus SPI ou du comportement des composants externes.

### H08 | Documentation toujours incohérente

Les fichiers de documentation n’ont pas changé. La RAM est décrite comme 64 ou 128 octets alors que le RTL en contient 80 ; le déplacement LD/ST est signé −32 à +31, et non 0 à 63 ; la pile de banque contient huit entrées, et non cinq. La carte des registres MMIO reste à rédiger.

Les broches SCL/SDA sur uio[0:1] et l’horloge SPI utilisateur sur uo[3] sont sans libellé. Le nom irq_n suggère une polarité active basse alors que le circuit détecte le front montant. Cela peut conduire à un programme ou à un câblage incompatible.

À publier : une carte mémoire, une ISA et un brochage concordants, le protocole IRQ, le contexte sauvegardé, la politique d’IRQ imbriquée, les limites de pile et les séquences de commande des périphériques.

[Sources : docs/HEPIA-RISC_ISA.md, docs/info.md et info.yaml](https://github.com/leonllrmc/ttihp26b_llr_hepiarisc/blob/0ab411f183bfb27c6413beb2892b547374577f4b/docs/HEPIA-RISC_ISA.md)

NOUVEAUX ARTEFACTS / MÊME COMMIT 0ab411f

## 4. Implantation physique et fabrication

Les artefacts de la nouvelle exécution GDS ont été téléchargés. Leur commit_id.json correspond exactement à 0ab411f. Flux : **LibreLane 3.0.5 / IHP SG13G2**, PDK `c4b8b4e…`. Le contrôle porte sur les résultats publiés ; le placement/routage, l’extraction, DRC/LVS et STA n’ont pas été recalculés localement.

| Contrôle publié | Résultat courant |
| --- | --- |
| Horloge / coins temporels | 20 ns (50 MHz) ; fast, typ et slow ; RC nominal |
| Pire marge setup / hold | +7,355 ns / +0,120 ns |
| Violations setup / hold | 0 / 0 sous les contraintes du flux |
| DRC finale / LVS / antennes | 0 / 0 / 0 |
| Précontrôle Tiny Tapeout | 10 contrôles réussis, dont DRC KLayout |
| Slew / capacité | 0 dépassement rapporté |
| Fanout | 73 dépassements dans chaque coin ; 72 dans l’ancien audit |

### H09 | Dépassements de fanout à traiter

Les rapports STA retrouvent 73 buffers d’horloge chargés à **12–16 pour une limite de 8**. Ces dépassements doivent être corrigés ou acceptés avec justification par le responsable physique/shuttle. Les marges setup/hold positives ne les expliquent pas à elles seules. Ce constat ne démontre pas, isolément, une panne électrique.

### H10 | Intégration externe à valider

Le flux utilise des délais génériques d’entrée/sortie de 4 ns et une incertitude de 0,25 ns. Cela ne prouve pas le trajet SCLK–flash–MISO d’une flash réelle à 25 MHz. Il reste à vérifier la référence de flash, ses délais et son démarrage, les tensions/pads, les marges de carte et les résistances de rappel I²C.

Le relâchement du reset, la synchronisation des entrées externes et leur stabilité doivent être définis. Aucune panne de métastabilité n’est déduite d’une simulation logique.

La nouvelle netlist a été simulée localement avec la bibliothèque du PDK correspondant, **sans délais SDF**. La vérification d’équivalence du flux est désactivée. Le chip complet, le boîtier, la carte et le silicium ne sont pas validés par cet audit.

[Workflow GDS et précontrôle : exécution 35441840577](https://github.com/leonllrmc/ttihp26b_llr_hepiarisc/actions/runs/35441840577)

SYNTHÈSE DES NOUVELLES EXÉCUTIONS

## 5. Preuves et critères de revalidation

| Vérification | Résultat |
| --- | --- |
| Suite originale du dépôt | Réussie ; ALU, banques, RAM, appels imbriqués et I²C. |
| ALU exhaustive, 524 288 cas | Résultats et N/Z corrects ; V ADD et V SUB : 32 768 erreurs chacun ; C SUB incohérent avec les branches. |
| IRQ / SPI / reset, système RTL | 2 succès : donnée SPI et reset I²C ; 2 échecs : systick et IRQ pendant fetch. |
| Six scénarios par les broches | RTL : 2 succès / 4 échecs. Nouvelle netlist : mêmes résultats. |
| Contre-exemples CPU IRQ | Retour PC=1, branche dans la mauvaise banque et effets de pile manquants reproduits. |

Les deux scénarios par les broches qui passent sont GPIO positif et transmission SPI. Les quatre échecs sont ADD V, SUB C, timer et le nouveau SUB V. L’émulateur flash de l’audit initialise explicitement ses registres de décalage ; le RTL du projet n’a pas été modifié.

### Ordre de correction recommandé

**1.** Corriger H01/H02/H11 et exiger zéro écart exhaustif des indicateurs. **2.** Résoudre H03/H04 avec acquittement réel et continuation cohérente ; couvrir IRQ pendant fetch, ALU, LD/ST, branches et changements de banque. **3.** Conserver les tests de H05/H06/H07 et aligner documentation/contrats. **4.** Relancer tous les tests et le flux physique sur le commit corrigé ; résoudre le fanout et le budget temporel des interfaces.

### Traçabilité

Les nouvelles preuves sont isolées sous hepiarisc/.review/recheck-2026-09-19 ; les preuves anciennes sont conservées. Outils : Verilator 5.052, Icarus 13.0, cocotb 2.0.1. Le banc CPU affiche les états observés ; ses sorties sont comparées explicitement aux états attendus dans ce rapport.

[Résultats ALU exhaustifs](/Users/fabien/Documents/_projects/10_hepia/TinyTapeout/work/reviews-2026-09-18/hepiarisc/.review/recheck-2026-09-19/units-results.log)

[Scénarios CPU IRQ et banques](/Users/fabien/Documents/_projects/10_hepia/TinyTapeout/work/reviews-2026-09-18/hepiarisc/.review/recheck-2026-09-19/irq-results.log)

[Tests intégrés et reset](/Users/fabien/Documents/_projects/10_hepia/TinyTapeout/work/reviews-2026-09-18/hepiarisc/.review/recheck-2026-09-19/integration.log)

[Tests via les broches : RTL](/Users/fabien/Documents/_projects/10_hepia/TinyTapeout/work/reviews-2026-09-18/hepiarisc/.review/recheck-2026-09-19/ports-rtl.log)

[Tests via les broches : nouvelle netlist](/Users/fabien/Documents/_projects/10_hepia/TinyTapeout/work/reviews-2026-09-18/hepiarisc/.review/recheck-2026-09-19/ports-gl.log)

[Artefacts physiques et preuve de commit](/Users/fabien/Documents/_projects/10_hepia/TinyTapeout/work/reviews-2026-09-18/hepiarisc/.review/recheck-2026-09-19/artifacts/tt_submission/tt_submission/commit_id.json)

[Rapport STA : contraintes et dépassements de fanout](/Users/fabien/Documents/_projects/10_hepia/TinyTapeout/work/reviews-2026-09-18/hepiarisc/.review/recheck-2026-09-19/artifacts/runs/wokwi/55-openroad-stapostpnr/nom_typ_1p20V_25C/checks.rpt)

Les liens de code et de CI sont publics ; les journaux sont conservés dans le dossier local d’audit. Le rapport expose les résultats sans nécessiter l’accès à ces journaux.
