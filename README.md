# PIO ASIC — coprocesseur d'entrées-sorties programmable

## État : première version fonctionnelle en simulation, pas prête à fabriquer

Ce projet est un **PIO généraliste** relié à un LPC55xxx par SPI. WS2812 est
une application de validation, pas une fonction câblée dans l'ASIC.

Base : [template officiel IHP](https://github.com/TinyTapeout/ttihp-verilog-template),
commit `6598bef4d3159f19fe471a2a2225df52e6f5ad25`, vérifié le 17 septembre 2026.
Le dépôt Git local possède une branche `main`, sans aucun remote : aucun dépôt
distant n'a été créé et aucun fichier n'a été publié. Le template d'origine est
identifié ci-dessus pour conserver sa provenance.

## Objectif de conception

- Cible provisoire : TTIHP26b, IHP SG13G2, **deux tiles (`1x2`)**.
- Un moteur d'exécution partagé par **deux contextes** programmables.
- Ordonnancement déterministe, attentes d'événement et de temps.
- SPI dédié vers le LPC, interruptions et petits tampons de données.
- Programme chargé par l'ARM après reset ; aucune flash interne prévue.
- Huit GPIO bidirectionnelles, cinq entrées fixes et six sorties fixes pour les programmes.
- Aucune dépendance à un décodeur WS2812, UART ou SPI applicatif câblé.

Deux contextes sont implémentés ; leur tenue physique dans deux tiles et la
profondeur mémoire finale restent à valider. `clock_hz: 50000000` et la contrainte de 20 ns sont des
**objectifs exploratoires**, pas une fréquence garantie. Le nom de module,
l'auteur et le brochage restent à confirmer avant publication.

## Ce qui existe aujourd'hui

- Interface Tiny Tapeout : SPI dédié, IRQ et 19 signaux applicatifs.
- Deux contextes, 16 instructions de 16 bits chacun, accumulateurs 16 bits.
- Créneaux fixes alternés, attente d'entrée et temporisation non bloquantes pour l'autre contexte.
- 15 instructions génériques, sorties et directions protégées par masques disjoints.
- Chargement/lecture SPI, protection contre la modification du code actif, fautes et reset.
- Assembleur minimal, formation de paquets hôte et deux exemples programmables.
- Tests RTL sur les broches et tests des outils hôte.
- Workflows du template ; génération GDS et FPGA volontairement bloquée au stade prototype.
- [ISA v0, registres et timing](docs/isa-v0.md).
- [Architecture et décisions ouvertes](docs/architecture.md).
- [Plan de vérification](docs/verification.md).

**Pas encore de FIFOs, de streaming, d'échanges entre contextes ou de pilote LPC.
Aucune validation WS2812, synthèse IHP, mesure de surface ou GDS. Ne pas soumettre
ce prototype.** Les 64 octets de code sont en logique inférée, pas en macro SRAM.
L'ISA et les registres sont provisoires et pourront évoluer.

## Vérification locale

Préparer un environnement avec Python 3.11 à 3.13 (cocotb 2.0.1 ne prend pas en
charge Python 3.14), ainsi qu'Icarus Verilog dans le PATH :

```sh
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r test/requirements.txt
make test
```

`make check` vérifie la structure et les outils sans simulation RTL. Assembler
un programme (mots hexadécimaux sur la sortie standard) :

```sh
python tools/pioasm.py examples/blink.pio
```

Les workflows GDS et FPGA sont manuels. Leur verrou `tools/require_rtl.py`
échoue volontairement tant que `design_status.json` indique `rtl_prototype`.
Le passage à `rtl_implemented` nécessitera d'implémenter et vérifier le périmètre
PIO prévu ; ce statut ne vaut jamais validation physique ou autorisation de
soumission. Une simulation RTL à période 20 ns ne prouve pas un timing silicium.

## Prochain jalon

Mesurer tôt la surface de cette base, puis ajouter les files RX/TX et les échanges
entre contextes avec leurs tests. Étendre ensuite l'ordonnancement aux événements
et échéances nécessaires aux applications ; ne pas transformer le cœur en
décodeur WS2812 spécialisé. La référence exacte du LPC55xxx et les tensions
seront nécessaires au pilote, au DMA et au raccordement matériel.

## Coupons et soumission

Aucun coupon n'est nécessaire pour concevoir ou simuler. Les coupons restent
hors du code, de Git et des fichiers de configuration. Leur validité, le run,
l'expiration et le nombre de tiles couvertes se vérifient dans le portail.
Ne pas supposer que deux coupons sont cumulables ni qu'ils couvrent le devkit.
Publication GitHub, réservation, utilisation d'un coupon et soumission finale
seront des étapes séparées à valider avec l'utilisateur.

Licence du template conservée : Apache-2.0.
