# HISTORIQUE — ISA v0, remplacée par [isa-v2.md](isa-v2.md)

> **Document historique — pas la référence ABI 5.** Cette page est conservée
> pour retracer les premières versions du projet. Pour le circuit accepté
> (commit `1b1c9118`, PR149), consulter la [documentation finale](../../../README.md)
> et la [datasheet ABI 5](../../datasheet/README.md). Les anciennes instructions de
> soumission et exceptions SRAM ne s’appliquent pas à la version finale.

Contrat de l'ancien prototype, **ne pas utiliser pour le RTL actuel**.
Les FIFOs, le streaming, les événements entre contextes et les échéances absolues
ne sont pas encore implémentés. Cette version ne valide pas l'application WS2812.

## Ressources et temps

Deux contextes, chacun avec un PC de 4 bits, un accumulateur `A` de 16 bits,
un compteur d'attente de 12 bits et 16 instructions de 16 bits. La mémoire totale
vaut **64 octets** ; c'est un tableau de logique inférée, **pas une macro SRAM**.
Ses 32 bits de validité sont effacés au reset ; aucun programme n'est exécutable
avant chargement. Un mot non chargé se lit comme zéro mais provoque une faute
s'il est exécuté. Le contenu des cellules mémoire n'est pas remis à zéro.

Un créneau par contexte tous les **deux cycles `clk`**, y compris si l'autre est
arrêté ou attend. Pas de redistribution de créneaux ni priorité dynamique dans
ce prototype. Toutes les instructions prennent un créneau, sauf `WAIT` et
`DELAY` qui retiennent ou suspendent leur propre contexte. Le PC reboucle de 15
à 0. Aucun effet de bord d'instruction n'est répété pendant un délai.

À 50 MHz *si cette fréquence est validée physiquement*, un créneau vaut 40 ns.
Un changement d'entrée traverse deux bascules de synchronisation puis attend le
créneau d'exécution : la simulation ne modélise ni métastabilité ni délai de pad.
Une entrée doit rester assez longtemps stable pour être échantillonnée ; ce
cœur n'est pas un compteur d'impulsions asynchrones arbitrairement courtes.

## Broches logiques

| Usage | Indices | Broches physiques |
| --- | --- | --- |
| Lecture `IN` et `WAIT` | 0..7 | uio[0..7] |
| Lecture `IN` et `WAIT` | 8..12 | ui[3..7] |
| Écriture `OUT`, masque de propriété | 0..7 | uio[0..7] |
| Écriture `OUT`, masque de propriété | 8..13 | uo[2..7] |
| Direction `DIR` | 0..7 | uio_oe[0..7], 1 = sortie |

Les indices d'entrée et de sortie sont deux espaces distincts. `IN` échantillonne
le pad d'entrée, pas un rebouclage interne de la valeur de sortie.
Les masques de propriété des contextes doivent être disjoints. Le matériel
rejette un chevauchement. `OUT` et `DIR` n'affectent que les broches possédées.
Les sorties fixes ne peuvent pas devenir haute impédance.

## Instructions

Opcode = bits 15..12. Bits non mentionnés ignorés par le RTL et mis à zéro par
l'assembleur. Les immédiats ne sont pas signés ; l'arithmétique reboucle sur 16 bits.

| Opcode | Syntaxe | Effet |
| --- | --- | --- |
| 0 | `NOP` | Avance le PC |
| 1 | `LDI n` | A = immédiat 12 bits, extension par zéro |
| 2 | `IN` | A = les 13 entrées synchronisées, extension par zéro |
| 3 | `OUT` | A[13:0] vers les sorties possédées |
| 4 | `DIR` | A[7:0] vers les directions possédées |
| 5 | `JMP cible` | PC = bits 3..0 |
| 6 | `JNZ cible` | Saut si A ≠ 0, sinon avance |
| 7 | `DEC` | A = A − 1 modulo 65536 |
| 8 | `WAIT pin, niveau` | Attend égalité ; pin bits 3..0, niveau bit 8 |
| 9 | `DELAY n` | Avance le PC puis saute n créneaux propres supplémentaires |
| A | `XOR n` | A XOR immédiat 12 bits, extension par zéro |
| B | `SHL` | Décale A à gauche d'un bit, zéro inséré |
| C | `SHR` | Décale A à droite d'un bit, zéro inséré |
| D | `IRQ` | Positionne le drapeau d'interruption du contexte et avance |
| E | `HALT` | Avance puis arrête le contexte, état conservé |
| F | réservé | Faute et arrêt du contexte |

Un indice `WAIT` supérieur à 12 est une faute. Faute et `HALT` **ne libèrent pas
les sorties** ; le niveau et la direction restent conservés. Les immédiats LDI
n'atteignent pas directement les bits 12..15 : utiliser des décalages ou charger
A par SPI pendant l'arrêt pour les valeurs plus grandes.

Exemple : `OUT; DELAY 3; LDI 0; OUT` produit une distance de six créneaux entre
les deux écritures, soit 12 cycles `clk`. `DELAY 0` occupe seulement son propre
créneau. L'assembleur accepte les labels, les entiers décimaux/hexadécimaux et
les commentaires `#` ; la profondeur maximale est vérifiée.

## SPI hôte

SPI **mode 0**, MSB d'abord, un seul paquet de quatre octets par assertion CS :
`[commande][adresse][donnée haute][donnée basse]`.

- `0x02` : écriture, validée une seule fois après réception du 32e bit.
- `0x03` : lecture, réponse 16 bits dans les deux derniers octets ; les deux
  premiers octets reçus valent zéro. MOSI de ces deux derniers octets est ignoré.
- Commande inconnue : ignorée ; adresse inconnue en lecture : zéro.
- CS relevé avant 32 bits : aucune écriture. Les horloges au-delà de 32 bits sont
  ignorées jusqu'au prochain CS haut. Il n'existe ni burst ni CRC ni acquittement
  dans cette version. Consulter `ERRORS` et relire les programmes après chargement.

SCK, MOSI et CS sont synchronisés sur `clk`. **Contrat de simulation provisoire** :
SCK haut et bas pendant au moins 5 périodes `clk`, CS setup/hold et temps haut
inter-paquets au moins 5 périodes `clk`. MOSI change sur front descendant et
reste stable jusqu'après le front montant suivant. Limite de protocole :
`f_SPI ≤ f_clk/10`, donc 5 MHz avec une horloge 50 MHz supposée valide.
Il ne s'agit pas d'une garantie électrique après fabrication. La lecture prend
un instantané du registre au front descendant synchronisé suivant le 16e bit.

MISO sur uo[0] est **toujours une sortie pilotée**, à zéro hors transaction : bus
SPI dédié obligatoire, sauf ajout d'un buffer externe ou changement de brochage.
IRQ sur uo[1] est un niveau actif haut = drapeaux IRQ OU fautes OU erreur hôte.

## Registres 16 bits

| Adresse | Nom | Lecture / écriture |
| --- | --- | --- |
| 00 | ID | R : 0x5049 |
| 01 | VERSION | R : 0x0001 |
| 02 | STATUS | R : bit 0 contexte 0 actif, bit 1 contexte 1 actif |
| 03 | RUN | R/W : mêmes bits ; écriture remplace le masque d'activation |
| 04 | RESTART | W : bits 0/1 remettent le contexte choisi à zéro et l'arrêtent |
| 05 | IRQ_PENDING | R/W1C : bits 0/1 des interruptions logicielles |
| 06 | ERRORS | R : bit 0 erreur hôte, bits 8/9 fautes contextes ; W1C bit 0 |
| 07 | OUTPUTS | R : 14 niveaux de sortie |
| 08 | DIRECTIONS | R : 8 directions bidirectionnelles |
| 09 | INPUTS | R : 13 entrées synchronisées |
| 10 / 20 | OWNERSHIP 0 / 1 | R/W : masque de sortie de 14 bits |
| 11 / 21 | PC 0 / 1 | R/W : PC de 4 bits |
| 12 / 22 | A 0 / 1 | R/W : accumulateur de 16 bits |
| 13 / 23 | DELAY_REMAINING 0 / 1 | R : compteur de créneaux, 12 bits |
| 40..4F | PROGRAM 0 | R/W : 16 mots d'instruction |
| 50..5F | PROGRAM 1 | R/W : 16 mots d'instruction |

Toutes les adresses du tableau sont hexadécimales. W1C : écrire un 1 efface le
drapeau correspondant ; écrire 0 le laisse inchangé. Une nouvelle instruction
IRQ dans le même cycle que son acquittement est prioritaire : elle reste pendante.

Règles de contrôle :

- Programme et propriété modifiables uniquement quand **les deux contextes sont
  arrêtés**. PC/A modifiables uniquement si leur contexte est arrêté.
- Écriture interdite/inconnue : ignorée, avec erreur hôte persistante et IRQ.
  Champs plus étroits : seuls les bits documentés sont utilisés.
- RUN n'efface pas PC/A/délai/IRQ ; pause/reprise conservant l'état. Un contexte
  en faute ne redémarre pas tant qu'un RESTART ne l'a pas réinitialisé.
- RESTART remet PC, A, délai, faute et IRQ du contexte à zéro, sans effacer
  programme, propriété, valeurs de sortie ou directions.
- Modifier OWNERSHIP efface les niveaux et directions de **toutes les anciennes
  broches possédées** par ce contexte. Affecter zéro libère ses bidirectionnelles.
- Un RUN supprime l'exécution du créneau courant de ce cycle ; un RESTART la
  supprime seulement si le contexte du créneau est visé. Les autres transactions
  SPI ne volent aucun créneau. Le lancement n'a pas de phase externe garantie.
- Reset ou `ena=0` masque immédiatement toutes les sorties, puis réinitialise
  l'état sur `clk` : maintenir au moins deux cycles pour un redémarrage propre.
  La mémoire est invalidée, les masques sont nuls et toutes les GPIO sont entrées.

## Séquence de démarrage

1. Appliquer reset avec horloge active, puis placer CS haut.
2. Lire ID/VERSION ; écrire RUN=0 puis RESTART=3.
3. Charger et relire les mots de chaque programme. Recharger un programme plus
   court ne supprime pas automatiquement ses anciens mots restants : remplacer
   les cases inutilisées par HALT ou assurer qu'elles sont inaccessibles.
4. Affecter deux masques disjoints ; effacer ERRORS bit 0 et IRQ_PENDING bits 0/1.
5. Vérifier ERRORS=0 ; écrire RUN=1, 2 ou 3.

`tools/host_protocol.py` forme les paquets ; il n'est **pas** un pilote LPC/DMA.
`tools/pioasm.py examples/blink.pio` assemble un exemple. Aucun de ces exemples
ne prouve encore la capacité de capturer ou retransmettre un flux WS2812.
