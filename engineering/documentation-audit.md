# Audit de publication documentaire

23 septembre 2026. Interface AstraPIO ABI 5, source matérielle
`1b1c91183a4a9a5ea3516699845336175ffe6d96`.

## Verdict

La documentation utilisateur locale est publiable comme documentation
préliminaire du composant. Elle décrit l’interface actuelle, ses limites et
son utilisation, sans récit des décisions ou des architectures abandonnées.
La qualification électrique sur carte et sur silicium n’est pas revendiquée.

Les corrections éditoriales des sources sont vérifiées par reconstruction
exacte à partir de copies de la référence soumise. Le manifeste original et
les contrôles physiques sont inchangés. La fusion du texte Tiny Tapeout
relève séparément des mainteneurs du shuttle.

## Périmètre et vérifications

| Ensemble | Vérification et résultat |
|---|---|
| README principal | Réduit de 84 à 40 lignes, de 686 à 285 mots ; présentation, capacités, liens, précautions essentielles et ressources du dépôt |
| Documentation active | Relecture des 15 Markdown hors archives : documentation utilisateur, exemples, guides de test, index d’ingénierie, artefacts et provenance des modèles tiers |
| Contrat ABI 5 | Broches, registres, valeurs de reset, SPI, mémoire, instructions, FIFO, erreurs et moteur temporel comparés au RTL et aux interfaces du pilote |
| Datasheet et note d’application | 22 et 7 pages ; 415 paragraphes/cellules d’au moins 25 caractères retrouvés dans les PDF et le Markdown après normalisation de la mise en forme ; contrôle des tableaux et des six figures |
| Word | Aucun commentaire ni modification suivie ; métadonnées du modèle corrigées ; figure d’architecture rendue générique sans modifier les autres parties du document |
| Rendu | Datasheet de 22 pages régénérée après correction de la figure 1 : page 3 inspectée, 21 autres pages identiques pixel par pixel au rendu précédent ; note d’application de 7 pages inchangée |
| Navigation locale active | 57 liens Markdown relatifs contrôlés, aucun destinataire manquant avant ajout du présent compte rendu |
| Exemples | Premier programme assemblé en `0002 0301 0371 0306` ; exemple C de la note compilé en contrôle de syntaxe strict |
| Intégrité et outils | `make check` réussi : 50 identités gelées, 4 corrections éditoriales exactes, structure et garde-fous, 10 tests des outils, 6 tests de politique de publication et 12 tests du contrôle d’intégrité |
| Pilotes hôte | Tests C réussis avec détection des accès mémoire invalides et comportements indéfinis ; déclarations du pilote temporel identiques après prétraitement |
| Archives | 53 Markdown inventoriés et analysés par recherche transversale ; historique séparé de la documentation utilisateur, non requalifié techniquement |
| Recherche de données sensibles | Aucun motif de coupon SwissChips, jeton GitHub ou clé privée trouvé dans les fichiers texte suivis ; contrôle limité à ces motifs et à l’arbre courant, pas une preuve d’absence de tout secret dans l’historique Git |

Les deux chemins d’archives dans `design_status.json` ont été mis à jour.
Les champs d’autorisation matérielle, les tests physiques et le manifeste
restent inchangés. Les nouveaux tests d’intégrité vérifient notamment le rejet
d’une modification du RTL, d’une déclaration du pilote, de la fréquence,
d’un commentaire non prévu, du GDS ou des copies originales. Ces contrôles
locaux ne sont pas une nouvelle qualification physique.

La figure 1 de la datasheet emploie « Microcontrôleur hôte » à la place de
« LPC546xx ou autre ». L’image du manuel en ligne et celle du Word sont
identiques ; le PDF a été réexporté depuis ce Word. Texte et autres figures
de la datasheet ne mentionnent pas le LPC546xx. Dans la documentation
utilisateur, cette référence est réservée à la note d’application WS2812.

## Corrections de publication

### Texte proposé à Tiny Tapeout

Le [texte utilisateur audité](../docs/info.md) est la référence documentaire
pour la [PR 252](https://github.com/TinyTapeout/tinytapeout-ihp-26b/pull/252).
Il remplace le récit du projet par l’utilisation du composant. Les documents
du dépôt AstraPIO doivent être disponibles sur `main` avant la demande de
fusion, pour que leurs liens publics fonctionnent. Cette PR ne remplace
aucun artefact de la révision matérielle acceptée.

### Textes inclus dans la référence gelée

| Fichier actuel | Correction appliquée |
|---|---|
| `info.yaml` | Description du PIO et du moteur temporel ABI 5 ; commentaires de statut actualisés, valeurs techniques inchangées |
| `firmware/pio_timed.h` | Description de l’interface temporelle présente, sans référence à une ancienne soumission |
| `src/project.v` | Description générique de l’architecture ABI 5 |
| `src/pio_spi.v` | Renvoi vers `docs/reference.md` |

Les [quatre originaux](../release/reference-text/README.md) conservent leurs
empreintes du manifeste inchangé et ont été comparés au commit soumis.
Le contrôle applique uniquement les remplacements littéraux approuvés puis
compare tous les octets aux fichiers actuels. Il n’ignore aucun commentaire
arbitraire et ne tolère aucune autre différence. Le code matériel, les
déclarations du pilote et la configuration technique ne changent pas.

### Archives et portée de la publication

Les 52 occurrences de liens locaux non résolus sont exclusivement dans les
archives ; elles désignent notamment des résultats supprimés et des chemins
de travail historiques. Leur avertissement d’archive les identifie comme tels.
Ne pas inclure ce dossier dans un paquet de documentation destiné à
l’utilisateur du composant. Sa conservation dans le dépôt sert uniquement
à la traçabilité ; ce n’est pas un ensemble de guides encore exécutables.

## État de livraison

Ce jeu de modifications concerne la documentation et la vérification de sa
provenance. Il n’autorise ni nouveau build matériel ni nouvelle soumission.
La publication GitHub et l’intégration documentaire dans Tiny Tapeout sont
deux étapes distinctes ; le statut de la PR 252 fait foi pour cette dernière.
