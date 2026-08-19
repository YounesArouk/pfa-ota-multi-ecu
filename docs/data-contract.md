# Contrat de données OTA commun

## 1. Objectif

Ce contrat définit le format commun utilisé par :

- les 28 ECU Python simulés ;
- l'ECU réel QEMU/RAUC ;
- l'orchestrateur ;
- l'API ;
- le dashboard.

## 2. Sources des données

Valeurs autorisées pour `source_type` :

- `SIMULATED` : ECU simulé avec Python ;
- `REAL_QEMU` : ECU réel exécuté sous QEMU.

Valeurs autorisées pour `source_mode` :

- `SIMULATION` : campagne entièrement simulée ;
- `REAL_QEMU` : campagne mono-ECU réelle ;
- `HYBRID` : un ECU réel et des ECU simulés.

## 3. États OTA d'un ECU

- `IDLE` : ECU disponible, aucune mise à jour en cours ;
- `WAITING_DEPENDENCIES` : attente de ses prérequis ;
- `DOWNLOADING` : téléchargement du bundle ;
- `VERIFYING_SIGNATURE` : vérification de la signature ;
- `VERIFYING_CHECKSUM` : vérification de l'intégrité ;
- `INSTALLING` : écriture du banc inactif ;
- `REBOOTING` : redémarrage vers le nouveau banc ;
- `SELF_TEST` : contrôle de santé ;
- `CONFIRMED` : nouvelle version validée ;
- `ROLLBACK` : retour vers l'ancien banc ;
- `RECOVERY` : démarrage de la partition recovery ;
- `REJECTED` : mise à jour refusée ;
- `OFFLINE` : ECU non joignable.

## 4. États des partitions

- `GOOD` : partition valide ;
- `BAD` : partition invalide ;
- `EMPTY` : partition sans image ;
- `WRITING` : écriture en cours.

La partition `RECOVERY` doit toujours avoir `read_only=true`.

## 5. États de santé

- `GOOD`
- `DEGRADED`
- `BAD`
- `UNKNOWN`

## 6. États d'une campagne

- `CREATED`
- `VALIDATING`
- `READY`
- `RUNNING`
- `COMPLETED`
- `PARTIAL_SUCCESS`
- `ROLLED_BACK`
- `REJECTED`
- `FAILED`
- `STOPPED`

## 7. Politiques de rollback

- `LOCAL` : rollback uniquement de l'ECU défaillant ;
- `GLOBAL` : rollback des ECU déjà mis à jour dans la campagne.

## 8. Règles obligatoires

1. `progress_pct` doit être compris entre 0 et 100.
2. Une signature doit être validée avant toute installation.
3. L'ECU écrit uniquement dans le banc inactif.
4. La partition recovery ne doit jamais être écrite par OTA.
5. Un ECU confirmé doit exécuter la version cible.
6. Une dépendance doit réussir avant le démarrage de l'ECU dépendant.
7. Un graphe contenant un cycle doit être rejeté.
8. Le nombre total d'ECU d'une campagne doit être égal à 28.
9. La campagne nominale doit respecter un budget simulé de 90 secondes.
10. Chaque événement doit identifier sa source réelle ou simulée.
## Extension pour les scénarios de rollback

Les états ECU contiennent deux champs supplémentaires :

- `rollback_trigger` : identifiant du défaut ayant provoqué le rejet ou le rollback, par exemple `RB-01` ou `RB-04` ;
- `last_rollback_duration_s` : durée simulée du dernier rollback en secondes.

Pour une mise à jour nominale, les deux champs valent `null`.

Pour `RB-01`, la mise à jour est rejetée avant l'installation. Aucun rollback de partition n'est nécessaire.

Pour `RB-04`, le self-test échoue après le redémarrage sur le nouveau slot. L'ECU réactive alors son ancien slot sans télécharger une seconde fois le logiciel.
