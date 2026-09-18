# AstraPIO — réservation administrative TTIHP26b

État au 18 septembre 2026, vers 08:10 Europe/Zurich.

L'utilisateur demande de procéder maintenant à l'inscription et à la saisie des
codes sur la plateforme, sans attendre la résolution des défauts de fabrication.
Il a explicitement choisi le nom **AstraPIO**. Deux tiles 1×2 sont visées.

## État vérifié

- Le portail affiche l'expiration de la réservation collective SwissChips au
  **18 septembre 2026 à 22:00 UTC+2** et la clôture du shuttle au 21 septembre à 22:00.
- Après connexion GitHub par l'utilisateur, les deux coupons ont été validés
  puis utilisés sur TTIHP26b. Chacun a déclenché une confirmation explicite
  d'ajout d'un tile et d'un PCB. Les coupons utilisés ne sont plus réutilisables.
- La page « Your allocations » confirme **2 tiles** et **2 DevKits** sur
  **Tiny Tapeout IHP 26b**. Aucun paiement supplémentaire n'a été effectué.
- L'utilisateur a ensuite autorisé la publication. Le dépôt public
  [fvannel/AstraPIO](https://github.com/fvannel/AstraPIO) est créé, les sources
  sont poussées sur `main`, et `origin/main` est configurée comme branche suivie.
- [AstraPIO n°5799](https://app.tinytapeout.com/projects/5799) est créé à partir
  de cette URL. La plateforme affiche **Tiles: 1x2**, **Tiny Tapeout IHP 26b**
  et confirme que l'espace est **affecté au projet**, mais que le projet n'est
  pas encore inclus. Il ne s'agit plus seulement d'un solde inutilisé du compte.
- Aucune révision GDS n'est enregistrée. Le bouton « Submit a new revision » a
  été actionné avant puis après le workflow officiel, mais le portail a refusé
  les deux tentatives faute d'artefact `tt_submission`.
- Aucun code n'est conservé dans les fichiers. Le GDS intermédiaire est présent
  dans les journaux GitHub du workflow échoué, pas dans une révision du shuttle.
  Aucune fabrication validée.

Sources : [allocations du compte](https://app.tinytapeout.com/),
[page coupons](https://app.tinytapeout.com/redeem),
[TTIHP26b](https://app.tinytapeout.com/shuttles/ttihp26b).

## Suite

**Mise à jour :** après recherche des précédents et essai du deck IHP corrigé,
l'utilisateur a explicitement demandé la première soumission provisoire avec
Magic DRC non bloquant. Cette seule politique change ; le precheck officiel
reste inchangé. La génération est à relancer et aucune nouvelle révision n'est
encore confirmée au moment de ce commit. Voir `provisional-submission.md`.
Les paragraphes suivants décrivent les tentatives précédentes.

L'utilisateur a maintenant donné son accord pour la première révision provisoire.
La première tentative via « Submit a new revision » a été refusée : aucun
artefact `tt_submission` pour le commit `9d86c4a`, le workflow GDS n'ayant pas
encore été exécuté. Aucune révision n'a été créée lors de cette tentative.

Le workflow GDS officiel du run a été exécuté sur `a2bd076` avec les versions
documentées (tt-support-tools `01d5d28`, LibreLane 3.0.5). Il a échoué sur
60767 erreurs Magic DRC ; l'archive `tt_submission` n'a pas été produite.
La deuxième tentative a été explicitement refusée pour ce commit. Les contrôles
sont restés actifs ; aucun `continue-on-error`, faux succès ni artefact de
remplacement n'a été ajouté. Voir `first-revision-attempt.md` pour les preuves.

Le blocage SRAM et les hypothèses de timing devront être résolus avant de
considérer le design qualifié. Dépôt, projet et affectation sont confirmés ;
l'inclusion du GDS reste une étape séparée. Les problèmes SRAM correspondants
sont déjà suivis chez IHP ; une procédure acceptée pour TTIHP26b doit maintenant
être confirmée auprès des responsables. Aucun message d'assistance n'a été envoyé.

Un paiement complémentaire, une acceptation de nouvelles conditions ou un choix
de dépôt public non résolu nécessitera une validation spécifique. Ne pas déclarer
le DRC réussi ni le circuit prêt à fabriquer. Le statut technique détaillé reste
dans `verification.md` ; la réservation n'en lève pas les blocages.
