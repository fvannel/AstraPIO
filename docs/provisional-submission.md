# Première soumission provisoire — autorisation et périmètre

18 septembre 2026. L'utilisateur demande explicitement la première soumission
après avoir été informé du contrôle Magic non bloquant et de l'absence de
validation finale pour fabrication. La soumission n'est pas encore confirmée
au moment de ce commit ; le résultat sera enregistré après réponse du portail.

## Modification limitée

`src/config.json` ajoute uniquement `ERROR_ON_MAGIC_DRC: false` au flow physique.
Magic reste exécuté et ses erreurs, métriques et rapports sont conservés. Cela
permet au flow officiel de produire `tt_submission` malgré ce contrôle.
Le precheck officiel TTIHP26b reste inchangé et son résultat réel reste visible.
Les contrôles LVS, routage, timing et simulations ne sont pas rendus non bloquants.
Aucun RTL, brochage, capacité mémoire, layout de macro ou règle PDK n'est modifié.

Cette décision s'appuie sur le [précédent Multi Segment Monitor sur TTIHP26b](https://github.com/TinyTapeout/tinytapeout-ihp-26b/pull/22),
fusionné par `urish` avec un precheck en échec et le même réglage Magic.
Ce précédent n'est pas une dérogation générale ni une garantie d'acceptation.

## Contrôle indépendant, distinct du precheck officiel

Le deck principal KLayout IHP corrigé
`5e6d592e4002946a4616f798c357f0f3c06cf3b6` a été testé sur le **même GDS complet**
du premier run officiel : **0 violation**, contre 1768 pour le deck du shuttle
`c4b8b4e5e7a05f375cca3815d51b3a37721fbf5c`. La SRAM seule passe aussi à zéro.
Les correctifs sont ceux de [IHP #819](https://github.com/IHP-GmbH/IHP-Open-PDK/pull/819),
pas un filtre de violations rédigé pour ce projet.

SHA256 du GDS testé :
`b26268a19c6b8c35964268fd1b3392a4d4dab1fedecd8ebdbfcbd3c6d0a3de2e`.
Les rapports XML et logs sont dans `evidence/sram-drc/`.
Ces preuves portent sur le GDS antérieur ; le nouvel artefact doit être vérifié
à son tour après génération. Le test couvre la table principale, pas une
validation de densité/antenne du chip complet.

L'essai local du nouveau deck Magic a planté (code 139) : il n'est pas déclaré
réussi. Les hypothèses timing et autres réserves restent dans `verification.md`.

## Distinction des états

Produire une archive, créer une révision, obtenir son inclusion dans le shuttle
et qualifier le circuit pour fabrication sont quatre résultats différents.
`physical_validation_passed` et `ready_for_submission` restent faux (ce dernier
champ historique désigne la qualification finale, pas l'autorisation provisoire).
La plateforme et le statut JSON seront mis à jour uniquement sur preuve effective.
