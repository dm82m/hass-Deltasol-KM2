""" Constants for the Resol KM1/KM2, DL2/DL3, VBus/LAN, VBus/USB component. """
import logging

_LOGGER = logging.getLogger('custom_components.deltasol')
DOMAIN = "deltasol"
DEFAULT_NAME = "Resol KM1/KM2, DL2/DL3, VBus/LAN, VBus/USB"
DEFAULT_TIMEOUT = 60

#Additional device attributes on sensors
ATTR_PRODUCT_DESCRIPTION = "Product Description"
ATTR_DESTINATION_NAME = "Destination Name"
ATTR_SOURCE_NAME = "Source Name"
ATTR_UNIQUE_ID = "Internal Unique ID"
ATTR_PRODUCT_SERIAL = "Product Serial"
ATTR_PRODUCT_NAME = "Product Name"
ATTR_PRODUCT_VENDOR = "Product Vendor"
ATTR_PRODUCT_BUILD = "Product Build"
ATTR_PRODUCT_VERSION = "Product Version"
ATTR_PRODUCT_FEATURES = "Product Features"
ATTR_LAST_UPDATED = "Last Updated"
