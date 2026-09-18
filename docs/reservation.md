# AstraPIO — réservation administrative TTIHP26b

État au 18 septembre 2026, vers 07:10 Europe/Zurich.

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
- Aucune révision GDS n'est envoyée. Le bouton « Submit a new revision » crée
  une demande d'inclusion à partir du GDS : il n'a pas été actionné, puisque
  les blocages DRC et de qualification demeurent.
- Aucun code n'est conservé dans les fichiers. GDS non téléversé,
  aucune fabrication validée.

Sources : [allocations du compte](https://app.tinytapeout.com/),
[page coupons](https://app.tinytapeout.com/redeem),
[TTIHP26b](https://app.tinytapeout.com/shuttles/ttihp26b).

## Suite

Résoudre le blocage SRAM avec Tiny Tapeout/IHP et faire qualifier les hypothèses
de timing, puis rejouer le flow et les contrôles sur le commit final avant de
créer une révision de fabrication. Le dépôt, le projet et l'affectation sont
confirmés ; l'inclusion du GDS reste une étape séparée.

Un paiement complémentaire, une acceptation de nouvelles conditions ou un choix
de dépôt public non résolu nécessitera une validation spécifique. Ne pas déclarer
le DRC réussi ni le circuit prêt à fabriquer. Le statut technique détaillé reste
dans `verification.md` ; la réservation n'en lève pas les blocages.
