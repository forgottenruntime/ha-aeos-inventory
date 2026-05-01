"""Constants for the Nedap AEOS Inventory integration."""
from __future__ import annotations

DOMAIN = "aeos_inventory"

CONF_HOST = "host"
CONF_PORT = "port"
CONF_USE_SSL = "use_ssl"
CONF_VERIFY_SSL = "verify_ssl"
CONF_API_KEY = "api_key"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_PORT = 8088
DEFAULT_USE_SSL = False
DEFAULT_VERIFY_SSL = True
DEFAULT_SCAN_INTERVAL = 300  # seconds

INVENTORY_PATH = "/aeosws/inventory"
HEALTH_PATH = "/healthz"

MANUFACTURER = "Nedap N.V."
