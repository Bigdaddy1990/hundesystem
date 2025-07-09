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
    _LOGGER.info("=== HUNDESYSTEM SETUP START für %s ===", dog_name)
    
    # Store config data
    hass.data[DOMAIN][entry.entry_id] = {
        "config": entry.data,
        "dog_name": dog_name,
        "store": Store(hass, 1, f"{DOMAIN}_{dog_name}")
    }
    
    try:
        # Step 1: Create helper entities first
        _LOGGER.info("Step 1: Creating helper entities for %s", dog_name)
        await async_create_helpers_robust(hass, dog_name, entry.data)
        _LOGGER.info("Helper entities created successfully for %s", dog_name)
        
        # Step 2: Wait for entities to be ready
        _LOGGER.info("Step 2: Waiting for entities to be ready...")
        await asyncio.sleep(3)
        
        # Step 3: Set up platforms
        _LOGGER.info("Step 3: Setting up platforms for %s", dog_name)
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        _LOGGER.info("Platforms set up successfully for %s", dog_name)
        
        # Step 4: Create dashboard if requested
        if entry.data.get(CONF_CREATE_DASHBOARD, True):
            _LOGGER.info("Step 4: Creating dashboard for %s", dog_name)
            try:
                await async_create_dashboard(hass, dog_name, entry.data)
            except Exception as e:
                _LOGGER.warning("Dashboard creation failed for %s: %s", dog_name, e)
        
        # Step 5: Register services (only once)
        if len(hass.data[DOMAIN]) == 1:
            _LOGGER.info("Step 5: Registering services")
            await _register_services(hass)
        
        # Step 6: Setup automations
        _LOGGER.info("Step 6: Setting up automations for %s", dog_name)
        await _setup_daily_reset(hass, dog_name)
        
        door_sensor = entry.data.get(CONF_DOOR_SENSOR)
        if door_sensor:
            await _setup_door_sensor_automation(hass, dog_name, door_sensor)
        
        # Step 7: Verify setup
        _LOGGER.info("Step 7: Verifying setup for %s", dog_name)
        await _verify_setup(hass, dog_name)
        
        _LOGGER.info("=== HUNDESYSTEM SETUP COMPLETE für %s ===", dog_name)
        return True
        
    except Exception as e:
        _LOGGER.error("=== HUNDESYSTEM SETUP FAILED für %s: %s ===", dog_name, e, exc_info=True)
        return False


async def async_create_helpers_robust(hass: HomeAssistant, dog_name: str, config: dict) -> None:
    """Create helper entities with robust error handling."""
    
    helper_data = {
        # Input Booleans
        "input_boolean": [
            (f"{dog_name}_feeding_morning", "Frühstück", "mdi:weather-sunrise"),
            (f"{dog_name}_feeding_lunch", "Mittagessen", "mdi:weather-sunny"),
            (f"{dog_name}_feeding_evening", "Abendessen", "mdi:weather-sunset"),
            (f"{dog_name}_feeding_snack", "Leckerli", "mdi:food-croissant"),
            (f"{dog_name}_outside", "War draußen", "mdi:door-open"),
            (f"{dog_name}_poop_done", "Geschäft gemacht", "mdi:emoticon-poop"),
            (f"{dog_name}_visitor_mode_input", "Besuchsmodus", "mdi:account-group"),
            (f"{dog_name}_emergency_mode", "Notfallmodus", "mdi:alarm-light"),
            (f"{dog_name}_medication_given", "Medikament gegeben", "mdi:pill"),
            (f"{dog_name}_auto_reminders", "Automatische Erinnerungen", "mdi:bell-ring"),
            (f"{dog_name}_tracking_enabled", "Tracking aktiviert", "mdi:chart-line"),
            (f"{dog_name}_weather_alerts", "Wetter-Warnungen", "mdi:weather-partly-cloudy"),
        ],
        # Counter
        "counter": [
            (f"{dog_name}_feeding_morning_count", "Frühstück Zähler", "mdi:weather-sunrise"),
            (f"{dog_name}_feeding_lunch_count", "Mittagessen Zähler", "mdi:weather-sunny"),
            (f"{dog_name}_feeding_evening_count", "Abendessen Zähler", "mdi:weather-sunset"),
            (f"{dog_name}_feeding_snack_count", "Leckerli Zähler", "mdi:food-croissant"),
            (f"{dog_name}_outside_count", "Draußen Zähler", "mdi:door-open"),
            (f"{dog_name}_walk_count", "Gassi Zähler", "mdi:walk"),
            (f"{dog_name}_play_count", "Spiel Zähler", "mdi:tennis-ball"),
            (f"{dog_name}_training_count", "Training Zähler", "mdi:school"),
            (f"{dog_name}_poop_count", "Geschäft Zähler", "mdi:emoticon-poop"),
            (f"{dog_name}_activity_count", "Aktivitäten gesamt", "mdi:chart-line"),
        ],
        # Input DateTime
        "input_datetime": [
            (f"{dog_name}_feeding_morning_time", "Frühstück Zeit", True, False, "07:00:00", "mdi:weather-sunrise"),
            (f"{dog_name}_feeding_lunch_time", "Mittagessen Zeit", True, False, "12:00:00", "mdi:weather-sunny"),
            (f"{dog_name}_feeding_evening_time", "Abendessen Zeit", True, False, "18:00:00", "mdi:weather-sunset"),
            (f"{dog_name}_feeding_snack_time", "Leckerli Zeit", True, False, "15:00:00", "mdi:food-croissant"),
            (f"{dog_name}_last_outside", "Letzter Gartengang", True, True, None, "mdi:door-open"),
            (f"{dog_name}_last_feeding_morning", "Letztes Frühstück", True, True, None, "mdi:weather-sunrise"),
            (f"{dog_name}_last_feeding_lunch", "Letztes Mittagessen", True, True, None, "mdi:weather-sunny"),
            (f"{dog_name}_last_feeding_evening", "Letztes Abendessen", True, True, None, "mdi:weather-sunset"),
            (f"{dog_name}_last_feeding_snack", "Letztes Leckerli", True, True, None, "mdi:food-croissant"),
            (f"{dog_name}_last_activity", "Letzte Aktivität", True, True, None, "mdi:chart-line"),
            (f"{dog_name}_last_door_ask", "Letzte Türfrage", True, True, None, "mdi:door"),
            (f"{dog_name}_next_vet_appointment", "Nächster Tierarzttermin", True, True, None, "mdi:medical-bag"),
            (f"{dog_name}_medication_time", "Medikamentenzeit", True, False, "08:00:00", "mdi:pill"),
        ],
        # Input Text
        "input_text": [
            (f"{dog_name}_notes", "Notizen", 255, "mdi:note-text"),
            (f"{dog_name}_visitor_name", "Besuchername", 100, "mdi:account-group"),
            (f"{dog_name}_health_notes", "Gesundheitsnotizen", 255, "mdi:heart-pulse"),
            (f"{dog_name}_emergency_contact", "Notfallkontakt", 200, "mdi:phone-alert"),
            (f"{dog_name}_vet_contact", "Tierarzt Kontakt", 200, "mdi:medical-bag"),
            (f"{dog_name}_last_activity_notes", "Letzte Aktivität Notizen", 255, "mdi:note-text"),
            (f"{dog_name}_medication_notes", "Medikamenten Notizen", 255, "mdi:pill"),
        ],
        # Input Number
        "input_number": [
            (f"{dog_name}_weight", "Gewicht", 0.1, 0, 100, 10, "kg", "mdi:weight-kilogram"),
            (f"{dog_name}_health_score", "Gesundheits Score", 1, 0, 10, 8, "points", "mdi:heart-pulse"),
            (f"{dog_name}_temperature", "Körpertemperatur", 0.1, 35, 42, 38.5, "°C", "mdi:thermometer"),
            (f"{dog_name}_energy_level", "Energie Level", 1, 0, 10, 7, "points", "mdi:flash"),
        ],
        # Input Select
        "input_select": [
            (f"{dog_name}_health_status", "Gesundheitsstatus", 
             ["Ausgezeichnet", "Gut", "Normal", "Schwach", "Krank", "Notfall"], 
             "Gut", "mdi:heart-pulse"),
            (f"{dog_name}_mood", "Stimmung", 
             ["Sehr glücklich", "Glücklich", "Neutral", "Gestresst", "Ängstlich", "Krank"], 
             "Glücklich", "mdi:emoticon-happy"),
            (f"{dog_name}_energy_level_category", "Energie Level", 
             ["Sehr müde", "Müde", "Normal", "Energiegeladen", "Hyperaktiv"], 
             "Normal", "mdi:flash"),
            (f"{dog_name}_appetite_level", "Appetit Level", 
             ["Kein Appetit", "Wenig Appetit", "Normal", "Guter Appetit", "Sehr hungrig"], 
             "Normal", "mdi:food-variant"),
        ],
    }
    
    for domain, entities in helper_data.items():
        await _create_helpers_for_domain(hass, domain, entities, dog_name)


async def _create_helpers_for_domain(hass: HomeAssistant, domain: str, entities: list, dog_name: str) -> None:
    """Create helpers for a specific domain."""
    
    created_count = 0
    skipped_count = 0
    failed_count = 0
    
    for entity_data in entities:
        entity_name = entity_data[0]
        friendly_name = entity_data[1]
        entity_id = f"{domain}.{entity_name}"
        
        # Skip if already exists
        if hass.states.get(entity_id):
            _LOGGER.debug("Entity %s already exists, skipping", entity_id)
            skipped_count += 1
            continue
        
        try:
            service_data = {
                "name": f"{dog_name.title()} {friendly_name}",
            }
            
            # Domain-specific parameters
            if domain == "input_boolean":
                icon = entity_data[2] if len(entity_data) > 2 else "mdi:dog"
                service_data["icon"] = icon
                
            elif domain == "counter":
                icon = entity_data[2] if len(entity_data) > 2 else "mdi:counter"
                service_data.update({
                    "initial": 0,
                    "step": 1,
                    "minimum": 0,
                    "icon": icon
                })
                
            elif domain == "input_datetime":
                has_time, has_date, initial = entity_data[2], entity_data[3], entity_data[4]
                icon = entity_data[5] if len(entity_data) > 5 else "mdi:calendar-clock"
                service_data.update({
                    "has_time": has_time,
                    "has_date": has_date,
                    "icon": icon
                })
                if initial:
                    service_data["initial"] = initial
                    
            elif domain == "input_text":
                max_length = entity_data[2]
                icon = entity_data[3] if len(entity_data) > 3 else "mdi:text"
                service_data.update({
                    "max": max_length,
                    "initial": "",
                    "icon": icon
                })
                
            elif domain == "input_number":
                step, min_val, max_val, initial, unit = entity_data[2:7]
                icon = entity_data[7] if len(entity_data) > 7 else "mdi:numeric"
                service_data.update({
                    "min": min_val,
                    "max": max_val,
                    "step": step,
                    "initial": initial,
                    "unit_of_measurement": unit,
                    "icon": icon
                })
                
            elif domain == "input_select":
                options, initial = entity_data[2], entity_data[3]
                icon = entity_data[4] if len(entity_data) > 4 else "mdi:format-list-bulleted"
                service_data.update({
                    "options": options,
                    "initial": initial,
                    "icon": icon
                })
            
            # Service call with timeout
            await asyncio.wait_for(
                hass.services.async_call(domain, "create", service_data, blocking=True),
                timeout=15.0
            )
            
            _LOGGER.debug("Created %s: %s", domain, entity_id)
            created_count += 1
            await asyncio.sleep(0.2)  # Small delay between creations
            
        except asyncio.TimeoutError:
            _LOGGER.warning("Timeout creating %s: %s", domain, entity_id)
            failed_count += 1
        except Exception as e:
            _LOGGER.warning("Failed to create %s %s: %s", domain, entity_id, e)
            failed_count += 1
    
    _LOGGER.info("Domain %s for %s: %d created, %d skipped, %d failed", 
                 domain, dog_name, created_count, skipped_count, failed_count)


async def _verify_setup(hass: HomeAssistant, dog_name: str) -> None:
    """Verify that setup was successful."""
    
    # Check some key entities
    key_entities = [
        f"input_boolean.{dog_name}_feeding_morning",
        f"input_boolean.{dog_name}_outside",
        f"counter.{dog_name}_outside_count",
        f"input_text.{dog_name}_notes",
    ]
    
    existing_entities = []
    missing_entities = []
    
    for entity_id in key_entities:
        if hass.states.get(entity_id):
            existing_entities.append(entity_id)
        else:
            missing_entities.append(entity_id)
    
    _LOGGER.info("Setup verification for %s: %d/%d entities exist", 
                 dog_name, len(existing_entities), len(key_entities))
    
    if missing_entities:
        _LOGGER.warning("Missing entities for %s: %s", dog_name, missing_entities)
    
    # Send setup notification
    status = "✅ Erfolgreich" if not missing_entities else "⚠️ Teilweise"
    await hass.services.async_call(
        "persistent_notification", "create",
        {
            "title": f"🐶 Hundesystem für {dog_name.title()}",
            "message": f"""
Setup {status} abgeschlossen!

**Erstellte Entitäten:** {len(existing_entities)}/{len(key_entities)}

**Verfügbare Services:**
- hundesystem.trigger_feeding_reminder
- hundesystem.daily_reset  
- hundesystem.test_notification

**Nächste Schritte:**
Gehen Sie zu Einstellungen > Geräte & Dienste > Hundesystem um alle Entitäten zu sehen.
            """,
            "notification_id": f"hundesystem_setup_{dog_name}"
        },
        blocking=False
    )


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
                    f"input_boolean.{dog}_poop_done",
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
                counter_types = FEEDING_TYPES + ["outside", "walk", "play", "training", "poop", "activity"]
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
                
                _LOGGER.info("Daily reset completed for %s", dog)
                
                # Send confirmation
                await _send_notification(
                    hass, config,
                    f"🔄 Tagesreset - {dog.title()}", 
                    "Alle Statistiken wurden zurückgesetzt"
                )
                
            except Exception as err:
                _LOGGER.error("Error during daily reset for %s: %s", dog, err)
    
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
            counter_entity = f"counter.{dog}_{activity_type}_count"
            if hass.states.get(counter_entity):
                await hass.services.async_call(
                    "counter", "increment",
                    {"entity_id": counter_entity},
                    blocking=True
                )
            
            # Increment general activity counter
            general_counter = f"counter.{dog}_activity_count"
            if hass.states.get(general_counter):
                await hass.services.async_call(
                    "counter", "increment",
                    {"entity_id": general_counter},
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
    
    # Add persistent notification as fallback
    if not notification_targets:
        notification_targets = ["persistent_notification"]
    
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
    
    # KORRIGIERT: Verwende async_track_state_change_event
    async_track_state_change_event(hass, [door_sensor], door_sensor_callback)
    
    _LOGGER.info("Door sensor automation set up for %s with sensor %s", dog_name, door_sensor)
