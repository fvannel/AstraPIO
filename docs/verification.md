# Plan de vérification

## État initial

Seul un wrapper inerte existe. Les vérifications de structure ne remplacent
ni la simulation RTL ni la vérification physique. Le test cocotb initial
vérifie seulement que les sorties du squelette restent inactives.

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
