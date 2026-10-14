SUMMARY = "Bundle RAUC signe contenant la version V2 du projet PFE OTA"
DESCRIPTION = "Mise a jour RAUC V2 destinee au slot rootfs inactif"
LICENSE = "MIT"

inherit bundle

RAUC_BUNDLE_FORMAT = "verity"
RAUC_BUNDLE_COMPATIBLE = "pfe-ota-qemux86-64"
RAUC_BUNDLE_VERSION = "2.0.0"
RAUC_BUNDLE_DESCRIPTION = "PFE OTA - Mise a jour V2 signee"

RAUC_META_SECTIONS = "pfe"
RAUC_META_pfe[release-id] = "pfe-ota-v2-release-001"

RAUC_BUNDLE_SLOTS = "rootfs"

RAUC_SLOT_rootfs = "pfe-ota-image"
RAUC_SLOT_rootfs[fstype] = "ext4"

RAUC_CERT_FILE = "${THISDIR}/../rauc/files/ca.cert.pem"
