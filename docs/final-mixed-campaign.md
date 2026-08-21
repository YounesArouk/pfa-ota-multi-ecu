# Campagne finale multi-défauts des 28 ECU

## 1. Identification

- Date de validation : 21 août 2026
- Campaign ID : `CMP-FINAL-MIXED-001`
- Release ID : `pfe-ota-vehicle-v3-final-mixed-001`
- Version véhicule cible : `3.0.0`
- Nombre d’ECU : 28
- Nombre de vagues : 5
- Source : simulation synthétique
- Statut de validation : `PASSED`

## 2. Objectif

Cette campagne vérifie que l’orchestrateur peut gérer simultanément des mises à jour nominales, plusieurs scénarios de défaut et le blocage automatique des ECU dont les prérequis ne sont pas confirmés.

Elle constitue le jeu de données de référence destiné aux KPI, à l’API commune et au dashboard multi-ECU.

## 3. Défauts injectés

| ECU | Composant | Défaut | Résultat attendu |
|---|---|---|---|
| ECU-05 | Powertrain Domain Controller | RB-01 | Rejet après échec du checksum |
| ECU-11 | Brake Control Module | RB-04 | Rollback vers la partition précédente |
| ECU-17 | Front Radar | RB-18 | Verrouillage après deux rollbacks |
| ECU-02 | Connectivity Unit EP150 | PFE-RECOVERY | Démarrage sur la partition Recovery |

## 4. Effet des dépendances

`ECU-06`, `ECU-07`, `ECU-08` et `ECU-09` dépendent de `ECU-05`.

Comme `ECU-05` est rejeté par `RB-01`, ces quatre ECU ne démarrent pas leur mise à jour et passent dans l’état `BLOCKED`.

Cette décision évite de mettre à jour des calculateurs dépendants lorsque leur contrôleur de domaine n’a pas été confirmé.

## 5. Résultats fonctionnels

| État final | Nombre |
|---|---:|
| CONFIRMED | 20 |
| REJECTED | 1 |
| ROLLED_BACK | 1 |
| BLOCKED | 4 |
| ROLLBACK_LOCKOUT | 1 |
| RECOVERY_BOOT | 1 |
| Total | 28 |

L’invariant `20 + 1 + 1 + 4 + 1 + 1 = 28` est respecté.

La progression finale est de 100 % et le statut global est `COMPLETED_WITH_FAILURES`.

Ce statut signifie que l’orchestrateur a terminé le traitement des 28 cibles, mais que certaines mises à jour n’ont pas été confirmées.

## 6. Résultats temporels

La campagne utilise le modèle temporel simulé `PFE_OTA_TIMING_V1`.

Les ECU d’une même vague sont considérés comme exécutés en parallèle. La durée d’une vague correspond donc à la durée maximale de ses ECU.

| KPI temporel | Campagne nominale | Campagne multi-défauts |
|---|---:|---:|
| Durée totale | 75 s | 99 s |
| Budget | 90 s | 90 s |
| Marge | 15 s | 0 s |
| Dépassement | 0 s | 9 s |
| Traitement cumulé ECU | 420 s | 378 s |
| Durée moyenne ECU | 15 s | 13,5 s |
| Durée maximale ECU | 15 s | 36 s |

La durée maximale de 36 secondes correspond à `ECU-17`, qui exécute deux cycles défaillants avant le verrouillage `RB-18`.

Le traitement cumulé de la campagne multi-défauts est inférieur à celui de la campagne nominale, car quatre ECU sont bloqués avant téléchargement.

## 7. Traçabilité

La campagne a produit :

- cinq vagues d’exécution ;
- 65 événements ;
- un état final pour chacun des 28 ECU ;
- un historique des défauts ;
- des durées individuelles par ECU ;
- des KPI temporels destinés au dashboard.

Les fichiers de preuve sont :

- `evidence/final-mixed-campaign-28-ecu-v1.json`
- `evidence/nominal-timing-kpis-v1.json`
- `evidence/mixed-timing-kpis-v1.json`

Les tests principaux sont :

- `tests/test_final_mixed_campaign.py`
- `tests/test_timing.py`
- `tests/test_orchestrator_timing.py`
- `tests/test_timing_contract.py`

## 8. Conclusion

La campagne démontre que l’orchestrateur peut combiner des mises à jour nominales, des rejets, des rollbacks, un verrouillage RB-18, un démarrage Recovery et des blocages par dépendance dans une flotte de 28 ECU.

Le modèle temporel démontre également l’effet des défauts sur la durée totale et sur le respect du budget de campagne.

Le comportement global est couvert par 78 tests automatiques.

## 9. Limites

Les durées sont simulées, accélérées et déterministes. Elles servent à valider le calcul des KPI, les vagues et le dépassement du budget. Elles ne représentent pas encore des mesures physiques effectuées sur un véhicule réel.

La cible Yocto/RAUC sous QEMU reste une source distincte qui sera connectée ultérieurement à l’API et au dashboard.

`PFE-RECOVERY` est un scénario interne au démonstrateur. Sa correspondance exacte avec une nomenclature externe devra être documentée séparément.
