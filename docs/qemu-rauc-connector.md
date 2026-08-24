# Connecteur hybride QEMU / RAUC

## 1. Objectif

Le connecteur hybride relie la plateforme multi-ECU simulée à une cible Linux Yocto/RAUC réellement exécutée sous QEMU.

L’interface commune présente :

- une flotte synthétique de 28 ECU ;
- les KPI de la campagne simulée ;
- une cible Yocto/RAUC réelle ;
- la version installée ;
- le slot RAUC actif ;
- le résultat du health check ;
- l’état de la connexion SSH.

La cible QEMU reste séparée des compteurs de la campagne simulée.

## 2. Architecture

Le système utilise le mode `HYBRID`.

```text
Flotte de 28 ECU simulés
          |
          v
  Exports JSON et CSV
          |
          +----------------------+
                                 |
Cible réelle Yocto/RAUC         |
sous QEMU                       |
          |                      |
          v                      v
  Connecteur SSH --------> API FastAPI
                                 |
                                 v
                       Dashboard hybride
```

La flotte simulée et la cible réelle utilisent la même API, tout en restant deux sources distinctes.

## 3. Séparation des sources

La route suivante retourne uniquement les 28 ECU simulés :

```text
GET /api/v1/ecus
```

La cible réelle est exposée séparément par :

```text
GET /api/v1/qemu-ecu
```

La route suivante décrit les deux sources :

```text
GET /api/v1/sources
```

Cette séparation garantit que `QEMU-ECU-01` n’est pas compté comme un vingt-neuvième ECU dans les KPI simulés.

## 4. Référence mono-ECU

La chaîne Yocto/RAUC mono-ECU validée est conservée dans :

```text
/home/pfaota/pfe-ota-yocto/meta-pfe-ota
```

Référence protégée :

- commit : `048ff33` ;
- tag : `pfe-ota-mono-ecu-v2-validated`.

L’image dédiée au connecteur a été ajoutée sur :

- branche : `feature/v2-dashboard-connector` ;
- commit : `a19f3e3` ;
- image : `pfe-ota-dashboard-image`.

Cette image ajoute Dropbear SSH à la chaîne Yocto/RAUC validée.

## 5. Démarrage de QEMU

La cible réelle utilise :

- QEMU x86-64 ;
- la machine `q35` ;
- le firmware UEFI OVMF ;
- un disque WIC avec partitions A/B ;
- un overlay QCOW2 ;
- la redirection `127.0.0.1:2222` vers le port SSH 22 ;
- un journal série persistant.

OVMF est nécessaire parce que l’image WIC démarre avec EFI et GRUB.

L’overlay QCOW2 protège l’image WIC originale contre les modifications directes.

## 6. Lecture des données réelles

Le connecteur est implémenté dans :

```text
api/qemu_rauc_connector.py
```

Il lit par SSH :

```text
/etc/pfe-ota-version
/proc/cmdline
rauc status --output-format=json
```

Une session SSH unique regroupe les trois lectures. Cette optimisation réduit la latence et limite les risques de timeout.

## 7. États de la cible

Lorsque QEMU est disponible et que le slot actif est marqué `good`, le résultat contient notamment :

```text
ecu_id             QEMU-ECU-01
source_type         QEMU_REAL
current_version     2.0.0
active_partition    A
ota_status          CONFIRMED
health_status       GOOD
connected           true
```

Lorsque QEMU est arrêté ou inaccessible, le connecteur retourne un état contrôlé :

```text
active_partition    UNKNOWN
ota_status          BLOCKED
health_status       OFFLINE
connected           false
```

L’indisponibilité de QEMU ne provoque donc pas l’arrêt de l’API ni du dashboard.

## 8. Routes de l’API

Le connecteur ajoute deux routes en lecture seule :

| Méthode | Route | Rôle |
|---|---|---|
| `GET` | `/api/v1/qemu-ecu` | Retourne l’état de la cible QEMU/RAUC |
| `GET` | `/api/v1/sources` | Décrit la simulation et la cible réelle |

Les routes de campagne, KPI, ECU, vagues et événements restent associées à la flotte simulée de 28 ECU.

## 9. Intégration au dashboard

Le dashboard contient un panneau séparé intitulé :

```text
ECU Yocto / RAUC sous QEMU
```

Ce panneau affiche :

- la disponibilité de la cible ;
- l’identifiant `QEMU-ECU-01` ;
- la source `QEMU_REAL` ;
- la version Yocto ;
- le slot RAUC actif ;
- l’état OTA ;
- l’état de santé ;
- l’erreur du connecteur si la cible est hors ligne.

Les KPI du dashboard restent ceux des 28 ECU simulés.

## 10. Politique SSH

La connexion est limitée à la cible locale :

```text
root@127.0.0.1:2222
```

Le connecteur utilise notamment :

- `BatchMode=yes` ;
- `ConnectTimeout=3` ;
- un délai maximal d’exécution ;
- `StrictHostKeyChecking=no` ;
- `UserKnownHostsFile=/dev/null`.

Cette politique convient au démonstrateur QEMU local et éphémère. Elle ne doit pas être utilisée telle quelle en production.

## 11. Performance

La première implémentation ouvrait trois sessions SSH indépendantes. Certaines lectures duraient entre 5 et 30 secondes.

La version optimisée utilise une seule session SSH.

Mesures obtenues :

| Mesure | Durée |
|---|---:|
| Lecture directe 1 | 1,71 s |
| Lecture directe 2 | 1,86 s |
| Lecture directe 3 | 1,89 s |
| Endpoint QEMU pendant la preuve | 1,094 s |
| Endpoint sources pendant la preuve | 1,139 s |

## 12. Validation

La validation a confirmé :

- le démarrage UEFI de Yocto ;
- le démarrage du serveur Dropbear ;
- la communication SSH locale ;
- la lecture de la version `2.0.0` ;
- la détection du slot `A` ;
- le statut RAUC `good` ;
- l’état OTA `CONFIRMED` ;
- le health check `GOOD` ;
- la séparation entre 28 ECU simulés et `QEMU-ECU-01` ;
- le mode hors ligne contrôlé ;
- l’affichage réel dans le dashboard hybride.

La suite complète contient :

```text
Ran 120 tests
OK
```

## 13. Preuves

La preuve structurée est conservée dans :

```text
evidence/qemu-rauc-hybrid-connector-v1.json
```

Le journal série normalisé est conservé dans :

```text
evidence/qemu-rauc-hybrid-connector-v1.log
```

Son empreinte SHA-256 est :

```text
0cc3501efb6643e45409473479d76016d6dd9cf4c90f52201927147441a6ab1e
```

Le journal démontre notamment :

- le démarrage du noyau Linux ;
- le montage de la partition racine ;
- la configuration réseau ;
- le démarrage de Dropbear ;
- le succès du health check ;
- le marquage du slot actif comme `good`.

## 14. Limites actuelles

Le connecteur est en lecture seule : il supervise la cible, mais ne lance pas encore une installation RAUC depuis le dashboard.

Le lancement de QEMU repose encore sur une commande manuelle utilisant OVMF et un overlay QCOW2.

La politique SSH est adaptée au démonstrateur local, pas à un environnement de production.

Les prochaines améliorations concernent :

- l’automatisation du démarrage et de l’arrêt de QEMU ;
- la démonstration d’une mise à jour RAUC observée depuis le dashboard ;
- la préparation du scénario final de démonstration hybride.
