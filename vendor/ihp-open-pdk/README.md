# Modèles de simulation IHP

Seuls les modèles fonctionnels Verilog standard-cell et IO sont conservés,
copiés de l'installation Ciel du PDK IHP SG13G2 gelé :
`c4b8b4e5e7a05f375cca3815d51b3a37721fbf5c`.

Ils permettent les régressions RTL et gate-level sans conserver le PDK complet.
Ils ne suffisent pas à la synthèse, au placement/routage, à la DRC, à la LVS
ou à une qualification temporelle. Les simulations utilisent `FUNCTIONAL`,
sans annotation SDF.

Sources amont : [IHP Open PDK](https://github.com/IHP-GmbH/IHP-Open-PDK/tree/c4b8b4e5e7a05f375cca3815d51b3a37721fbf5c).
Copyright et en-têtes originaux conservés ; licence Apache 2.0 dans `LICENSE`.
Les empreintes des deux modèles et de la licence figurent dans
`release/manifest.json` à la racine du projet.
