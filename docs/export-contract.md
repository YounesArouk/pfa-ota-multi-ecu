# Contrat d’export des campagnes OTA

## 1. Objectif

Le module `simulator/exporter.py` transforme un résumé de campagne en fichiers JSON et CSV utilisables par l’API, les graphiques et le dashboard.

Les exports sont produits avec Python standard, sans dépendance externe.

## 2. Répertoire de référence

Les dernières données validées sont enregistrées dans `data/latest`.

Ce répertoire contient une campagne multi-défauts complète de 28 ECU.

## 3. Fichiers produits

| Fichier | Format | Contenu |
|---|---|---|
| `campaign-summary.json` | JSON | Résumé complet de campagne |
| `campaign-kpis.json` | JSON | KPI fonctionnels et temporels |
| `ecu-results.csv` | CSV | Un enregistrement par ECU |
| `wave-timing.csv` | CSV | Un enregistrement par vague |
| `events.csv` | CSV | Journal des événements |

## 4. Règles CSV

Les fichiers utilisent :

- l’encodage UTF-8 ;
- la virgule comme séparateur de colonnes ;
- une première ligne contenant les en-têtes ;
- le point comme séparateur décimal ;
- un ordre stable des ECU ;
- le caractère `|` pour séparer plusieurs identifiants dans une même cellule.

Les valeurs numériques restent numériques afin de permettre les calculs et les graphiques.

## 5. Colonnes ECU

Le fichier `ecu-results.csv` contient notamment :

- `campaign_id` ;
- `ecu_id` ;
- `name` ;
- `domain` ;
- `current_version` ;
- `target_version` ;
- `active_partition` ;
- `ota_status` ;
- `health_status` ;
- `progress_pct` ;
- `elapsed_s` ;
- `rollback_trigger` ;
- `rollback_counter` ;
- `rollback_lockout` ;
- `recovery_boot_counter` ;
- `dependencies`.

## 6. Colonnes des vagues

Le fichier `wave-timing.csv` contient :

- l’identifiant de campagne ;
- le numéro de vague ;
- le nombre d’ECU ;
- les identifiants ECU ;
- la durée simulée de la vague.

Les ECU d’une même vague sont considérés comme exécutés en parallèle.

## 7. Événements

Le fichier `events.csv` contient notamment :

- l’identifiant d’événement ;
- l’horodatage ;
- l’identifiant de campagne ;
- l’ECU concerné ;
- le niveau ;
- le code d’événement ;
- l’état OTA ;
- la progression ;
- le message ;
- le déclencheur de rollback.

## 8. KPI

Le fichier `campaign-kpis.json` contient :

- le nombre total d’ECU ;
- le nombre d’ECU confirmés et défaillants ;
- les taux de confirmation, rejet et rollback ;
- les taux de blocage, verrouillage et Recovery ;
- la durée totale ;
- l’utilisation du budget ;
- la marge ou le dépassement ;
- les durées moyenne, minimale et maximale ;
- le nombre de vagues ;
- le nombre d’événements.

## 9. Résultat de référence

La campagne `CMP-FINAL-MIXED-001` produit :

| KPI | Valeur |
|---|---:|
| ECU | 28 |
| Confirmés | 20 |
| Défaillants | 8 |
| Vagues | 5 |
| Événements | 65 |
| Durée | 99 s |
| Budget | 90 s |
| Utilisation du budget | 110 % |

Ces fichiers constituent la source de référence du futur dashboard.
