# Première mise en service d’AstraPIO

Ce guide permet d’identifier AstraPIO ABI 5 et de piloter une première sortie.
Il utilise uniquement le PIO ; le moteur temporel reste désactivé.

## Raccorder le module

Utiliser la correspondance de broches de la carte Tiny Tapeout IHP reçue.
Les ports ci-dessous sont des noms logiques, pas des numéros de connecteur.
Relier les masses et vérifier alimentations, seuils et adaptations de niveau.

| Hôte ou instrument | Port AstraPIO |
|---|---|
| SPI SCK | `ui_in[0]` |
| SPI MOSI | `ui_in[1]` |
| SPI CS actif bas | `ui_in[2]` |
| Entrée SPI MISO dédiée | `uo_out[0]` |
| Entrée IRQ optionnelle | `uo_out[1]` |
| Analyseur logique ou oscilloscope | `uio[1]`, sans autre driver connecté |
| Horloge et reset du module | `clk` et `rst_n` via l’infrastructure de la carte |

MISO ne se libère pas quand CS est haut. Ne pas le raccorder directement
à d’autres sorties MISO push-pull.

## Réinitialiser et lire les identités

Sélectionner AstraPIO, fournir une horloge stable et garder CS haut et SCK bas.
Pour la séquence fonctionnelle de démarrage, maintenir le reset bas au moins
cinq cycles CLK, puis attendre au moins cinq cycles après sa libération.
Ces durées ne sont pas des limites électriques caractérisées.

Configurer le maître SPI en mode 0, MSB en premier, quatre octets par assertion
de CS. Choisir au départ une cadence basse, par exemple 1 MHz si CLK vaut
50 MHz. Chaque demi-période SCK et chaque délai CS setup/hold/gap doit durer
au moins six cycles CLK, soit 120 ns à cette fréquence d’ASIC.

| Registre | MOSI en hexadécimal | Deux derniers octets MISO attendus |
|---|---|---|
| ID `0x00` | `03 00 00 00` | `50 49` |
| ABI `0x01` | `03 01 00 00` | `05 00` |
| Contextes `0x02` | `03 02 00 00` | `00 01` |
| Capacité `0x0F` | `03 0F 00 00` | `10 02` |

Ne pas continuer si l’une de ces valeurs diffère. Pour une écriture, envoyer
`02 adresse donnée_haute donnée_basse`. Une réussite du contrôleur SPI hôte
ne prouve pas que le registre a accepté la valeur : utiliser les relectures.

## Charger un programme de quatre instructions

```text
LDI 2       # ACC = 0x02
DIR         # uio1 devient une sortie dans le masque attribué
SET 1,1     # uio1 passe à 1
HALT        # fin du programme, niveau de sortie conservé
```

Les mots ABI 5 correspondants sont `0x002`, `0x301`, `0x371`, `0x306`.
Pour assembler un fichier source, préciser toujours `--abi 5` :

```sh
python3 tools/pioasm.py --abi 5 docs/examples/first_output.pio
```

La notation W/R ci-dessous représente une transaction SPI complète.
Contrôler les erreurs de transport et borner toute attente par un timeout.

```text
W(03, 0000)            arrêter le PIO
W(04, 0001)            remettre son état et ses FIFO à zéro
W(06, 0001)            acquitter une éventuelle erreur hôte diagnostiquée
attendre R(0B) == 0
W(0A, 0000)            invalider le programme
W(40, 0002)
W(41, 0301)
W(42, 0371)
W(43, 0306)
```

Après chaque mot, attendre `PROGRAM_BUSY=0` et relire le mot écrit.
Vérifier ensuite `PROGRAM_LENGTH=4` et `PIO_ERROR=0`.
Écrire `OUTPUT_MASK` (`0x10`) à `0x0002`, puis `PC` (`0x11`) à zéro.
Relire ces deux valeurs, puis écrire `RUN` (`0x03`) à `1`.

## Résultat attendu

`uio[1]` est pilotée à 1. Après HALT, `RUN=0`, `PC=4`, `PIO_ERROR=0`,
`PIO_OUT=0x0002` et `PIO_OE=0x0002`. Le niveau haut reste présent.
Pour rejouer, remettre PC à zéro avant de relancer RUN ; RUN seul reprend
au PC courant, ici au-delà des quatre mots chargés.

Une remise à zéro globale libère les drivers bidirectionnels et invalide le
programme. Ne pas confondre cet effet avec l’arrêt du PIO, qui garde ses
sorties. Le registre de masque est une attribution de broches, pas un
registre d’écriture directe de leurs niveaux.

## Passer aux échanges de données

Les [exemples UART et SPI](../examples/README.md) utilisent la FIFO TX.
`PULL` attend si elle est vide ; `PUSH` attend si RX est pleine. Chaque FIFO
contient deux octets : prévoir un service hôte compatible avec le débit réel.
Le [manuel de référence](reference.md) détaille registres, interruptions,
instructions et moteur temporel.
