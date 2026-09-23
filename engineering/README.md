# Validation et maintenance d’AstraPIO

Ce dossier rassemble les preuves techniques et les archives d’ingénierie.
Le contrat d’utilisation du composant est décrit dans la
[documentation utilisateur](../docs/README.md).

## Identité du circuit

- Interface ABI 5, source `1b1c91183a4a9a5ea3516699845336175ffe6d96`.
- Projet Tiny Tapeout 5799, TTIHP26b, allocation 1 × 2 tiles.
- PDK `c4b8b4e5e7a05f375cca3815d51b3a37721fbf5c`, LibreLane 3.0.5.
- [Artefacts et manifeste d’identité](../release/README.md).

Le contrôle `python3 tools/check_final_release.py` vérifie les empreintes des
50 fichiers protégés. Une identité vérifiée n’est pas une nouvelle simulation
ni une nouvelle qualification physique.

## Résultats de référence

| Contrôle | Résultat et périmètre |
|---|---|
| Simulation RTL | 25 scénarios d’intégration par les broches |
| Simulation gate-level | Les mêmes 25 scénarios sur la netlist routée, sans SDF |
| Moteur temporel et application WS2812 | 12 scénarios en RTL et 12 en gate-level ; le scénario compteur contrôle 12 trames et 1 440 bits par mode |
| Placement et routage | 56 841,5 µm² de cellules ; occupation du cœur de 94,5637 % |
| Contrôles physiques | DRC Magic/KLayout et antenne sans violation ; LVS et XOR conformes ; dix prechecks réussis |
| Analyse temporelle complémentaire | Trois coins, facteurs early 0,95 et late 1,05 ; contrôles setup/hold, recovery/removal, gating, largeur d’impulsion et contraintes électriques |

Les rapports et résultats détaillés sont conservés dans
[release/validation](../release/validation/). La reproduction des simulations
est décrite dans le [guide de test](../test/README.md) et le
[guide du scénario WS2812](../test/ws2812/README.md).

Références publiques :

- [Construction physique officielle](https://github.com/fvannel/AstraPIO/actions/runs/35442726541).
- [Audit temporel complémentaire](https://github.com/fvannel/AstraPIO/actions/runs/35448283122).
- [Contrôles centraux du shuttle](https://github.com/TinyTapeout/tinytapeout-ihp-26b/actions/runs/35450180122).
- [Révision acceptée PR149](https://github.com/TinyTapeout/tinytapeout-ihp-26b/pull/149).

## Portée et limites

Les résultats s’appliquent uniquement au circuit et aux artefacts identifiés.
La marge hold minimale de l’audit est de +0,004872 ns au coin fast ; elle
concerne les contraintes déclarées et les parasites nominaux extraits.
Les simulations fonctionnelles n’incluent pas d’annotation SDF.

Le transport SPI est modélisé en simulation : il ne s’agit pas d’une exécution
du pilote sur un LPC réel. Horloge, niveaux électriques, transport SPI/DMA,
adaptations de tension et comportement sur carte restent à qualifier.
L’acceptation d’une révision dans le shuttle ne prouve pas une fabrication achevée.

## Archives

Les [archives d’ingénierie](archive/README.md) conservent les études, comptes
rendus et décisions pour la traçabilité. Elles ne font pas partie du manuel
du composant et ne définissent pas les caractéristiques de l’ABI 5.
