# ISA et ABI v2 — contrat courant

> **Document historique — pas la référence ABI 5.** Cette page est conservée
> pour retracer les premières versions du projet. Pour le circuit accepté
> (commit `1b1c9118`, PR149), consulter la [documentation finale](../../../README.md)
> et la [datasheet ABI 5](../../datasheet/README.md). Les anciennes instructions de
> soumission et exceptions SRAM ne s’appliquent pas à la version finale.

Identifiant `0x5049`, version `0x0200`. Incompatible avec v0 et RP2040 PIO.
Deux contextes, A=8 bits, X=4 bits, PC=6 bits, code limité à 48 mots de 16 bits.
Chaque contexte exécute une instruction tous les six clocks. DELAY N insère N
créneaux supplémentaires ; DELAY 0 coûte donc un créneau, comme NOP.

## SPI hôte

Mode 0, MSB d'abord : `[commande 8][adresse 8][donnée 16]`. `02` écrit, `03` lit.
Un seul paquet par activation CS. Une lecture retourne zéro pendant l'en-tête,
puis la donnée instantanée. CS doit repasser haut pour une autre transaction.
Trames incomplètes/commandes inconnues : aucun effet. Les clocks après la 32e
sont ignorés. Les commandes valides sur registres d'écriture inconnus signalent
`host_error`. Une lecture d'adresse inconnue retourne zéro.

SCK haut et bas ≥6 clocks ; CS setup, hold et intervalle haut ≥6 clocks.
Objectif à 50 MHz : SCK ≤4,167 MHz. MISO n'est **pas** haute impédance hors CS.
Le transport LPC doit respecter les durées minimales, pas seulement une fréquence
moyenne. Les interruptions/DMA doivent sérialiser les transactions par périphérique.

## Registres globaux

| Adresse | Lecture | Écriture |
|---|---|---|
| 00 | ID 5049 | erreur |
| 01 | version 0200 | erreur |
| 02 | RUN bits 1:0 | erreur |
| 03 | RUN | remplace RUN, ne relance pas un contexte en faute |
| 04 | 0 | RESTART des contextes dont le bit vaut 1 |
| 05 | IRQ logicielles bits 1:0 | W1C |
| 06 | fautes en 9:8, erreur hôte en 0 | bit0=1 efface seulement erreur hôte |
| 07 | niveaux des 14 sorties applicatives | erreur |
| 08 | directions des 8 uio | erreur |
| 09 | 13 entrées synchronisées | erreur |
| 0A | pointeur programme logique | pointeur 8 bits |
| 0B | mot programme, ou 0 si actif/invalide | mot programme |
| 0C | masque IRQ RX non vide bits 1:0 | remplace masque |
| 0D | événements bits 1:0 | W1S |
| 0E | mêmes événements | W1C |

W1C efface les bits écrits à 1 ; W1S les positionne. Un événement/IRQ produit
par l'instruction du même clock prend priorité sur une écriture hôte du même bit.
Le RUN remplace le masque, il ne s'ajoute pas aux contextes actifs.

## Registres d'un contexte

Base `10` pour C0, `20` pour C1. Tous les nombres d'adresses sont hexadécimaux.

| Offset | Lecture | Écriture |
|---|---|---|
| 0 | masque de sorties, indices **globaux** | C0 bits6:0, C1 bits13:7 ; les deux arrêtés |
| 1 | PC | bas 6 bits, contexte arrêté |
| 2 | A | bas 8 bits, contexte arrêté |
| 3 | délai restant | erreur |
| 4 | 0 | ajoute bas 8 bits dans TX ; pleine → erreur sans écriture |
| 5 | bit15=valide, bits7:0=octet RX | erreur |
| 6 | niveau RX bits12:8, niveau TX bits4:0 (0…16) | erreur |
| 7 | X | bas 4 bits, contexte arrêté |
| F | longueur programme 0…48 | zéro seulement, les deux arrêtés : invalide code et PC=0 |

L'instantané RX est réservé dès l'en-tête. Le transfert complet de 32 clocks
consomme un octet **seulement si l'instantané était valide**. Abandon CS ne
consomme rien. Un autre contexte ne peut pas RECV cet octet pendant la lecture.
Une PUSH simultanée à une consommation peut utiliser immédiatement la place libérée.

## Chargement programme

Les deux contextes doivent être arrêtés. Effacer la longueur avec 1F/2F=0,
puis écrire séquentiellement : C0 pointeurs logiques 0…47, C1 64…111, via 0A/0B.
0A n'est pas auto-incrémenté. Trous, offsets ≥48 et bit7 du pointeur sont refusés.
Les alias 40…4F et 50…5F adressent les seize premiers mots de C0/C1.
Un mot existant peut être réécrit. La fenêtre ne permet pas d'écraser les files.
Lire le code n'est possible que les deux contextes arrêtés ; sinon retour zéro.
Reset invalide toutes les longueurs, RESTART les conserve.

## Instructions

| Encodage canonique | Assembleur | Effet |
|---|---|---|
| 0000 | NOP | aucun |
| 10nn | LDI n | A=n, n=0…255 |
| 2000 / 2100 | IN / IN 1 | A=uio[7:0] / entrées fixes[4:0] |
| 3000 | OUT | A[6:0] vers banque locale masquée |
| 4000 | DIR | A[6:0] pour uio0…6 en C0 ; A[0] pour uio7 en C1 |
| 50pp / 60pp | JMP p / JNZ p | PC=p inconditionnel / si A≠0 |
| 7000 | DEC | A=A−1 modulo256 |
| 80pi / 81pi | WAIT i,0 / WAIT i,1 | i=0…12 dans bits3:0 ; attend niveau |
| 90nn | DELAY n | ajoute n créneaux d'attente |
| A0nn | XOR n | A=A xor n |
| B000 / C000 | SHL / SHR | décalage logique A d'un bit |
| D000 / E000 | IRQ / HALT | positionne IRQ propre / arrête contexte |
| F000 / F100 | PULL / PUSH | TX propre→A / A→RX propre, bloquant |
| F2p0 / F2p1 | SET p,0 / SET p,1 | sortie **locale** p=0…6 |
| F3p0 | OUTBIT p | sort A[7], puis A=A<<1, p=0…6 |
| F40i | INBIT i | A=(A<<1) + entrée globale i=0…12 |
| F50n | LDX n | X=n=0…15 |
| F6pp | DJNZ p | X=X−1 modulo16 ; branche si ancien X≠1 |
| F700 / F710 / F720 | SIGNAL / AWAIT / CLR_EVENT | événement du pair / attend-consomme propre / efface propre |
| F8pp | JBIT p | branche si A[7]=1 |
| F900 | RECV | RX du pair→A, bloquant ; hôte prioritaire |

WAIT s'encode exactement `8000 | (niveau<<8) | index`. Les p/pp de saut sont des
adresses 0…47 pour l'assembleur. X initial à zéro donne 16 itérations avec DJNZ.
Les opcodes 0…E ignorent les bits non utilisés ; écrire la forme canonique.
L'extension F rejette les encodages non listés. WAIT/INBIT hors plage, pin locale7
et PC hors longueur provoquent faute+arrêt. Un saut à 48…63 faute au prochain
créneau. Aucun fetch non initialisé ne devient une instruction exécutable.

OUT/SET ne touchent que les sorties autorisées. OUTBIT sur pin valide non possédée
décale quand même A. Les masques sont strictement limités à la banque du contexte.
En changeant un masque à l'arrêt, les **anciens** niveaux/directions de la banque
possédée sont effacés. Stop/HALT/faute/RESTART conservent sinon ces états.

## Priorités particulières

Une écriture RUN suspend l'instruction de ce clock ; RESTART suspend celle du
contexte visé. RESTART annule ses retours de file et vide ses quatre pointeurs.
Un événement est coalescent, pas compté. AWAIT qui consomme un bit l'emporte sur
un W1S simultané du même bit. Les applications ne doivent pas présumer un comptage
de deux événements simultanés. Une faute nécessite RESTART avant RUN.
