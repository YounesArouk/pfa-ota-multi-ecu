# Dashboard OTA multi-ECU

## 1. Objectif

Le dashboard fournit une vue de supervision de la campagne OTA simulée sur 28 ECU.

Il permet de consulter :

- l’état global de la campagne ;
- les KPI fonctionnels ;
- les KPI temporels ;
- la répartition des états OTA ;
- les durées des vagues ;
- les résultats détaillés des ECU ;
- le journal des événements.

## 2. Architecture

Le dashboard est servi par la même application FastAPI que l’API :

```text
Simulateur
    ↓
Exports JSON et CSV
    ↓
API FastAPI
    ↓
Dashboard HTML/CSS/JavaScript
```

L’adresse du dashboard est :

```text
http://127.0.0.1:8000/dashboard/
```

La route `/` redirige automatiquement vers `/dashboard/`.

L’API et le dashboard utilisent la même origine HTTP. Aucune configuration CORS supplémentaire n’est donc nécessaire.

## 3. Fichiers

| Fichier | Rôle |
|---|---|
| `dashboard/index.html` | Structure sémantique |
| `dashboard/styles.css` | Thème, graphiques et responsive |
| `dashboard/app.js` | Chargement et rendu des données |
| `dashboard/config.json` | Routes, états, couleurs et configuration |

Aucune bibliothèque JavaScript externe n’est nécessaire.

## 4. Données affichées

Le dashboard charge les routes suivantes :

| Route | Utilisation |
|---|---|
| `/health` | État de connexion |
| `/api/v1/campaign` | Identification et statut |
| `/api/v1/kpis` | KPI fonctionnels et temporels |
| `/api/v1/ecus` | Tableau des 28 ECU |
| `/api/v1/waves` | Graphique des cinq vagues |
| `/api/v1/events` | Journal des événements |

Les données sont actualisées automatiquement toutes les 10 secondes.

## 5. Résultat de référence

| KPI | Valeur |
|---|---:|
| ECU ciblés | 28 |
| ECU confirmés | 20 |
| ECU en échec | 8 |
| Taux de confirmation | 71,43 % |
| Taux d’échec | 28,57 % |
| Durée de campagne | 99 s |
| Budget | 90 s |
| Dépassement | 9 s |
| Événements | 65 |
| Vagues | 5 |

Répartition des états :

| État | Nombre |
|---|---:|
| `CONFIRMED` | 20 |
| `REJECTED` | 1 |
| `ROLLED_BACK` | 1 |
| `BLOCKED` | 4 |
| `ROLLBACK_LOCKOUT` | 1 |
| `RECOVERY_BOOT` | 1 |

Durées des vagues :

```text
15 s, 15 s, 36 s, 15 s, 18 s
```

## 6. Interactions

Le dashboard permet :

- l’actualisation manuelle ;
- l’actualisation automatique ;
- la recherche par identifiant, nom ou domaine ;
- le filtrage des ECU par état ;
- le filtrage des événements par niveau ;
- l’affichage des événements les plus récents en premier.

Les données insérées dans le HTML sont échappées avant leur affichage.

## 7. Convention visuelle

| État | Couleur |
|---|---|
| Confirmé | Vert |
| Rejeté | Rouge |
| Restauré | Orange |
| Bloqué | Gris |
| Verrouillé | Violet |
| Recovery | Cyan |

Le thème sombre représente une interface de supervision automobile et met en évidence les états critiques.

## 8. Démarrage

Depuis la racine du projet :

```bash
source .venv/bin/activate

python -m uvicorn \
api.main:app \
--host 127.0.0.1 \
--port 8000
```

Ouvrir ensuite :

```text
http://127.0.0.1:8000/dashboard/
```

## 9. Accessibilité et responsive

L’interface comprend :

- une structure HTML sémantique ;
- des libellés accessibles ;
- des styles de focus clavier ;
- un contraste adapté au thème sombre ;
- une prise en charge de `prefers-reduced-motion` ;
- une adaptation aux ordinateurs, tablettes et petits écrans ;
- des tableaux défilables horizontalement.

## 10. Validation

La validation couvre :

- les quatre ressources statiques ;
- la redirection depuis `/` ;
- les six routes API ;
- les identifiants HTML obligatoires ;
- l’unicité des identifiants ;
- l’absence de ressources externes ;
- les règles responsive ;
- les fonctions JavaScript principales ;
- le contrat de configuration ;
- l’exécution réelle avec Uvicorn et Firefox.

Le projet contient 113 tests automatiques réussis.

La preuve est disponible dans :

```text
evidence/multi-ecu-dashboard-v1.json
```

## 11. Limites

Cette version utilise un instantané de campagne exporté dans `data/latest`.

Elle ne comprend pas encore :

- données temps réel provenant de QEMU/RAUC ;
- authentification utilisateur ;
- gestion de plusieurs campagnes ;
- acquittement des alertes ;
- export depuis l’interface ;
- persistance des préférences utilisateur.

Ces fonctions pourront être ajoutées lors de l’intégration hybride.
