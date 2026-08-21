# PFE OTA Multi-ECU Simulator

Plateforme de simulation d’une campagne OTA sécurisée sur 28 ECU avec dépendances, partitions A/B, rollback, Recovery, KPI temporels, exports JSON/CSV et API REST.

## Contexte

La chaîne OTA mono-ECU réelle a été validée sous QEMU avec Yocto, RAUC, GRUB, signature numérique, health check, rollback, anti-downgrade et anti-replay.

Ce dépôt étudie l’extension de cette architecture à un véhicule simulé comportant 28 ECU.

## Architecture

```text
Inventaire 28 ECU
        ↓
Orchestrateur de campagne
        ↓
Modèle de défauts et de timing
        ↓
Exports JSON et CSV
        ↓
API REST FastAPI
        ↓
Dashboard multi-ECU
```

Les données sont actuellement simulées et identifiées par le mode `SIMULATION`.

## Fonctionnalités validées

- inventaire synthétique de 28 ECU ;
- dépendances entre ECU ;
- cinq vagues d’installation ;
- vérification de signature du manifeste ;
- partitions A/B et Recovery ;
- mise à jour nominale ;
- `RB-01` : checksum invalide ;
- `RB-04` : échec du self-test et rollback ;
- `RB-18` : verrouillage après deux rollbacks ;
- `PFE-RECOVERY` : démarrage Recovery si A et B sont invalides ;
- blocage des ECU dépendants ;
- modèle temporel déterministe ;
- KPI fonctionnels et temporels ;
- exports JSON et CSV ;
- API REST en lecture seule ;
- documentation OpenAPI ;
- preuves JSON reproductibles ;
- 100 tests automatiques.

## Résultat de référence

La campagne multi-défauts finale contient :

| État final | Nombre |
|---|---:|
| `CONFIRMED` | 20 |
| `REJECTED` | 1 |
| `ROLLED_BACK` | 1 |
| `BLOCKED` | 4 |
| `ROLLBACK_LOCKOUT` | 1 |
| `RECOVERY_BOOT` | 1 |
| Total | 28 |

Sa durée simulée est de 99 secondes pour un budget de 90 secondes.

## Installation de l’API

Créer et activer l’environnement virtuel :

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Installer les dépendances :

```bash
python -m pip install \
-r requirements.txt
```

## Démarrage de l’API

```bash
python -m uvicorn \
api.main:app \
--host 127.0.0.1 \
--port 8000
```

Documentation interactive :

```text
http://127.0.0.1:8000/docs
```

## Routes principales

| Méthode | Route |
|---|---|
| `GET` | `/health` |
| `GET` | `/api/v1/campaign` |
| `GET` | `/api/v1/kpis` |
| `GET` | `/api/v1/ecus` |
| `GET` | `/api/v1/waves` |
| `GET` | `/api/v1/events` |

La documentation détaillée se trouve dans `docs/common-api.md`.

## Tests

Avec `.venv` activé :

```bash
python -W error -m unittest \
discover -s tests -v
```

Résultat validé :

```text
Ran 100 tests
OK
```

## Données de référence

Les données destinées à l’API et au futur dashboard sont dans :

```text
data/latest/
```

Ce répertoire contient :

- `campaign-summary.json` ;
- `campaign-kpis.json` ;
- `ecu-results.csv` ;
- `wave-timing.csv` ;
- `events.csv`.

## Structure principale

```text
api/         API REST et chargeur de données
config/      contrats et configurations
data/        inventaire et exports de référence
dashboard/   futur dashboard multi-ECU
docs/        documentation technique
evidence/    preuves JSON
simulator/   ECU, orchestrateur, timing et exporteur
tests/       tests automatiques
```

## Référence mono-ECU réelle

- dépôt : `/home/pfaota/pfe-ota-yocto/meta-pfe-ota` ;
- commit validé : `048ff33` ;
- tag : `pfe-ota-mono-ecu-v2-validated`.

## Jalons Git multi-ECU

- `additional-faults-pass-v1` ;
- `final-mixed-campaign-pass-v1` ;
- `simulated-timing-kpis-pass-v1` ;
- `campaign-exports-pass-v1`.

## Prochaines étapes

- développer le dashboard multi-ECU ;
- connecter le dashboard à l’API ;
- ajouter le connecteur vers la cible QEMU/RAUC ;
- préparer la démonstration hybride.
