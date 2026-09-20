# Première révision AstraPIO — tentative bloquée

Rapport historique du premier essai. Une nouvelle tentative avec Magic non
bloquant a ensuite été autorisée explicitement ; voir `provisional-submission.md`.

18 septembre 2026. **Aucune révision créée sur le portail.** Les deux tiles
restent affectées au [projet AstraPIO 5799](https://app.tinytapeout.com/projects/5799).
L'accord de l'utilisateur portait sur une première révision provisoire, pas sur
la suppression des contrôles ou une déclaration de conformité.

## Exécution officielle

- Commit : `a2bd076e76adf3fc3acbecdbb4394a236044a5c4`.
- [Workflow GDS #1](https://github.com/fvannel/AstraPIO/actions/runs/35311159552),
  du 18 septembre 07:31:52 à 07:51:38, Europe/Zurich.
- Action `TinyTapeout/tt-gds-action@ttihp26b`, révision consultée
  `85a4c4128c10aa024ea8a02c7b3828d11c14ed90`.
- tt-support-tools `01d5d2814fa9dd61e9d211e0b235a4a592a9316a`, LibreLane 3.0.5,
  PDK IHP `c4b8b4e5e7a05f375cca3815d51b3a37721fbf5c`.
- Conclusion GitHub : **failure**. Seul l'artefact `GDS_logs` est disponible ;
  **aucun `tt_submission`** n'a été généré.

## Résultats obtenus et limites

| Contrôle dans le job GDS | Résultat |
|---|---|
| Synthèse, placement, CTS et routage | Vues finales produites, deux tiles |
| DRC du routeur | 0 violation |
| Antennes, broches déconnectées | 0 violation |
| LVS | 0 différence ; circuits correspondants |
| Setup / hold extraits | Pas de violation sous les hypothèses documentées |
| Slew / capacité / fanout | 0 violation rapportée |
| Magic DRC | **60767 erreurs**, échec du flow |

Les chiffres de surface et de timing reproduisent les résultats locaux :
58432,6 µm² cellules/macro/remplissage, setup minimal +9,167 ns et hold minimal
+0,07935 ns. Les réserves sur l'incertitude hold de 50 ps, les températures
et la carte restent celles de `verification.md`.

Les jobs GitHub **precheck**, **gl_test** et **viewer** ont été **sautés**, car ils
dépendent du succès de `gds`. Les 1768 erreurs KLayout documentées ailleurs
proviennent du precheck local antérieur, pas d'un precheck distant exécuté ici.
Les tests numériques et la documentation du commit passent séparément :
[tests](https://github.com/fvannel/AstraPIO/actions/runs/35311158588),
[documentation](https://github.com/fvannel/AstraPIO/actions/runs/35311158572).

## Réponse effective du portail

Deux tentatives ont été faites via « Submit a new revision » : avant la
génération sur `9d86c4a`, puis après l'échec sur `a2bd076`. Pour le second commit,
le portail indique qu'aucun artefact `tt_submission` n'existe et demande de
vérifier que le workflow GDS a terminé avec succès. La liste des révisions
reste vide. Aucune pull request de révision n'a été créée par cette procédure.

La possibilité de remplacer une révision ultérieurement ne supprime donc pas
ce prérequis. Le [guide officiel](https://tinytapeout.com/guides/workshop/submit-your-design/)
mentionne également un workflow GDS réussi comme préalable.

## Prochaine décision

Le ticket ouvert [IHP #793](https://github.com/IHP-GmbH/IHP-Open-PDK/issues/793)
recense exactement les catégories KLayout SRAM constatées localement. Le ticket
[IHP #1024](https://github.com/IHP-GmbH/IHP-Open-PDK/issues/1024) documente aussi
des divergences Magic/KLayout. Il faut demander à Tiny Tapeout quelle macro,
révision PDK ou procédure officiellement acceptée appliquer sur TTIHP26b.
Nous n'avons ni modifié le PDK, ni neutralisé le DRC, ni fabriqué une archive
de remplacement pour contourner le prérequis. Aucun message d'assistance envoyé.

## Preuves conservées

`work/revision-1/official-gds.log`, `workflow-result.json` et `GDS_logs/` contiennent
les rapports téléchargés du run. Les fichiers RTL et contraintes ont été comparés
octet par octet aux sources du commit. Le GDS GitHub a pour SHA256 :
`b26268a19c6b8c35964268fd1b3392a4d4dab1fedecd8ebdbfcbd3c6d0a3de2e`.
Les fichiers de travail et les coupons restent hors Git.
