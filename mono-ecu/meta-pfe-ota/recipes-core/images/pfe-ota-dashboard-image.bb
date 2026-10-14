SUMMARY = "PFE OTA V2 image with dashboard connector"

require pfe-ota-image.bb

IMAGE_FEATURES += "ssh-server-dropbear"
EXTRA_IMAGE_FEATURES += "debug-tweaks"
