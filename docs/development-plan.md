# Plan de développement et fermeture — 17 septembre 2026

## Autorité et périmètre

Développer un PIO numérique généraliste dans exactement deux tiles IHP, avec
mémoire de programme, tampons de données, SPI hôte et protocoles applicatifs
programmables. WS2812 reste un programme de validation. Aucun dépôt distant,
publication, usage de coupon ou envoi au portail n'est autorisé à ce stade.
L'objectif est un dossier technique prêt à soumettre, sans prétendre à des tests
exhaustifs ni à une validation silicium avant fabrication.

## Jalons

1. Installer le flow officiel du run, figer ses versions, mesurer le prototype.
2. Arbitrer la mémoire sur des mesures : coût des registres, macros réellement
   présentes dans le PDK autorisé, géométrie, routage et timing.
3. Étendre par tranches testées : FIFOs hôte, échanges entre contextes,
   instructions de sérialisation et ordonnanceur à contrat de temps explicite.
4. Applications : génération/capture de signaux, UART, SPI applicatif,
   transfert bidirectionnel et relais programmable de type WS2812.
5. Plusieurs bancs : instructions et référence logicielle, transactions SPI,
   concurrence/FIFOs, aléas/reset, protocoles, seconde simulation, netlist.
6. Synthèse, floorplan deux tiles, placement/routage, DRC/LVS, timing et precheck.
7. Revue contradictoire, correction des anomalies, dossier de soumission et
   matrice explicite PASS / FAIL / non exécuté / confirmation externe requise.

## Décisions non bloquantes

- Hôte LPC546xx confirmé par l'utilisateur ; référence complète et brochage non fournis.
- Deux tiles réservées selon l'utilisateur le 18 septembre ; run TTIHP26b confirmé
  par le message SwissChips fourni. Affectation à un projet individuel non vérifiée.
  Orientation 1x2 retenue. Codes de coupon exclus de tous les fichiers.
- Portail vérifié le 18 septembre : réservation collective SwissChips jusqu'au
  18 septembre 2026 à 22:00 Europe/Zurich ; clôture du run le 21 septembre à 22:00.
  Ces échéances ne sont pas équivalentes ; les codes ne prouvent pas l'affectation.
- Favoriser la mémoire utile et le déterminisme, sans remplir artificiellement
  chaque micron : le routage, l'alimentation et les marges de timing priment.
- Aucun recours à un serveur distant payant ni à des outils commerciaux sans
  autorisation. Ne pas supprimer de fichiers existants pour libérer du disque.

## Méthode

Tests par interfaces observables, une fonctionnalité à la fois, régression après
chaque modification ; pas de faux tests qui reproduisent uniquement le RTL.
Le suivi reste dans les documents locaux existants. L'installation de conventions
de tickets/AGENTS, qui demanderait des choix d'organisation, est différée.

## Références vérifiées

- [SwissChips infrastructure](https://swisschips.ethz.ch/research/ic-design-infrastructure.html)
- [SwissChips outreach](https://swisschips.ethz.ch/education-outreach/education-outreach-original.html)
- [Soumission et révisions Tiny Tapeout](https://tinytapeout.com/guides/workshop/submit-your-design/)
- [Hardening local](https://tinytapeout.com/guides/local-hardening/)
- [Action du run IHP26b](https://github.com/TinyTapeout/tt-gds-action/blob/ttihp26b/action.yml)
- [Précautions HDL](https://tinytapeout.com/hdl/important/)
- [Tests et simulation de netlist](https://tinytapeout.com/hdl/testing/)
- [Options mémoire et limites](https://tinytapeout.com/specs/memory/)

SwissChips fournit le cadre d'accompagnement et de financement ; ses pages ne
remplacent pas le contrat technique du shuttle. Le guide atelier de soumission
vise surtout une révision Wokwi : pour notre Verilog, utiliser le template IHP
et le flow du run, puis vérifier que la révision finale soumise correspond au
GDS effectivement contrôlé. Les conventions et versions peuvent évoluer.
