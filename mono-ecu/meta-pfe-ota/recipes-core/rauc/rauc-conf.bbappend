FILESEXTRAPATHS:prepend := "${THISDIR}/files:"

SRC_URI += " \
    file://pfe-anti-replay-pre \
    file://pfe-anti-replay-post \
"

do_install:append() {
    install -d ${D}${libexecdir}/rauc

    install -m 0755 ${WORKDIR}/pfe-anti-replay-pre \
        ${D}${libexecdir}/rauc/pfe-anti-replay-pre

    install -m 0755 ${WORKDIR}/pfe-anti-replay-post \
        ${D}${libexecdir}/rauc/pfe-anti-replay-post
}

FILES:${PN} += " \
    ${libexecdir}/rauc/pfe-anti-replay-pre \
    ${libexecdir}/rauc/pfe-anti-replay-post \
"
