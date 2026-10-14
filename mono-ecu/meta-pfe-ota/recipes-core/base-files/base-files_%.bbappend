FILESEXTRAPATHS:prepend := "${THISDIR}/files:"

SRC_URI += "file://pfe-fstab"

do_install:append() {
    install -d ${D}/boot
    install -d ${D}/data

    cat ${WORKDIR}/pfe-fstab >> ${D}${sysconfdir}/fstab
}
