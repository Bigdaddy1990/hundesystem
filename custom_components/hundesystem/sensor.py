from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.typing import HomeAssistantType
from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from homeassistant.helpers.event import async_track_state_change_event

DOMAIN = "hundesystem"

STAT_TYPES = ["walk", "feeding", "potty"]
CYCLES = ["today", "week"]

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    return True  # not used

async def async_setup_entry(hass: HomeAssistantType, entry, async_add_entities):
    """Optional future support via config entry."""
    return True

async def async_setup(hass: HomeAssistantType, config: dict):
    """Initialisiert die Statistik-Sensoren zur Laufzeit."""
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    if "stat_sensors" not in hass.data[DOMAIN]:
        hass.data[DOMAIN]["stat_sensors"] = []

    return True
