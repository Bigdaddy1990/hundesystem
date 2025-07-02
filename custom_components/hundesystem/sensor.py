from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.template import TemplateSensor

DOMAIN = "hundesystem"

async def async_setup_statistics(hass: HomeAssistant, dog_name: str):
    """Optionaler Hook für zukünftige dynamische Sensor-Erzeugung."""
    # Diese Funktion kann für dynamisches Registrieren von Statistiksensoren verwendet werden.
    # Aktuell: Sensoren als template/utility_meter via YAML empfohlen.
    return True
