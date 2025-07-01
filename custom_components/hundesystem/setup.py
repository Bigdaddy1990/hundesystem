# custom_components/hundesystem/setup.py
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.entity_registry import async_get as async_get_registry
from homeassistant.helpers.area_registry import async_get as async_get_area_registry
from homeassistant.helpers.device_registry import async_get as async_get_device_registry
from homeassistant.helpers.entity_platform import async_get_platforms
from homeassistant.helpers import entity_component
from datetime import time

INPUT_BOOLEAN_DOMAIN = "input_boolean"
COUNTER_DOMAIN = "counter"

async def async_create_helpers(hass: HomeAssistant, name: str):
    """Erstellt alle erforderlichen Entitäten dynamisch, falls sie nicht existieren."""
    suffixes_boolean = [
        "feeding_morning",
        "feeding_lunch",
        "feeding_evening",
        "feeding_snack",
        "outside",
        "visitor_mode",
        "statistic_reset"
    ]
    suffixes_counter = [
        "feeding_morning",
        "feeding_lunch",
        "feeding_evening",
        "feeding_snack",
        "outside"
    ]

    for suffix in suffixes_boolean:
        entity_id = f"{INPUT_BOOLEAN_DOMAIN}.{name}_{suffix}"
        if not hass.states.get(entity_id):
            await hass.services.async_call(
                INPUT_BOOLEAN_DOMAIN,
                "turn_on",
                {"entity_id": entity_id},
                blocking=False,
            )
            hass.states.async_set(entity_id, "off", {"friendly_name": suffix.replace("_", " ").capitalize()})

    for suffix in suffixes_counter:
        entity_id = f"{COUNTER_DOMAIN}.{name}_{suffix}"
        if not hass.states.get(entity_id):
            hass.states.async_set(entity_id, "0", {
                "friendly_name": f"{suffix.replace('_', ' ').capitalize()} Counter",
                "unit_of_measurement": "x"
            })

    async def reset_counters(now):
        for suffix in suffixes_counter:
            entity_id = f"{COUNTER_DOMAIN}.{name}_{suffix}"
            if hass.states.get(entity_id):
                await hass.services.async_call(COUNTER_DOMAIN, "reset", {"entity_id": entity_id}, blocking=False)

    async_track_time_change(hass, reset_counters, hour=23, minute=59, second=0)
