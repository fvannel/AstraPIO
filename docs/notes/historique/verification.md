# Vérification — candidat v2, 18 septembre 2026

Le nom public a ensuite été changé en **AstraPIO**, sans changement du RTL ni
du nom technique. Les résultats physiques ci-dessous correspondent à l'instantané
`buffered-v2` et au commit `22e40dc`, avant ce changement de métadonnées.
L'inscription administrative et les coupons sont suivis séparément dans `reservation.md`.

**Décision technique : ne pas valider pour fabrication.** Une première révision
provisoire a été autorisée et tentée, mais le portail l'a refusée après l'échec
du workflow officiel ; voir `first-revision-attempt.md`.
Le circuit fonctionne dans les tests numériques
et possède un GDS routé dans deux tiles. Le contrôle DRC officiel de la SRAM
échoue ; les hypothèses d'horloge et l'intégration de carte ne sont pas qualifiées.
Un succès de simulation ou un GDS produit n'annule pas ces blocages.

## Matrice de preuves

| Vérification | Résultat / périmètre |
|---|---|
| Structure, broches, cohérence listes de sources | PASS |
| Assembleur et paquets hôte | 6 tests Python PASS |
| Bibliothèque C | PASS, assertions + AddressSanitizer/UBSan ; objet Cortex-M4 compilé |
| RTL portable, Icarus13.0 | 22 scénarios PASS |
| RTL + SRAM et buffers PDK réels, modèle fonctionnel | 22 scénarios PASS |
| RTL portable, Verilator5.052 | 22 scénarios PASS |
| Netlist finale placée/routée + cellules et SRAM PDK | 22 scénarios PASS ; simulation fonctionnelle sans annotation SDF |
| Lint du flow, Verilator5.044 | 0 erreur ; 1 avertissement reset sync/async expliqué ci-dessous |
| Synthèse, floorplan, placement, CTS, routage | GDS produit, 202,08×313,74µm, 1×2 tiles |
| DRC du routeur | 0 violation |
| Antennes, broches déconnectées, grille d'alimentation | 0 violation rapportée |
| LVS Netgen | 0 différence, correspondance des circuits |
| Setup/hold extraits, trois coins nominaux RC | 0 violation sous les hypothèses SDC décrites ci-dessous |
| Slew, capacité et fanout | 0 violation aux trois coins |
| Precheck officiel TT | FAIL : 1768 erreurs KLayout SRAM ; 9 autres contrôles PASS |
| Magic DRC du flow | FAIL : 60767 erreurs ; ne pas assimiler au deck officiel KLayout |
| Preuve formelle exhaustive / simulation avec SDF | NON EXÉCUTÉ |
| Revue indépendante de signoff | NON RÉALISÉE ; revue locale dans `review-notes.md` |
| Validation FPGA, carte LPC, niveaux électriques et silicium | NON EXÉCUTÉ |
| Allocation individuelle et publication | MISE À JOUR : dépôt GitHub publié, projet 5799 créé et 1×2 tiles affectées ; voir `reservation.md` |
| Révision GDS au portail | NON SOUMISE ; aucun succès de signoff revendiqué |

Les quatre configurations de simulation exécutent **les mêmes 22 scénarios**,
pas 88 scénarios indépendants. Chaque suite simule environ 34,789 ms au total.
Le FIFO autonome historique (`pio_fifo.v`) a aussi un test de 2000 cycles
pseudo-aléatoires ; il **n'est pas instancié dans l'ASIC**. Les vraies files
partagées SRAM sont testées par les scénarios de streaming aux broches.

## Ce que les scénarios couvrent

- SPI à plusieurs phases (demi-périodes 120/127/129/131/133/137ns), ID/ABI,
  commandes inconnues, trames interrompues, clocks en excès, reset durant transfert.
- Deux contextes, banques protégées, direction et lecture des entrées,
  pause/reprise, HALT, IRQ, événements coalescents et transfert entre moteurs.
- Instructions et branches, limites PC/programme, encodages F invalides,
  compteur initial 0 donnant 16 itérations, 16 programmes ALU pseudo-aléatoires
  comparés à une référence Python indépendante.
- Programme de 96 mots total, fenêtre/alias, refus des trous et offsets réservés.
  Motifs 0000/FFFF/AAAA/5555 écrits et relus dans tous les mots, sans écraser TX.
- Plein/vide, pression arrière, overflow signalé, wrap des pointeurs,
  instantanés RX atomiques, abandon de lecture sans consommation, arrivée
  après instantané vide, isolation d'un RESTART et scoreboard aléatoire de 420 opérations.
- Cadence GPIO inchangée pendant les accès hôte ; reset/ena masquent les sorties.
- UART 8N1, SPI émission, SPI émission→réception entre contextes via broches,
  génération WS2812-like, capture→XOR→hôte et relais modifié sur 48 octets.

Les tests principaux n'utilisent que les broches Tiny Tapeout. Les programmes
applicatifs sont assemblés depuis les exemples ou explicités dans le banc.
La référence logicielle couvre l'ALU et les files, pas une preuve indépendante
de chaque état du système. Aucune couverture exhaustive d'opcodes/états ou MTBF
de métastabilité n'est revendiquée.

## Résultat physique de référence

Entrées figées : `work/hardening-buffered-v2/src/`, hashes dans `inputs.sha256`.
Sorties : `work/hardening-buffered-v2/run/final/`.
PDK et outils : voir `toolchain.md`. Le flow retourne un code non nul à cause
des erreurs Magic DRC ; on conserve cette sortie d'échec, sans forcer le succès.

| Mesure | Valeur |
|---|---:|
| Surface du rectangle | 63400,6µm² |
| Surface du core | 60109,3µm² |
| Macro SRAM | 17546,9µm² |
| Cellules + macro + remplissage | 58432,6µm² |
| Remplissage inclus ci-dessus | 3108,07µm² |
| Utilisation standard cells rapportée | 88,7583% de l'espace hors macro |
| Pire marge setup | +9,167ns |
| Pire marge hold | +0,07935ns |

| Coin | Setup minimal | Hold minimal |
|---|---:|---:|
| fast1,32V, standard cells−40°C / SRAM−55°C | +11,099ns | +0,07935ns |
| typ1,20V25°C | +10,762ns | +0,14434ns |
| slow1,08V125°C | +9,167ns | +0,25558ns |

Contraintes : 20 ns, incertitude setup 250 ps / hold 50 ps, derates early/late±5%,
horloge propagée, parasitiques extraits, IO génériques 4 ns. Aucun faux chemin de
données ajouté. Les 50 ps de hold sont une hypothèse de même arête corrélée à
faire approuver, **pas une mesure d'horloge**. Avec 250 ps en hold, les essais
antérieurs n'avaient pas fermé le placement. Ne pas prétendre satisfaire cette
contrainte plus forte ou garantir 50 MHz sur carte.

Le warning `SYNCASYNCNET` vient du reset commun, utilisé comme reset asynchrone
et comme autorisation synchrone des données/SRAM. Il est asserté de façon
asynchrone puis relâché par deux bascules communes. Nous le conservons visible.
Les avertissements de pins SRAM hors grille de routage et de règles LEF non
prises en charge imposent de lire le DRC GDS complet, pas seulement le routeur.
L'IR-drop utilise des sources idéalisées : pas de qualification alimentation/EM
du chip complet. Pas de corner RC extrême ni de température rapide homogène−55°C.

## Résolution du blocage mémoire

Le GDS de la macro officielle **seul**, identique octet par octet à l'amont,
produit les mêmes 1768 violations : 796 Sdiod.d, 796 Sdiod.e, 176 Cnt.c.digibnd.
Voir `sram-drc-blocker.md` pour la commande, le hash et la question à soumettre
aux responsables. Nous n'avons changé ni les règles ni la géométrie du PDK.

## Reproduction et logs

`make test` : contrôles, Python, FIFO auxiliaire, bibliothèque C, suite Icarus.
Autres modes : `make -C test SRAM=yes` avec PDK_ROOT ;
`make -C test SIM=verilator SIM_BUILD=sim_build/verilator` ;
`make -C test GATES=yes` après copie de la netlist finale dans
`test/gate_level_netlist.v` et définition de PDK_ROOT.

Logs complets finaux : `work/release-rtl-tests.log`, `release-pdk-tests.log`,
`release-verilator-tests.log`, `release-gate-tests.log`. Résultats XML dans `test/`.
Le vérificateur `tools/check_results.py` refuse échecs, résultats vides et skips.
Le precheck possède ses propres rapports, archivés à côté du candidat physique.

## Critères de levée du NO-GO

1. Résolution officielle et reproductible du DRC SRAM (ou architecture mémoire
   alternative à refaire qualifier) ; aucune dérogation implicite.
2. Revue des hypothèses horloge/IO/coins et de la couverture CDC/électrique.
3. Allocation des deux tiles et publication désormais réalisées pour AstraPIO ;
   référence de carte LPC et revue finale du dossier restent nécessaires.
4. Rejouer le flow officiel et la netlist sur le commit publié, vérifier la
   révision réellement déposée avant l'échéance du shuttle.
