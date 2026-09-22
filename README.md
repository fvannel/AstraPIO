# AstraPIO — coprocesseur d’entrées/sorties programmables

AstraPIO est un ASIC numérique associant **un PIO programmable** et **un moteur
temporel autonome**, pilotés par un microcontrôleur via SPI. Le projet vise
notamment un hôte **LPC546xx**, sur **deux tiles 1 × 2 de Tiny Tapeout IHP26b**.
Le traitement de flux WS2812 est une application validée en simulation,
pas la définition exclusive de la puce.

## Version finale acceptée : ABI 5

| Référence | Version retenue |
|---|---|
| Source exacte soumise | [`1b1c91183a4a9a5ea3516699845336175ffe6d96`](https://github.com/fvannel/AstraPIO/tree/1b1c91183a4a9a5ea3516699845336175ffe6d96) |
| Projet Tiny Tapeout | [AstraPIO n°5799](https://app.tinytapeout.com/projects/5799) |
| Shuttle et surface réservée | TTIHP26b, 1 × 2 tiles |
| Révision acceptée | [PR149, fusionnée le 19 septembre 2026](https://github.com/TinyTapeout/tinytapeout-ihp-26b/pull/149) |
| Identité logicielle | ID `0x5049`, ABI `0x0500`, un contexte PIO |
| Nom du module RTL | `tt_um_fabien_pio` |

**Attention aux branches :** cette page décrit la version finale ci-dessus.
Les sources, scripts, workflows et `design_status.json` à la racine de `main`
appartiennent encore à l’ancienne version SRAM/double-contexte. Ils ne sont
**pas** le circuit accepté. Cette mise à jour est documentaire uniquement :
elle ne remplace ni le code de `main`, ni le commit soumis à Tiny Tapeout.
Pour examiner ou utiliser le circuit final, prendre les
[sources figées ABI 5](https://github.com/fvannel/AstraPIO/tree/1b1c91183a4a9a5ea3516699845336175ffe6d96),
et non les fichiers historiques de `main`.

## Architecture du circuit final

| Bloc | Capacité |
|---|---|
| PIO | Un interpréteur ; une instruction tous les quatre cycles ASIC |
| Programme | 16 instructions de 10 bits, soit 160 bits / 20 octets utiles, en latches de cellules standard |
| Registres de calcul | Accumulateur 8 bits, compteur 4 bits |
| Files de données PIO | TX : 2 octets ; RX : 2 octets |
| Moteur temporel | Capture et remplacement d’un préfixe programmable de 1 à 24 bits, puis relais régénéré du flux |
| Données du moteur temporel | Capture RX 24 bits, valeur TX préparée 24 bits, valeur TX active 24 bits |
| Interface hôte | SPI mode 0, MSB en premier, transactions de 32 bits ; IRQ |
| E/S applicatives | 8 bidirectionnelles, 5 entrées fixes, 6 sorties fixes : 13 entrées et 14 sorties logiques accessibles |
| Horloge de référence | 50 MHz ; créneau PIO de 80 ns à cette fréquence |

Le PIO et le moteur temporel peuvent fonctionner simultanément, avec une
attribution exclusive des sorties : ils ne doivent pas piloter la même broche.
Il n’y a **ni macro SRAM, ni second contexte PIO, ni extension OUTMSB/ABI 6**
dans la version retenue. L’ISA n’est pas compatible avec celle du RP2040.

## Exemple validé : modifier un flux WS2812

Après détection de l’intervalle de reset du flux :

1. Le moteur capture les 24 premiers bits de DIN, que le LPC peut lire via SPI.
2. Pendant leur réception, DOUT émet la valeur de remplacement préparée par le LPC.
3. Les bits suivants sont retransmis avec les mêmes données et des impulsions régénérées.
4. Le LPC incrémente son compteur sur demande et prépare la valeur de la trame suivante.

La gestion des impulsions est autonome dans l’ASIC : le LPC n’a pas à traiter
chaque front. **Le compteur applicatif est calculé par le LPC**, pas par un
compteur matériel 24 bits dans AstraPIO. L’application doit configurer les
temporisations correspondant aux LED réellement utilisées.

Le rejeu de la version finale a réussi **12 scénarios en RTL et 12 sur la netlist
routée exacte**, sans SDF. Le scénario compteur couvre 12 trames et 1 440 bits
de sortie dans chaque mode, avec une latence observée de 680 à 699 ns.
Le LPC est représenté par un modèle de transactions SPI ; ce n’est pas une
exécution du firmware sur un ARM réel.

## Documentation de référence

- **[Datasheet française — PDF, 24 pages](docs/datasheet/AstraPIO_Datasheet_ABI5_Rev1.0_FR.pdf)**
- [Datasheet modifiable — Word](docs/datasheet/AstraPIO_Datasheet_ABI5_Rev1.0_FR.docx)
- [Contenu et périmètre de la datasheet](docs/datasheet/README.md)
- [Validation finale et références des preuves](docs/final-validation-abi5.md)
- [RTL exact accepté](https://github.com/fvannel/AstraPIO/tree/1b1c91183a4a9a5ea3516699845336175ffe6d96/src)
- [Pilotes C de la version acceptée](https://github.com/fvannel/AstraPIO/tree/1b1c91183a4a9a5ea3516699845336175ffe6d96/firmware)
- [Assembleur de la version acceptée](https://github.com/fvannel/AstraPIO/blob/1b1c91183a4a9a5ea3516699845336175ffe6d96/tools/pioasm.py)

La datasheet décrit le brochage logique Tiny Tapeout, les registres, l’ISA,
le protocole SPI, le moteur temporel, les chronogrammes et l’intégration LPC.
Les anciens documents SRAM, ISA v0/v2 et soumission provisoire sont conservés
comme **historique**, pas comme instructions pour utiliser ou refabriquer l’ABI 5.

## Utiliser les bonnes sources

Pour travailler dans une copie séparée du circuit accepté :

```sh
git clone https://github.com/fvannel/AstraPIO.git AstraPIO-ABI5
cd AstraPIO-ABI5
git checkout --detach 1b1c91183a4a9a5ea3516699845336175ffe6d96
python3 tools/pioasm.py --abi 5 examples/compact/uart_tx.pio
```

Toujours assembler avec **`--abi 5`** : les anciens binaires ne sont pas
compatibles. Vérifier ID, ABI, nombre de contextes et capacité avant le
chargement. Arrêter le PIO avant de modifier son programme.

Le transport SPI exige au minimum six cycles ASIC pour chaque demi-période
SCK et pour les temps de préparation, maintien et repos de CS.
**MISO n’est pas à haute impédance lorsque CS est inactif** : prévoir ce point
si le bus est partagé. Les niveaux électriques et l’adaptation vers les
périphériques doivent être vérifiés sur la carte utilisée.

## Validation et limites

Le circuit figé a passé le flow physique officiel, les contrôles Magic/KLayout
DRC, LVS, XOR et antenne, les dix prechecks, ainsi que 25 scénarios de test
fonctionnel sur netlist routée. Un audit temporel complémentaire à trois coins,
avec facteurs early 0,95 / late 1,05, est également passé.
Voir [le bilan détaillé et ses limites](docs/final-validation-abi5.md).

**Aucun contournement DRC/SRAM n’est utilisé pour qualifier cette version finale.**
Les exceptions des premières expériences sont obsolètes et ne constituent pas
une autorisation de fabrication. Ne pas relancer les anciens workflows de `main`
pour produire l’ABI 5.

L’acceptation du projet dans le shuttle n’atteste pas que la fabrication ou la
qualification sur silicium soit terminée. Pas de simulation avec SDF ni de
validation sur carte LPC546xx/LED réelles à ce stade. La datasheet est donc une
documentation **pré-silicium**, pas une garantie de caractéristiques électriques
mesurées.

Cette publication documentaire ne déclenche aucune nouvelle soumission Tiny Tapeout.

## Licence et origine

Projet sous [licence Apache-2.0](LICENSE), issu du
[template officiel Tiny Tapeout IHP](https://github.com/TinyTapeout/ttihp-verilog-template/tree/6598bef4d3159f19fe471a2a2225df52e6f5ad25).
