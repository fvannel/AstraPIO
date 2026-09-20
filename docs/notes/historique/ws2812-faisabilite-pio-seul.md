# Faisabilité historique WS2812 avec l'ancien PIO seul

Résumé conservé lors du nettoyage du 20 septembre 2026, depuis
`work/ws2812-feasibility/{run,rx-only,limits}.log` et leurs XML.
Ces essais précèdent le moteur temporel final ; ce ne sont pas des échecs du
rejeu ABI 5 aujourd'hui conservé dans `test/ws2812/`.

- Caractérisation préfixe duplex : trois tests réussis, mais ils incluent
  explicitement la démonstration que la boucle préfixe ne relaie pas la fin
  de trame. « PASS » signifie ici que la limitation attendue est observée.
- Copie d'arêtes isolée : 96 bits corrects, latence 148 ns, cinq instructions,
  sans détection du reset ni sélection du préfixe. Ce n'est pas une solution
  complète ni une régénération générale des impulsions.
- Réception seule : un test nominal/coin d'entrée réussi.
- Contrôle strict des limites V5 : **deux échecs sur deux**. La boucle duplex
  viole les largeurs basses ; des bits « 1 » pourtant légaux de 580 ns peuvent
  être mal lus à cause du surcoût entre octets.

Conclusion historique : ne pas présenter le programme PIO seul comme une
solution complète validée au remplacement/relais WS2812. La version finale
utilise le moteur temporel concurrent, dont les tests et preuves sont séparés.
Les anciennes sources d'essai et traces brutes sont retirées du dossier actif
et récupérables dans la Corbeille du nettoyage.
