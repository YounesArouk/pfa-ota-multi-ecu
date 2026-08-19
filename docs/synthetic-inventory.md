# Inventaire synthétique des 28 ECU

## Identification

- Dataset : `SYNTHETIC_PFE_V1`
- Nombre d'ECU : 28
- Nature : données synthétiques pour simulation PFE
- Statut : non constructeur et non destiné à la production

## Objectif

Cet inventaire permet de développer et tester l'orchestration d'une campagne OTA multi-ECU sans attendre la base constructeur définitive.

Le simulateur charge les données depuis des fichiers CSV. La base synthétique pourra donc être remplacée ultérieurement sans modifier le moteur Python.

## Architecture retenue

L'inventaire contient :

- 1 Central Gateway jouant le rôle d'OTA Master ;
- 1 unité de connectivité inspirée de l'Aptiv EP-150 ;
- des ECU Powertrain ;
- des ECU Chassis ;
- des ECU ADAS ;
- des ECU Body et zonaux ;
- des ECU Infotainment.

Le Central Gateway est inclus dans les 28 ECU.

## Versions

Chaque ECU possède :

- sa propre version actuelle ;
- sa propre version cible ;
- son propre paquet logiciel.

La campagne véhicule ne signifie pas que la même version logicielle est installée dans les 28 ECU.

## Partitions

Pour les besoins de la simulation, tous les ECU utilisent :

- une partition A ;
- une partition B ;
- une partition recovery en lecture seule.

Cette hypothèse permet de tester uniformément le rollback et le recovery.

## Priorités

Les priorités vont de 1 à 5 :

- 1 : priorité la plus élevée ;
- 5 : priorité la plus faible.

Le Central Gateway est mis à jour en premier. Son état de campagne devra être sauvegardé avant son redémarrage.

L'unité de connectivité EP-150 est planifiée en dernier afin de conserver la communication OTA pendant la campagne.

## Dépendances

Les relations sont de type `HARD` : un ECU dépendant ne peut pas démarrer avant la réussite de son prérequis.

La règle suivante est explicitement intégrée :

`Central_Gateway` doit être mis à jour avant `Zone_Front`.

Le planificateur vérifie également l'absence de dépendance circulaire.

## Limites

- Les versions et tailles d'images sont représentatives.
- Les temps réels de flash ne sont pas fournis par un constructeur.
- Les bus indiqués représentent une architecture automobile plausible.
- L'inventaire devra être remplacé si la base définitive devient disponible.
