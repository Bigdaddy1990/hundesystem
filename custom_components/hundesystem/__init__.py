"""The Hundesystem integration."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry
from homeassistant.helpers.storage import Store
from homeassistant.exceptions import ServiceValidationError

from .const import (
    DOMAIN,
    CONF_DOG_NAME,
    CONF_PUSH_DEVICES,
    CONF_PERSON_TRACKING,
    CONF_CREATE_DASHBOARD,
    SERVICE_TRIGGER_FEEDING_REMINDER,
    SERVICE_DAILY_RESET,
    SERVICE_SEND_NOTIFICATION,
    SERVICE_SET_VISITOR_MODE,
    SERVICE_LOG_ACTIVITY,
    MEAL_TYPES,
    ACTIVITY_TYPES,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
]

# Service schemas
TRIGGER_FEEDING_REMINDER_SCHEMA = vol.Schema({
    vol.Required("meal_type"): vol.In(MEAL_TYPES.keys()),
    vol.Optional("message"): cv.string,
})

SEND_NOTIFICATION_SCHEMA = vol.Schema({
    vol.Required("title"): cv.string,
    vol.Required("message"): cv.string,
    vol.Optional("target"): cv.string,
})

SET_VISITOR_MODE_SCHEMA = vol.Schema({
    vol.Required("enabled"): cv.boolean,
    vol.Optional("visitor_name"): cv.string,
})

LOG_ACTIVITY_SCHEMA = vol.Schema({
    vol.Required("activity_type"): vol.In(ACTIVITY_TYPES.keys()),
    vol.Optional("duration"): vol.Range(min=1, max=480),
    vol.Optional("notes"): cv.string,
})


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Hundesystem from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    # Store config data
    hass.data[DOMAIN][entry.entry_id] = {
        "config": entry.data,
        "store": Store(hass, 1, f"{DOMAIN}_{entry.data[CONF_DOG_NAME]}")
    }
    
    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Create helper entities
    await _setup_helper_entities(hass, entry)
    
    # Register services
    await _register_services(hass, entry)
    
    # Create dashboard if requested
    if entry.data.get(CONF_CREATE_DASHBOARD, True):
        await _create_dashboard(hass, entry)
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok


async def _setup_helper_entities(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Set up helper entities (input_boolean, counter, etc.)."""
    dog_name = entry.data[CONF_DOG_NAME]
    
    # Input boolean entities
    input_booleans = [
        f"feeding_morning",
        f"feeding_lunch", 
        f"feeding_evening",
        f"feeding_snack",
        f"outside",
        f"visitor_mode_input"
    ]
    
    # Counter entities  
    counters = [
        f"feeding_count",
        f"outside_count",
        f"activity_count"
    ]
    
    # Input datetime entities
    input_datetimes = [
        f"last_feeding_morning",
        f"last_feeding_lunch",
        f"last_feeding_evening",
        f"last_feeding_snack", 
        f"last_outside"
    ]
    
    # Input text entities
    input_texts = [
        f"notes",
        f"visitor_name",
        f"last_activity_notes"
    ]
    
    try:
        # Create input_boolean entities
        for entity in input_booleans:
            entity_id = f"input_boolean.{dog_name}_{entity}"
            if not hass.states.get(entity_id):
                await hass.services.async_call(
                    "input_boolean", "create",
                    {"name": f"{dog_name.title()} {entity.replace('_', ' ').title()}"},
                    blocking=True
                )
        
        # Create counter entities
        for entity in counters:
            entity_id = f"counter.{dog_name}_{entity}"
            if not hass.states.get(entity_id):
                await hass.services.async_call(
                    "counter", "create", 
                    {"name": f"{dog_name.title()} {entity.replace('_', ' ').title()}"},
                    blocking=True
                )
        
        # Create input_datetime entities
        for entity in input_datetimes:
            entity_id = f"input_datetime.{dog_name}_{entity}"
            if not hass.states.get(entity_id):
                await hass.services.async_call(
                    "input_datetime", "create",
                    {
                        "name": f"{dog_name.title()} {entity.replace('_', ' ').title()}",
                        "has_date": True,
                        "has_time": True
                    },
                    blocking=True
                )
        
        # Create input_text entities
        for entity in input_texts:
            entity_id = f"input_text.{dog_name}_{entity}"
            if not hass.states.get(entity_id):
                await hass.services.async_call(
                    "input_text", "create",
                    {
                        "name": f"{dog_name.title()} {entity.replace('_', ' ').title()}",
                        "max": 255 if "notes" in entity else 100
                    },
                    blocking=True
                )
                
    except Exception as err:
        _LOGGER.error("Error creating helper entities: %s", err)


async def _register_services(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Register services for the integration."""
    dog_name = entry.data[CONF_DOG_NAME]
    
    async def trigger_feeding_reminder(call: ServiceCall) -> None:
        """Handle feeding reminder service call."""
        meal_type = call.data["meal_type"]
        message = call.data.get("message", f"Zeit für {MEAL_TYPES[meal_type]}!")
        
        # Send notification
        await _send_notification(hass, entry, "🐶 Fütterungszeit", message)
        
        _LOGGER.info("Feeding reminder sent for %s: %s", dog_name, meal_type)
    
    async def daily_reset(call: ServiceCall) -> None:
        """Handle daily reset service call."""
        try:
            # Reset all feeding input_booleans
            for meal in ["morning", "lunch", "evening", "snack"]:
                entity_id = f"input_boolean.{dog_name}_feeding_{meal}"
                if hass.states.get(entity_id):
                    await hass.services.async_call(
                        "input_boolean", "turn_off",
                        {"entity_id": entity_id},
                        blocking=True
                    )
            
            # Reset outside status
            outside_entity = f"input_boolean.{dog_name}_outside"
            if hass.states.get(outside_entity):
                await hass.services.async_call(
                    "input_boolean", "turn_off",
                    {"entity_id": outside_entity},
                    blocking=True
                )
            
            # Reset counters
            for counter in ["feeding_count", "outside_count", "activity_count"]:
                entity_id = f"counter.{dog_name}_{counter}"
                if hass.states.get(entity_id):
                    await hass.services.async_call(
                        "counter", "reset",
                        {"entity_id": entity_id},
                        blocking=True
                    )
            
            _LOGGER.info("Daily reset completed for %s", dog_name)
            
        except Exception as err:
            _LOGGER.error("Error during daily reset: %s", err)
            raise ServiceValidationError(f"Daily reset failed: {err}")
    
    async def send_notification(call: ServiceCall) -> None:
        """Handle send notification service call."""
        title = call.data["title"]
        message = call.data["message"]
        target = call.data.get("target")
        
        await _send_notification(hass, entry, title, message, target)
    
    async def set_visitor_mode(call: ServiceCall) -> None:
        """Handle set visitor mode service call."""
        enabled = call.data["enabled"]
        visitor_name = call.data.get("visitor_name", "")
        
        # Set visitor mode input_boolean
        visitor_entity = f"input_boolean.{dog_name}_visitor_mode_input"
        if hass.states.get(visitor_entity):
            action = "turn_on" if enabled else "turn_off"
            await hass.services.async_call(
                "input_boolean", action,
                {"entity_id": visitor_entity},
                blocking=True
            )
        
        # Set visitor name
        if visitor_name:
            name_entity = f"input_text.{dog_name}_visitor_name"
            if hass.states.get(name_entity):
                await hass.services.async_call(
                    "input_text", "set_value",
                    {"entity_id": name_entity, "value": visitor_name},
                    blocking=True
                )
        
        _LOGGER.info("Visitor mode %s for %s", "enabled" if enabled else "disabled", dog_name)
    
    async def log_activity(call: ServiceCall) -> None:
        """Handle log activity service call."""
        activity_type = call.data["activity_type"]
        duration = call.data.get("duration", 0)
        notes = call.data.get("notes", "")
        
        # Increment activity counter
        counter_entity = f"counter.{dog_name}_activity_count"
        if hass.states.get(counter_entity):
            await hass.services.async_call(
                "counter", "increment",
                {"entity_id": counter_entity},
                blocking=True
            )
        
        # Update notes if provided
        if notes:
            notes_entity = f"input_text.{dog_name}_last_activity_notes"
            if hass.states.get(notes_entity):
                activity_note = f"{ACTIVITY_TYPES[activity_type]}"
                if duration:
                    activity_note += f" ({duration} min)"
                activity_note += f": {notes}"
                
                await hass.services.async_call(
                    "input_text", "set_value",
                    {"entity_id": notes_entity, "value": activity_note},
                    blocking=True
                )
        
        _LOGGER.info("Activity logged for %s: %s", dog_name, activity_type)
    
    # Register services
    hass.services.async_register(
        DOMAIN, SERVICE_TRIGGER_FEEDING_REMINDER, 
        trigger_feeding_reminder, TRIGGER_FEEDING_REMINDER_SCHEMA
    )
    
    hass.services.async_register(
        DOMAIN, SERVICE_DAILY_RESET,
        daily_reset
    )
    
    hass.services.async_register(
        DOMAIN, SERVICE_SEND_NOTIFICATION,
        send_notification, SEND_NOTIFICATION_SCHEMA
    )
    
    hass.services.async_register(
        DOMAIN, SERVICE_SET_VISITOR_MODE,
        set_visitor_mode, SET_VISITOR_MODE_SCHEMA
    )
    
    hass.services.async_register(
        DOMAIN, SERVICE_LOG_ACTIVITY,
        log_activity, LOG_ACTIVITY_SCHEMA
    )


async def _send_notification(
    hass: HomeAssistant, 
    entry: ConfigEntry, 
    title: str, 
    message: str, 
    target: str | None = None
) -> None:
    """Send notification via configured services."""
    push_devices = entry.data.get(CONF_PUSH_DEVICES, [])
    
    if not push_devices and not target:
        _LOGGER.warning("No push devices configured for notifications")
        return
    
    try:
        devices = [target] if target else push_devices
        
        for device in devices:
            await hass.services.async_call(
                "notify", device,
                {"title": title, "message": message},
                blocking=False
            )
        
        _LOGGER.debug("Notification sent: %s - %s", title, message)
        
    except Exception as err:
        _LOGGER.error("Error sending notification: %s", err)


async def _create_dashboard(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Create Lovelace dashboard for the dog."""
    dog_name = entry.data[CONF_DOG_NAME]
    
    # Dashboard creation logic would go here
    # This is a placeholder - you would need to implement the actual
    # dashboard creation using the Lovelace API
    
    _LOGGER.info("Dashboard creation requested for %s", dog_name)
