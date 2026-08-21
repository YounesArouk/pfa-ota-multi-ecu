# Campagne finale multi-défauts des 28 ECU

## 1. Identification

- Date de validation : 21 août 2026
- Campaign ID : `CMP-FINAL-MIXED-001`
- Release ID : `pfe-ota-vehicle-v3-final-mixed-001`
- Version véhicule cible : `3.0.0`
- Nombre d’ECU : 28
- Nombre de vagues : 5
- Type de données : simulation synthétique
- Statut de validation : `PASSED`

## 2. Objectif

Cette campagne vérifie que l’orchestrateur peut gérer simultanément une mise à jour nominale de plusieurs ECU, différents scénarios de défaut et le blocage automatique des ECU dont les prérequis ne sont pas confirmés.

Elle constitue le jeu de données de référence destiné aux futurs KPI, à l’API commune et au dashboard multi-ECU.

## 3. Défauts injectés

| ECU | Composant | Défaut | Résultat attendu |
|---|---|---|---|
| ECU-05 | Powertrain Domain Controller | RB-01 | Rejet du package après échec du checksum |
| ECU-11 | Brake Control Module | RB-04 | Rollback vers la partition précédente |
| ECU-17 | Front Radar | RB-18 | Verrouillage après deux rollbacks consécutifs |
| ECU-02 | Connectivity Unit EP150 | PFE-RECOVERY | Démarrage sur la partition Recovery |

## 4. Effet des dépendances

`ECU-06`, `ECU-07`, `ECU-08` et `ECU-09` dépendent de `ECU-05`.

Comme `ECU-05` est rejeté par `RB-01`, ces quatre ECU ne démarrent pas leur mise à jour et passent dans l’état `BLOCKED`.

Cette décision évite de mettre à jour des calculateurs dépendants lorsque leur contrôleur de domaine n’a pas été confirmé.

## 5. Résultats obtenus

| État final | Nombre |
|---|---:|
| CONFIRMED | 20 |
| REJECTED | 1 |
| ROLLED_BACK | 1 |
| BLOCKED | 4 |
| ROLLBACK_LOCKOUT | 1 |
| RECOVERY_BOOT | 1 |
| Total | 28 |

L’invariant suivant est respecté :

```text
20 + 1 + 1 + 4 + 1 + 1 = 28
