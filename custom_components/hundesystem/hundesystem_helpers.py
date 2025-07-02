"""Helper functions for creating entities."""
import logging
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import FEEDING_TYPES, ACTIVITY_TYPES, HELPER_TYPES, ICONS

_LOGGER = logging.getLogger(__name__)

async def async_create_helpers(hass: HomeAssistant, name: str):
    """Create helper entities for the dog system."""
    entity_registry = er.async_get(hass)
    
    # Create input_boolean entities
    boolean_suffixes = FEEDING_TYPES + ACTIVITY_TYPES + HELPER_TYPES
    
    for suffix in boolean_suffixes:
        entity_id = f"input_boolean.{name}_{suffix}"
        
        if not entity_registry.async_get(entity_id):
            try:
                friendly_name = f"{name.title()} {suffix.replace('_', ' ').title()}"
                icon = ICONS.get(suffix, ICONS["dog"])
                
                await hass.services.async_call(
                    "input_boolean", "create",
                    {
                        "name": friendly_name,
                        "icon": icon,
                    },
                    blocking=True
                )
                _LOGGER.debug("Created input_boolean: %s", entity_id)
            except Exception as e:
                _LOGGER.error("Failed to create input_boolean %s: %s", entity_id, e)
    
    # Create counter entities
    counter_suffixes = FEEDING_TYPES + ["outside"]
    
    for suffix in counter_suffixes:
        entity_id = f"counter.{name}_{suffix}"
        
        if not entity_registry.async_get(entity_id):
            try:
                friendly_name = f"{name.title()} {suffix.replace('_', ' ').title()} Count"
                icon = ICONS.get(suffix, ICONS["dog"])
                
                await hass.services.async_call(
                    "counter", "create",
                    {
                        "name": friendly_name,
                        "icon": icon,
                        "initial": 0,
                        "step": 1,
                    },
                    blocking=True
                )
                _LOGGER.debug("Created counter: %s", entity_id)
            except Exception as e:
                _LOGGER.error("Failed to create counter %s: %s", entity_id, e)
    
    # Create input_datetime for feeding times (optional for future use)
    datetime_suffixes = FEEDING_TYPES
    
    for suffix in datetime_suffixes:
        entity_id = f"input_datetime.{name}_{suffix}_time"
        
        if not entity_registry.async_get(entity_id):
            try:
                friendly_name = f"{name.title()} {suffix.replace('_', ' ').title()} Time"
                
                # Default times
                default_times = {
                    "morning": "07:00:00",
                    "lunch": "12:00:00", 
                    "evening": "18:00:00",
                    "snack": "15:00:00"
                }
                
                await hass.services.async_call(
                    "input_datetime", "create",
                    {
                        "name": friendly_name,
                        "has_time": True,
                        "has_date": False,
                        "initial": default_times.get(suffix, "12:00:00"),
                    },
                    blocking=True
                )
                _LOGGER.debug("Created input_datetime: %s", entity_id)
            except Exception as e:
                _LOGGER.error("Failed to create input_datetime %s: %s", entity_id, e)
    
    # Create input_text for additional notes/status
    try:
        entity_id = f"input_text.{name}_notes"
        if not entity_registry.async_get(entity_id):
            await hass.services.async_call(
                "input_text", "create",
                {
                    "name": f"{name.title()} Notes",
                    "max": 255,
                    "initial": "",
                },
                blocking=True
            )
            _LOGGER.debug("Created input_text: %s", entity_id)
    except Exception as e:
        _LOGGER.error("Failed to create input_text %s: %s", entity_id, e)
    
    _LOGGER.info("Helper entities creation completed for %s", name)