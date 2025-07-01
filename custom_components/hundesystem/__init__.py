import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

DOMAIN = "hundesystem"

async def async_setup(hass: HomeAssistant, config: dict):
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    hass.data.setdefault(DOMAIN, {})
    _LOGGER.debug("Hundesystem Setup gestartet")
    # Setup-Logik folgt
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    return True
