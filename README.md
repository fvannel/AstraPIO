# AstraPIO — version finale soumise (ABI 5)

Version retenue : `1b1c91183a4a9a5ea3516699845336175ffe6d96`,
projet **5799**, shuttle **TTIHP26b**, **1 × 2 tiles**.
[PR149 acceptée](https://github.com/TinyTapeout/tinytapeout-ihp-26b/pull/149),
fusionnée le 19 septembre 2026. Le dépôt local est une présentation nettoyée :
le circuit et sa configuration sont identiques à cette version, mais le
commit de nettoyage n'est pas une nouvelle soumission.

`info.yaml` est conservé byte pour byte comme dans le commit soumis, y compris
ses anciens commentaires prudents. Le statut à jour est décrit ici et dans
`design_status.json`, pas dans ces commentaires historiques.

## Circuit conservé

- Un PIO programmable, une instruction tous les quatre cycles.
- Programme de 16 × 10 bits (20 octets), mémorisé avec des latches standard.
- Files TX et RX de deux octets chacune.
- Moteur temporel autonome, interface hôte SPI et IRQ, horloge 50 MHz.
- Application WS2812 : capture du premier mot DIN de 24 bits vers le LPC,
  remplacement simultané sur DOUT par son compteur, puis relais régénéré
  des mots suivants. Les mises à jour s'appliquent à la trame suivante.
- Pas de macro SRAM, pas d'extension OUTMSB de l'étude ABI 6.

## Organisation

| Répertoire | Contenu |
|---|---|
| `src/` | Les six fichiers RTL utilisés et leur configuration finale |
| `firmware/`, `tools/`, `examples/` | Pilote C, assembleur et outils utiles |
| `test/` | Régressions finales et scénario WS2812 ABI 5 |
| `release/` | Une seule copie des artefacts de fabrication et preuves finales |
| `vendor/` | Uniquement les modèles Verilog nécessaires aux simulations |
| `docs/` | Description finale, bilan de validation et notes des essais |

Voir [la description](docs/info.md), [l'ISA ABI 5](docs/dense-pio-v5.md),
[le bilan des tests](docs/validation-finale.md) et
[l'index des notes historiques](docs/notes/README.md).
Le [compte rendu de nettoyage](docs/nettoyage-20260920.md) indique ce qui
a été retiré, comment le récupérer et les régressions exécutées.

## Vérification et développement

Les six RTL, la configuration de fabrication et les fichiers protégés sont
comparés par empreintes au commit soumis :

```sh
python3 tools/check_final_release.py
```

Pour reproduire les simulations, installer Icarus Verilog **13** et un
environnement Python avec `test/requirements.txt`, puis :

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r test/requirements.txt
make test
make -C test/ws2812 MODE=rtl
make -C test/ws2812 MODE=gl
```

L'assembleur doit être appelé avec **`--abi 5`**. Les modèles de simulation
locaux sont ceux du PDK gelé
`c4b8b4e5e7a05f375cca3815d51b3a37721fbf5c`.
Le PDK complet et les environnements temporaires ont été retirés.

Le suivi automatique est arrêté. Les workflows de fabrication restent manuels
et le verrou local refuse une nouvelle construction distante sans nouvelle
autorisation. Aucun workflow officiel de vérification n'a été contourné.
Le nettoyage local n'a rien publié sur GitHub ou Tiny Tapeout.

## Limites

Les simulations sont fonctionnelles, sans SDF. Les vérifications physiques
concernent le circuit figé et les conditions documentées, pas une carte réelle.
Le LPC546xx, ses transferts SPI/DMA, les niveaux électriques et les LED réelles
restent à qualifier sur matériel.
