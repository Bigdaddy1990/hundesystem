from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_component import async_update_entity
from homeassistant.helpers.entity_registry import async_get
from homeassistant.helpers.typing import ConfigType

from homeassistant.components.input_datetime import (
    DOMAIN as INPUT_DATETIME_DOMAIN
)
from homeassistant.components.input_boolean import (
    DOMAIN as INPUT_BOOLEAN_DOMAIN
)
from homeassistant.components.counter import (
    DOMAIN as COUNTER_DOMAIN
)

from homeassistant.util.dt import now

async def async_create_helpers_for_dog(hass: HomeAssistant, dog_id: str):
    """Erzeuge benötigte Helfer für Gassi, Fütterung, Geschäft, Besucher-Modus."""

    # Timestamp Helper (z.B. letzter Gassi)
    await hass.services.async_call(
        INPUT_DATETIME_DOMAIN,
        "set_datetime",
        {
            "entity_id": f"input_datetime.last_walk_{dog_id}",
            "timestamp": now().timestamp()
        },
        blocking=True
    )

    # Counter für tägliche Ereignisse
    for counter in ["feeding", "walk", "potty"]:
        await hass.services.async_call(
            COUNTER_DOMAIN,
            "configure",
            {
                "entity_id": f"counter.{counter}_{dog_id}",
                "initial": 0,
                "minimum": 0,
                "maximum": 20,
                "step": 1,
                "restore": True
            },
            blocking=True
        )

    # Boolean: Besucher-Modus für diesen Hund
    await hass.services.async_call(
        INPUT_BOOLEAN_DOMAIN,
        "turn_off",
        {
            "entity_id": f"input_boolean.visitor_mode_{dog_id}"
        },
        blocking=True
    )


    # Letzte Aktivität
    await hass.services.async_call(
        "input_text",
        "set_value",
        {
            "entity_id": f"input_text.last_activity_{dog_id}",
            "value": "Noch keine Aktivität"
        },
        blocking=True
    )
