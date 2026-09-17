# Architecture de travail — PIO généraliste

## Périmètre convenu

Deux tiles IHP comme budget cible, un hôte ARM LPC55xxx, liaison SPI dédiée,
et deux contextes PIO partageant un moteur. Chaque contexte conserve sa position
dans le programme, son état de travail et ses conditions d'attente. Le nombre
de contextes et la surface restent des objectifs à vérifier.

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
contexte. Les indices logiques vus par les instructions restent à spécifier.
La référence LPC exacte et ses broches ne sont pas encore connues.

## Fonctions génériques à spécifier

- Lecture/écriture masquée des broches et contrôle de leur direction.
- Décalage de données, petits registres et branchements.
- Attente d'un niveau ou d'un événement, temporisation et échéances.
- Échange avec l'hôte et entre contextes, sans imposer un détour ARM.
- Arrêt, reprise, remise à zéro et indication des erreurs.

Ces familles ne constituent pas encore une ISA : pas d'encodage, de largeur de
registre ou de sémantique cycle par cycle figés. On ne revendique pas de
compatibilité RP2040/RP2350.

## Ordonnanceur

Commencer par comparer des créneaux fixes et des tâches en attente pouvant
libérer des créneaux. Une priorité dynamique seule ne garantit pas le timing.
Documenter une borne de latence pour lecture, sortie et reprise après événement.
Un contexte bloqué ne doit pas empêcher l'autre d'avancer. Deux instructions
ne s'exécutent pas au même cycle sur un moteur simple partagé.

Conflits de broches : imposer une propriété explicite ou des masques disjoints.
Les états de sortie persistent entre instructions. Définir le comportement en
cas de dépassement d'échéance ou de file pleine/vide.

## Mémoire

RAM de programme volatile chargée par SPI ; petits tampons RX/TX locaux ;
stockage volumineux dans le LPC. Profondeur et réalisation (bascules/latches/
macro SRAM autorisée) ouvertes.

Ne pas supposer qu'un tableau Verilog devient automatiquement une macro SRAM.
Les SRAM 256x8/512x8 du catalogue IHP principal ne figurent pas dans la version
`e16d00b7b26a93956563c373b782f54dd4d77a7f` actuellement référencée par le dépôt
IHP26b, vérifiée le 17 septembre 2026. Leur emploi demande confirmation du flow.
La macro 1024x8 présente dans cette version est grande pour notre budget.

Si code et données partagent un port mémoire, inclure les conflits d'accès et
la latence de lecture dans le modèle d'exécution. Le rechargement de programme
pendant l'exécution sera interdit ou fera l'objet d'un mécanisme atomique défini.

## Interface et horloges

Définir le mode SPI, le format des transactions, le registre d'état, les seuils
d'interruption et le débit garanti. Prévoir une stratégie de transfert entre
l'horloge SPI et l'horloge du moteur. Le DMA est celui du LPC, pas un accès direct
de l'ASIC à sa RAM. Aucun débit SPI n'est garanti à ce stade.

## Ordre de développement

1. ISA minimale, traces de référence et contrat de timing.
2. Chargement SPI, mémoire programme et exécution mono-contexte.
3. Deuxième contexte, ordonnancement, attentes et tampons.
4. Mesure de surface et placement-routage très tôt.
5. UART/SPI applicatifs, puis WS2812 émission, réception et modification.
6. Validation FPGA avec le LPC et préparation de la soumission.

## Sources

- [Template IHP](https://github.com/TinyTapeout/ttihp-verilog-template/tree/6598bef4d3159f19fe471a2a2225df52e6f5ad25)
- [Mémoires Tiny Tapeout](https://tinytapeout.com/specs/memory/)
- [Run IHP26b](https://github.com/TinyTapeout/tinytapeout-ihp-26b)
- [PDK référencé](https://github.com/TinyTapeout/IHP-Open-PDK/tree/e16d00b7b26a93956563c373b782f54dd4d77a7f)
