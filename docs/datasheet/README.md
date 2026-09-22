# Datasheet AstraPIO — ABI 5

DS APIO 001, révision documentaire 1.0, 20 septembre 2026, français.

- [PDF — 24 pages](AstraPIO_Datasheet_ABI5_Rev1.0_FR.pdf)
- [Word modifiable](AstraPIO_Datasheet_ABI5_Rev1.0_FR.docx)

Cette documentation décrit la version soumise
[`1b1c91183a4a9a5ea3516699845336175ffe6d96`](https://github.com/fvannel/AstraPIO/tree/1b1c91183a4a9a5ea3516699845336175ffe6d96),
projet 5799, TTIHP26b, [PR149 acceptée](https://github.com/TinyTapeout/tinytapeout-ihp-26b/pull/149) :
un PIO, programme 16 × 10 bits en latches, FIFO de deux octets, moteur temporel,
SPI et IRQ. Elle ne décrit pas les variantes SRAM ou ABI 6.

Les sources actives de `main` sont maintenant alignées sur cette version finale.
Le lien figé ci-dessus reste la référence de la soumission. La révision 1.0 du
document et la fusion de `main` ne sont pas de nouvelles révisions matérielles
Tiny Tapeout.

## Contenu

Architecture et schémas de principe ; brochage logique ; horloge et reset ;
statut des caractéristiques électriques ; protocole et chronogrammes SPI ;
registres et champs de bits ; ISA complète ; moteur temporel ; connexion
LPC546xx ; application WS2812 ; programmes UART/SPI ; API C ; erreurs et
récupération ; qualification et références.

## Portée

Les comportements ont été recoupés avec le RTL et les pilotes de la version
finale. Voir le [bilan de validation](../final-validation-abi5.md) pour les preuves
et limites. Les caractéristiques électriques, le brochage du module livré et
les performances réelles sur carte restent à qualifier.

Le PDF est exporté du DOCX et sa mise en page a été contrôlée page par page.
Les exemples PIO ont été comparés après assemblage aux programmes du projet.
Les deux documents sont publiés sans modification depuis leur validation locale ;
les fichiers temporaires de rendu ne sont pas inclus.
