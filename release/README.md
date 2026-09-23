# Artefacts de la version finale

Source : `1b1c91183a4a9a5ea3516699845336175ffe6d96` — ABI 5, 1 × 2 tiles.
[Construction officielle 35442726541](https://github.com/fvannel/AstraPIO/actions/runs/35442726541),
[soumission PR149](https://github.com/TinyTapeout/tinytapeout-ihp-26b/pull/149).

Une seule copie du GDS, OAS, LEF, netlist, SPEF nominal et SDC final est conservée.
`commit_id.json`, `pdk.json` et `resolved.json` conservent la provenance et la
configuration résolue. `validation/` contient les métriques finales, résultats
des dix prechecks, des 25 simulations gate-level, des trois audits temporels
et du scénario WS2812 complémentaire.

`manifest.json` lie ces fichiers, les modèles de simulation et 25 fichiers
sources/outils à leurs empreintes SHA-256. Les empreintes des sources ont été
calculées directement depuis le commit soumis. Pour les quatre fichiers dont
seuls des textes ont été corrigés, les [copies originales](reference-text/README.md)
gardent ces empreintes ; le contrôle reconstruit chaque fichier actuel par une
liste fermée de remplacements et exige une égalité byte pour byte. Les autres
fichiers sont comparés directement aux empreintes originales.
Vérification : `python3 tools/check_final_release.py` à la racine.
Ce contrôle d'identité n'est pas un test fonctionnel ni une nouvelle qualification.

Ces artefacts correspondent exclusivement à la source identifiée ci-dessus ;
ils ne qualifient pas un circuit modifié.
Les chemins `work/...` présents dans les journaux et configurations résolues
sont les chemins historiques du build ; ils n'ont volontairement pas été réécrits.

Voir le [dossier de validation](../engineering/README.md).
