from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.components.utility_meter import DEFAULT_TARIFF
from homeassistant.const import CONF_NAME
from homeassistant.helpers.entity_component import async_update_entity
import logging

_LOGGER = logging.getLogger(__name__)
DOMAIN = "hundesystem"

# Utility-Meter-spezifische Datenstruktur
def _build_um_config(counter_entity: str, cycle: str, sensor_name: str):
    return {
        "source": counter_entity,
        "cycle": cycle,
        "name": sensor_name,
    }

async def async_setup_statistics(hass: HomeAssistant, dog_name: str):
    """Dynamisch utility_meter Sensoren registrieren."""
    dog_id = dog_name.lower().replace(" ", "_")
    cycles = ["daily", "weekly"]
    activities = ["walk", "feeding", "potty"]

    created = []

    for activity in activities:
        counter_id = f"counter.{activity}_{dog_id}"
        if not hass.states.get(counter_id):
            _LOGGER.warning("Zähler %s existiert nicht – überspringe", counter_id)
            continue

        for cycle in cycles:
            um_entity_id = f"sensor.{activity}s_{cycle}_{dog_id}"
            config = _build_um_config(counter_id, cycle, um_entity_id)

            # Simuliere Helper-Erstellung (Home Assistant native support wäre besser)
            await hass.services.async_call(
                "utility_meter",
                "calibrate",
                {
                    "entity_id": um_entity_id,
                    "value": hass.states.get(counter_id).state
                },
                blocking=True,
            )

            _LOGGER.info("Utility Meter Sensor %s für %s erstellt", um_entity_id, activity)
            created.append(um_entity_id)

    return created
