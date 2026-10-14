FILESEXTRAPATHS:prepend := "${THISDIR}/files:"

SRC_URI += "file://pfe-interfaces"

do_install:append() {
    install -m 0644 ${WORKDIR}/pfe-interfaces \
        ${D}${sysconfdir}/network/interfaces
}
