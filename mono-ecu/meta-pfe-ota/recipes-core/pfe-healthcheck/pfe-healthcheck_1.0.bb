SUMMARY = "Automatic health check for the PFE OTA A/B system"
DESCRIPTION = "Validates the running slot and controls RAUC mark-good or mark-bad"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

SRC_URI = " \
    file://pfe-healthcheck \
    file://pfe-demo-app \
    file://pfe-healthcheck.init \
    file://pfe-ota-version \
"

S = "${WORKDIR}"

inherit update-rc.d

INITSCRIPT_NAME = "pfe-healthcheck"
INITSCRIPT_PARAMS = "start 99 2 3 4 5 . stop 01 0 1 6 ."

RDEPENDS:${PN} += "rauc"

do_install() {
    install -d ${D}${bindir}
    install -m 0755 ${WORKDIR}/pfe-healthcheck \
        ${D}${bindir}/pfe-healthcheck
    install -m 0755 ${WORKDIR}/pfe-demo-app \
        ${D}${bindir}/pfe-demo-app

    install -d ${D}${sysconfdir}
    install -m 0644 ${WORKDIR}/pfe-ota-version \
        ${D}${sysconfdir}/pfe-ota-version

    install -d ${D}${sysconfdir}/init.d
    install -m 0755 ${WORKDIR}/pfe-healthcheck.init \
        ${D}${sysconfdir}/init.d/pfe-healthcheck
}

FILES:${PN} += " \
    ${sysconfdir}/init.d/pfe-healthcheck \
"
