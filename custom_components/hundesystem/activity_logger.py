from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.typing import ConfigType
from homeassistant.util.dt import now

from .const import DOMAIN


async def async_log_activity(hass: HomeAssistant, dog_name: str, activity_type: str):
    """Logge eine Hundeaktivität für Statistikzwecke."""
    dog_id = dog_name.lower().replace(" ", "_")

    # Counter aktualisieren
    counter_entity = f"counter.{activity_type}_{dog_id}"
    if counter_entity in hass.states.async_entity_ids("counter"):
        await hass.services.async_call("counter", "increment", {"entity_id": counter_entity})

    # Zeit speichern, falls Gassi
    if activity_type == "walk":
        await hass.services.async_call(
            "input_datetime",
            "set_datetime",
            {
                "entity_id": f"input_datetime.last_walk_{dog_id}",
                "timestamp": now().timestamp()
            }
        )


    # Letzte Aktivität updaten
    readable = {
        "walk": "Gassi",
        "feeding": "Fütterung",
        "potty": "Geschäft"
    }
    label = readable.get(activity_type, activity_type)
    from datetime import datetime
    now_str = datetime.now().strftime("%H:%M")
    await hass.services.async_call(
        "input_text",
        "set_value",
        {
            "entity_id": f"input_text.last_activity_{dog_id}",
            "value": f"{now_str} – {label}"
        }
    )
