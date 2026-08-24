# API commune OTA multi-ECU

## 1. Objectif

L’API commune expose en lecture seule les résultats de la campagne OTA multi-ECU et l’état de la cible Yocto/RAUC sous QEMU.

Elle constitue l’interface entre :

```text
Simulation → Exports JSON/CSV ─┐
                              ├→ API → Dashboard
QEMU/RAUC réel → SSH ─────────┘
```

L’API utilise le mode `HYBRID`. Les données de campagne restent simulées et déterministes, tandis que les routes dédiées à QEMU lisent l’état réel de la cible Yocto/RAUC par SSH.

## 2. Technologies

L’API utilise :

- Python 3.12 ;
- FastAPI 0.141.1 ;
- Uvicorn 0.52.1 ;
- HTTPX2 2.9.1 pour les tests HTTP ;
- OpenAPI pour la documentation automatique.

Les dépendances sont installées dans l’environnement virtuel `.venv`.

## 3. Sources de données

L’API lit les fichiers suivants :

| Fichier | Contenu |
|---|---|
| `data/latest/campaign-summary.json` | Résumé complet de campagne |
| `data/latest/campaign-kpis.json` | KPI fonctionnels et temporels |
| `data/latest/ecu-results.csv` | États finaux des 28 ECU |
| `data/latest/wave-timing.csv` | Durées des cinq vagues |
| `data/latest/events.csv` | Événements de campagne |

Le chargeur `api/data_store.py` convertit les valeurs CSV en types JSON adaptés :

- nombres entiers ;
- nombres décimaux ;
- booléens ;
- listes de dépendances ;
- valeurs nulles.

## 4. Routes disponibles

| Méthode | Route | Description |
|---|---|---|
| `GET` | `/health` | État du service |
| `GET` | `/api/v1/campaign` | Résumé de campagne |
| `GET` | `/api/v1/kpis` | KPI de campagne |
| `GET` | `/api/v1/ecus` | Résultats des 28 ECU |
| `GET` | `/api/v1/waves` | Résultats des cinq vagues |
| `GET` | `/api/v1/events` | Événements de campagne |
| `GET` | `/api/v1/qemu-ecu` | État de la cible QEMU/RAUC |
| `GET` | `/api/v1/sources` | Description des sources hybrides |

Le contrat machine lisible est disponible dans :

```text
config/api-contract.json
```

## 5. Démarrage

Depuis la racine du projet :

```bash
source .venv/bin/activate

python -m uvicorn \
api.main:app \
--host 127.0.0.1 \
--port 8000
```

L’API devient disponible à l’adresse :

```text
http://127.0.0.1:8000
```

## 6. Documentation interactive

FastAPI génère automatiquement deux interfaces :

```text
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/redoc
```

Le contrat OpenAPI brut est disponible sur :

```text
http://127.0.0.1:8000/openapi.json
```

## 7. Exemples

Vérifier le service :

```bash
curl http://127.0.0.1:8000/health
```

Afficher les KPI :

```bash
curl http://127.0.0.1:8000/api/v1/kpis
```

Afficher les ECU :

```bash
curl http://127.0.0.1:8000/api/v1/ecus
```

## 8. Codes HTTP

| Code | Signification |
|---:|---|
| `200` | Données retournées correctement |
| `405` | Méthode d’écriture refusée |
| `500` | Fichier exporté absent ou invalide |

L’API ne fournit actuellement aucune route `POST`, `PUT`, `PATCH` ou `DELETE`.

## 9. Validation

La validation comprend :

- tests du contrat API ;
- tests du chargeur JSON/CSV ;
- tests des huit routes ;
- contrôle des types JSON ;
- contrôle OpenAPI ;
- contrôle du mode lecture seule ;
- exécution réelle avec Uvicorn.

Le projet contient actuellement 120 tests automatiques réussis.

Les preuves sont enregistrées dans :

```text
evidence/common-api-v1.json
evidence/qemu-rauc-hybrid-connector-v1.json
```

## 10. Limites

Cette version est destinée à une démonstration locale.

Elle ne comprend pas encore :

- authentification ;
- chiffrement TLS ;
- contrôle d’accès par rôle ;
- pagination des événements ;
- gestion de plusieurs cibles QEMU ;
- commande d’installation RAUC depuis l’API ;
- configuration CORS pour un dashboard sur une autre origine.

La connexion SSH actuelle est réservée au démonstrateur local. Une architecture de production nécessiterait une gestion sécurisée des identités, certificats et autorisations.
