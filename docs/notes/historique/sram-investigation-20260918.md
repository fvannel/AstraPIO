# AstraPIO — enquête SRAM et prochaine révision sans contournement

État au 18 septembre 2026. Recherche publique, lecture des configurations des
révisions réellement soumises et essais locaux. Aucun push, aucune nouvelle
soumission et aucun message à un tiers pendant cette enquête.

Ce document conserve l'état de l'enquête initiale. La suite, autorisée ensuite,
est décrite dans [le protocole CI de diagnostic](sram-diagnostic-ci.md) : branche
isolée, contrôles bloquants, aucune nouvelle révision Tiny Tapeout.

## Conclusion

**Nous avons une cause démontrée pour les 1 768 erreurs KLayout, mais pas encore
une chaîne de validation physique entièrement propre et acceptée par TTIHP26b.**

- Le PDK imposé par le shuttle est antérieur aux corrections SRAM d'IHP.
- Le GDS exact de notre première révision passe désormais les **10 contrôles du
  precheck local**, avec le programme de contrôle officiel inchangé et le PDK
  amont corrigé. Aucun filtre de violations ni modification du GDS.
- Magic reste un blocage distinct : son contrôle avec le PDK récent et le script
  SRAM officiel plante dans notre environnement. Ce n'est pas un résultat DRC nul.
- Les précédents Tiny Tapeout examinés prouvent l'intégration de SRAM, mais
  comportent des contrôles désactivés ou échoués. Ils ne justifient pas de
  reproduire ces dérogations.
- Les deux contournements spécifiques à notre première révision ont été retirés
  **localement**. La révision déjà soumise et le dépôt distant restent inchangés.

## 1. Périmètre et limites de la recherche

Sources examinées : guide mémoire Tiny Tapeout, dépôts de shuttles et de projets,
workflows et configurations aux commits soumis, issues/PR/discussions IHP,
exemple LibreLane IHP, sources du fork de precheck utilisé par d'autres projets,
recherches dans les archives publiques de discussions silicium.

Les recherches GitHub de macros dans l'organisation TinyTapeout ont permis de
retrouver les quatre cas détaillés ci-dessous. Les recherches de discussions
contenant « SRAM » ont retourné une discussion IHP et aucune dans l'organisation
TinyTapeout. Cela ne constitue pas un inventaire exhaustif de tous les circuits,
branches ou messages historiques.

**Discord direct reste inaccessible : l'onglet est à l'écran de connexion.**
Une demande de connexion a été adressée à l'utilisateur. Aucun canal privé n'a
été lu. Les notes publiques d'Essenceia relatent une aide reçue sur Discord ;
elles ne remplacent pas la lecture de la discussion originale.

## 2. Preuve différentielle sur notre GDS

Révision soumise : `487ee6cf5936a1e0e0b7fc0d2b341f32f04f2790`.
GDS SHA256 :
`9368dfb687cbaf7a24e27f5b2ca6ca83eac38f7453b46e7047a7975839f3c240`.

| Essai | Règles IHP | Résultat |
|---|---|---|
| Precheck central de la première soumission | `c4b8b4e…` | 9 contrôles réussis, DRC en échec : 1 768 |
| SRAM seule, GDS fournisseur inchangé, essai de référence | `c4b8b4e…` | Les mêmes 1 768 erreurs |
| Même SRAM seule, essai différentiel de référence | `5e6d592…` | 0 erreur dans le deck principal |
| GDS soumis complet, nouveau precheck local | `5e6d592…` | **10/10 contrôles réussis**, 0 erreur DRC |
| SRAM seule, Magic 8.3.623, script officiel d'import | `5e6d592…` | Arrêt du processus, code 139, deux essais |

Répartition des anciennes erreurs : 796 `Sdiod.d`, 796 `Sdiod.e`,
176 `Cnt.c.digibnd`. Elles existaient déjà à l'intérieur de la macro intacte.

Le contrôle local du 18 septembre terminé à 10:35 UTC utilise
`tt-support-tools@01d5d2814fa9dd61e9d211e0b235a4a592a9316a` sans modification.
Le SHA256 de `precheck.py` est identique à celui du dépôt officiel :
`373d64678888bab22b38bbb3751ecb04293d76a4c2a960766f1825f6e85a8c6a`.
PDK de diagnostic : `5e6d592e4002946a4616f798c357f0f3c06cf3b6`, copie propre
du dépôt IHP. KLayout est fourni par l'image LibreLane 3.0.5 ; le contrôle de
syntaxe Verilog local utilise Yosys 0.63 via yowasp. Ce n'est donc pas une
nouvelle exécution du workflow GitHub central dans son environnement exact.

Les dix contrôles couvrent le DRC principal, les labels, objets d'aire nulle,
broches, frontière, couches interdites, noms, broches analogiques et syntaxe
Verilog. **Ils ne remplacent ni LVS, ni STA, ni Magic, ni la validation de densité
et d'antenne du chip complet.** Le succès local n'est pas une acceptation du
shuttle et ne rend pas vert le precheck central existant.

Preuves de cette passe : `work/sram-audit-20260918/corrected-pdk-precheck.log`
et `work/sram-audit-20260918/tt/precheck/reports/`. Les essais antérieurs sont
conservés dans `docs/evidence/sram-drc/` et le dossier de première soumission.

## 3. Pourquoi le precheck actuel échoue

Le [precheck de l'action TTIHP26b](https://github.com/TinyTapeout/tt-gds-action/blob/ttihp26b/precheck/action.yml)
et le [workflow central de soumission](https://github.com/TinyTapeout/tinytapeout-ihp-26b/blob/014be02cb66c8966a751785b27bb1bc3ae5ec64b/.github/workflows/project_submission.yaml)
imposent tous deux `c4b8b4e5e7a05f375cca3815d51b3a37721fbf5c`, du 16 janvier 2026.
Changer seulement notre `tools-ref` ne met pas à jour ce PDK central.

La [PR IHP #819](https://github.com/IHP-GmbH/IHP-Open-PDK/pull/819), fusionnée le
10 mars 2026, corrige précisément les trois familles observées : prise en compte
des régions SRAM pour `Cnt.c`, et application de `Sdiod.d/e` aux seuls dispositifs
Schottky. Le deck distingue notamment l'enclosure SRAM de 0,006 µm de celle des
autres régions. C'est une correction amont générale, pas une exception propre
à AstraPIO. Le ticket de suivi [#793](https://github.com/IHP-GmbH/IHP-Open-PDK/issues/793)
restait ouvert malgré cette correction : son seul statut ne suffisait pas à
conclure qu'il n'existait aucune solution.

La [PR #1025](https://github.com/IHP-GmbH/IHP-Open-PDK/pull/1025), fusionnée le
22 juillet, a aussi retiré du contrôle de grille les datatypes sans géométrie
fabriquée, dont les marqueurs de broches. Le problème était documenté dans
[#1023](https://github.com/IHP-GmbH/IHP-Open-PDK/issues/1023). Ne pas modifier les
polygones de la macro fournisseur pour corriger un contrôle inadapté.

**Suite nécessaire : faire approuver une version cohérente du PDK et des outils
par Tiny Tapeout, puis la faire utiliser aussi par le contrôle central.** Notre
test ne permet pas de décider unilatéralement d'une version de fabrication.

## 4. Ce que les anciens runs ont réellement fait

| Run / projet | Révision et taille | Méthode et limite vérifiées |
|---|---|---|
| TTIHP0p2 — SRAM test d'Uri Shaked | `2632a990…`, 2×2, SRAM 1024×8 | Flow ORFS `ttihp0p2-skip-lvs`, job precheck commenté. Fusion le 4 novembre 2024. |
| TTIHP26a — KianV Linux SoC | `b70b138e…`, 8×4, deux SRAM 512×64 | Magic non bloquant ; fork de precheck `ihp-8x4`. Contrôle central en échec malgré fusion le 15 mars 2026. |
| TTIHP26a — TinyMOA | `bf6ab407…`, 8×2, SRAM double port 512×32 | Magic non bloquant ; même fork. Contrôle central en échec malgré fusion le 23 mars 2026. |
| TTIHP26b — Multi Segment Monitor | `1d893fb8…`, 2×2, SRAM 1024×8 | Magic non bloquant et extraction abstraite de la macro. Contrôle central en échec malgré fusion le 27 août 2026. |

Sources, avec les commits effectivement soumis et leurs contrôles :

- [TTIHP0p2 PR #134](https://github.com/TinyTapeout/tinytapeout-ihp-0p2/pull/134),
  [workflow exact](https://github.com/urish/ttihp-sram-test/blob/2632a9900f668e66340abd46a1452736d07a29c1/.github/workflows/gds.yaml).
- [TTIHP26a PR #304](https://github.com/TinyTapeout/tinytapeout-ihp-26a/pull/304),
  [configuration KianV](https://github.com/splinedrive/kianv-sv32-tt-linux-soc/blob/b70b138ef0f2f7792149edd3832a70782b0b1627/src/config.json).
- [TTIHP26a PR #475](https://github.com/TinyTapeout/tinytapeout-ihp-26a/pull/475),
  [configuration TinyMOA](https://github.com/EzraWolf/TinyMOA-IHP26a/blob/bf6ab40705360950a3a34487e48a7b753cd80aac/src/config.json).
- [TTIHP26b PR #22](https://github.com/TinyTapeout/tinytapeout-ihp-26b/pull/22),
  [configuration Multi Segment Monitor](https://github.com/mattvenn/multi-seg-monitor/blob/1d893fb8d230497a268a1e820ac1d2a0c3d47b6d/src/config.json).

Le [fork `ihp-8x4`, commit 542b524](https://github.com/urish/tt-support-tools/commit/542b5249d89eb4b058f1b3ecc73c581c2c0d08ac)
réécrit une copie du deck pour soustraire les régions SRAM aux couches contrôlées
en FEOL. **Nous ne reprendrons pas cette méthode.**

Le [guide mémoire Tiny Tapeout](https://tinytapeout.com/specs/memory/) confirme
un test silicium réussi de la SRAM 1024×8 sur TTIHP0p2. Il donne la 256×8 comme
compatible avec 1×2 après rotation. Notre choix reste donc plausible ; il ne faut
pas confondre preuve silicium d'une autre macro, conformité de notre intégration
et bon fonctionnement de tous les vérificateurs.

## 5. Magic : méthode officielle et blocage restant

La [discussion IHP #794](https://github.com/IHP-GmbH/IHP-Open-PDK/issues/794)
explique les ambiguïtés de couches lorsque certaines sous-cellules SRAM sont
lues séparément. Aplatir ces sous-cellules à l'import résout des erreurs de
lecture ; cela ne revient pas à ignorer la zone SRAM au DRC. La discussion
signale aussi de possibles erreurs résiduelles de contacts hors cœur SRAM :
ne pas déclarer toutes les erreurs inoffensives par principe.

La [PR #863](https://github.com/IHP-GmbH/IHP-Open-PDK/pull/863), fusionnée le
16 mars, ajoute les règles SRAM et le
[script officiel `read_sram_gds.tcl`](https://github.com/IHP-GmbH/IHP-Open-PDK/blob/5e6d592e4002946a4616f798c357f0f3c06cf3b6/ihp-sg13g2/libs.tech/magic/read_sram_gds.tcl).
Il faut le charger **avant** la lecture GDS. Les familles concernées sont
`lvsres_*`, `*_CELL_SUB`, `VIA_M1_*`, `VIA_M2_*`, `RSC_*`, `*_CELL_CORNER`.
Les fonctions correspondantes nécessitent Magic 8.3.616 ou supérieur.

Notre image LibreLane 3.0.5 contient Magic 8.3.623. Avec les règles et ce script
officiels, la macro 256×8 seule provoque un arrêt code 139 pendant le contrôle.
Même résultat en limitant les descripteurs de fichiers à 1 024. Aucun rapport
DRC exploitable n'est produit : le diagnostic précis du crash reste à faire.
Les scripts et journaux sont conservés dans `work/sram-research/check_magic.tcl`
et `work/sram-audit-20260918/magic-current-macro*.log`.

Deux autres éléments empêchent de promettre un simple changement de version :

- Le GDS final Tiny Tapeout préfixe des noms de cellules. Les motifs d'import
  devront être contrôlés sur ces noms réels ; certains motifs non préfixés ne
  correspondent plus. Le crash existe toutefois aussi sur la macro originale.
- [IHP #1024](https://github.com/IHP-GmbH/IHP-Open-PDK/issues/1024) reste ouvert :
  la règle Magic `Cnt.c` SRAM à 0,02 µm diverge de la règle KLayout à 0,006 µm.
  Aucune modification locale arbitraire de cette valeur n'est justifiée.

Une piste positive : [Harald Pretl rapporte le 31 juillet](https://github.com/IHP-GmbH/IHP-Open-PDK/issues/1023#issuecomment-5142787807)
un résultat Magic nul avec **notre même macro 256×8**, dans IIC-OSIC-TOOLS et
LibreLane, alors que seul le contrôle KLayout des marqueurs de broches échouait.
C'est un témoignage direct intéressant, mais sans image/version/configuration
complète permettant de reproduire ce résultat ici. Il faut obtenir ces éléments,
pas assimiler ce témoignage à notre propre validation.

Attention également au [template LibreLane officiel IHP](https://github.com/IHP-GmbH/ihp-sg13g2-librelane-template) :
sa CI consultée appelle `make librelane-nodrc`, qui saute Magic DRC, KLayout DRC,
antenne et densité. Son voyant vert n'est pas la preuve que ces contrôles passent.

## 6. Méthode d'intégration à retenir

1. Conserver un ensemble cohérent GDS/LEF/Liberty/CDL/modèle Verilog, sans modifier
   le dessin fournisseur. Notre GDS SRAM intact a pour SHA256
   `38ccf93cdc4ef0635aa008ef963fd10cabb82e7701f78f66b800b9e81561d634`.
2. Raccorder les deux alimentations `VDD!` et `VDDARRAY!`, et `VSS!`. Les accès
   de la macro sont sur Metal4 ; le raccordement à TopMetal1 doit être réel,
   pas seulement déclaré dans la netlist.
3. Vérifier placement, rotation, halos et accès aux broches. AstraPIO place
   actuellement `core.imem.sram` en orientation E à `[124, 8]`.
4. Utiliser le traitement d'import SRAM prévu par IHP, vérifier son application
   après renommage des cellules, puis conserver le caractère bloquant du DRC.
5. Rejouer LVS, alimentation, STA aux corners cohérents et tests avec le modèle
   SRAM réel. Le succès du modèle logique ne prouve pas la tenue physique.

Les [notes publiques d'Essenceia](https://github.com/Essenceia/essenceia.github.io/blob/master/content/projects/IHP_SRAM/notes.md)
décrivent, après échange avec `tnt` et `mole99` sur Discord, l'ajout de straps
Metal5 entre Metal4 et TopMetal1. Ce document est un brouillon public, pas une
procédure de signoff. AstraPIO a déjà une connexion PDN spécifique Metal4 vers
TopMetal1 ; une autre topologie doit être mesurée, pas copiée à l'aveugle.
Elle n'explique pas nos 1 768 erreurs présentes aussi dans la macro isolée.

Notre RTL fixe bien `A_DLY=1`, désactive BIST et fournit le masque d'écriture.
Le piège `A_DLY` est documenté dans [IHP #462](https://github.com/IHP-GmbH/IHP-Open-PDK/issues/462).
La [discussion IHP #836](https://github.com/IHP-GmbH/IHP-Open-PDK/discussions/836)
précise que le générateur actuel ne supporte pas une autre alimentation nominale :
ne pas extrapoler les bibliothèques SRAM 1,2 V à 1,5 V.

## 7. Protections rétablies pour la prochaine publication

Changements locaux, sans RTL ni PDK de production modifié :

- `ERROR_ON_MAGIC_DRC: true`.
- Retrait de `continue-on-error` du precheck et de l'appel à
  `tools/provisional_precheck.py` dans le workflow GDS.
- Rapports bruts toujours conservés, même en cas d'échec.
- Retrait des autorisations de non-blocage pour les prochaines révisions dans
  `design_status.json`, tout en conservant les faits de la première soumission.
- Quatre tests de garde-fou exécutés avant construction GDS et dans `make check`.
  Ils ont échoué sur l'ancienne configuration, puis réussi après correction.

Ces tests empêchent le retour des contournements connus ; ils ne constituent pas
un analyseur général de tous les moyens de désactiver une vérification. L'ancien
script et ses fixtures restent comme historique, sans appel dans la publication.

Vérification locale après modification : `make test` réussit, avec les 22 scénarios
RTL, le test FIFO, le test hôte C sous AddressSanitizer/UndefinedBehaviorSanitizer,
6 tests d'outillage, les 16 tests historiques de la politique provisoire et les
4 nouveaux garde-fous. Aucun nouveau placement/routage ni test netlist/SDF n'a
été lancé pendant cette enquête. Les tests historiques ne réactivent pas leur
politique dans le workflow de publication.

Les valeurs du template `RUN_KLAYOUT_DRC=0` et `RUN_KLAYOUT_XOR=0` n'ont pas été
changées : le DRC KLayout obligatoire est exécuté par le precheck séparé. Leur
présence n'est pas une validation XOR ; ce contrôle reste à considérer pour
comparer les exports lors de la qualification du nouveau flow.

**Avec le PDK actuel du shuttle, la prochaine construction stricte doit échouer
tant que les causes ne sont pas résolues. C'est le comportement attendu.**

## 8. Prochaines actions, dans l'ordre

1. Lire les canaux pertinents du serveur Tiny Tapeout après connexion Discord,
   en recherchant la macro exacte, `Cnt.c`, `read_sram_gds`, `ihp-8x4`,
   `ERROR_ON_MAGIC_DRC`, `SRAM` et les échanges des mainteneurs. Ne rien publier
   sans demande explicite.
2. Soumettre aux mainteneurs, après accord de l'utilisateur, la reproduction
   minimale et demander le **couple outils/PDK officiellement retenu pour 26b**.
   Mentionner #819, #863, #1024 et les deux endroits où le PDK est figé.
3. Reproduire la macro seule avec une version Magic récente et une configuration
   connue, idéalement celle du témoignage IIC-OSIC-TOOLS. Identifier le crash,
   puis examiner chaque éventuelle erreur restante sans filtre.
4. Intégrer le flow validé sur une branche de travail. Refaire placement/routage,
   DRC bloquants, LVS, STA, alimentation, comparaison des exports et simulations
   RTL/modèle SRAM/netlist ; conserver les limitations SDF et carte tant qu'elles
   ne sont pas levées.
5. Publier une nouvelle révision seulement après revue des preuves et contrôles
   requis réellement réussis. Ne pas réutiliser le feu vert provisoire précédent.

Il n'existe pas dans les éléments examinés une recette Tiny Tapeout 26b totalement
reproductible, sans dérogation, déjà validée pour AstraPIO. La piste prioritaire
est la mise à jour officielle du flow, **pas l'abandon immédiat de la SRAM**.

Méthode de diagnostic utilisée : comparaison du même artefact entre versions,
réduction au GDS fournisseur seul, séparation KLayout/Magic, puis test de
non-régression avant restauration des protections. Le blocage physique reste
explicitement ouvert.
