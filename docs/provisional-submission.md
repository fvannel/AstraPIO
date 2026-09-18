# Première soumission provisoire — autorisation et périmètre

18 septembre 2026. L'utilisateur demande explicitement la première soumission
après avoir été informé du contrôle Magic non bloquant et de l'absence de
validation finale pour fabrication. La soumission n'est pas encore confirmée
au moment de ce commit ; le résultat sera enregistré après réponse du portail.

## Modification limitée

`src/config.json` ajoute uniquement `ERROR_ON_MAGIC_DRC: false` au flow physique.
Magic reste exécuté et ses erreurs, métriques et rapports sont conservés. Cela
permet au flow officiel de produire `tt_submission` malgré ce contrôle.
Les règles et rapports du precheck officiel TTIHP26b restent inchangés et son
résultat réel reste visible. L'extension d'autorisation ci-dessous décrit
désormais une exception provisoire limitée pour son caractère bloquant.
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

## Résultat du 18 septembre, 10:42 Zurich

Le [run 35322726665](https://github.com/fvannel/AstraPIO/actions/runs/35322726665)
sur `8fc3ae86ec69b14de9b2b9c87c811f68cc5ab077` produit cette fois l'archive
officielle `tt_submission` (artefact 10538796473). Le job GDS réussit et les
22 simulations après routage réussissent, sans échec ni test ignoré (sans SDF).
LVS, routage et timing passent sous les contraintes documentées. Magic conserve
ses 60767 erreurs, avec le réglage non bloquant explicitement autorisé.

Le nouveau GDS complet donne **0 violation** avec le même deck principal IHP
corrigé, sans filtre ajouté. Son SHA256 est
`5cae657694699e2eb8d1c193b0e197853405f94015b0623d1ca8e9051736330a`.
Le precheck officiel inchangé donne 9 contrôles réussis et 1 échec : 1768 DRC,
répartis en 796 `Sdiod.d`, 796 `Sdiod.e` et 176 `Cnt.c.digibnd`.

GitHub Pages a été activé selon la FAQ officielle. Après sauvegarde locale des
deux archives de prévisualisation en doublon et leur suppression distante, seul
le job viewer a été relancé : il réussit. L'artefact `tt_submission`, le GDS et
les rapports de contrôles n'ont pas été supprimés ni remplacés.

**Le portail refuse toujours avec « GDS workflow failed »**, alors que seul le
precheck reste en échec. Aucune révision et aucune PR de soumission n'ont été
créées. Le menu alternatif propose seulement un ancien commit, pas une option
pour ignorer ce contrôle. Le précédent public ne garantit donc pas l'accès à
la même procédure dans notre session.

Les deux tiles restent affectées au projet 5799. Pour poursuivre, il faut soit
une prise en charge/validation du cas SRAM par Tiny Tapeout, soit une nouvelle
décision explicite sur le caractère bloquant du precheck. Il n'a pas été rendu
non bloquant et ses règles n'ont pas été modifiées. Aucun message d'assistance,
aucune dérogation, aucun faux résultat de validation n'a été créé.

## Extension explicitement autorisée après le refus du portail

L'utilisateur a répondu « oui je te confirme » à la demande de rendre également
le precheck SRAM non bloquant pour la première révision provisoire, en conservant
les erreurs/rapports et sans valider le circuit pour fabrication.

Le workflow exécute toujours la même action officielle et le même deck épinglé.
Une étape de politique séparée ne tolère que le résultat déjà analysé : les neuf
autres contrôles passent, le DRC signale exactement 1768 erreurs, et les signatures
triées (catégorie, cellule, multiplicité, géométrie) correspondent exactement au
rapport du run `35322726665`, après normalisation du seul préfixe généré à deux
lettres des cellules SRAM (voir le diagnostic ci-dessous). Leur SHA256 canonique est
`6e3e0f139182f47cd77e9cb095f350294e30e247d211040dfba8d281229a5aad`.
Les rapports originaux servant de fixture sont dans `test/fixtures/precheck/`.
Une erreur différente, un rapport absent, un test omis ou une modification de
géométrie d'erreur bloque encore le workflow. Seize tests vérifient ce garde-fou.

Une annotation et un résumé signalent explicitement **OFFICIAL PRECHECK FAILED**
et **NOT qualified for fabrication**. Aucun rapport n'est réécrit en succès.
Un workflow global vert signifie ici seulement que la politique de soumission
provisoire autorisée a été respectée, pas que le DRC officiel a réussi.
Cette autorisation du propriétaire ne vaut pas dérogation Tiny Tapeout/IHP.
Le nouveau résultat du portail reste à vérifier après génération.

## Régression du garde-fou corrigée : préfixe des cellules générées

Le run `35326459266` sur `4751cf6` a reproduit 1768 violations, mais mon premier
garde-fou les a refusées : toutes les cellules SRAM avaient un préfixe `YH_`
au lieu de `RT_`. Deux reproductions locales ont confirmé l'échec. En changeant
uniquement ce préfixe en mémoire, les 1768 signatures deviennent exactement
identiques, y compris cellules de base, orientations, multiplicité et géométries.
Le GDS de ce run passe aussi le deck IHP corrigé à zéro.

Un test de régression sur le rapport complet a échoué avant correction.
Le garde-fou normalise maintenant uniquement ce préfixe à deux lettres majuscules,
uniquement devant les noms `RM_IHPSG13_...` et `RSC_IHPSG13_...`, et exige un seul
espace de noms dans tout le rapport. Le reste de la signature reste identique.
Les tests refusent encore un mélange de préfixes, une cellule de base différente
ou une géométrie modifiée. La boucle est ensuite rejouée sur le rapport réel.
Cette normalisation aurait dû faire partie du test initial : un nom généré
par le flow n'est pas une identité géométrique stable.
