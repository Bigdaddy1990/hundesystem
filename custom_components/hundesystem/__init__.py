"""The Hundesystem integration."""
from __future__ import annotations

import asyncio
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
from homeassistant.helpers.event import async_track_time_change, async_track_state_change_event
from homeassistant.exceptions import ServiceValidationError

from .const import (
    DOMAIN,
    CONF_DOG_NAME,
    CONF_PUSH_DEVICES,
    CONF_PERSON_TRACKING,
    CONF_CREATE_DASHBOARD,
    CONF_DOOR_SENSOR,
    SERVICE_TRIGGER_FEEDING_REMINDER,
    SERVICE_DAILY_RESET,
    SERVICE_SEND_NOTIFICATION,
    SERVICE_SET_VISITOR_MODE,
    SERVICE_LOG_ACTIVITY,
    SERVICE_ADD_DOG,
    SERVICE_TEST_NOTIFICATION,
    MEAL_TYPES,
    ACTIVITY_TYPES,
    FEEDING_TYPES,
    ICONS,
)
from .helpers import async_create_helpers
from .dashboard import async_create_dashboard

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
    Platform.BUTTON,
]

# Service schemas
TRIGGER_FEEDING_REMINDER_SCHEMA = vol.Schema({
    vol.Required("meal_type"): vol.In(MEAL_TYPES.keys()),
    vol.Optional("message"): cv.string,
    vol.Optional("dog_name"): cv.string,
})

SEND_NOTIFICATION_SCHEMA = vol.Schema({
    vol.Required("title"): cv.string,
    vol.Required("message"): cv.string,
    vol.Optional("target"): cv.string,
    vol.Optional("dog_name"): cv.string,
    vol.Optional("data"): dict,
})

SET_VISITOR_MODE_SCHEMA = vol.Schema({
    vol.Required("enabled"): cv.boolean,
    vol.Optional("visitor_name"): cv.string,
    vol.Optional("dog_name"): cv.string,
})

LOG_ACTIVITY_SCHEMA = vol.Schema({
    vol.Required("activity_type"): vol.In(ACTIVITY_TYPES.keys()),
    vol.Optional("duration"): vol.Range(min=1, max=480),
    vol.Optional("notes"): cv.string,
    vol.Optional("dog_name"): cv.string,
})

ADD_DOG_SCHEMA = vol.Schema({
    vol.Required("dog_name"): cv.string,
    vol.Optional("push_devices"): [cv.string],
    vol.Optional("door_sensor"): cv.entity_id,
    vol.Optional("create_dashboard", default=True): cv.boolean,
})

TEST_NOTIFICATION_SCHEMA = vol.Schema({
    vol.Optional("dog_name"): cv.string,
})


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Hundesystem from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    dog_name = entry.data[CONF_DOG_NAME]
    
    # Store config data
    hass.data[DOMAIN][entry.entry_id] = {
        "config": entry.data,
        "dog_name": dog_name,
        "store": Store(hass, 1, f"{DOMAIN}_{dog_name}")
    }
    
    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Create helper entities
    await async_create_helpers(hass, dog_name, entry.data)
    
    # Create dashboard if requested
    if entry.data.get(CONF_CREATE_DASHBOARD, True):
        await async_create_dashboard(hass, dog_name, entry.data)
    
    # Register services (only once, not per dog)
    if len(hass.data[DOMAIN]) == 1:
        await _register_services(hass)
    
    # Setup daily reset automation
    await _setup_daily_reset(hass, dog_name)
    
    # Setup door sensor automation if configured
    door_sensor = entry.data.get(CONF_DOOR_SENSOR)
    if door_sensor:
        await _setup_door_sensor_automation(hass, dog_name, door_sensor)
    
    _LOGGER.info("Hundesystem successfully set up for: %s", dog_name)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
        
        # Remove services if no more instances
        if not hass.data[DOMAIN]:
            services = [
                SERVICE_TRIGGER_FEEDING_REMINDER,
                SERVICE_DAILY_RESET,
                SERVICE_SEND_NOTIFICATION,
                SERVICE_SET_VISITOR_MODE,
                SERVICE_LOG_ACTIVITY,
                SERVICE_ADD_DOG,
                SERVICE_TEST_NOTIFICATION,
            ]
            for service in services:
                if hass.services.has_service(DOMAIN, service):
                    hass.services.async_remove(DOMAIN, service)
    
    return unload_ok


async def _register_services(hass: HomeAssistant) -> None:
    """Register services for the integration."""
    
    async def trigger_feeding_reminder(call: ServiceCall) -> None:
        """Handle feeding reminder service call."""
        meal_type = call.data["meal_type"]
        message = call.data.get("message", f"🐶 Zeit für {MEAL_TYPES[meal_type]}!")
        dog_name = call.data.get("dog_name")
        
        # Get target config entries
        target_entries = []
        if dog_name:
            # Find specific dog
            for entry_id, data in hass.data[DOMAIN].items():
                if data["dog_name"] == dog_name:
                    target_entries.append(data)
                    break
        else:
            # All dogs
            target_entries = list(hass.data[DOMAIN].values())
        
        for entry_data in target_entries:
            config = entry_data["config"]
            dog = entry_data["dog_name"]
            
            # Update feeding datetime
            datetime_entity = f"input_datetime.{dog}_last_feeding_{meal_type}"
            if hass.states.get(datetime_entity):
                await hass.services.async_call(
                    "input_datetime", "set_datetime",
                    {
                        "entity_id": datetime_entity,
                        "datetime": datetime.now().isoformat()
                    },
                    blocking=True
                )
            
            # Send notification
            await _send_notification(hass, config, f"🍽️ Fütterungszeit - {dog.title()}", message)
            
            _LOGGER.info("Feeding reminder sent for %s: %s", dog, meal_type)
    
    async def daily_reset(call: ServiceCall) -> None:
        """Handle daily reset service call."""
        dog_name = call.data.get("dog_name")

        # Get target entries
        target_entries = []
        if dog_name:
            for entry_id, data in hass.data[DOMAIN].items():
                if data["dog_name"] == dog_name:
                    target_entries.append(data)
                    break
        else:
            target_entries = list(hass.data[DOMAIN].values())
        
        for entry_data in target_entries:
            dog = entry_data["dog_name"]
            config = entry_data["config"]
            
            try:
                # Reset all feeding input_booleans
                for meal in FEEDING_TYPES:
                    entity_id = f"input_boolean.{dog}_feeding_{meal}"
                    if hass.states.get(entity_id):
                        await hass.services.async_call(
                            "input_boolean", "turn_off",
                            {"entity_id": entity_id},
                            blocking=True
                        )
                
                # Reset activity booleans
                activity_entities = [
                    f"input_boolean.{dog}_outside",
                    f"input_boolean.{dog}_visitor_mode_input"
                ]
                
                for entity_id in activity_entities:
                    if hass.states.get(entity_id):
                        await hass.services.async_call(
                            "input_boolean", "turn_off",
                            {"entity_id": entity_id},
                            blocking=True
                        )
                
                # Reset counters
                counter_types = FEEDING_TYPES + ["outside", "activity"]
                for counter_type in counter_types:
                    entity_id = f"counter.{dog}_{counter_type}_count"
                    if hass.states.get(entity_id):
                        await hass.services.async_call(
                            "counter", "reset",
                            {"entity_id": entity_id},
                            blocking=True
                        )
                
                # Clear notes
                notes_entity = f"input_text.{dog}_notes"
                if hass.states.get(notes_entity):
                    await hass.services.async_call(
                        "input_text", "set_value",
                        {"entity_id": notes_entity, "value": ""},
                        blocking=True
                    )
                
                _LOGGER.info("Daily reset completed successfully for %s", dog_name or "all dogs")
                
                # Send confirmation
                await _send_notification(
                    hass, config,
                    f"🔄 Tagesreset - {dog.title()}", 
                    "Alle Statistiken wurden zurückgesetzt"
                )
                
            except Exception as err:
                _LOGGER.error("Daily reset failed for %s: %s", dog_name or "all dogs", err)
                raise ServiceValidationError(f"Daily reset failed for {dog}: {err}")
    
    async def send_notification(call: ServiceCall) -> None:
        """Handle send notification service call."""
        title = call.data["title"]
        message = call.data["message"]
        target = call.data.get("target")
        dog_name = call.data.get("dog_name")
        data = call.data.get("data", {})
        
        # Get target config
        if dog_name:
            config = None
            for entry_data in hass.data[DOMAIN].values():
                if entry_data["dog_name"] == dog_name:
                    config = entry_data["config"]
                    break
            
            if config:
                await _send_notification(hass, config, title, message, target, data)
        else:
            # Send to all dogs
            for entry_data in hass.data[DOMAIN].values():
                config = entry_data["config"]
                await _send_notification(hass, config, title, message, target, data)
    
    async def set_visitor_mode(call: ServiceCall) -> None:
        """Handle set visitor mode service call."""
        enabled = call.data["enabled"]
        visitor_name = call.data.get("visitor_name", "")
        dog_name = call.data.get("dog_name")
        
        # Get target dogs
        target_dogs = []
        if dog_name:
            target_dogs.append(dog_name)
        else:
            target_dogs = [data["dog_name"] for data in hass.data[DOMAIN].values()]
        
        for dog in target_dogs:
            # Set visitor mode input_boolean
            visitor_entity = f"input_boolean.{dog}_visitor_mode_input"
            if hass.states.get(visitor_entity):
                action = "turn_on" if enabled else "turn_off"
                await hass.services.async_call(
                    "input_boolean", action,
                    {"entity_id": visitor_entity},
                    blocking=True
                )
            
            # Set visitor name
            if visitor_name:
                name_entity = f"input_text.{dog}_visitor_name"
                if hass.states.get(name_entity):
                    await hass.services.async_call(
                        "input_text", "set_value",
                        {"entity_id": name_entity, "value": visitor_name},
                        blocking=True
                    )
            
            _LOGGER.info("Visitor mode %s for %s", "enabled" if enabled else "disabled", dog)
    
    async def log_activity(call: ServiceCall) -> None:
        """Handle log activity service call."""
        activity_type = call.data["activity_type"]
        duration = call.data.get("duration", 0)
        notes = call.data.get("notes", "")
        dog_name = call.data.get("dog_name")
        
        # Get target dogs
        target_dogs = []
        if dog_name:
            target_dogs.append(dog_name)
        else:
            target_dogs = [data["dog_name"] for data in hass.data[DOMAIN].values()]
        
        for dog in target_dogs:
            # Increment activity counter
            counter_entity = f"counter.{dog}_activity_count"
            if hass.states.get(counter_entity):
                await hass.services.async_call(
                    "counter", "increment",
                    {"entity_id": counter_entity},
                    blocking=True
                )
            
            # Update last activity datetime
            datetime_entity = f"input_datetime.{dog}_last_activity"
            if hass.states.get(datetime_entity):
                await hass.services.async_call(
                    "input_datetime", "set_datetime",
                    {
                        "entity_id": datetime_entity,
                        "datetime": datetime.now().isoformat()
                    },
                    blocking=True
                )
            
            # Update notes if provided
            if notes:
                notes_entity = f"input_text.{dog}_last_activity_notes"
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
            
            _LOGGER.info("Activity logged for %s: %s", dog, activity_type)
    
    async def add_dog(call: ServiceCall) -> None:
        """Handle add dog service call."""
        new_dog_name = call.data["dog_name"].lower().strip()
        push_devices = call.data.get("push_devices", [])
        door_sensor = call.data.get("door_sensor")
        create_dashboard = call.data.get("create_dashboard", True)
        
        # Check if dog already exists
        for entry_data in hass.data[DOMAIN].values():
            if entry_data["dog_name"] == new_dog_name:
                raise ServiceValidationError(f"Dog '{new_dog_name}' already exists")
        
        # Create new config entry data
        new_config = {
            CONF_DOG_NAME: new_dog_name,
            CONF_PUSH_DEVICES: push_devices,
            CONF_PERSON_TRACKING: True,
            CONF_CREATE_DASHBOARD: create_dashboard,
        }
        
        if door_sensor:
            new_config[CONF_DOOR_SENSOR] = door_sensor
        
        # Create helper entities
        await async_create_helpers(hass, new_dog_name, new_config)
        
        # Create dashboard if requested
        if create_dashboard:
            await async_create_dashboard(hass, new_dog_name, new_config)
        
        # Setup daily reset
        await _setup_daily_reset(hass, new_dog_name)
        
        # Setup door sensor if provided
        if door_sensor:
            await _setup_door_sensor_automation(hass, new_dog_name, door_sensor)
        
        _LOGGER.info("New dog added: %s", new_dog_name)
    
    async def test_notification(call: ServiceCall) -> None:
        """Handle test notification service call."""
        dog_name = call.data.get("dog_name")
        
        if dog_name:
            config = None
            for entry_data in hass.data[DOMAIN].values():
                if entry_data["dog_name"] == dog_name:
                    config = entry_data["config"]
                    break
            
            if config:
                await _send_notification(
                    hass, config,
                    f"🧪 Test - {dog_name.title()}", 
                    "Test-Benachrichtigung funktioniert! 🐶"
                )
        else:
            # Test all dogs
            for entry_data in hass.data[DOMAIN].values():
                config = entry_data["config"]
                dog = entry_data["dog_name"]
                await _send_notification(
                    hass, config,
                    f"🧪 Test - {dog.title()}", 
                    "Test-Benachrichtigung funktioniert! 🐶"
                )
    
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
    
    hass.services.async_register(
        DOMAIN, SERVICE_ADD_DOG,
        add_dog, ADD_DOG_SCHEMA
    )
    
    hass.services.async_register(
        DOMAIN, SERVICE_TEST_NOTIFICATION,
        test_notification, TEST_NOTIFICATION_SCHEMA
    )


async def _send_notification(
    hass: HomeAssistant, 
    config: dict, 
    title: str, 
    message: str, 
    target: str | None = None,
    data: dict | None = None
) -> None:
    """Send notification via configured services."""
    push_devices = config.get(CONF_PUSH_DEVICES, [])
    person_tracking = config.get(CONF_PERSON_TRACKING, False)
    
    # If person tracking is enabled, try to send to home persons first
    notification_targets = []
    
    if person_tracking and not target:
        # Get home persons
        for entity_id in hass.states.async_entity_ids("person"):
            state = hass.states.get(entity_id)
            if state and state.state == "home":
                person_name = entity_id.replace("person.", "")
                mobile_app = f"mobile_app_{person_name}"
                
                # Check if this mobile app service exists
                if hass.services.has_service("notify", mobile_app):
                    notification_targets.append(mobile_app)
    
    # Fallback to configured devices
    if not notification_targets:
        notification_targets = [target] if target else push_devices
    
    if not notification_targets:
        _LOGGER.warning("No notification targets available")
        return
    
    # Prepare notification data
    notification_data = {"title": title, "message": message}
    if data:
        notification_data["data"] = data
    
    try:
        for device in notification_targets:
            service_name = device.replace("notify.", "") if device.startswith("notify.") else device
            
            await hass.services.async_call(
                "notify", service_name,
                notification_data,
                blocking=False
            )
        
        _LOGGER.debug("Notification sent: %s - %s", title, message)
        
    except Exception as err:
        _LOGGER.error("Error sending notification: %s", err)


async def _setup_daily_reset(hass: HomeAssistant, dog_name: str) -> None:
    """Setup daily reset automation for a dog."""
    
    async def daily_reset_callback(now):
        """Daily reset callback."""
        try:
            await hass.services.async_call(
                DOMAIN, SERVICE_DAILY_RESET,
                {"dog_name": dog_name},
                blocking=True
            )
        except Exception as err:
            _LOGGER.error("Daily reset failed for %s: %s", dog_name, err)
    
    # Schedule daily reset at 23:59
    async_track_time_change(
        hass, daily_reset_callback,
        hour=23, minute=59, second=0
    )
    
    _LOGGER.info("Daily reset scheduled for %s at 23:59", dog_name)


async def _setup_door_sensor_automation(hass: HomeAssistant, dog_name: str, door_sensor: str) -> None:
    """Setup door sensor automation for a dog."""
    
    async def door_sensor_callback(entity_id, old_state, new_state):
        """Handle door sensor state changes."""
        if (new_state and new_state.state == "off" and 
            old_state and old_state.state == "on"):
            
            # Door closed - ask if dog was outside
            await asyncio.sleep(2)  # Wait a moment
            
            # Check if we should ask (avoid spam)
            last_ask_entity = f"input_datetime.{dog_name}_last_door_ask"
            last_ask_state = hass.states.get(last_ask_entity)
            
            should_ask = True
            if last_ask_state and last_ask_state.state not in ["unknown", "unavailable"]:
                try:
                    last_ask = datetime.fromisoformat(last_ask_state.state.replace("Z", "+00:00"))
                    if (datetime.now() - last_ask).total_seconds() < 300:  # 5 minutes
                        should_ask = False
                except ValueError:
                    pass
            
            if should_ask:
                # Update last ask time
                if hass.states.get(last_ask_entity):
                    await hass.services.async_call(
                        "input_datetime", "set_datetime",
                        {
                            "entity_id": last_ask_entity,
                            "datetime": datetime.now().isoformat()
                        }
                    )
                
                # Find config for this dog
                config = None
                for entry_data in hass.data[DOMAIN].values():
                    if entry_data["dog_name"] == dog_name:
                        config = entry_data["config"]
                        break
                
                if config:
                    # Send interactive notification
                    notification_data = {
                        "actions": [
                            {"action": f"dog_outside_yes_{dog_name}", "title": "✅ Ja"},
                            {"action": f"dog_outside_no_{dog_name}", "title": "❌ Nein"}
                        ]
                    }
                    
                    await _send_notification(
                        hass, config,
                        f"🚪 War {dog_name.title()} draußen?",
                        "Türsensor hat Bewegung erkannt. War der Hund draußen?",
                        data=notification_data
                    )
    
async def _setup_door_sensor_automation(hass: HomeAssistant, dog_name: str, door_sensor: str) -> None:
    """Setup door sensor automation for a dog."""
    
    async def door_sensor_callback(event):
        """Handle door sensor state changes."""
        # Get the new and old states from the event
        new_state = event.data.get("new_state")
        old_state = event.data.get("old_state")
        
        if (new_state and new_state.state == "off" and 
            old_state and old_state.state == "on"):
            
            # Door closed - ask if dog was outside
            await asyncio.sleep(2)  # Wait a moment
            
            # Check if we should ask (avoid spam)
            last_ask_entity = f"input_datetime.{dog_name}_last_door_ask"
            last_ask_state = hass.states.get(last_ask_entity)
            
            should_ask = True
            if last_ask_state and last_ask_state.state not in ["unknown", "unavailable"]:
                try:
                    last_ask = datetime.fromisoformat(last_ask_state.state.replace("Z", "+00:00"))
                    if (datetime.now() - last_ask).total_seconds() < 300:  # 5 minutes
                        should_ask = False
                except ValueError:
                    pass
            
            if should_ask:
                # Update last ask time
                if hass.states.get(last_ask_entity):
                    await hass.services.async_call(
                        "input_datetime", "set_datetime",
                        {
                            "entity_id": last_ask_entity,
                            "datetime": datetime.now().isoformat()
                        }
                    )
                
                # Find config for this dog
                config = None
                for entry_data in hass.data[DOMAIN].values():
                    if entry_data["dog_name"] == dog_name:
                        config = entry_data["config"]
                        break
                
                if config:
                    # Send interactive notification
                    notification_data = {
                        "actions": [
                            {"action": f"dog_outside_yes_{dog_name}", "title": "✅ Ja"},
                            {"action": f"dog_outside_no_{dog_name}", "title": "❌ Nein"}
                        ]
                    }
                    
                    await _send_notification(
                        hass, config,
                        f"🚪 War {dog_name.title()} draußen?",
                        "Türsensor hat Bewegung erkannt. War der Hund draußen?",
                        data=notification_data
                    )
    
    # KORRIGIERT: Verwende async_track_state_change_event anstatt async_track_state_change
    from homeassistant.helpers.event import async_track_state_change_event
    async_track_state_change_event(hass, [door_sensor], door_sensor_callback)
    
    _LOGGER.info("Door sensor automation set up for %s with sensor %s", dog_name, door_sensor)
