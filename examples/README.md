# Exemples AstraPIO ABI 5

| Programme | Ressources | Fonction et limites |
|---|---|---|
| [UART TX](compact/uart_tx.pio) | 14 instructions, uio0, masque `0x0001` | Émission 8N1, 115 740,7 bauds calculés à CLK 50 MHz ; pas de récepteur ni de contrôle de flux |
| [Émission série SPI](compact/spi_tx.pio) | 9 instructions, uio0 MOSI et uio1 SCK, masque `0x0003` | MSB en premier ; 3,125 Mbit/s à l’intérieur de l’octet, rapport cyclique 25 % ; CS et MISO non gérés |

Depuis la racine du dépôt :

```sh
python3 tools/pioasm.py --abi 5 examples/compact/uart_tx.pio
python3 tools/pioasm.py --abi 5 examples/compact/spi_tx.pio
```

Les deux programmes consomment les octets de la FIFO TX. `PULL` attend lorsque
celle-ci est vide ; des pauses entre octets sont donc possibles. Les débits
dans le tableau supposent CLK à 50 MHz et ne représentent pas un débit
soutenu garanti par le transport SPI hôte.

Charger le programme à l’arrêt, configurer son masque de sorties, positionner
PC à zéro, puis lancer le PIO. Voir le [démarrage rapide](../docs/getting-started.md)
et la [référence des instructions](../docs/reference.md).

Le [patching WS2812](../docs/application-notes/AN-APIO-001-ws2812-live-patching.md)
utilise le moteur temporel ; il ne consomme pas de mots de programme PIO.
