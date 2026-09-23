# Tests de la version finale ABI 5

`make test` conserve les **25 scénarios** `test_single`, `test_timed` et
`test_dense`, les tests de l'assembleur/protocole, les garde-fous de soumission,
les unités FIFO et latches (10 et 16 bits), les pilotes C avec sanitizers,
et les **1 988 traces différentielles**. La référence RTL v4 dans
`differential/` est un oracle de test, pas une autre version à fabriquer.

Le scénario applicatif supplémentaire est dans
[ws2812/README.md](ws2812/README.md). Il s'exécute en RTL ou sur le netlist
exactement soumis, conservé dans `release/`. Il ne remplace pas les 25 tests.

Le PDK complet n'est pas nécessaire à ces simulations : seuls les modèles
Verilog gelés sont conservés dans `vendor/ihp-open-pdk/`.
La variable `PDK_ROOT` permet toujours une installation externe.
Utiliser Icarus 13 et les dépendances Python de `requirements.txt`.

Depuis la racine du dépôt, préparer puis lancer les vérifications locales :

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r test/requirements.txt
python3 tools/check_final_release.py
make check
make test
make -C test/ws2812 MODE=rtl
make -C test/ws2812 MODE=gl
```

Un compilateur C est nécessaire pour les tests des pilotes. Ces commandes
ne construisent pas de nouveau GDS et ne soumettent rien à Tiny Tapeout.

Les anciens tests SRAM/dual-context et leurs outils ont été retirés du
répertoire actif ; leur bilan est dans `docs/notes/` et leur code reste
dans l'historique Git. Aucun scénario de la suite finale n'a été supprimé.

Ces simulations sont fonctionnelles, sans SDF. Voir
[le bilan de validation](../docs/validation-finale.md) pour leur portée.
