# Références employées, classées par source et étape

> **Document historique — pas la référence ABI 5.** Cette page est conservée
> pour retracer les premières versions du projet. Pour le circuit accepté
> (commit `1b1c9118`, PR149), consulter la [documentation finale](../README.md)
> et la [datasheet ABI 5](datasheet/README.md). Les anciennes instructions de
> soumission et exceptions SRAM ne s’appliquent pas à la version finale.

Vérifiées les 17–18 septembre 2026. Le dossier documentaire initial téléchargé reste
dans les livrables `ic-submission-dossier/` (README, SOURCES, hashes, pages,
template DOCX et PDFs). Le catalogue historique est dans `catalogue-tiny-tapeout/`.
Le présent dépôt contient le projet de développement, pas une copie de tout le PDK.

| Source | Étape / document | Usage pour ce projet |
|---|---|---|
| SwissChips ETH | [IC Design Infrastructure](https://swisschips.ethz.ch/research/ic-design-infrastructure.html) | cadre de soutien, contacts et demande de financement distincte de la soumission TT |
| SwissChips ETH | [Tiny Tapeout / éducation](https://swisschips.ethz.ch/education-outreach/education-outreach-original.html) | participation au shuttle sponsorisé |
| Tiny Tapeout | [HDL templates](https://tinytapeout.com/hdl/templates/) | point de départ officiel IHP |
| Tiny Tapeout | [IHP Verilog template](https://github.com/TinyTapeout/ttihp-verilog-template) | fichiers de projet, broches, workflows |
| Tiny Tapeout | [Important HDL](https://tinytapeout.com/hdl/important/) | reset, horloges, contraintes ASIC |
| Tiny Tapeout | [Mémoire](https://tinytapeout.com/specs/memory/) | comparaison bascules/macros, intégration non triviale |
| Tiny Tapeout | [Tests](https://tinytapeout.com/hdl/testing/) | banc cocotb et simulation netlist |
| Tiny Tapeout | [Hardening local](https://tinytapeout.com/guides/local-hardening/) | flow de placement/routage local |
| Tiny Tapeout | [Action GDS du run](https://github.com/TinyTapeout/tt-gds-action/blob/ttihp26b/action.yml) | version LibreLane et infrastructure |
| Tiny Tapeout | [Precheck du run](https://github.com/TinyTapeout/tt-gds-action/blob/ttihp26b/precheck/action.yml) | révision PDK et contrôles obligatoires |
| Tiny Tapeout | [tt-support-tools](https://github.com/TinyTapeout/tt-support-tools) | configuration et precheck exécutés localement |
| Tiny Tapeout | [Submit Your Design](https://tinytapeout.com/guides/workshop/submit-your-design/) | révision du GDS puis mise à jour explicite sur portail |
| Tiny Tapeout | [Portail TTIHP26b](https://app.tinytapeout.com/shuttles/ttihp26b) | allocation des tiles, échéances, soumission ; aucune mutation effectuée |
| IHP | [PDK exact](https://github.com/IHP-GmbH/IHP-Open-PDK/tree/c4b8b4e5e7a05f375cca3815d51b3a37721fbf5c) | LEF/GDS/Liberty/Verilog/CDL et deck DRC |
| NXP | [LPC546xx](https://www.nxp.com/products/LPC546XX) et [datasheet PDF](https://www.nxp.com/docs/en/data-sheet/LPC546XX.pdf) | futur raccordement, SPI/DMA à configurer pour la carte exacte |

La page SwissChips propose un template de demande de 1–2 pages ; ce formulaire
de financement n'est pas le formulaire de dépôt du design Tiny Tapeout.
La date d'évaluation affichée en avril2026 sur cette page n'est pas l'échéance
du shuttle TTIHP26b. Le guide atelier TT vise surtout Wokwi ; nous utilisons
le template Verilog IHP et les actions du run pour les contraintes techniques.

La petite SRAM 256×8 est présente dans le PDK imposé par le precheck actuel,
mais cela ne prouve pas que ses erreurs DRC sont acceptées. Ce point requiert
une décision officielle. Les coupons, confirmations de commande et codes
d'accès ne font partie ni des sources ni des artefacts du dépôt.
