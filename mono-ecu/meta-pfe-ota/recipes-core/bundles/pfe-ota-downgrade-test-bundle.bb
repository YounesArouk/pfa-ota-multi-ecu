SUMMARY = "Old signed bundle used for RAUC downgrade rejection testing"
DESCRIPTION = "Validly signed bundle with an intentionally old version"
LICENSE = "MIT"

inherit bundle

RAUC_BUNDLE_FORMAT = "verity"
RAUC_BUNDLE_COMPATIBLE = "pfe-ota-qemux86-64"
RAUC_BUNDLE_VERSION = "1.0.0"
RAUC_BUNDLE_DESCRIPTION = "PFE OTA - Bundle ancien pour test anti-downgrade"

RAUC_BUNDLE_SLOTS = "rootfs"

RAUC_SLOT_rootfs = "pfe-ota-image"
RAUC_SLOT_rootfs[fstype] = "ext4"

RAUC_CERT_FILE = "${THISDIR}/../rauc/files/ca.cert.pem"
