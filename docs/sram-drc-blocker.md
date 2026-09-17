# Blocage DRC reproductible — macro SRAM IHP

Constaté localement le 18 septembre 2026. **Aucune règle ni géométrie PDK modifiée ;
aucune dérogation demandée ou appliquée.** Ce rapport est prêt à communiquer,
mais aucun message n'a été envoyé à Tiny Tapeout/IHP.

## Résultat

Le precheck officiel TTIHP26b (tt-support-tools
`01d5d2814fa9dd61e9d211e0b235a4a592a9316a`) échoue sur le GDS complet avec
1768 violations KLayout SG13G2. Les neuf autres contrôles passent.
Le même deck exécuté sur **le GDS SRAM seul, inchangé** produit les mêmes
1768 violations, par catégories :

| Règle | Nombre |
|---|---:|
| Sdiod.d | 796 |
| Sdiod.e | 796 |
| Cnt.c.digibnd | 176 |

PDK : `c4b8b4e5e7a05f375cca3815d51b3a37721fbf5c`, celui imposé par
[l'action precheck du run](https://github.com/TinyTapeout/tt-gds-action/blob/ttihp26b/precheck/action.yml).
Macro : `RM_IHPSG13_1P_256x8_c3_bm_bist`.
SHA256 du GDS installé **et** de la copie téléchargée directement du dépôt amont :
`38ccf93cdc4ef0635aa008ef963fd10cabb82e7701f78f66b800b9e81561d634`.

[GDS amont exact](https://github.com/IHP-GmbH/IHP-Open-PDK/blob/c4b8b4e5e7a05f375cca3815d51b3a37721fbf5c/ihp-sg13g2/libs.ref/sg13g2_sram/gds/RM_IHPSG13_1P_256x8_c3_bm_bist.gds).
Cette égalité exclut une altération par notre copie locale. Elle n'établit pas
si la bonne correction appartient à la macro, au deck ou au traitement officiel
des cellules SRAM : cette décision revient aux responsables du flow/fondeur.

## Reproduction minimale

Depuis la racine, avec le PDK installé selon `toolchain.md` :

```sh
mkdir -p work/sram-drc-repro
docker run --rm -v "$PWD:/project" -w /project \
  ghcr.io/librelane/librelane:3.0.5 klayout -b \
  -r /project/work/pdk/ihp-sg13g2/libs.tech/klayout/tech/drc/ihp-sg13g2.drc \
  -rd input=/project/work/pdk/ihp-sg13g2/libs.ref/sg13g2_sram/gds/RM_IHPSG13_1P_256x8_c3_bm_bist.gds \
  -rd report=/project/work/sram-drc-repro/original.xml
```

Preuves conservées : `work/sram-drc/original.xml`, `original.log`,
`upstream-256x8.gds`, et `work/hardening-buffered-v2/precheck-reports/` pour le projet complet.
Des exports par Magic et par KLayout ont donné le même résultat sur un candidat
antérieur. L'outil Magic rapporte en outre des erreurs de macro, mais le contrôle
IHP de référence dans le precheck Tiny Tapeout est ici celui de KLayout.

## Question à faire valider avant soumission

« La macro 256×8 du PDK c4b8… est-elle autorisée sur TTIHP26b ? Avec le deck fourni,
son GDS amont inchangé produit 1768 violations Sdiod.d/Sdiod.e/Cnt.c.digibnd.
Quelle révision ou procédure **officielle** faut-il appliquer ? »

Ne pas remplacer silencieusement le PDK, filtrer les erreurs, modifier le layout
de la macro ou déclarer le precheck réussi. Les variantes à mémoire en bascules
mesurées précédemment dépassaient le budget pour les fonctionnalités visées.
Une solution sans cette SRAM demanderait un nouvel arbitrage de capacité.
