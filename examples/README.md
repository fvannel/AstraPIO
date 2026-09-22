# Exemples AstraPIO ABI 5

Deux petits programmes sources compatibles avec la version finale :

- `compact/uart_tx.pio` : émission UART, 14 instructions.
- `compact/spi_tx.pio` : émission série SPI, 9 instructions.

Le nom de sous-dossier `compact/` est conservé pour garder le test UART
officiel inchangé. Il contient uniquement ces deux sources compatibles ABI 5,
pas les anciennes variantes du circuit.

Toujours assembler avec `python3 tools/pioasm.py --abi 5 ...` depuis la racine
(consulter `--help` pour les options de sortie). Les anciens binaires ABI 3/4
ne sont pas compatibles. Régler masque, directions et cadence avant exécution.
Ces exemples ne prétendent pas implémenter des contrôleurs UART/SPI complets.

Le cas WS2812 utilise le moteur temporel configurable en parallèle du PIO :
voir `test/ws2812/README.md`, `test/test_ws2812_counter.py` et le pilote
`firmware/pio_timed.c`. Aucun ancien programme double-contexte n'est actif.
