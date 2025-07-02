"""Hundesystem Integration für Home Assistant."""
import asyncio
import logging
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.typing import ConfigType
import homeassistant.helpers.config_validation as cv
from homeassistant.const import Platform

from .const import (
    DOMAIN,
    CONF_NAME,
    CONF_PUSH_DEVICES,
    CONF_PERSON_TRACKING,
    CONF_DASHBOARD,
    SERVICE_TRIGGER_FEEDING_REMINDER,
    SERVICE_DAILY_RESET,
    SERVICE_SEND_NOTIFICATION,
)
from .helpers import async_create_helpers
from .dashboard import async_create_dashboard

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.BUTTON]

# Service Schemas
SERVICE_TRIGGER_FEEDING_REMINDER_SCHEMA = vol.Schema({
    vol.Optional("meal_type", default="morning"): cv.string,
    vol.Optional("message"): cv.string,
})

SERVICE_SEND_NOTIFICATION_SCHEMA = vol.Schema({
    vol.Required("title"): cv.string,
    vol.Required("message"): cv.string,
})

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Hundesystem from configuration.yaml."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Hundesystem from config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    name = entry.data.get(CONF_NAME, "hund")
    push_devices = entry.data.get(CONF_PUSH_DEVICES, [])
    
    # Store configuration
    hass.data[DOMAIN][entry.entry_id] = {
        "config": entry.data,
        "name": name,
        "push_devices": push_devices,
        "person_tracking": entry.data.get(CONF_PERSON_TRACKING, True),
        "dashboard": entry.data.get(CONF_DASHBOARD, True),
    }
    
    # Create helper entities
    try:
        await async_create_helpers(hass, name)
        _LOGGER.info("Helper entities created for %s", name)
    except Exception as e:
        _LOGGER.error("Failed to create helpers: %s", e)
    
    # Create dashboard if requested
    if entry.data.get(CONF_DASHBOARD, True):
        try:
            await async_create_dashboard(hass, name)
        except Exception as e:
            _LOGGER.warning("Failed to create dashboard: %s", e)
    
    # Setup platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Register services
    await async_setup_services(hass, entry)
    
    _LOGGER.info("Hundesystem successfully set up for: %s", name)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Hundesystem config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        
        # Remove services if no other instances
        if not hass.data[DOMAIN]:
            services = [
                SERVICE_TRIGGER_FEEDING_REMINDER,
                SERVICE_DAILY_RESET,
                SERVICE_SEND_NOTIFICATION,
            ]
            for service in services:
                if hass.services.has_service(DOMAIN, service):
                    hass.services.async_remove(DOMAIN, service)
    
    return unload_ok

async def async_setup_services(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Setup services for the integration."""
    name = entry.data.get(CONF_NAME, "hund")
    push_devices = entry.data.get(CONF_PUSH_DEVICES, [])
    
    async def trigger_feeding_reminder(call: ServiceCall):
        """Service to trigger feeding reminder."""
        meal_type = call.data.get("meal_type", "morning")
        custom_message = call.data.get("message")
        
        if custom_message:
            message = custom_message
        else:
            meal_names = {
                "morning": "Frühstück",
                "lunch": "Mittagessen", 
                "evening": "Abendessen",
                "snack": "Leckerli"
            }
            meal_name = meal_names.get(meal_type, meal_type)
            message = f"🐶 Wurde {name.title()} schon gefüttert? ({meal_name})"
        
        await send_push_notification(hass, push_devices, "🐶 Fütterungserinnerung", message)
    
    async def daily_reset(call: ServiceCall):
        """Service for daily reset."""
        entities_to_reset = []
        
        # Input Boolean entities
        boolean_types = ["feeding_morning", "feeding_lunch", "feeding_evening", 
                        "feeding_snack", "outside", "visitor_mode"]
        for entity_type in boolean_types:
            entities_to_reset.append(f"input_boolean.{name}_{entity_type}")
        
        # Counter entities  
        counter_types = ["feeding_morning", "feeding_lunch", "feeding_evening",
                        "feeding_snack", "outside"]
        for entity_type in counter_types:
            entities_to_reset.append(f"counter.{name}_{entity_type}")
        
        # Reset counters
        counter_entities = [e for e in entities_to_reset if e.startswith("counter.")]
        if counter_entities:
            try:
                await hass.services.async_call(
                    "counter", "reset", {"entity_id": counter_entities}, blocking=True
                )
            except Exception as e:
                _LOGGER.error("Failed to reset counters: %s", e)
        
        # Reset input booleans
        boolean_entities = [e for e in entities_to_reset if e.startswith("input_boolean.")]
        if boolean_entities:
            try:
                await hass.services.async_call(
                    "input_boolean", "turn_off", {"entity_id": boolean_entities}, blocking=True
                )
            except Exception as e:
                _LOGGER.error("Failed to reset input booleans: %s", e)
        
        _LOGGER.info("Daily reset completed for %s", name)
        await send_push_notification(
            hass, push_devices, 
            "🐶 Hundesystem", 
            f"Tagesstatistiken für {name.title()} wurden zurückgesetzt"
        )
    
    async def send_notification_service(call: ServiceCall):
        """Service to send notifications."""
        title = call.data.get("title", "Hundesystem")
        message = call.data.get("message", "Benachrichtigung")
        
        await send_push_notification(hass, push_devices, title, message)
    
    # Register services
    hass.services.async_register(
        DOMAIN, SERVICE_TRIGGER_FEEDING_REMINDER, 
        trigger_feeding_reminder, SERVICE_TRIGGER_FEEDING_REMINDER_SCHEMA
    )
    hass.services.async_register(DOMAIN, SERVICE_DAILY_RESET, daily_reset)
    hass.services.async_register(
        DOMAIN, SERVICE_SEND_NOTIFICATION, 
        send_notification_service, SERVICE_SEND_NOTIFICATION_SCHEMA
    )

async def send_push_notification(hass: HomeAssistant, push_devices: list, title: str, message: str):
    """Send push notification to configured devices."""
    if not push_devices:
        _LOGGER.warning("No push devices configured")
        return
    
    for device in push_devices:
        try:
            service_name = device.replace("notify.", "") if device.startswith("notify.") else device
            await hass.services.async_call(
                "notify", service_name,
                {"title": title, "message": message},
                blocking=False
            )
            _LOGGER.debug("Notification sent to %s", device)
        except Exception as e:
            _LOGGER.error("Failed to send notification to %s: %s", device, e)