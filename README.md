# PFE OTA Multi-ECU Simulator

Simulation Python d'une campagne OTA sécurisée sur 28 ECU avec dépendances, stratégie A/B, rollback et dashboard.

## Contexte

La chaîne OTA mono-ECU réelle a été validée sous QEMU avec Yocto, RAUC, GRUB, signature, rollback, health check, anti-downgrade et anti-replay.

Ce projet indépendant étudie l'extension de cette chaîne à une architecture véhicule de 28 ECU.

## Architecture prévue

- Simulateur Python de 28 ECU
- Orchestrateur de campagne
- Détection des dépendances circulaires
- Rollback local et global
- Partition recovery simulée
- API commune
- Dashboard multi-ECU
- Connecteur vers le mono-ECU QEMU réel
- Démonstration hybride

## Référence mono-ECU

- Dépôt : /home/pfaota/pfe-ota-yocto/meta-pfe-ota
- Commit validé : 048ff33
- Tag : pfe-ota-mono-ecu-v2-validated

## Statut

Gate M1 : initialisation du projet multi-ECU.
