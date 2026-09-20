# Audit HEPIARISC — 18 septembre 2026

**Verdict : corrections nécessaires avant de considérer le processeur comme fonctionnellement validé pour fabrication.** Les contrôles physiques disponibles passent, mais plusieurs erreurs du RTL sont reproduites en simulation. Aucun fichier source suivi par Git n’a été modifié.

- Dépôt : https://github.com/leonllrmc/ttihp26b_llr_hepiarisc
- Commit audité : `b7ca0d604f634dd638069b3e0b9ff002ec49f433` (`main`, réduction de la RAM de 96 à 80 octets).
- Périmètre : ensemble du RTL, ISA et assembleur fournis, interfaces externes, tests, workflows et artefacts physiques du même commit.
- Copie locale et preuves : [dossier d’audit](hepiarisc/.review/).
- P1 = défaut fonctionnel important à corriger ; P2 = défaut de fonctionnalité secondaire, de test ou de documentation à traiter.

## Constats confirmés

### 1. P1 — L’addition produit un indicateur de débordement signé incorrect

**Localisation :** [src/hepiarisc_alu.sv:43–46](https://github.com/leonllrmc/ttihp26b_llr_hepiarisc/blob/b7ca0d604f634dd638069b3e0b9ff002ec49f433/src/hepiarisc_alu.sv#L43-L46).

La même formule de débordement est utilisée pour ADD et SUB. Cette formule correspond à SUB. Par exemple `0x7F + 1 = 0x80` donne `V=0`, alors qu’un dépassement signé a eu lieu. Les branchements qui consultent V après une addition prennent donc parfois le mauvais chemin.

**Preuve :** balayage exhaustif des 65 536 couples d’opérandes ADD : **32 768 indicateurs V incorrects**. Les résultats numériques, N, Z et le carry ADD sont corrects. Le V de SUB est correct sur les 65 536 couples.

**Correction :** séparer les formules ADD et SUB. Pour ADD : `~(A[7] ^ B[7]) & (A[7] ^ result[7])`. Pour SUB : `(A[7] ^ B[7]) & (A[7] ^ result[7])`.

Le V d’ASR mérite aussi correction ou définition explicite dans l’ISA : `ASR(1)` donne un résultat nul avec `V=1`, bien qu’un décalage arithmétique droit ne dépasse pas l’intervalle signé. Ce point est distinct de la preuve exhaustive sur ADD.

### 2. P1 — Le carry de SUB inverse les comparaisons non signées

**Localisation :** [src/hepiarisc_alu.sv:35–38](https://github.com/leonllrmc/ttihp26b_llr_hepiarisc/blob/b7ca0d604f634dd638069b3e0b9ff002ec49f433/src/hepiarisc_alu.sv#L35-L38), [src/hepiarisc.sv:174–185](https://github.com/leonllrmc/ttihp26b_llr_hepiarisc/blob/b7ca0d604f634dd638069b3e0b9ff002ec49f433/src/hepiarisc.sv#L174-L185), `docs/HEPIA-RISC_ISA.md:259–270` et `customasm_sample.s:41–44`.

SUB exporte le bit d’emprunt de la soustraction étendue comme C. Or BGEU/BGTU supposent la convention opposée, C=1 lorsqu’il n’y a pas d’emprunt. `3 - 2` donne `C=0` : BGEU n’est pas pris et BLTU est pris, à l’inverse de la comparaison attendue.

**Preuve :** **65 536 désaccords sur 65 536 couples** par rapport à la convention exigée par les branchements documentés.

**Correction :** inverser le carry de SUB, ou modifier de façon cohérente le décodage et la spécification des conditions. Ajouter des tests des branchements unsigned, incluant l’égalité et les bornes 0/255.

### 3. P1 — Les interruptions ne sont pas mémorisées pendant la lecture SPI ; le systick n’atteint pas le CPU

**Localisation :** [src/project.sv:149–170](https://github.com/leonllrmc/ttihp26b_llr_hepiarisc/blob/b7ca0d604f634dd638069b3e0b9ff002ec49f433/src/project.sv#L149-L170), `src/project.sv:357–368`, [src/systick_gen.sv:20–26](https://github.com/leonllrmc/ttihp26b_llr_hepiarisc/blob/b7ca0d604f634dd638069b3e0b9ff002ec49f433/src/systick_gen.sv#L20-L26), `src/hepiarisc.sv:222,265–277`.

Le CPU ne traite l’IRQ que pendant son cycle d’exécution. L’IRQ externe est une impulsion d’un seul cycle d’horloge, sans registre de demande en attente : une impulsion reçue pendant le chargement SPI disparaît avant l’exécution suivante.

Le systick est incrémenté pendant le cycle d’exécution et produit son impulsion après ce front, quand le CPU est désactivé. L’impulsion retombe bien avant l’instruction suivante.

**Preuves sur le module Tiny Tapeout complet, avec chargement des programmes par SPI :**

- 103 instructions exécutées, 14 impulsions systick observées, **0 entrée dans la routine d’interruption**.
- Une impulsion sur l’entrée externe, après activation de sa source et pendant le fetch, donne **0 entrée dans la routine** après 3 000 cycles supplémentaires.
- Un banc unitaire indépendant retrouve 7 impulsions systick pour 64 instructions, sans aucune prise en compte.

**Correction :** mémoriser les demandes IRQ jusqu’à leur acceptation par le CPU, définir un acquittement et une priorité commune. Utiliser uniquement des affectations non bloquantes dans le processus séquentiel du systick.

### 4. P1 — Le retour d’interruption rejoue une instruction ; les sauts peuvent ignorer l’IRQ

**Localisation :** [src/hepiarisc.sv:222–228](https://github.com/leonllrmc/ttihp26b_llr_hepiarisc/blob/b7ca0d604f634dd638069b3e0b9ff002ec49f433/src/hepiarisc.sv#L222-L228), [src/hepiarisc.sv:265–301](https://github.com/leonllrmc/ttihp26b_llr_hepiarisc/blob/b7ca0d604f634dd638069b3e0b9ff002ec49f433/src/hepiarisc.sv#L265-L301).

Quand une IRQ est acceptée sur une instruction ALU, l’écriture du résultat a lieu, mais l’adresse sauvegardée est celle de cette même instruction. BIR la fait donc exécuter une seconde fois. Les branches BL/B/Bcc/BR passent avant l’IRQ dans la logique du PC, alors que la sauvegarde du contexte peut tout de même se produire.

**Preuves :**

- ADD à l’adresse 17 sous IRQ : R0 passe à 1, PC devient 1, mais IRL vaut 17 au lieu de 18. Après BIR et reprise, R0 passe à **2**, au lieu de rester à 1.
- B +5 à l’adresse 16 sous IRQ : PC devient **21**, IRL vaut **16**. L’ISA exige une entrée au vecteur 1 avec sauvegarde de la destination 21.

**Correction :** calculer une adresse de continuation unique, correspondant à l’instruction réellement exécutée, puis appliquer l’IRQ avec la priorité choisie et sauvegarder cette continuation. Définir également la politique d’IRQ dans les banques et les routines d’interruption ; le contexte actuel ne sauvegarde pas la banque.

### 5. P2 — Le SPI utilisateur ignore l’octet écrit

**Localisation :** [src/project.sv:409–413](https://github.com/leonllrmc/ttihp26b_llr_hepiarisc/blob/b7ca0d604f634dd638069b3e0b9ff002ec49f433/src/project.sv#L409-L413).

Une écriture à `0x98` charge toujours `8'hFF` dans le SPI, sans utiliser `hepiarisc_memop_output`.

**Preuve sur les broches :** écriture CPU de `0xA5`, puis observation de 8 fronts sur l’horloge SPI utilisateur : **octet transmis = `0xFF`**.

Le commit précédent décrit cette interface comme un prototype. Elle ne doit donc pas être annoncée comme un SPI général pleinement opérationnel dans cet état.

**Correction :** transmettre la donnée écrite, ou spécifier explicitement une commande de lecture seule à octet factice ; documenter aussi le partage de MOSI/MISO et la sélection du périphérique.

### 6. P2 — La suite fournie échoue sur une adresse RAM supprimée et masque les scénarios suivants

**Localisation :** [test/test.py:323–327](https://github.com/leonllrmc/ttihp26b_llr_hepiarisc/blob/b7ca0d604f634dd638069b3e0b9ff002ec49f433/test/test.py#L323-L327), `test/test.py:392–397`, `src/project.sv:244,371,450`.

Le RTL implémente maintenant `0x00–0x4F`. Le programme du test écrit et lit `0x50 + 0x0F = 0x5F`, adresse devenue non implémentée, puis attend encore `0x38`. La lecture retourne correctement la valeur par défaut zéro selon le nouveau décodage.

**Preuves :** [CI du commit en échec](https://github.com/leonllrmc/ttihp26b_llr_hepiarisc/actions/runs/35326899575), reproduit avec Verilator à 70 100 ns. Dans une **copie diagnostique du test uniquement**, remplacer les deux constantes `0x8850` par `0x8840` déplace l’accès à `0x4F` : toute la suite d’origine passe ensuite, y compris les deux appels imbriqués de banques et le scénario I²C.

Cela ne prouve pas une panne de la RAM restante. Cela prouve une incohérence entre la capacité choisie et la suite fournie. Tous les scénarios sont dans un unique test Cocotb : l’assertion RAM empêche actuellement d’exécuter les scénarios suivants en CI.

**Correction :** faire dériver les bornes des tests de la capacité réelle, tester les adresses limites, et séparer les scénarios en tests indépendants avec délais maximums.

### 7. P2 — La documentation ne permet pas d’utiliser fidèlement le circuit actuel

**Localisation :** `docs/info.md:20–21`, `docs/HEPIA-RISC_ISA.md:16–17,77–85,138–143,223,386`, `info.yaml:33,44,51–52`.

- La RAM est décrite comme ayant 64 ou 128 octets ; le RTL en a 80.
- Les déplacements LD/ST sont documentés non signés 0–63, mais le RTL les étend avec signe (`src/hepiarisc.sv:64–65`) et l’assembleur utilise `i6`. Un déplacement encodé 32 signifie donc **−32** dans le matériel.
- La pile de banques est décrite avec 5 éléments, mais le RTL en implémente 8, sans protection de débordement.
- La table MMIO reste `TBD`.
- `uio[0]` et `uio[1]` sont annoncées inutilisées alors qu’elles portent SCL/SDA ; `uo[3]` porte l’horloge SPI utilisateur. L’entrée `irq_n` est nommée active à zéro alors que le RTL détecte un front montant.

**Correction :** publier une carte mémoire et un brochage uniques issus de cette version du RTL, avec polarités, protocole IRQ, capacité mémoire et restrictions des périphériques.

### 8. P2 — Une commande I²C en attente survit au reset

**Localisation :** `src/project.sv:251–257,262–289` et `src/i2c_master.v:115–122`.

Les six registres d'impulsion I²C ne sont pas affectés dans la branche reset. Une impulsion START créée juste avant le reset reste à 1 pendant celui-ci, puis est consommée par le contrôleur au premier cycle suivant.

**Preuve RTL complémentaire :** après une instruction d'écriture à `0x90`, reset maintenu cinq cycles : `I2C_start_pulse=1`, `I2C_busy=0` pendant le reset, puis `I2C_busy=1` au premier front après relâchement, sans nouvelle instruction I²C. La transaction est redémarrée à tort. Le scénario a été reproduit en RTL ; il n'a pas été rejoué sur la netlist.

**Correction :** mettre à zéro toutes les impulsions de commande dans la branche reset et vérifier l'annulation d'une commande en attente ainsi que les resets durant chaque état. Preuves : `.review/audit_reset.py`, `.review/reset-results.log`.

## Ce qui a été vérifié positivement

- Les **524 288 combinaisons** des huit opérations ALU et des deux opérandes 8 bits produisent le bon résultat numérique et les bons indicateurs N/Z.
- Le carry ADD et le débordement signé SUB passent chacun les 65 536 couples d’entrée.
- Les scénarios fournis d’ALU simple, fetch SPI, changement de banque, appels de banques imbriqués, RAM dans la plage corrigée du test et I²C passent dans la copie diagnostique. Ce sont des tests ciblés, pas une couverture exhaustive de ces sous-systèmes.
- La liste des sources et le module supérieur de `info.yaml` correspondent au RTL.
- Le lint Verilator termine sans erreur avec les avertissements non bloquants ; plusieurs avertissements restent, notamment l’affectation bloquante du systick.
- Un nouveau test de commande des GPIO par un programme chargé depuis la flash passe en RTL et dans la netlist finale publiée.

## Vérification des résultats physiques existants

Les artefacts téléchargés identifient explicitement le commit `b7ca0d6`, le PDK IHP SG13G2 et LibreLane 3.0.5. Il s’agit de la vérification des résultats de la CI, sans relance locale complète du placement/routage.

[Construction et précontrôle du commit](https://github.com/leonllrmc/ttihp26b_llr_hepiarisc/actions/runs/35326899567) : succès.

| Vérification | Résultat observé |
|---|---:|
| Période cible | 20 ns, soit 50 MHz |
| Pire marge setup rapportée | +7,813 ns |
| Pire marge hold rapportée | +0,132 ns |
| Erreurs DRC Magic | 0 |
| Erreurs LVS | 0 |
| Violations d’antenne | 0 |
| Violations de limite de fanout rapportées | 72, non bloquantes dans ce flux |
| Précontrôle Tiny Tapeout | 10 contrôles passés, dont DRC KLayout |

Sources locales : `.review/artifacts/tt_submission/tt_submission/stats/metrics.csv`, `.review/artifacts/precheck_reports/results.md` et `.review/ci-gds.log`.

Ces résultats attestent du succès du flux configuré. La contrelecture des trois `55-openroad-stapostpnr/nom_*/checks.rpt` confirme 72 dépassements de limite de fanout sur l'arbre d'horloge, avec 11 à 16 charges pour une limite de 8 ; ils ne sont pas des violations setup/hold. Il faut une correction ou une exception justifiée acceptée lors de la validation physique. Les trois listes de violations temporelles ne contiennent aucune entrée ; slew et capacité sont conformes. Le SDC fixe 20 ns, 0,25 ns d'incertitude et 4 ns de délai générique aux entrées/sorties, reset inclus. Les contraintes temporelles sont celles du flux générique : la compatibilité électrique/temporelle avec une référence précise de flash ou un montage externe n’est pas établie ici.

Le job de simulation après synthèse est commenté (`.github/workflows/gds.yaml:28–38`) et la vérification d’équivalence est désactivée dans le flux observé. **L’audit a donc effectué une simulation locale supplémentaire de la netlist finale**, avec la bibliothèque officielle SG13G2 au commit PDK `c4b8b4e5e7a05f375cca3815d51b3a37721fbf5c`, sans annotation des délais SDF. Cinq tests utilisent seulement les broches : le contrôle GPIO passe ; les branches après ADD et SUB, le systick et la donnée SPI utilisateur échouent de façon identique en RTL et en netlist. Ces quatre défauts survivent donc à la synthèse. Les autres défauts IRQ ont été reproduits au niveau RTL seulement.

## Reproduction et preuves conservées

Tous les chemins ci-dessous sont relatifs à la copie `hepiarisc/` de cet audit.

| Preuve | Fichier |
|---|---|
| Banc exhaustif ALU et cas CPU/IRQ | `.review/audit_units.sv` |
| Résultats de ces cas | `.review/units-results.log` |
| Scénarios sur le module complet | `.review/audit_integration.py` |
| Résultats : 3 comportements attendus en échec | `.review/integration-results.log` |
| Banc via les broches, compatible RTL/netlist | `.review/audit_ports.py` |
| Résultats comparés RTL/netlist : 1 succès, 4 défauts reproduits | `.review/ports-rtl-results.log`, `.review/gatelevel-results.log` |
| Construction de la simulation netlist | `.review/Makefile.gl` |
| Suite d’origine reproduite en échec | `.review/verilator-tests-final.log` |
| Copie du test avec accès RAM ramené à 0x4F | `.review/test_ram80.py` |
| Suite diagnostique passée | `.review/test-ram80.log` |
| Lint et historique CI | `.review/verilator.log`, `.review/ci-test-failed.log`, `.review/ci-gds.log` |
| Versions et commit | `.review/metadata.json` |

Banc unitaire, depuis `hepiarisc/` :

```sh
verilator --binary --timing -Wno-fatal --top-module audit_units \
  --Mdir .review/obj_units .review/audit_units.sv \
  src/hepiarisc_alu.sv src/hepiarisc.sv src/hepiarisc_regbank.sv src/systick_gen.sv
.review/obj_units/Vaudit_units
```

Pour Cocotb, activer l’environnement contenant Cocotb 2.0.1 puis, depuis `hepiarisc/test/` :

```sh
make SIM=verilator EXTRA_ARGS='--no-timing -Wno-fatal' SIM_BUILD=../.review/obj_cocotb
PYTHONPATH=../.review make SIM=verilator EXTRA_ARGS='--no-timing -Wno-fatal' \
  SIM_BUILD=../.review/obj_cocotb COCOTB_TEST_MODULES=audit_integration
PYTHONPATH=../.review make SIM=verilator EXTRA_ARGS='--no-timing -Wno-fatal' \
  SIM_BUILD=../.review/obj_cocotb COCOTB_TEST_MODULES=test_ram80
```

Les deux premières commandes Cocotb échouent comme décrit ; la troisième passe. Le banc unitaire imprime les écarts, son code de sortie ne représente pas un verdict de conformité. `--no-timing` ignore uniquement le délai `#1` du bloc de préparation du dump dans le banc fourni ; l’horloge reste pilotée par Cocotb. La version locale Icarus 13.0 refuse certaines déclarations après utilisation, alors que la CI les accepte : les reproductions fonctionnelles ont donc utilisé Verilator 5.052 sur le RTL original, sans déplacement des déclarations.

Pour la comparaison par les broches, remplacer `COCOTB_TEST_MODULES` par `audit_ports` dans la commande RTL. Depuis `.review/`, lancer `make -f Makefile.gl` pour la netlist sous Icarus. Le Makefile réutilise la bibliothèque PDK téléchargée pour l’audit NPU, dans `../../simple_NPU/.review/sg13g2_stdcell.v`. Le modèle flash de ce banc est une copie du modèle fourni, avec initialisation explicite des deux registres de décalage pour éviter une erreur Python lors des transitions de reset entre tests ; elle est conservée dans `.review/flash_model.py`. Aucun changement n’est apporté au circuit.

## Priorité de remise en état

1. Corriger les indicateurs ADD/SUB et l’ensemble acceptation/sauvegarde/retour des IRQ.
2. Ajouter les cas reproduits à une suite séparée, notamment les interruptions pendant fetch, branches et banques.
3. Aligner tests, mémoire, brochage et documentation ; terminer ou restreindre explicitement le SPI utilisateur.
4. Refaire le flux physique sur le RTL corrigé, activer une validation après synthèse adaptée, puis valider les interfaces avec les composants externes prévus.

L’audit ne constitue pas une preuve formelle exhaustive du processeur, ni une validation sur silicium. Les défauts P1 ci-dessus suffisent néanmoins à écarter un verdict « tout est correct » sur ce commit.
