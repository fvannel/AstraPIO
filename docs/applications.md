# Applications et intégration LPC546xx

## Programmes validés numériquement

Les durées suivantes supposent `clk=50 MHz`. Les programmes se rechargent via SPI ;
aucun décodeur UART, SPI ou WS2812 dédié n'est présent dans le silicium.

| Exemple / banc | Ressources | Mesure attendue et vérifiée aux broches |
|---|---|---|
| `blink.pio` | C1, masque0100 | sortie fixe PIO_OUT0, temporisation programmable |
| `wait_input.pio` | C0, masque0001 | attend entrée globale8, active uio0, IRQ, arrêt |
| `spi_tx.pio` | C0, masque0003 | MOSI=uio0, SCK=uio1, MSB-first mode0, 6 octets vérifiés |
| SPI émission→réception | C0→broches→C1, `spi_rx.pio` | 16 octets transmis et capturés via rebouclage externe simulé |
| `uart_tx.pio` | C0, masque0001 | uio0, UART 8N1, bits8,64µs (~115741bauds), 3 octets décodés |
| `ws2812_tx.pio` | C1, masque0100 | hauts360/720ns, périodes1200/1320ns, 6 octets et pause>300 µs |
| capture→transformation | C0→C1→RX1 | capture sur entrée8, XOR5A, 12 octets lus par hôte |
| relais modifié | C0→C1→PIO_OUT0 | 48 octets, 384 impulsions décodées/modifiées/réémises |

Les deux derniers programmes sont construits explicitement dans
`test/test_applications.py`. Le récepteur utilise WAIT/DELAY/INBIT (34 mots),
le relais remplace PULL par RECV puis XOR dans l'émetteur. Cette démonstration
prouve la programmabilité, **pas la compatibilité avec toutes les LED WS2812**.
Elle suppose des octets complets, alignés, à 800 kbit/s et des hauts350/700ns.
Pas de resynchronisation automatique après une demi-trame, pas de validation
électrique, ni de tests couvrant toutes les tolérances des multiples révisions.
Il faut vérifier le datasheet de la LED exacte, le niveau électrique et tester
au banc avant de raccorder une chaîne réelle.

Un relais ajoute au moins un octet de latence. Le programme XOR est une modification
fixe ; le remplacement sélectif à la demande du LPC nécessite un programme et un
protocole de commande supplémentaires. Ce n'est pas encore un produit
d'interception complet avec gestion des erreurs et des limites de trame.

## Débit et dimensionnement

Chaque moteur a 8,333 millions de créneaux/s à 50 MHz. Les transferts FIFO peuvent
attendre le créneau SRAM ; les files n'absorbent que16 octets chacune. Les 48 mots
par moteur suffisent aux exemples, pas nécessairement à tout protocole complexe.

L'hôte transfère quatre octets SPI pour un octet utile de flux. À SCK=clk/12,
avec les marges CS minimales, compter environ 8 µs par paquet à 50 MHz, soit environ
124 ko/s unidirectionnels avant lectures de statut et overhead logiciel.
Émettre un flux800 kbit/s demande100 ko/s : marge limitée, à mesurer avec le LPC.
Lire et écrire continuellement100 ko/s chacun via ce même SPI **ne tient pas**.
Le relais direct entre contextes évite cet aller-retour ARM.

`pio_push()` relit le crédit à chaque octet : pratique mais trop lent pour un
streaming LED continu. `pio_push_many()` amortit une lecture de niveau sur jusqu'à
16 écritures, en respectant les crédits. Précharger la file, puis la réalimenter
avec DMA/interruptions bornées. Les horloges doivent rester actives durant CS.
Ne pas dépasser les crédits ni retenter aveuglément une lecture RX après erreur
transport : un octet pourrait déjà avoir été consommé.

## Bibliothèque C et carte ARM

`firmware/pio_host.c/.h` est portable C11, testée sur l'hôte avec contrôle mémoire
et comportement indéfini, et compilée en objet ARM Cortex-M4 freestanding.
Elle fournit probe/stop/chargement vérifié/masques/run,
push/pop et push en lot. L'adaptateur SPI matériel est volontairement un callback.
Ce n'est **pas** un firmware LPC complet lié à un SDK ou testé sur carte.

Avant portage MCUXpresso : référence complète LPC546xx, carte, brochage libre,
instance SPI, source d'horloge ASIC, tension IO et accès DMA doivent être connus.
Configurer mode0, MSB-first, 32 clocks par CS, bas/haut/setup/hold/gap≥6clocks ASIC,
et attendre la fin réelle sur le fil avant de relever CS. IRQ peut être une entrée
interruptible LPC. `pio_load()` arrête les **deux** moteurs ; il ne faut pas
l'appeler pendant une émission devant rester continue.

Le LPC possède son propre SPI/DMA ; le maximum du contrôleur LPC ne définit pas
celui de notre esclave suréchantillonné. Références officielles :
[famille LPC546xx](https://www.nxp.com/products/LPC546XX),
[datasheet](https://www.nxp.com/docs/en/data-sheet/LPC546XX.pdf).

Pas de liaison directe supposée à 5 V. Un changement de direction uio doit éviter
la contention avec l'émetteur externe. Reset ou ena=0 force les sorties à0 et
uio en entrée ; HALT/stop/faute ne libère pas spontanément les lignes.
