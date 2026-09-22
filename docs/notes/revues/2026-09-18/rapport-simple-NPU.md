# Audit de ttihp26b_simple_NPU

Date : 18 septembre 2026. Commit examiné : `ad804f87f964325e06132a3c2f75ca132b8e9706` (« converting to 1x1 »). Dépôt : [leonllrmc/ttihp26b_simple_NPU](https://github.com/leonllrmc/ttihp26b_simple_NPU). Sources de travail : [/Users/fabien/Documents/_projects/10_hepia/TinyTapeout/work/reviews-2026-09-18/simple_NPU](/Users/fabien/Documents/_projects/10_hepia/TinyTapeout/work/reviews-2026-09-18/simple_NPU). Aucune correction des sources, aucun commit et aucune publication n’ont été effectués.

## Verdict

**Le projet n’est pas entièrement correct. Je déconseille de figer cette version pour fabrication avant correction du calcul signé et du reset.** La chaîne ASIC aboutit et les trois tests existants passent, mais ces succès masquent des erreurs fonctionnelles confirmées dans le RTL **et dans la netlist finale du GDS publié**.

Deux défauts sont certains : multiplication négative incorrecte et commande de sauvegarde survivant au reset. Deux comportements supplémentaires de l’interface doivent être corrigés ou explicitement spécifiés : capture des données un cycle après le strobe, et perte de la première entrée lors d’une nouvelle inférence sans reset. Les sections « How it works » et « How to test » de la documentation sont toujours `TODO`, donc un contrat alternatif d’interface ne peut pas être vérifié.

## Résultats prioritaires

### 1. P1 — Les produits signés sont calculés comme des produits non signés

Localisation : [src/neuron.sv, ligne 14](https://github.com/leonllrmc/ttihp26b_simple_NPU/blob/ad804f87f964325e06132a3c2f75ca132b8e9706/src/neuron.sv#L14), puis quantification aux lignes 18–26.

`prev_activation` et `weight` sont déclarés comme des vecteurs packed signés à deux dimensions. Une sélection de sous-vecteur comme `prev_activation[j]` est cependant non signée. Le caractère signé de `mul_result[j]` ne corrige pas les opérandes de la multiplication.

Reproduction unitaire, une seule voie active, biais nul :

- activation `0xF` (−1), poids `0x1` (+1) ;
- produit RTL : +15, au lieu de −1 ;
- après la quantification déjà présente `product[5:2]`, sortie `0x3` (+3), au lieu de `0xF` (−1).

Le test exhaustif couvre les 256 couples −8…7 sur chacune des huit voies : **1 152 divergences sur 2 048 essais**. Le modèle attendu conserve exactement la division par quatre par produit et le débordement modulo 16 du RTL ; l’échec ne dépend donc pas d’une politique de saturation inventée par l’audit.

Une inférence complète alimentée par une flash SPI simulée, avec les huit neurones lisant la même entrée −1 pondérée par +1, produit `[3,3,3,3,3,3,3,3]` au lieu de `[15,15,15,15,15,15,15,15]`. Résultat identique en RTL et en netlist finale.

Impact : les poids négatifs ou activations négatives donnent des résultats incorrects, donc une grande partie des réseaux signés est inutilisable.

Correction conseillée : convertir explicitement **chaque opérande** avec `$signed(prev_activation[j]) * $signed(weight[j])`, ou utiliser des éléments réellement typés signés. Conserver le banc exhaustif et ajouter des inférences négatives aux tests CI. Décider séparément du format fixe et des débordements souhaités.

Preuves : [banc exhaustif](/Users/fabien/Documents/_projects/10_hepia/TinyTapeout/work/reviews-2026-09-18/simple_NPU/.review/mac_exhaustive.sv), [résultat exhaustif](/Users/fabien/Documents/_projects/10_hepia/TinyTapeout/work/reviews-2026-09-18/simple_NPU/.review/mac_exhaustive.log), [simulations RTL](/Users/fabien/Documents/_projects/10_hepia/TinyTapeout/work/reviews-2026-09-18/simple_NPU/.review/review-tests.log), [simulations netlist](/Users/fabien/Documents/_projects/10_hepia/TinyTapeout/work/reviews-2026-09-18/simple_NPU/.review/gatelevel-tests.log).

### 2. P2 — Une sauvegarde en attente survit au reset et peut déclencher une inférence fantôme

Localisation : [src/project.sv, lignes 198–199](https://github.com/leonllrmc/ttihp26b_simple_NPU/blob/ad804f87f964325e06132a3c2f75ca132b8e9706/src/project.sv#L198), reset [lignes 210–225](https://github.com/leonllrmc/ttihp26b_simple_NPU/blob/ad804f87f964325e06132a3c2f75ca132b8e9706/src/project.sv#L210), détection [lignes 227–228](https://github.com/leonllrmc/ttihp26b_simple_NPU/blob/ad804f87f964325e06132a3c2f75ca132b8e9706/src/project.sv#L227).

`data_save_pulse` et `data_save_old` ne sont pas initialisés dans la branche reset. Une impulsion générée juste avant le reset reste mémorisée pendant celui-ci. Au premier front après relâchement, `STATE_INPUT_VALUES` consomme cette ancienne impulsion avec l’adresse et les données présentes à ce moment.

Reproduction : créer une sauvegarde en attente, activer le reset pendant trois cycles, garder `save_activation=0`, présenter adresse 7/donnée 5 et relâcher le reset. Sans nouvelle sauvegarde, `activation[7]` devient 5 et `CS` passe à 0 : le moteur SPI démarre. Même résultat RTL et netlist.

Impact : écriture intempestive et calcul démarré avec des activations incomplètes après une réinitialisation en fonctionnement. À la première mise sous tension, ces registres ne sont pas non plus garantis connus par le reset.

Correction conseillée : réinitialiser les deux registres à zéro et vérifier le reset depuis chaque état avec bouton haut/bas et impulsion en attente. Le choix de traiter un bouton déjà haut au relâchement comme une commande doit être spécifié.

### 3. P2 — Le premier chargement après une inférence est perdu, sauf impulsion de réarmement supplémentaire

Localisation : [src/project.sv, lignes 343–346](https://github.com/leonllrmc/ttihp26b_simple_NPU/blob/ad804f87f964325e06132a3c2f75ca132b8e9706/src/project.sv#L343).

Dans `STATE_INSTRUCTION_END`, une sauvegarde fait uniquement revenir vers `STATE_INPUT_VALUES` ; elle n’enregistre pas la donnée. Le même protocole « écrire les huit activations 0 à 7 » fonctionne après reset, mais perd l’écriture 0 après la première inférence.

Reproduction avec un réseau identité : première inférence sur `[1,1,1,1,1,1,1,1]`, puis chargement de `[2,2,2,2,2,2,2,2]` sans reset. La seconde sortie est `[1,2,2,2,2,2,2,2]`, en RTL comme en netlist. Chaque entrée est maintenue plusieurs cycles : ce résultat est indépendant du problème de strobe court ci-dessous.

Correction conseillée : enregistrer la première entrée tout en quittant `END`, ou retourner directement à un état prêt pour le chargement. Si une commande de réarmement séparée est voulue, la documenter clairement et la distinguer du chargement. **Le comportement est confirmé ; son statut de défaut dépend d’un protocole de réarmement qui est actuellement absent de la documentation.**

### 4. P2 — Le strobe et son adresse/donnée ne sont pas capturés ensemble

Localisation : [src/project.sv, lignes 227–235](https://github.com/leonllrmc/ttihp26b_simple_NPU/blob/ad804f87f964325e06132a3c2f75ca132b8e9706/src/project.sv#L227).

L’impulsion est enregistrée dans `data_save_pulse`, puis utilisée au front suivant ; `data_addr` et `data_input` sont lus directement lors de ce second front. Un strobe valide un cycle avec adresse 2/donnée 5, suivi d’adresse 3/donnée 6 au cycle suivant, écrit **6 à l’adresse 3** et ne modifie pas l’adresse 2. Reproduit en RTL et netlist.

Les tests existants gardent le bus et le strobe hauts deux cycles, ce qui masque ce comportement ([test/test.py, lignes 183–197](https://github.com/leonllrmc/ttihp26b_simple_NPU/blob/ad804f87f964325e06132a3c2f75ca132b8e9706/test/test.py#L183)).

Correction conseillée : capturer adresse, donnée et événement ensemble, ou utiliser la détection du front directement pour l’écriture. À défaut, publier un contrat exigeant que le bus soit maintenu jusqu’au front suivant. **En l’absence de contrat, l’audit le classe comme anomalie d’interface à résoudre, sans affirmer qu’une durée de deux cycles serait impossible à utiliser.**

## Ce qui fonctionne et ce qui a été vérifié

Architecture observée : huit activations de quatre bits, huit poids de quatre bits par neurone, biais quatre bits, huit fonctions d’activation. Une instruction comprend un en-tête `end[7], activation[6:4], bias[3:0]` puis quatre octets de poids, nibble fort en premier. Huit neurones forment une couche ; les résultats temporaires sont transférés ensemble dans la mémoire d’activations. La lecture SPI commence à `0x000000` avec la commande `0x03`, adresse 24 bits, mode 0 et SCLK à 25 MHz pour une horloge système de 50 MHz.

- Les noms de module, liste des trois sources, broches et directions d’I/O correspondent à `info.yaml`. `uio_oe=0x07` vérifié en simulation ; sorties inutilisées affectées. `ena` ignoré conformément au contrat/commentaire Tiny Tapeout de ce wrapper : pas de défaut signalé pour cela.
- **Trois tests existants : 3/3 réussis** sous Verilator 5.052 et cocotb 2.0.1 ; le [workflow test du commit](https://github.com/leonllrmc/ttihp26b_simple_NPU/actions/runs/35253058500) est également vert.
- Nouveau test de deux couches positives, permutations inverses avec poids 4, résultats `[0,1,2,3,4,5,6,7]` : réussi en RTL et netlist. Il vérifie l’ordre des poids, les huit écritures d’une couche, le transfert de couche, la commande SPI, l’adresse zéro, la fin de programme et la lecture par les broches.
- Les cinq scénarios complémentaires donnent **1 succès et 4 échecs expliqués ci-dessus**, à l’identique dans les deux représentations.
- Lint Verilator terminé sans erreur avec `-Wno-fatal`, mais avec avertissements : largeurs de comparaisons dans SPI, affectations bloquantes dans processus séquentiels, initialisations de registres et signaux inutilisés. Aucune déduction de latch dans les métriques Yosys publiées.

## Vérification ASIC à partir des artefacts du commit

Le [workflow GDS du 17 septembre 2026](https://github.com/leonllrmc/ttihp26b_simple_NPU/actions/runs/35253058716), son job précontrôle et son viewer ont réussi. Les artefacts ont été téléchargés et leur [commit_id.json](/Users/fabien/Documents/_projects/10_hepia/TinyTapeout/work/reviews-2026-09-18/simple_NPU/.review/gds_logs/runs/wokwi/final/commit_id.json) correspond exactement au commit audité.

Le [précontrôle](/Users/fabien/Documents/_projects/10_hepia/TinyTapeout/work/reviews-2026-09-18/simple_NPU/.review/precheck/results.md) contient dix vérifications réussies : notamment DRC SG13G2, labels, broches, frontières, couches et syntaxe. Les [métriques finales](/Users/fabien/Documents/_projects/10_hepia/TinyTapeout/work/reviews-2026-09-18/simple_NPU/.review/gds_logs/runs/wokwi/final/metrics.json) indiquent zéro erreur DRC finale, zéro erreur LVS, zéro violation d’antenne, zéro cellule non mappée, zéro latch inféré.

La STA publiée à 20 ns couvre les coins `nom_fast_1p32V_m40C`, `nom_typ_1p20V_25C` et `nom_slow_1p08V_125C` : WNS et TNS nuls, pire marge setup **+9,6065 ns**, pire marge hold **+0,1145 ns**. Une violation de fanout demeure dans chaque coin : `clkbuf_0_clk/X` charge 16 pour une limite 8. Elle n’a pas fait échouer le flow ; à faire examiner dans la configuration CTS et les règles du shuttle, sans la confondre avec une violation setup/hold.

La simulation de la netlist finale utilise la bibliothèque officielle SG13G2 au même commit PDK `c4b8b4e5e7a05f375cca3815d51b3a37721fbf5c`. Elle est fonctionnelle, **sans annotation SDF**. Elle confirme que les défauts retenus ne disparaissent pas à la synthèse. Le job de simulation gate-level du dépôt est commenté ([.github/workflows/gds.yaml, lignes 28–38](https://github.com/leonllrmc/ttihp26b_simple_NPU/blob/ad804f87f964325e06132a3c2f75ca132b8e9706/.github/workflows/gds.yaml#L28)) ; les tests existants accèdent à des signaux internes absents après aplatissement et devraient être adaptés aux broches pour l’activer.

Ces contrôles reposent sur les artefacts publiés et sur une simulation locale de leur netlist. Le placement/routage, l’extraction, la STA, DRC et LVS n’ont pas été recalculés localement. La fabrication, les pads du chip complet, le boîtier et la carte ne sont pas validés par cet audit.

## Lacunes à traiter avant une validation complète

1. Définir le format numérique : position binaire, troncature **de chaque produit avant somme**, somme/biais modulo 16, comportement aux débordements, `abs(-8)` et `-(-8)` non représentables positivement sur quatre bits. Les fonctions sigmoid produisent respectivement des codes 4…11 et 2…14, alors que les calculs voisins utilisent un domaine signé −8…7 ; il faut définir la conversion entre couches. Ce sont des choix non documentés, pas des bugs supplémentaires démontrés ici.
2. Renseigner [docs/info.md, lignes 12–22](https://github.com/leonllrmc/ttihp26b_simple_NPU/blob/ad804f87f964325e06132a3c2f75ca132b8e9706/docs/info.md#L12) : encodage flash, exemples binaires, programmation d’un réseau, protocole de chargement/redémarrage, durée du strobe, fin d’inférence, contraintes de reset. Le fichier `customasm_sample.s` décrit un processeur distinct et ne fournit pas un assembleur utilisable pour ce NPU.
3. Les tests actuels ne couvrent que l’identité et des données non négatives, sans seconde inférence ni reset en fonctionnement. Les boucles `while 1` n’ont pas de délai maximal réel : `max_cycles` compte des neurones terminés, pas les cycles d’horloge. Ajouter un timeout indépendant et des tests des huit fonctions d’activation.
4. L’entrée `data_save_btn` est utilisée sans synchronisation/dérebond. Si elle provient réellement d’un bouton ou d’un microcontrôleur asynchrone, définir et traiter la traversée de domaine et la stabilité du bus. Un contrôleur synchrone respectant le timing peut être utilisé ; aucune panne de métastabilité n’est revendiquée sur la seule simulation.
5. La flash n’est modélisée qu’au niveau protocole logique. Les contraintes SDC imposent des délais génériques d’entrée/sortie de 4 ns par rapport à `clk` ; elles ne prouvent pas le trajet aller-retour SCLK/flash/MISO d’une carte à 25 MHz. Sélectionner une référence de flash, vérifier son délai de sortie, démarrage/reset, tension et marges PCB/pads. La phrase « any flash » de la documentation est trop large pour établir cette compatibilité.
6. La commande `make` par défaut échoue localement avec Icarus 13.0 sur la référence à `xfer_active` avant sa déclaration ([src/spi_master.v, lignes 54 et 67](https://github.com/leonllrmc/ttihp26b_simple_NPU/blob/ad804f87f964325e06132a3c2f75ca132b8e9706/src/spi_master.v#L54)). La CI et Verilator acceptent ce code. Déplacer la déclaration avant utilisation ou fixer la version du simulateur ; ceci est un problème de portabilité, pas une preuve d’échec de synthèse.

## Reproduction et fichiers de preuve

Les ajouts d’audit sont isolés dans [/Users/fabien/Documents/_projects/10_hepia/TinyTapeout/work/reviews-2026-09-18/simple_NPU/.review](/Users/fabien/Documents/_projects/10_hepia/TinyTapeout/work/reviews-2026-09-18/simple_NPU/.review). `git diff --exit-code` retourne zéro : aucun fichier versionné n’a été modifié. Python 3.12.10 a été utilisé, car cocotb 2.0.1 ne prend pas en charge Python 3.14 installé par défaut. Outils : Icarus 13.0, Verilator 5.052, cocotb 2.0.1. La synthèse publiée utilise Yosys 0.62.

Depuis le dépôt audité, lancer le test unitaire (sortie non nulle attendue avant correction) :

```sh
iverilog -g2012 -s mac_exhaustive -o .review/mac_exhaustive.vvp src/neuron.sv .review/mac_exhaustive.sv
vvp .review/mac_exhaustive.vvp
```

Depuis `test/`, avec l’environnement Python de l’audit, lancer les tests RTL :

```sh
PATH="$PWD/../.review/venv312/bin:$PATH" COMPILE_ARGS='-Wno-fatal --no-timing' make SIM=verilator
PATH="$PWD/../.review/venv312/bin:$PATH" PYTHONPATH="$PWD/../.review:$PWD" COMPILE_ARGS='-Wno-fatal --no-timing' make SIM=verilator COCOTB_TEST_MODULES=review_tests
```

Depuis `.review/`, exécuter la netlist publiée :

```sh
PATH="$PWD/venv312/bin:$PATH" make -f Makefile.gl
```

Journaux : [tests initiaux](/Users/fabien/Documents/_projects/10_hepia/TinyTapeout/work/reviews-2026-09-18/simple_NPU/.review/baseline-verilator-tests.log), [lint](/Users/fabien/Documents/_projects/10_hepia/TinyTapeout/work/reviews-2026-09-18/simple_NPU/.review/verilator.log), [échec Icarus RTL](/Users/fabien/Documents/_projects/10_hepia/TinyTapeout/work/reviews-2026-09-18/simple_NPU/.review/baseline-tests.log), [tests supplémentaires RTL](/Users/fabien/Documents/_projects/10_hepia/TinyTapeout/work/reviews-2026-09-18/simple_NPU/.review/review-tests.log), [tests supplémentaires netlist](/Users/fabien/Documents/_projects/10_hepia/TinyTapeout/work/reviews-2026-09-18/simple_NPU/.review/gatelevel-tests.log), [workflow GDS](/Users/fabien/Documents/_projects/10_hepia/TinyTapeout/work/reviews-2026-09-18/simple_NPU/.review/gds-workflow.log). Banc complet : [review_tests.py](/Users/fabien/Documents/_projects/10_hepia/TinyTapeout/work/reviews-2026-09-18/simple_NPU/.review/review_tests.py). Les échecs des bancs supplémentaires sont attendus et matérialisent les constats de cet audit.

## Complément de contrelecture

Les huit fonctions d'activation ont été vérifiées sur leurs seize entrées possibles : **128 cas, zéro divergence par rapport aux formules/LUT présentes dans le RTL**. Cela vérifie leur implémentation actuelle, sans approuver un format numérique qui reste à spécifier. Banc et résultat : `.review/activation_exhaustive.sv`, `.review/activation_exhaustive.log`. La note `.review/complement-conception-fabrication.md` détaille les trois coins STA, les contraintes de reset/interfaces et les critères de revalidation.
