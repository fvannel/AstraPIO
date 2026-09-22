# Revue locale de conception

> **Document historique — pas la référence ABI 5.** Cette page est conservée
> pour retracer les premières versions du projet. Pour le circuit accepté
> (commit `1b1c9118`, PR149), consulter la [documentation finale](../README.md)
> et la [datasheet ABI 5](datasheet/README.md). Les anciennes instructions de
> soumission et exceptions SRAM ne s’appliquent pas à la version finale.

Revue effectuée pendant l'implémentation, **non indépendante**, sans approbation
par un second ingénieur ou une fonderie. Elle ne remplace pas une revue tapeout.

## Points contrôlés et décisions

- **Atomicité SPI/RX** : l'instantané et sa validité sont figés avant les données ;
  un abandon ne consomme pas l'octet. Test spécifique d'une arrivée après un
  instantané vide, tests de trames interrompues et scoreboard aléatoire.
- **Port SRAM unique** : fetch bas/haut distincts des créneaux données, priorité
  hôte explicite. Le retour de lecture arrive avant le prochain créneau du
  contexte. Le host maintient les données assez longtemps ; ses durées CS/SCK
  font partie du contrat, elles ne peuvent pas être remplacées par une simple
  limite de fréquence moyenne.
- **Partition mémoire** : les adresses programme excluent les pages des files ;
  longueurs valides et chargement sans trous évitent l'exécution de données
  indéfinies. Le test de motifs garde des sentinelles dans les TX simultanément.
- **GPIO et reset** : banques disjointes, masques limités, sortie/OE forcées à zéro
  à la désactivation. Stop et faute ne libèrent pas les lignes : choix explicite,
  à prendre en compte pour éviter une contention matérielle.
- **SRAM physique** : DLY=1, BIST désactivé, VDD et VDDARRAY reliées, rotation dans
  deux tiles. Des buffers standard du PDK isolent les sorties SRAM et renforcent
  les adresses ; les violations de slew/capacité restantes ont ainsi été éliminées.
- **Transport hôte** : transactions sérialisées ; pas de retry automatique d'une
  RX destructive incertaine. Envoi par lots nécessaire pour le débit soutenu.
  La compilation ARM et le test C ne valident pas le DMA ou les broches LPC.
- **Critères de release** : les résultats d'un ancien candidat ne sont pas
  attribués au RTL final. La passe physique et ses entrées sont figées et hachées.
  Les erreurs de la macro amont et les hypothèses SDC ne sont ni supprimées ni
  converties en succès. Les workflows distants restent verrouillés.

## Sujets à faire vérifier indépendamment

Résolution officielle DRC SRAM ; incertitude hold50ps et horloge du shuttle ;
association de températures des bibliothèques rapides ; CDC/MTBF ; limites des
pads, alimentation et charge réelle ; couvertures SDF/formelle et essais FPGA/LPC ;
révision exacte à publier et attribuer aux tiles. Le statut reste NO-GO.
