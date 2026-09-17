# Plan de vérification

## Résultat local — 17 septembre 2026

Icarus Verilog 13.0, cocotb 2.0.1, Python 3.13.9, horloge simulée 20 ns.
**9 scénarios RTL et 4 tests d'outils passent**. Les tests RTL n'accèdent qu'aux
broches Tiny Tapeout, jamais aux registres internes du RTL.

- Lecture ID, 32 mots programme avec données pseudo-aléatoires, lecture/écriture
  SPI, interruptions de transfert à 7 longueurs, commande inconnue et horloges
  surnuméraires. SPI à phases variables avec demi-périodes 100/109/113/137 ns.
- Deux contextes indépendants, attente non bloquante, masques de propriété,
  lecture d'entrées et directions de sortie.
- Refus des écritures dangereuses, faute sur instruction non chargée, opcode
  invalide et mauvais indice WAIT ; remise à zéro des fautes.
- Instructions, branches, rebouclage du PC, pause/reprise, attente haute/basse,
  16 programmes arithmétiques pseudo-aléatoires comparés à un calcul Python.
- Impulsions de 12 et 14 cycles d'horloge, sans variation observée pendant les
  lectures SPI et acquittements d'IRQ, avec l'autre contexte bloqué.
- Reset/désactivation : sorties masquées, directions libérées et code invalidé ;
  reset pendant un transfert SPI partiel.
- Assembleur : encodages, labels, limites et erreurs ; helpers de paquets SPI.

Le calcul Python de référence couvre l'arithmétique, **pas encore un modèle
indépendant complet du système**. Il ne s'agit ni de couverture exhaustive, ni
de preuve formelle. Aucune synthèse, simulation de netlist ou mesure physique
n'a été effectuée. Une période de simulation de 20 ns ne valide pas 50 MHz.

Reproduction : `make test` dans l'environnement documenté dans le README.
Résultats détaillés générés dans `test/results.xml`, traces dans `test/tb.fst`
(fichiers ignorés par Git). Le vérificateur rejette aussi les tests sautés.

## Tests nécessaires avant de figer l'ASIC

1. Modèle de référence du jeu d'instructions, distinct du RTL.
2. Instructions, branches, boucles, reset, stop/start et limites mémoire.
3. SPI : lectures/écritures, transaction interrompue, reset pendant transfert,
   phases d'horloge variées, limites de fréquence et intégrité des mots.
4. Concurrence : contexte bloqué, conflits de broches, priorités/créneaux,
   échéances simultanées et partage de mémoire.
5. Tampons : plein/vide, overflow/underflow, données périmées, signalement d'erreur,
   hôte absent et indépendance du chemin temps réel.
6. Direction des GPIO : absence de contention et état défini au reset/arrêt.
7. Programmes indépendants : impulsions, UART, SPI applicatif puis WS2812.
8. WS2812 comme application : variations de durée des bits, fins de trame,
   modification aux limites de trame, flux longs et dérive de cadence.
9. Synthèse IHP puis placement/routage, DRC/LVS, antennes, timing aux coins
   applicables et simulation de la netlist.
10. Essais FPGA avec le LPC exact et instrumentation des signaux externes.

## Critères d'arrêt avant soumission

Ne pas soumettre un squelette, une netlist qui ne passe pas les tests, un projet
hors surface, des violations de timing non résolues ou une architecture dont
les limites ne sont pas documentées. Un workflow vert ne prouve pas que toutes
les applications ou toutes les fréquences fonctionnent.
