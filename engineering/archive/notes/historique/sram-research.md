# AstraPIO — solutions SRAM trouvées dans les projets et discussions

Recherche et essais du 18 septembre 2026. Aucun message externe publié. Aucun
changement au RTL, au GDS, au PDK installé ou au workflow de soumission.
La première révision AstraPIO n'est toujours pas enregistrée.

## Conclusion

Le blocage n'impose pas d'abandonner la SRAM ou de diminuer la mémoire :

1. Un projet SRAM a déjà été intégré **sur TTIHP26b** avec Magic non bloquant
   et un precheck officiel en échec.
2. Les corrections KLayout nécessaires ont déjà été fusionnées par IHP.
3. Notre **GDS complet inchangé donne zéro violation** avec le deck principal
   IHP corrigé, contre 1768 avec celui imposé actuellement par Tiny Tapeout.

Cela justifie une voie de révision provisoire documentée, mais ne transforme
pas automatiquement l'ancien precheck officiel en succès ni ne vaut accord
de fabrication pour AstraPIO.

## Précédents vérifiés

### Matt Venn : Multi Segment Monitor, TTIHP26b

- [Soumission intégrée #22](https://github.com/TinyTapeout/tinytapeout-ihp-26b/pull/22),
  fusionnée par `urish` le 27 août 2026 à 17:00:23 UTC.
- Révision intégrée : `1d893fb8d230497a268a1e820ac1d2a0c3d47b6d`.
- [Configuration exacte de cette révision](https://github.com/mattvenn/multi-seg-monitor/blob/1d893fb8d230497a268a1e820ac1d2a0c3d47b6d/src/config.json) :
  `ERROR_ON_MAGIC_DRC: false`, SRAM 1024×8, extraction SRAM abstraite.
- La PR présente `Check user project submission: SUCCESS` et
  `Run precheck: FAILURE` ; elle a néanmoins été fusionnée.
- [Run plus récent du 10 septembre](https://github.com/mattvenn/multi-seg-monitor/actions/runs/34474590388) :
  GDS, simulation de netlist et viewer réussis ; precheck échoué avec **2672**
  violations KLayout. Ce n'est donc pas un exemple de CI entièrement verte.
- Ce projet occupe 2×2 tiles et utilise une autre taille de SRAM. Le précédent
  concerne le traitement du contrôle, pas une preuve physique de notre 1×2.

### Uri Shaked : SRAM test, TTIHP0p2

- [Fiche officielle et retour de test silicium](https://tinytapeout.com/chips/ttihp0p2/tt_um_urish_sram_test/).
- [Révision effectivement intégrée](https://github.com/TinyTapeout/tinytapeout-ihp-0p2/blob/main/projects/tt_um_urish_sram_test/commit_id.json) :
  `2632a9900f668e66340abd46a1452736d07a29c1`, ancien flow `ttihp0p2-skip-lvs`.
- [Configuration modernisée en mars 2026](https://github.com/urish/ttihp-sram-test/blob/efca7b356e5df69fc9caa6bacb7b6c224a7001b1/src/config.json) :
  Magic non bloquant et extraction SRAM abstraite.
- [Run modernisé](https://github.com/urish/ttihp-sram-test/actions/runs/22628059705) :
  GDS et simulation de netlist réussis, precheck échoué. Les logs ont expiré ;
  la cause précise de ce precheck n'est donc pas affirmée.
- Ne pas confondre le silicium de 2024 avec la configuration modifiée en 2026.

### KianV SV32 TT Linux SoC, TTIHP26a

- [Soumission intégrée #304](https://github.com/TinyTapeout/tinytapeout-ihp-26a/pull/304),
  fusionnée le 15 mars 2026 malgré un contrôle central `Run precheck` en échec.
- [Configuration](https://github.com/splinedrive/kianv-sv32-tt-linux-soc/blob/b70b138ef0f2f7792149edd3832a70782b0b1627/src/config.json) :
  Magic non bloquant, deux SRAM 512×64, extraction abstraite.
- Son workflow utilise la branche `urish/tt-support-tools:ihp-8x4`.
  [Cette modification](https://github.com/urish/tt-support-tools/commit/542b5249d89eb4b058f1b3ecc73c581c2c0d08ac)
  exclut explicitement les régions SRAM des contrôles FEOL.
- Nous n'avons pas repris cette exclusion globale : le deck IHP corrigé permet
  déjà de contrôler notre layout sans ce filtrage.

## Correctifs officiels et discussions techniques

Le PDK imposé par [l'action precheck TTIHP26b](https://github.com/TinyTapeout/tt-gds-action/blob/ttihp26b/precheck/action.yml)
est `c4b8b4e5e7a05f375cca3815d51b3a37721fbf5c`, du 16 janvier 2026.

- [IHP PR #819](https://github.com/IHP-GmbH/IHP-Open-PDK/pull/819), fusionnée le
  10 mars : corrige `Cnt.c` selon les marqueurs SRAM/DigiBnd et réserve
  `Sdiod.d/e` aux dispositifs Schottky. Ce sont exactement les trois catégories
  de notre échec KLayout. Le fait que le ticket #793 reste ouvert était donc
  insuffisant pour conclure qu'aucune correction n'existait.
- [IHP PR #863](https://github.com/IHP-GmbH/IHP-Open-PDK/pull/863), fusionnée le
  16 mars : exceptions SRAM dans le deck Magic et script `read_sram_gds.tcl`.
- [Discussion technique #794](https://github.com/IHP-GmbH/IHP-Open-PDK/issues/794) :
  explications des ambiguïtés de lecture GDS, cellules à aplatir, exceptions
  SRAM et distinction avec les éventuelles vraies erreurs résiduelles.
- [Modèle LibreLane officiel IHP](https://github.com/IHP-GmbH/ihp-sg13g2-librelane-template/blob/main/librelane/config.yaml)
  : paramètre `MAGIC_GDS_FLATGLOB` pour lire les sous-cellules SRAM correctement.
- [IHP #1023](https://github.com/IHP-GmbH/IHP-Open-PDK/issues/1023) : témoignage
  utilisant précisément notre macro 256×8, puis correction du contrôle des
  couches `pin` hors grille. Ne pas modifier nous-mêmes la géométrie du fondeur.

## Essai comparatif sur AstraPIO

Outils : image `ghcr.io/librelane/librelane:3.0.5`, KLayout inclus, mode `deep`,
table `main`, aucun filtre de catégories, aucune option désactivant FEOL, BEOL,
offgrid, angle, pin ou forbidden. Ce test n'est pas une passe de densité/antenne
du chip complet ni un remplacement de tous les contrôles du precheck.

Deck corrigé, copie séparée inchangée du dépôt IHP :
`5e6d592e4002946a4616f798c357f0f3c06cf3b6`, main du 1er septembre 2026.

| GDS inchangé | Deck Tiny Tapeout c4b8… | Deck IHP 5e6d… |
|---|---:|---:|
| SRAM 256×8 seule | 1768 | **0** |
| AstraPIO complet, même GDS du run GitHub | 1768 | **0** |

Les deux contrôles du GDS complet ont été exécutés sur exactement le même fichier
du run GitHub, sans modification. Les trois catégories de l'ancien contrôle étaient
796 `Sdiod.d`, 796 `Sdiod.e`, 176 `Cnt.c.digibnd`.

SHA256 du GDS AstraPIO officiellement généré, utilisé sans modification :
`b26268a19c6b8c35964268fd1b3392a4d4dab1fedecd8ebdbfcbd3c6d0a3de2e`.
SHA256 du GDS SRAM :
`38ccf93cdc4ef0635aa008ef963fd10cabb82e7701f78f66b800b9e81561d634`.

Les rapports KLayout ont été ouverts avec l'API `klayout.rdb` et comptés :
zéro entrée chacun, pas seulement un code de sortie égal à zéro.

Reproduction : utiliser l'image ci-dessus pour exécuter `klayout -b -r
CHEMIN_DU_DECK/ihp-sg13g2.drc -rd input=GDS -rd report=RAPPORT.xml -rd thr=1
-rd threads=1`. Seul le chemin du deck change entre les deux mesures AstraPIO.
Les résultats bruts sont `astrapio-pinned.xml` (1768), `astrapio-current.xml`
(0), `sram-current.xml` (0), accompagnés des logs.

### Limite Magic

Deux essais diagnostiques du nouveau deck Magic avec les flatglobs IHP sur le
GDS complet ont terminé par un crash du moteur (code 139, Magic 8.3.623 ARM64).
Le second reprenait la séquence de contrôle LibreLane, avec suspension des mises
à jour et limite de fichiers ouverts réduite. Aucun rapport final n'a été produit.
**Ne pas annoncer Magic corrigé ou DRC global intégralement validé.**

## Voie recommandée pour la première révision

Préparer une révision provisoire suivant le précédent TTIHP26b : Magic reste
exécuté et ses rapports conservés, mais son ancien résultat ne bloque plus la
production de `tt_submission`. Conserver le precheck officiel inchangé et son
résultat réel ; ajouter séparément la validation KLayout corrigée et sa provenance.
Puis relancer GDS, simulation de netlist et soumission via la plateforme.

Cela implique de changer explicitement la politique de blocage Magic, pas de
prétendre que les erreurs historiques sont résolues. Ce changement n'a **pas**
été appliqué pendant cette recherche. Ne pas promettre une fusion automatique
ni une autorisation de fabrication sur la seule base des précédents.

À plus long terme : aligner les versions du flow/PDK et résoudre ou qualifier
le contrôle Magic sans dépendre d'une tolérance provisoire.
