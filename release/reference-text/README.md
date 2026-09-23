# Copies originales des textes corrigés

Ces quatre fichiers sont des copies byte pour byte du commit soumis
`1b1c91183a4a9a5ea3516699845336175ffe6d96`. Ils conservent leurs commentaires
historiques ; ce ne sont pas les documents à utiliser pour intégrer le circuit.

Leurs empreintes restent celles du manifeste original, inchangé. Le contrôle
`tools/check_final_release.py` vérifie ces empreintes puis applique en mémoire
une liste fermée de remplacements éditoriaux. Le résultat doit correspondre
exactement aux fichiers actuels de `src/`, `firmware/` et `info.yaml`.

Aucune suppression générique des commentaires, normalisation du code ou
exemption de fichier n’est utilisée. Toute autre différence est une erreur,
y compris un autre commentaire, un changement de fréquence ou de déclaration.
Les 46 autres fichiers couverts par le manifeste sont contrôlés directement.

Ce mécanisme conserve la provenance documentaire ; il ne remplace aucun test
fonctionnel ou contrôle physique. Le GDS et tous les artefacts soumis restent
inchangés. Les sources compilées proviennent de `src/`, jamais de ce dossier.
