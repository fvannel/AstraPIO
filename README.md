# AstraPIO

Coprocesseur programmable d’entrées/sorties numériques, piloté par SPI.
AstraPIO associe un PIO pour les séquences GPIO et un moteur temporel
indépendant pour capturer, remplacer et régénérer des flux à impulsions.
Le microcontrôleur configure le circuit et échange les données ; l’ASIC
prend en charge les transitions sur les broches.

## Caractéristiques

- Un PIO, 16 instructions de 10 bits, accumulateur 8 bits et compteur 4 bits.
- Un créneau d’instruction toutes les 4 périodes CLK ; FIFO TX et RX de 2 octets chacune.
- 8 broches bidirectionnelles, 5 entrées et 6 sorties applicatives dédiées.
- Moteur temporel : capture d’un préfixe de 1 à 24 bits, remplacement atomique et relais régénéré de la suite.
- Interface hôte SPI mode 0 et interruption ; pilote C portable, interface ABI 5.

Les deux blocs peuvent fonctionner simultanément sur des sorties distinctes.
Programme et configuration sont volatiles et doivent être chargés après reset.

## Documentation

- [Démarrage rapide](docs/getting-started.md) : raccordement et premier programme.
- [Manuel de référence](docs/reference.md) : broches, SPI, registres et instructions.
- [Datasheet PDF et Word](docs/datasheet/README.md).
- [Exemples PIO](examples/README.md) : émission UART et série de type SPI.
- [Note d’application WS2812](docs/application-notes/AN-APIO-001-ws2812-live-patching.md) : remplacement du premier mot d’un flux en direct.

## Intégration et développement

Vérifier les niveaux électriques de la carte et les temporisations SPI avant
le raccordement. MISO reste piloté lorsque CS est inactif : prévoir une entrée
dédiée ou un isolement externe. Les caractéristiques électriques restent
préliminaires, sans qualification sur silicium.

Le dépôt fournit le [RTL](src/), le [pilote C](firmware/), l’[assembleur](tools/pioasm.py)
et les [tests](test/README.md). `make check` contrôle l’intégrité de la version
et les outils ; le guide de test décrit les simulations.

Projet [Tiny Tapeout IHP26b, 1 × 2 tiles](https://app.tinytapeout.com/projects/5799).
Licence [Apache 2.0](LICENSE).
