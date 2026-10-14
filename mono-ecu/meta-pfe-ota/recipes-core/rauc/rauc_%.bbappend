# Désactive la validation automatique du slot au démarrage.
# Le futur pfe-healthcheck décidera entre mark-good et mark-bad.
RRECOMMENDS:${PN}:remove = "${PN}-mark-good"
