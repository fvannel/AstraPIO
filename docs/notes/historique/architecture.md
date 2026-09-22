# Architecture v2 — 18 septembre 2026

> **Document historique — pas la référence ABI 5.** Cette page est conservée
> pour retracer les premières versions du projet. Pour le circuit accepté
> (commit `1b1c9118`, PR149), consulter la [documentation finale](../../../README.md)
> et la [datasheet ABI 5](../../datasheet/README.md). Les anciennes instructions de
> soumission et exceptions SRAM ne s’appliquent pas à la version finale.

## Choix fondés sur la surface mesurée

La première version à code en bascules dépassait les deux tiles. Une SRAM 256×16
laissait trop peu de place pour la logique. La version actuelle partage une
SRAM 256×8 entre **192 octets de code** et **64 octets de files**. Les banques
de sorties fixes et le datapath 8 bits réduisent le coût de la configuration.
Les capacités ci-dessous décrivent le RTL actuel, pas la première ISA v0.

## Brochage

| Fonction | Broches Tiny Tapeout | Indices vus par les programmes |
|---|---|---|
| SPI SCK / MOSI / CS_N | ui[0:2] | réservées à l'hôte |
| SPI MISO / IRQ | uo[0:1] | réservées à l'hôte |
| 5 entrées fixes | ui[3:7] | entrées 8…12 |
| 6 sorties fixes | uo[2:7] | sorties globales 8…13 |
| 8 bidirectionnelles | uio[0:7] | entrées et sorties globales 0…7 |

Horloge, reset et sélection `ena` sont dédiés. Il y a 19 signaux applicatifs,
pas 19 par contexte. Contexte 0 : sorties locales 0…6 → globales 0…6.
Contexte 1 : locales 0…6 → globales 7…13. Chaque banque possède un masque
d'activation de 7 bits, initialement nul. Les deux contextes lisent les 13 entrées.
Le MISO est une sortie permanente à zéro hors CS : **bus SPI dédié**, sans partage
avec un autre esclave MISO non isolé.

## Ordonnanceur et mémoire

Chaque tour de six clocks est fixe : fetch bas C0, fetch haut C0, exécution C0,
fetch bas C1, fetch haut C1, exécution C1. Les clocks d'exécution sont aussi les
créneaux du port mémoire de données. Une attente ne redistribue jamais le créneau
de l'autre contexte. À l'objectif de 50 MHz : 120 ns par créneau/contexte.

Le port de données arbitre dans l'ordre : prélecture RX de l'hôte, écriture TX
de l'hôte, opération du contexte actif. Une instruction PULL/PUSH/RECV peut
réessayer au tour suivant ; les instructions ordinaires gardent leur cadence.
Les accès programme exigent l'arrêt des deux contextes ; pas d'auto-modification.
La mémoire est volatile et non effacée au reset : longueurs valides et pointeurs
empêchent d'exécuter/lire le contenu non initialisé.

| Octets physiques SRAM | Usage |
|---|---|
| 00…5F | 48 mots de code contexte 0, little-endian dans SRAM |
| 60…6F / 70…7F | TX0 / RX0, 16 octets chacun |
| 80…DF | 48 mots de code contexte 1 |
| E0…EF / F0…FF | TX1 / RX1, 16 octets chacun |

PULL consomme TX propre ; PUSH produit RX propre ; RECV consomme RX du pair.
Le PC reste bloqué sur FIFO vide/pleine, sans perte. Une écriture hôte dans une
TX pleine est rejetée avec erreur persistante. La lecture RX est un instantané
réservé pendant la trame SPI ; seule une lecture complète et valide le consomme.
Une arrivée après un instantané vide reste disponible pour la trame suivante.

## Événements, reset et sûreté

SIGNAL positionne un bit chez le pair ; AWAIT attend puis consomme son bit.
Ces événements sont des drapeaux coalescents, pas des compteurs : deux SIGNAL
avant AWAIT ne comptent que pour un. L'hôte peut les positionner/acquitter.
IRQ combine événements logiciels, fautes, erreur hôte et RX non vide masquée.

Stop, HALT et faute conservent les sorties et directions. RESTART arrête le
contexte, réinitialise PC/A/X/délai/événement/faute/IRQ et vide ses files, mais
conserve son code, masque, sorties et directions. Reset ou `ena=0` libère
immédiatement les bidirectionnelles et invalide les deux programmes.
Assertion de reset asynchrone, relâchement synchronisé par deux bascules communes.
Les entrées applicatives et SPI traversent deux bascules de synchronisation.
Cela réduit le risque métastable mais ne constitue pas un calcul de MTBF.

Les limites importantes restent explicites : pas de capture d'impulsion plus
courte que la cadence de WAIT, pas de files infinies, pas de gigue nulle pour
une entrée asynchrone, pas de priorité dynamique ni de détection automatique
des trames d'un protocole particulier. Voir [ISA](isa-v2.md) et [tests](verification.md).
