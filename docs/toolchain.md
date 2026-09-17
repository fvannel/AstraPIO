# Flow physique reproductible — IHP26b

Vérifié le 18 septembre 2026. Des GDS ont été produits ; la qualification de
fabrication reste bloquée. Consulter la matrice dans `verification.md`.

| Élément | Version de travail |
| --- | --- |
| tt-support-tools | 01d5d2814fa9dd61e9d211e0b235a4a592a9316a |
| LibreLane | 3.0.5, version de l'action ttihp26b |
| Image ARM64 | ghcr.io/librelane/librelane:3.0.5 |
| Digest multi-architecture | sha256:ecabd075d0ddf6a2bd1cd4a32109c7dbb861ec007f7e4e423a9a081f8d23b8e2 |
| PDK du flow / precheck | IHP-Open-PDK c4b8b4e5e7a05f375cca3815d51b3a37721fbf5c |
| Rectangle 1x2 officiel | 202.08 × 313.74 µm |

## Attention aux références PDK

Le sous-module du dépôt global `tinytapeout-ihp-26b` pointe encore sur
`e16d00b7b26a93956563c373b782f54dd4d77a7f`, dont les petites SRAM sont absentes.
Mais **le precheck actuel du même run impose explicitement `c4b8...`**, également
version par défaut de LibreLane 3.0.5. Celle-ci contient notamment les SRAM
256x8, 512x8 et 256x16. Le choix du flow suit donc l'action de validation des
projets et non une déduction à partir du seul sous-module du chip complet.
Ne pas mélanger silencieusement les modèles, LEF, GDS et bibliothèques Liberty
de plusieurs révisions. Tout résultat doit indiquer sa révision exacte.

Sources : [GDS action](https://github.com/TinyTapeout/tt-gds-action/blob/ttihp26b/action.yml),
[precheck](https://github.com/TinyTapeout/tt-gds-action/blob/ttihp26b/precheck/action.yml),
[PDK du flow](https://github.com/IHP-GmbH/IHP-Open-PDK/tree/c4b8b4e5e7a05f375cca3815d51b3a37721fbf5c).

Les dépendances et essais sont sous `work/`, ignoré par Git. Le lien local `tt`
désigne `work/tt`. Aucun service distant ni dépôt privé n'est utilisé.

## Macro intégrée

`RM_IHPSG13_1P_256x8_c3_bm_bist` : 236,8×74,1µm, rotation E (270°).
La configuration source donne sa position et ses halos. Les broches `VDD!`
**et** `VDDARRAY!` sont reliées à VPWR, `VSS!` à VGND. `src/pdn.tcl` ajoute
la connexion Metal4→TopMetal1 pour la grille macro. `A_DLY=1` conformément
à la documentation du modèle, BIST désactivé, masque d'écriture FF.

Les bibliothèques SRAM et standard cells viennent du même commit. Le coin
rapide SRAM est caractérisé à−55°C, celui des standard cells à−40°C : c'est une
association disponible dans ce PDK, **pas une preuve uniforme à−55°C du système**.
Coins nominaux RC utilisés : fast1,32V, typ1,20V25°C, slow1,08V125°C.
Les coins RC extrêmes, si exigés par le shuttle, restent à faire valider.

## Horloge et limites de qualification

`src/timing.sdc` conserve les charges IO, délais IO, slew, fanout et derates
du fichier officiel LibreLane 3.0.5. Il sépare explicitement les incertitudes :
250 ps en setup, 50 ps résiduels en hold pour une même arête corrélée. Les
skews de l'arbre réel extrait et les derates early/late±5% restent actifs.
**Aucun chemin de données n'est mis en faux chemin.**

C'est une hypothèse d'ingénierie à confirmer avec l'intégration d'horloge du
shuttle, pas une mesure. Avec 250 ps aussi en hold, les essais inséraient environ
300 buffers et échouaient au placement. Avec 50 ps, le candidat final
`buffered-v2` entre et présente un hold extrait minimal de +79,35 ps ; on ne doit pas en déduire que
la contrainte initiale 250 ps passerait. Aucun résultat ne garantit encore 50 MHz
sur carte. Les IO restent modélisées par les délais génériques (4ns à20ns).
Les signaux asynchrones doivent aussi faire l'objet d'une revue CDC/MTBF.

Une simulation de netlist **fonctionnelle, sans SDF** vérifie la synthèse et
les connexions, pas les délais. Le STA utilise les parasitiques extraits.
Ne pas confondre les deux types de preuve.

## Reproduction locale

Les outils installés pour ce travail : Icarus13.0, Verilator5.052,
Python3.13.9/cocotb2.0.1 pour les tests ; Python3.12/LibreLane 3.0.5 et
tt-support-tools pour préparer les configurations. Le precheck a son propre
environnement Python3.12 avec les exigences exactes du dépôt (`work/precheck-venv`).
Le PDK a été installé avec Ciel ; le lien `work/pdk/ihp-sg13g2` désigne la
révision figée ci-dessus. Vérifier ce lien et les hashes avant une nouvelle passe.

```sh
sh tools/harden_local.sh nom-unique
```

Le script ne télécharge et ne publie rien. Il requiert Docker, l'image épinglée
par digest, `work/eda-venv`, `work/tt`, le lien `tt` et le PDK installés. Il crée
un instantané immuable sous `work/hardening-nom-unique`, conserve hashes d'entrées,
diff Git, digest d'image, log et code de sortie. Ne pas réutiliser un nom d'essai.

Installation dans une **nouvelle** copie du dépôt (ne pas écraser une installation
existante) :

```sh
mkdir -p work
python3.12 -m venv work/eda-venv
. work/eda-venv/bin/activate
python -m pip install librelane==3.0.5
git clone --no-checkout https://github.com/TinyTapeout/tt-support-tools.git work/tt
git -C work/tt checkout 01d5d2814fa9dd61e9d211e0b235a4a592a9316a
python -m pip install -r work/tt/requirements.txt
ln -s work/tt tt
ciel fetch --pdk-root "$PWD/work/pdk" --pdk ihp-sg13g2 c4b8b4e5e7a05f375cca3815d51b3a37721fbf5c
ciel enable --pdk-root "$PWD/work/pdk" --pdk ihp-sg13g2 c4b8b4e5e7a05f375cca3815d51b3a37721fbf5c
docker pull ghcr.io/librelane/librelane:3.0.5
```

Pour le precheck, créer séparément `work/precheck-venv` avec Python3.12, installer
`work/tt/precheck/requirements.txt`, et fournir un exécutable KLayout. Ici le
wrapper `work/host-bin/klayout` appelle celui de l'image Docker avec le même
chemin absolu monté. Prévoir plusieurs gigaoctets pour le PDK et les outils.

Le flow du run désactive certains contrôles KLayout dans LibreLane ; le precheck
officiel séparé reste indispensable. Dans `work/tt/precheck`, exécuter
`precheck.py --gds CHEMIN_ABSOLU.gds --tech ihp-sg13g2`, avec PDK_ROOT/PDK,
les dépendances officielles et KLayout dans PATH. Placer `info.yaml`, le LEF et
la netlist Verilog de même nom à côté du GDS. Le répertoire courant importe
car ce programme utilise des chemins relatifs.

Les résultats intermédiaires du routeur ne valent pas DRC du layout complet.
Le blocage SRAM est reproduit indépendamment dans `sram-drc-blocker.md`.
L'estimation IR-drop locale utilise des sources idéalisées : pas de qualification
de puissance du chip complet, de la carte ni d'électromigration.
