# Nettoyage local — 20 septembre 2026

Demande : ne garder que la version finale et les notes des tests.
Travail isolé sur `codex/astrapio-final`, sans push, lancement CI ni soumission.
Le circuit accepté reste `1b1c91183a4a9a5ea3516699845336175ffe6d96` / PR149.

## Conservé

- Les six fichiers RTL actifs, `src/config.json` et `info.yaml`, byte pour byte
  identiques au commit soumis ; pilotes, assembleur et tests utiles.
- Une copie des artefacts finaux dans `release/`, avec provenance, empreintes
  et rapports officiels. Aucun résultat historique n'est réattribué au nettoyage.
- Les deux modèles Verilog du PDK nécessaires aux simulations et leur licence.
- Les notes de tous les groupes d'essais, y compris les échecs et les études
  non retenues, indexées dans [notes/README.md](notes/README.md).
- L'historique Git et toutes les branches d'étude. La référence v4 dans les
  tests différentiels reste uniquement un oracle, pas un circuit à fabriquer.

## Retiré du dossier actif

Copies de travail expérimentales, PDK complets, environnements Python,
compilations, traces et sorties intermédiaires, copies de projets externes,
anciennes sources SRAM/double-contexte, anciens exemples et workflows de
diagnostic. Le helper de hardening local dépendant des anciens chemins est
également retiré ; son historique reste disponible dans Git.

Tout ce retrait passe par la **Corbeille macOS**, sans effacement définitif.
Principaux dossiers récupérables : `work`, `output`, `.cleanup-retired-20260920`
et `.venv`. macOS peut suffixer les noms de caches en doublon. Ne pas vider
la Corbeille avant d'avoir confirmé que rien ne manque. L'espace disque ne
sera effectivement libéré qu'après vidage de la Corbeille par l'utilisateur.

Les deux anciennes copies Git liées ont été recyclées avec `work/`. Seules
leurs inscriptions devenues invalides ont été élaguées ; leurs branches et
commits restent dans le dépôt principal. Pour les reprendre, recréer une
copie liée depuis la branche conservée plutôt que réutiliser leur ancien
fichier `.git` sans réparation.

## Régression après réorganisation

- Empreintes : 50 fichiers vérifiés ; structure et garde-fous inchangés.
- Python : dix tests outils/assembleur et six tests de politique de release.
- C : les deux exécutables de test passent avec AddressSanitizer/UBSan.
- Unités : FIFO et latches 10/16 bits réussis.
- Différentiel : 1 988 traces réussies.
- Broches : 25/25 scénarios réussis après recompilation propre.
- WS2812 : 12/12 RTL et 12/12 gate-level après recompilation propre, avec
  observations JSON identiques entre modes et aux rapports ABI 5 conservés.

Le premier passage avait 24/25 réussites : le test UART cherchait l'exemple
à son ancien chemin. Le chemin `examples/compact/uart_tx.pio` a été restauré,
sans modifier le test officiel ni le RTL, puis les 25 scénarios ont été relancés.
Ce défaut de rangement est résolu, pas ignoré.

Le [registre de contrôle](notes/registres/cleanup-validation-20260920.json)
conserve les noms des tests, comptes et empreintes des rapports de cette reprise.
Les nouvelles traces brutes sont recyclées ; les preuves du release restent
dans `release/validation/`. Après retrait du PDK et des caches, `make check`
et la vérification des empreintes passent encore.

Le verrou de fabrication distant est volontairement bloquant. Aucun contrôle
physique n'est supprimé ou assoupli. Pas de nouveau signoff physique, pas de
SDF, pas de validation sur carte. Le suivi périodique reste en pause.

## Suite du nettoyage

Après accord explicite de l'utilisateur, les reliquats déplacés dans la
Corbeille ainsi que les fichiers temporaires de création de la datasheet ont
été supprimés définitivement le 20 septembre. Ils ne sont donc plus récupérables
via la Corbeille. Les sources finales, les notes, les preuves et les livrables
PDF/DOCX ont été conservés et les 50 empreintes du release ont été revérifiées.

Le 22 septembre, l'utilisateur a demandé l'alignement de `main` sur cette
version nettoyée, avec conservation de la documentation publique récente.
Cette fusion n'est pas une nouvelle révision matérielle ; elle ne déclenche
aucune soumission Tiny Tapeout et laisse les constructions physiques verrouillées.
