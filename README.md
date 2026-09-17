# PIO ASIC — coprocesseur d'entrées-sorties programmable

## État : projet initialisé, moteur PIO non implémenté

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

Les deux contextes, la profondeur mémoire et la fréquence ne sont pas des
capacités validées. `clock_hz: 50000000` et la contrainte de 20 ns sont des
**objectifs exploratoires**, pas une fréquence garantie. Le nom de module,
l'auteur et le brochage restent à confirmer avant publication.

## Ce qui existe aujourd'hui

- Interface Tiny Tapeout et brochage proposé.
- Wrapper RTL inerte : sorties à zéro, broches bidirectionnelles en entrée.
- Test de démarrage du wrapper préparé pour cocotb, pas de test fonctionnel PIO.
- Workflows du template ; génération GDS et FPGA bloquée tant que le RTL est un squelette.
- [Architecture et décisions ouvertes](docs/architecture.md).
- [Plan de vérification](docs/verification.md).

**Il n'y a encore ni SPI fonctionnel, ni ordonnanceur, ni mémoire de programme,
ni programme exécutable, ni GDS validé. Ne pas soumettre ce squelette.**

## Vérification locale

Cohérence de la structure, sans simuler le circuit :

```sh
python3 tools/check_scaffold.py
```

Simulation du wrapper après installation d'Icarus Verilog et des dépendances
de `test/requirements.txt` dans un environnement Python dédié :

```sh
cd test
make
```

Les workflows GDS et FPGA sont manuels. Leur verrou `tools/require_rtl.py`
échoue volontairement tant que `design_status.json` indique un squelette.
Le passage à `rtl_implemented` nécessitera du RTL réel et des tests fonctionnels ;
ce statut ne vaut jamais validation physique ou autorisation de soumission.

## Prochain jalon

Fixer une ISA minimale, les contextes et le modèle de timing ; implémenter une
première tranche de bout en bout : chargement SPI d'un programme qui manipule
une sortie. Puis ajouter le deuxième contexte, les attentes et les files RX/TX,
mesurer la surface et exécuter le placement-routage IHP.

## Coupons et soumission

Aucun coupon n'est nécessaire pour concevoir ou simuler. Les coupons restent
hors du code, de Git et des fichiers de configuration. Leur validité, le run,
l'expiration et le nombre de tiles couvertes se vérifient dans le portail.
Ne pas supposer que deux coupons sont cumulables ni qu'ils couvrent le devkit.
Publication GitHub, réservation, utilisation d'un coupon et soumission finale
seront des étapes séparées à valider avec l'utilisateur.

Licence du template conservée : Apache-2.0.
