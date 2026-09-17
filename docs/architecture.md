# Architecture de travail — PIO généraliste

## Périmètre convenu

Deux tiles IHP comme budget cible, un hôte ARM LPC55xxx, liaison SPI dédiée,
et deux contextes PIO partageant un moteur. Chaque contexte conserve sa position
dans le programme, son état de travail et ses conditions d'attente. Le nombre
de contextes est réalisé dans le prototype ; la surface reste à vérifier.

Les protocoles applicatifs sont des programmes rechargeables après fabrication.
La réception, l'émission, le relais et la modification WS2812 constituent un
cas de validation exigeant ; aucun bloc de remplacement de pixels spécifique
ne doit entrer silencieusement dans l'architecture.

## Répartition des broches proposée

| Interface | Broches Tiny Tapeout | Direction vue par l'ASIC |
| --- | --- | --- |
| SPI hôte SCK, MOSI, CS_N | ui[0], ui[1], ui[2] | Entrées |
| SPI hôte MISO | uo[0] | Sortie, bus dédié |
| Interruption hôte | uo[1] | Sortie |
| PIO_IN0 à PIO_IN4 | ui[3] à ui[7] | Entrées |
| PIO_OUT0 à PIO_OUT5 | uo[2] à uo[7] | Sorties |
| PIO_IO0 à PIO_IO7 | uio[0] à uio[7] | Bidirectionnelles |

Horloge et reset dédiés en plus. Dix-neuf signaux applicatifs partagés, pas par
contexte. Les indices logiques sont définis dans [l'ISA v0](isa-v0.md).
La référence LPC exacte et ses broches ne sont pas encore connues.

## Fonctions génériques

- Lecture/écriture masquée des broches et contrôle de leur direction.
- Décalage de données, petits registres et branchements.
- Attente d'un niveau ou d'un événement, temporisation et échéances.
- Échange avec l'hôte et entre contextes, sans imposer un détour ARM.
- Arrêt, reprise, remise à zéro et indication des erreurs.

La première version dispose d'une ISA provisoire de 15 instructions, d'un
accumulateur 16 bits par contexte et d'un contrat cycle par cycle documenté.
Broches, décalages, branchements, attente de niveau, délai, stop/reprise et
erreurs sont implémentés. Événements inter-contextes, échéances absolues et
échanges de données via files restent à développer. Aucune compatibilité
RP2040/RP2350 n'est revendiquée.

## Ordonnanceur

Le prototype utilise des créneaux fixes : un contexte par cycle, en alternance,
même lorsque l'autre attend ou est arrêté. Chaque contexte conserve ainsi un
créneau tous les deux cycles. Ce premier ordonnanceur simple n'est pas encore
l'ordonnanceur avancé envisagé. L'éventuelle redistribution de créneaux, les
priorités et les échéances devront conserver un contrat de timing explicite.

Conflits de broches : masques disjoints vérifiés par le matériel. Les états de
sortie persistent entre instructions, et au stop/HALT/faute/RESTART. Reset ou
désactivation libèrent les bidirectionnelles ; modifier la propriété pendant
l'arrêt efface aussi les anciennes sorties possédées. Les politiques d'échéance
et de file pleine/vide restent à définir lors de leur implémentation.

## Mémoire

Le prototype charge 16 instructions de 16 bits par contexte via SPI, soit
64 octets au total, dans une mémoire inférée en logique avec bits de validité.
Les petits tampons RX/TX n'existent pas encore ; le stockage volumineux sera dans
le LPC. La profondeur finale et une éventuelle macro SRAM autorisée restent à
arbitrer après mesure. Aucune quantité de RAM silicium n'est garantie.

Ne pas supposer qu'un tableau Verilog devient automatiquement une macro SRAM.
Les SRAM 256x8/512x8 du catalogue IHP principal ne figurent pas dans la version
`e16d00b7b26a93956563c373b782f54dd4d77a7f` actuellement référencée par le dépôt
IHP26b, vérifiée le 17 septembre 2026. Leur emploi demande confirmation du flow.
La macro 1024x8 présente dans cette version est grande pour notre budget.

Le rechargement du programme et la modification des propriétés sont interdits
tant qu'au moins un contexte s'exécute. Une future mémoire code/données partagée
devra inclure ses conflits d'accès et sa latence dans le modèle d'exécution.

## Interface et horloges

SPI mode 0, transactions 32 bits, entrées suréchantillonnées et synchronisées
sur `clk`, registres et interruption définis dans l'ISA v0. Limite provisoire
de protocole : SCK au plus `clk/10`, à valider électriquement et physiquement.
Le DMA sera celui du LPC, pas un accès direct de l'ASIC à sa RAM. Le pilote LPC
et les FIFOs nécessaires au streaming ne sont pas implémentés.

## Ordre de développement

1. Réalisé : première ISA, SPI, deux contextes, attentes et tests RTL.
2. Prochainement : première synthèse/mesure de surface sur la base actuelle.
3. Tampons hôte et inter-contextes, politiques de blocage/perte, tests de streaming.
4. Ordonnancement avancé et placement-routage IHP très tôt.
5. UART/SPI applicatifs, puis WS2812 émission, réception et modification.
6. Validation FPGA avec le LPC et préparation de la soumission.

## Sources

- [Template IHP](https://github.com/TinyTapeout/ttihp-verilog-template/tree/6598bef4d3159f19fe471a2a2225df52e6f5ad25)
- [Mémoires Tiny Tapeout](https://tinytapeout.com/specs/memory/)
- [Run IHP26b](https://github.com/TinyTapeout/tinytapeout-ihp-26b)
- [PDK référencé](https://github.com/TinyTapeout/IHP-Open-PDK/tree/e16d00b7b26a93956563c373b782f54dd4d77a7f)
