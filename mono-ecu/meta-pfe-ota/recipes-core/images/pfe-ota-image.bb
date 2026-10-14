SUMMARY = "Image Linux personnalisée du projet PFE OTA"
DESCRIPTION = "Première image Yocto du démonstrateur OTA sécurisé avec rollback A/B"
LICENSE = "MIT"

require recipes-core/images/core-image-minimal.bb

IMAGE_INSTALL:append = " iproute2 iputils rauc grub-editenv pfe-healthcheck"
# Génération de l’image disque partitionnée A/B
IMAGE_FSTYPES += "wic"

WKS_FILE = "pfe-ota-ab.wks"

WKS_SEARCH_PATH:prepend = "${THISDIR}/../../wic:"

# Le fstab est gere par base-files afin de rester identique dans
# l'image WIC initiale et dans le rootfs ext4 installe par RAUC.
WIC_CREATE_EXTRA_ARGS:append = " --no-fstab-update"

EFI_PROVIDER = "grub-efi"

WKS_FILE_DEPENDS:append = " grub-efi-native"
# Copie grubenv dans la partition EFI partagée par A et B
IMAGE_EFI_BOOT_FILES:append = " pfe-grubenv;EFI/BOOT/grubenv"

# Crée pfe-grubenv avant la génération de l'image WIC
do_image_wic[depends] += "pfe-bootfiles:do_deploy"
