# AstraPIO

Coprocesseur programmable d’entrées/sorties numériques, à interface SPI.

AstraPIO exécute des séquences de broches sans intervention du microcontrôleur
à chaque transition. Il associe un **PIO programmable à cadence déterministe**
et un **moteur temporel autonome pour les flux à largeur d’impulsion**. Ces deux
blocs fonctionnent simultanément, sur des sorties distinctes.

Le microcontrôleur charge le programme, configure les broches et échange les
données par SPI. Une interruption signale les données disponibles et les erreurs.
Le pilote C est portable ; un LPC546xx est un exemple d’hôte compatible avec
ce modèle d’intégration, sous réserve du transport et des niveaux électriques.

## Caractéristiques

| Ressource | AstraPIO ABI 5 |
|---|---|
| Programme PIO | 16 instructions de 10 bits, mémoire volatile en latches |
| Calcul | Accumulateur 8 bits, compteur de boucle 4 bits |
| Cadence PIO | Une instruction tous les 4 cycles CLK, soit 80 ns à 50 MHz hors blocage |
| Échanges PIO | FIFO TX de 2 octets et FIFO RX de 2 octets |
| Entrées/sorties | 8 broches bidirectionnelles, 5 entrées et 6 sorties dédiées |
| Moteur temporel | Capture de 1 à 24 bits, remplacement atomique du préfixe et relais régénéré |
| Interface hôte | SPI mode 0, MSB en premier, transactions de 32 bits ; IRQ active à 1 |
| Identification | ID `0x5049`, ABI `0x0500`, capacité `0x1002` |
| Horloge de référence | CLK externe à 50 MHz ; temporisations configurées en cycles |

Les huit broches bidirectionnelles font partie à la fois des **13 sources
d’entrée** et des **14 destinations de sortie**. Ces nombres ne désignent pas
27 broches physiques distinctes.

## Documentation utilisateur

- [Datasheet et manuel de référence — PDF](docs/datasheet/AstraPIO_Datasheet_ABI5_Rev1.1_FR.pdf)
- [Manuel de référence en ligne](docs/reference.md) : brochage, SPI, registres, ISA, moteur temporel et erreurs.
- [Démarrage rapide](docs/getting-started.md) : identifier le circuit et exécuter un premier programme.
- [Pilotes C](firmware/) et [exemples PIO](examples/README.md).
- [AN APIO 001 — Patching en direct d’un flux WS2812](docs/application-notes/AN-APIO-001-ws2812-live-patching.md).

La [page documentation](docs/README.md) donne aussi accès aux versions Word
modifiables et aux documents d’intégration.

## Utilisation typique

Le PIO convient aux séquences de contrôle GPIO, à l’émission série et aux
échanges d’octets synchronisés avec des événements. Les exemples fournis
couvrent une émission UART 8N1 et une émission série de type SPI.

Le moteur temporel convient à la capture et à la régénération de flux dont les
bits sont codés par une largeur d’impulsion. Il peut remplacer le préfixe d’une
trame par une valeur préparée par l’hôte, sans interrompre la suite du flux.
Le patching WS2812 est détaillé dans la note d’application, pas requis pour
utiliser le PIO.

## Règles d’intégration essentielles

1. Fournir CLK, appliquer le reset et vérifier les registres d’identité.
2. Utiliser un SPI mode 0 avec au moins **six cycles CLK** pour chaque demi-période SCK et chaque délai CS de préparation, maintien et repos.
3. **MISO reste piloté lorsque CS est inactif.** Utiliser une entrée MISO dédiée ou une isolation externe pour un bus partagé.
4. Charger le programme PIO à l’arrêt et assembler explicitement avec `--abi 5`.
5. Affecter chaque sortie à un seul bloc ; dimensionner le service des FIFO de deux octets et des captures temporelles.

Le programme et la configuration doivent être rechargés après un reset global.
L’arrêt du PIO conserve ses niveaux de sortie ; il ne constitue pas une remise
à zéro électrique.

## Statut des caractéristiques

Documentation préliminaire de l’interface ABI 5. Le fonctionnement logique a
été vérifié en simulation ; les caractéristiques électriques et le fonctionnement
sur silicium et sur carte restent à qualifier. Les noms `ui_in`, `uo_out` et
`uio` désignent les ports logiques Tiny Tapeout, pas les numéros d’un boîtier.
Se référer à la carte IHP effectivement utilisée pour les alimentations,
les seuils, le brochage physique et les adaptations de niveau.

## Ressources du dépôt

`src/` contient le circuit ; `firmware/`, `tools/` et `examples/` les ressources
logicielles ; `test/` les régressions. Les éléments d’identification et de
validation physique sont regroupés dans [le dossier de validation](docs/final-validation-abi5.md)
et `release/`.

Projet sous [licence Apache-2.0](LICENSE), intégré au shuttle Tiny Tapeout IHP26b
sur un bloc 1 × 2 tiles. [Projet Tiny Tapeout](https://app.tinytapeout.com/projects/5799).
