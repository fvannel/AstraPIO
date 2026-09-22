# AstraPIO — validation de la version finale ABI 5

Mise à jour documentaire : 22 septembre 2026. Aucun nouveau test physique,
GDS ou dépôt de révision n’est produit par cette publication.

## Identité de la version

- Source : [`1b1c91183a4a9a5ea3516699845336175ffe6d96`](https://github.com/fvannel/AstraPIO/tree/1b1c91183a4a9a5ea3516699845336175ffe6d96).
- Projet [5799](https://app.tinytapeout.com/projects/5799), TTIHP26b, 1 × 2 tiles.
- [PR149](https://github.com/TinyTapeout/tinytapeout-ihp-26b/pull/149) fusionnée le 19 septembre 2026 à 15:14:01 UTC.
- Un PIO, programme 16 × 10 bits en latches, FIFO TX/RX de 2 octets, moteur temporel autonome.
- Sans macro SRAM, second contexte ou extension OUTMSB/ABI 6.
- PDK `c4b8b4e5e7a05f375cca3815d51b3a37721fbf5c`, LibreLane 3.0.5.

Les anciens fichiers de développement présents sur `main` et leur statut JSON
ne décrivent pas cette version. Le commit figé ci-dessus identifie le circuit ;
le commit de documentation n’en est pas une nouvelle révision matérielle.

## Résultats conservés

| Contrôle | Résultat et périmètre |
|---|---|
| RTL | 25 scénarios d’intégration par les broches |
| Gate-level | Les mêmes 25 scénarios sur la netlist routée, sans SDF |
| Comparaison ABI 4 → ABI 5 | 1 988 traces différentielles ; pas une preuve formelle |
| Unités et pilotes | FIFO, mémoire à latches 10/16 bits, assembleur, transport et pilotes C avec sanitizers |
| Placement/routage | Achevés ; 56 841,5 µm² de cellules, 94,5637 % d’occupation du cœur |
| Contrôles physiques officiels | Zéro violation DRC Magic/KLayout et antenne ; LVS et XOR conformes ; dix prechecks réussis |
| Audit temporel complémentaire | Trois coins ; early 0,95 / late 1,05 ; setup/hold, recovery/removal, gating, largeur d’impulsion, contraintes électriques et chemins non contraints |
| Intégration au shuttle | PR149 fusionnée ; contrôles centraux réussis |

Preuves publiques :

- [Construction officielle 35442726541](https://github.com/fvannel/AstraPIO/actions/runs/35442726541).
- [Audit complémentaire 35448283122](https://github.com/fvannel/AstraPIO/actions/runs/35448283122).
- [Contrôles centraux 35450180122](https://github.com/TinyTapeout/tinytapeout-ihp-26b/actions/runs/35450180122).
- [Révision acceptée PR149](https://github.com/TinyTapeout/tinytapeout-ihp-26b/pull/149).

Ces résultats concernent le candidat nommé et ses artefacts figés, pas un
autre état d’une branche. Aucun filtrage des erreurs DRC, dérogation SRAM ou
precheck rendu non bloquant n’est utilisé pour qualifier l’ABI 5 retenue.
Les procédures provisoires historiques présentes sur `main` ne s’appliquent pas.

## Marges temporelles

| Coin de cellules | Marge hold de l’audit complémentaire |
|---|---:|
| Fast, 1,32 V, −40 °C | +0,004872 ns |
| Typical, 1,20 V, 25 °C | +0,140331 ns |
| Slow, 1,08 V, 125 °C | +0,375741 ns |

La marge fast est étroite. Le périmètre est une horloge de 20 ns, les
contraintes d’E/S déclarées et les parasites nominaux extraits. Ces valeurs
ne constituent ni une plage d’alimentation garantie aux connecteurs de la
carte, ni une qualification électrique mesurée sur silicium.

## Rejeu WS2812 de la version finale

Le rejeu du 19 septembre couvre onze tests du moteur temporel et un scénario
compteur complet : **12/12 en RTL et 12/12 sur la netlist exacte soumise**, sans
échec ni test ignoré. Le scénario compteur vérifie, par mode :

- Douze trames et 1 440 bits en sortie.
- Capture du premier mot DIN de 24 bits, lu par le modèle d’hôte SPI pendant le relais.
- Remplacement sur DOUT par la valeur préparée par l’hôte.
- Relais régénéré des quatre mots suivants, données inchangées.
- Incrément du compteur sur demande, application à la trame suivante, retenue et bouclage 24 bits.
- IRQ, acquittement, absence d’erreurs et activité indépendante du PIO.

Latence observée : 680 à 699 ns ; impulsions hautes de 320/640 ns pour le profil
testé. Les observations RTL et gate-level concordent. Ces simulations ne
contiennent pas d’annotation SDF et ne modélisent pas toutes les variantes de LED.
Le modèle d’hôte SPI ne correspond pas à une exécution du code sur un ARM réel.

## Conservation et limites

Après réorganisation locale, les régressions ont été rejouées et les 50
empreintes des fichiers sources, outils, modèles et artefacts protégés ont été
vérifiées. Les fichiers lourds de travail ont ensuite été supprimés avec
l’accord de l’utilisateur ; les notes et preuves finales ont été conservées.
Cette opération n’a modifié ni le circuit soumis, ni son GDS.

Restent à qualifier sur matériel : transport SPI/DMA du LPC546xx, horloge,
niveaux électriques, adaptation de tension, carte et LED réelles. Aucune
simulation SDF ni qualification sur silicium n’est revendiquée. La fusion
de PR149 signifie acceptation de la révision, pas fabrication achevée.

La [datasheet ABI 5](datasheet/README.md) décrit le comportement programmé et
les limites connues. Le suivi automatique reste arrêté ; aucune nouvelle
construction matérielle ou soumission n’est autorisée par cette documentation.
