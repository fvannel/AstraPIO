# Documentation AstraPIO

Documentation de l’interface ABI 5 : ID `0x5049`, ABI `0x0500`, un PIO,
16 instructions de 10 bits et moteur temporel `0x5449` / `0x0118`.

## Intégrer et utiliser le circuit

| Document | Usage |
|---|---|
| [Démarrage rapide](getting-started.md) | Raccordement logique, identification et premier programme |
| [Manuel de référence](reference.md) | Broches, registres, SPI, instructions, temporisations et erreurs |
| [Datasheet PDF et Word](datasheet/README.md) | Référence téléchargeable pour le développeur et l’intégrateur |
| [Exemples PIO](../examples/README.md) | Émission UART et émission série de type SPI |
| [Note d’application WS2812](application-notes/AN-APIO-001-ws2812-live-patching.md) | Capture du premier mot, remplacement en direct et relais de la suite |

Le manuel et la datasheet décrivent la même interface. La note d’application
ajoute un câblage logique et une configuration pour un cas d’usage précis.

## Conditions d’utilisation

Les durées exprimées en nanosecondes supposent CLK à 50 MHz. Le circuit ne
déduit pas cette fréquence et ne reconfigure pas ses délais automatiquement.
L’alimentation, les niveaux électriques et le brochage du module livré doivent
être vérifiés sur la carte utilisée. Les caractéristiques électriques ne sont
pas encore garanties par une caractérisation sur silicium.

Les [preuves de validation](final-validation-abi5.md) sont un document
d’ingénierie distinct du manuel utilisateur.
