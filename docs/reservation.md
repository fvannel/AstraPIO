# AstraPIO — réservation administrative TTIHP26b

État au 18 septembre 2026, vers 07:06 Europe/Zurich.

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
- La page « Your projects » indique qu'aucun projet n'existe sur ce shuttle
  pour ce compte : aucun projet AstraPIO créé ni rattachement au design réalisé.
- La création demande obligatoirement une URL GitHub. Le dépôt local n'a pas
  de projet Tiny Tapeout correspondant à ce stade.
- L'utilisateur a ensuite autorisé la publication. Le dépôt public
  [fvannel/AstraPIO](https://github.com/fvannel/AstraPIO) est créé et configuré
  comme remote `origin` ; l'envoi des sources est en cours.
- Aucun code n'est conservé dans les fichiers. GDS non téléversé,
  aucune fabrication validée.

Sources : [allocations du compte](https://app.tinytapeout.com/),
[page coupons](https://app.tinytapeout.com/redeem),
[TTIHP26b](https://app.tinytapeout.com/shuttles/ttihp26b).

## Suite

Terminer l'envoi des sources, puis créer le projet Tiny Tapeout avec cette
URL et vérifier le rattachement des deux tiles. L'allocation sur le compte est
confirmée ; la soumission du design reste une étape séparée.

Un paiement complémentaire, une acceptation de nouvelles conditions ou un choix
de dépôt public non résolu nécessitera une validation spécifique. Ne pas déclarer
le DRC réussi ni le circuit prêt à fabriquer. Le statut technique détaillé reste
dans `verification.md` ; la réservation n'en lève pas les blocages.
