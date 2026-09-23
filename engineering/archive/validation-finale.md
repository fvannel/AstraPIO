# Bilan de validation — AstraPIO final ABI 5

Source gelée : **`1b1c91183a4a9a5ea3516699845336175ffe6d96`**.
Projet 5799, TTIHP26b, 1 × 2 tiles, PDK
`c4b8b4e5e7a05f375cca3815d51b3a37721fbf5c`, LibreLane 3.0.5.
Un PIO, 16 × 10 bits en latches, files TX/RX de deux octets et moteur temporel.
Pas de macro SRAM et pas d'extension OUTMSB/ABI 6.

## Résultats de la version soumise

| Contrôle | Résultat et périmètre |
|---|---|
| RTL | 25 scénarios d'intégration à travers les broches |
| Gate-level | Les mêmes 25 scénarios sur la netlist routée, sans SDF |
| Comparaison ABI 4 → ABI 5 | 1 988 traces différentielles, dont 944 opérations dans deux états et 100 programmes aléatoires ; pas une preuve formelle |
| Unités et pilotes | FIFO, mémoire à latches en largeurs 10/16, assembleur/protocole, pilotes C avec sanitizers |
| Placement et routage | Achevés ; 56 841,5 µm² de cellules, 94,5637 % d'occupation du cœur |
| Contrôles physiques officiels | Zéro violation Magic/KLayout DRC, LVS, XOR et antenne ; dix prechecks réussis |
| Audit temporel complémentaire | Trois coins, early 0,95 / late 1,05 explicites, contrôles setup/hold, recovery/removal, gating, largeur d'impulsion, électriques et chemins non contraints réussis |
| Soumission | PR149 fusionnée le 19 septembre 2026 à 15:14:01 UTC ; contrôles centraux réussis |

Preuves : [build officiel 35442726541](https://github.com/fvannel/AstraPIO/actions/runs/35442726541),
[audit 35448283122](https://github.com/fvannel/AstraPIO/actions/runs/35448283122),
[PR149](https://github.com/TinyTapeout/tinytapeout-ihp-26b/pull/149),
[contrôles centraux 35450180122](https://github.com/TinyTapeout/tinytapeout-ihp-26b/actions/runs/35450180122).
Les rapports finaux utiles sont également conservés dans `release/validation/`.

| Coin de cellules | Marge hold de l'audit explicite |
|---|---:|
| Fast, 1,32 V, −40 °C | +0,004872 ns |
| Typical, 1,20 V, 25 °C | +0,140331 ns |
| Slow, 1,08 V, 125 °C | +0,375741 ns |

La marge fast reste étroite. Ces résultats concernent l'horloge de 20 ns,
les contraintes d'entrées/sorties déclarées et les parasites nominaux extraits.
Ils ne valent ni pour des modifications arbitraires du circuit ni pour une carte réelle.

## Application WS2812 — rejeu du 19 septembre 2026

Les onze tests du moteur temporel et le scénario compteur complet réussissent :
**12/12 en RTL et 12/12 sur la netlist exacte soumise**, sans échec ni test ignoré.
Le scénario complet vérifie, par mode, douze trames et 1 440 bits de sortie :

- Capture du premier mot DIN de 24 bits, lu par l'hôte SPI pendant le relais.
- Remplacement simultané sur DOUT par le compteur préparé par l'hôte.
- Relais régénéré des quatre mots suivants, avec données inchangées.
- Incrément sur demande seulement, report à la trame suivante, retenue et bouclage sur 24 bits.
- IRQ, acquittement, absence d'erreurs et activité indépendante du PIO.

Latence mesurée : 680 à 699 ns ; impulsions hautes de 320/640 ns.
Les observations RTL et gate-level sont identiques hors étiquette du mode.
Voir [le détail reproductible](../../test/ws2812/README.md).

## Essais non retenus

Les notes de **toutes les familles d'essais** sont indexées dans
[docs/notes](notes/README.md), avec les registres de résultats et identifiants
des exécutions. SRAM, mémoire flip-flop et extension OUTMSB ne font pas partie
du design final. La réussite fonctionnelle des études ABI 6 ne compense pas
leurs échecs physiques. Aucun contrôle n'est désactivé pour les qualifier.

## Contrôle du nettoyage local — 20 septembre 2026

Les 25 scénarios de broches, les 1 988 traces différentielles, unités,
pilotes C et tests Python passent. Le rejeu WS2812 passe à nouveau en RTL et
gate-level : 12/12 dans chaque mode, observations identiques aux rapports
conservés. Les 50 empreintes du circuit et de ses fichiers protégés sont
vérifiées. Voir [le compte rendu de nettoyage](nettoyage-20260920.md), qui
documente aussi le chemin UART corrigé, le passage initial par la Corbeille
puis la suppression définitive des reliquats autorisée par l'utilisateur.

## Limites et gel

Pas de simulation SDF, pas d'exécution du firmware sur un LPC546xx réel, pas de
qualification électrique de la carte ou du silicium. L'hôte des simulations
est un modèle SPI. L'acceptation dans le shuttle n'est pas une preuve de fabrication.

Le suivi périodique reste en pause. Aucun push, build distant ou nouvelle
soumission n'est effectué par le nettoyage. `release/manifest.json` et
`tools/check_final_release.py` contrôlent l'identité des sources et des artefacts
conservés ; ce contrôle n'est pas une nouvelle qualification physique.
