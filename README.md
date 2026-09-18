# AstraPIO — coprocesseur numérique programmable

## État : RTL v2 testé, fabrication bloquée

Deux contextes PIO, un hôte **LPC546xx**, une SRAM de **256 octets** et une cible
**TTIHP26b, deux tiles 1×2**. Le placement/routage a produit un GDS dans cette
surface. **Ne pas valider pour fabrication** : la SRAM officielle échoue au DRC du run, des
hypothèses de timing restent à qualifier et le statut détaillé fait autorité.
Voir [vérification](docs/verification.md) et [blocage SRAM](docs/sram-drc-blocker.md).

Le projet reste un PIO généraliste : UART, SPI et WS2812 sont des programmes,
pas des circuits spécialisés. Il n'est pas compatible avec l'ISA RP2040.

## Capacité implémentée

- Deux contextes à créneaux fixes, chacun une instruction tous les six clocks.
- 48 instructions de 16 bits par contexte, accumulateur 8 bits, compteur 4 bits.
- Quatre files SRAM de 16 octets : TX et RX pour chacun des deux contextes.
- Attentes de niveau, délais relatifs, événements, IRQ et transfert direct entre contextes.
- SPI hôte dédié, mode 0, paquets de quatre octets ; SPI applicatif par programme.
- 8 broches bidirectionnelles, 5 entrées fixes et 6 sorties fixes applicatives.
- Deux banques de 7 sorties protégées ; les 13 entrées sont accessibles aux deux contextes.
- Assembleur, programmes démonstrateurs et bibliothèque C portable pour le transport LPC.

La répartition mémoire utilise les 256 octets : 192 de code et 64 de files.
Ce n'est pas une RAM librement adressable par les instructions. Il n'y a ni flash,
DMA autonome vers la RAM ARM, échéances absolues, ni ordonnanceur à priorités.
Les créneaux fixes privilégient un timing prévisible à un débit opportuniste.

## Documentation

- [Architecture et brochage](docs/architecture.md)
- [ISA v2 et registres, contrat de référence](docs/isa-v2.md)
- [Applications, débit et raccordement LPC546xx](docs/applications.md)
- [Versions EDA, SRAM, contraintes physiques](docs/toolchain.md)
- [Preuve reproductible du défaut DRC de la macro](docs/sram-drc-blocker.md)
- [Tests exécutés et limites](docs/verification.md)
- [Revue locale et points à faire vérifier](docs/review-notes.md)
- [Plan et limites d'autorisation](docs/development-plan.md)

## Reproduire les tests

Python 3.11–3.13, Icarus Verilog et un compilateur C sont requis.

```sh
python3.13 -m venv .venv
. .venv/bin/activate
python -m pip install -r test/requirements.txt
make test
python tools/pioasm.py examples/ws2812_tx.pio
```

Modèle mémoire PDK : `PDK_ROOT="$PWD/work/pdk" make test SRAM=yes`.
Deuxième simulateur : `make -C test SIM=verilator SIM_BUILD=sim_build/verilator`.
Les scripts de vérification rejettent les échecs et les tests sautés.
Le flow physique local est lancé avec `sh tools/harden_local.sh nom-essai` après
installation des versions indiquées dans la documentation ; il archive ses entrées.

## Publication et soumission

Dénomination choisie par l'utilisateur le 18 septembre 2026 : **AstraPIO**.
Le nom technique `tt_um_fabien_pio` reste inchangé pour préserver la correspondance
avec le GDS testé. Le changement de titre ne modifie pas le circuit.
L'utilisateur a demandé de procéder immédiatement à l'inscription sur la plateforme
et à l'utilisation des coupons pour sécuriser la réservation. Cette démarche
administrative ne constitue pas une validation de fabrication ; voir
[état de réservation](docs/reservation.md).

Dépôt public autorisé par l'utilisateur : [fvannel/AstraPIO](https://github.com/fvannel/AstraPIO),
branche `main`, remote `origin`. Les deux coupons ont été utilisés
le 18 septembre : le compte affiche deux tiles et deux DevKits sur TTIHP26b.
Aucun code n'est enregistré dans les fichiers. Le rattachement au projet sur la
plateforme est suivi dans `docs/reservation.md`. Le GDS n'est pas soumis.
Les workflows de tests et documentation peuvent s'exécuter sur GitHub ; les
workflows matériels restent manuels et verrouillés tant que le statut n'autorise
pas leur lancement. Un GDS existant,
des tests verts ou une simulation à 50 MHz ne signifient pas « prêt à fabriquer ».

Template officiel IHP, commit `6598bef4d3159f19fe471a2a2225df52e6f5ad25` :
[source](https://github.com/TinyTapeout/ttihp-verilog-template/tree/6598bef4d3159f19fe471a2a2225df52e6f5ad25).
Licence Apache-2.0 conservée. Attribution publique et unicité du nom de module à confirmer.
