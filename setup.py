# custom_components/hundesystem/setup.py
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.template import Template
from homeassistant.helpers.entity_component import async_update_entity
from homeassistant.helpers.entity_platform import async_get_platforms
from homeassistant.util import slugify
from datetime import time
from homeassistant.helpers.event import async_track_time_change

DOMAIN = "hundesystem"

INPUT_BOOLEAN_PLATFORM = "input_boolean"
COUNTER_PLATFORM = "counter"

async def async_create_helpers(hass: HomeAssistant, name: str):
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

    # Input Booleans
    for suffix in suffixes_boolean:
        entity_id = f"input_boolean.{name}_{suffix}"
        if not hass.states.get(entity_id):
            await hass.services.async_call(
                "input_boolean", "toggle",
                {"entity_id": entity_id},
                blocking=False,
            )

    # Counter
    for suffix in suffixes_counter:
        entity_id = f"counter.{name}_{suffix}"
        if not hass.states.get(entity_id):
            await hass.services.async_call(
                "counter", "reset",
                {"entity_id": entity_id},
                blocking=False,
            )

    # Counter Reset um 23:59
    async def reset_counters(now):
        for suffix in suffixes_counter:
            counter_id = f"counter.{name}_{suffix}"
            if hass.states.get(counter_id):
                await hass.services.async_call(
                    "counter", "reset", {"entity_id": counter_id},
                    blocking=False
                )

    async_track_time_change(hass, reset_counters, hour=23, minute=59, second=0)
