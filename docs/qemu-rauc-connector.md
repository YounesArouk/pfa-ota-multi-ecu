# Connecteur hybride QEMU / RAUC

## 1. Objectif

Le connecteur hybride relie le simulateur Python multi-ECU à la chaîne Yocto/RAUC exécutée sous QEMU.

L’objectif est de présenter dans une interface commune :

- une flotte synthétique de 28 ECU ;
- une cible Linux Yocto/RAUC réellement exécutée sous QEMU ;
- les KPI de la campagne simulée ;
- l’état réel du slot RAUC actif ;
- la version installée sur la cible ;
- le résultat du health check.

La cible QEMU reste séparée des compteurs de la campagne simulée.

## 2. Architecture

```text
28 ECU simulés
        |
        v
Exports JSON/CSV
        |
        +----------------------+
                               |
Cible QEMU Yocto/RAUC          |
        |                      |
        v                      v
Connecteur SSH ----------> API FastAPI
                               |
                               v
                     Dashboard hybride
