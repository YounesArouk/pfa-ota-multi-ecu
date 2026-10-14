SUMMARY = "Fichier persistant GRUB pour le démonstrateur OTA A/B"
LICENSE = "CLOSED"

SRC_URI = "file://grubenv"

S = "${WORKDIR}"

inherit deploy

do_compile[noexec] = "1"

do_deploy() {
    install -Dm 0644 ${WORKDIR}/grubenv ${DEPLOYDIR}/pfe-grubenv
}

addtask deploy after do_compile before do_build
