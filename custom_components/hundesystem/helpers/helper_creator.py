from homeassistant.helpers.entity_registry import async_entries_for_config_entry
from homeassistant.helpers.device_registry import async_get as async_get_device_registry
from homeassistant.const import STATE_HOME

async def get_all_door_sensors(hass):
    return [e.entity_id for e in hass.states.async_all() if "door" in e.entity_id or "tuersensor" in e.entity_id]

async def get_all_push_devices(hass):
    return [e.entity_id for e in hass.states.async_all() if e.entity_id.startswith("notify.")]

async def get_all_persons(hass):
    return [e.entity_id for e in hass.states.async_all() if e.entity_id.startswith("person.")]
