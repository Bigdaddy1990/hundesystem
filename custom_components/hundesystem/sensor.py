"""Sensor platform for Hundesystem."""
import logging
from datetime import datetime, timedelta

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.const import STATE_ON, STATE_OFF

from .const import DOMAIN, CONF_NAME, FEEDING_TYPES, ICONS, MEAL_TRANSLATIONS

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Hundesystem sensors."""
    name = config_entry.data.get(CONF_NAME, "hund")
    
    entities = []
    
    # Status sensor
    entities.append(HundeStatusSensor(hass, name))
    
    # Feeding status sensor
    entities.append(HundeFeedingStatusSensor(hass, name))
    
    # Activity sensor
    entities.append(HundeActivitySensor(hass, name))
    
    # Daily summary sensor
    entities.append(HundeDailySummarySensor(hass, name))
    
    # Last activity sensor
    entities.append(HundeLastActivitySensor(hass, name))
    
    async_add_entities(entities)

class HundeStatusSensor(SensorEntity):
    """Sensor for overall dog status."""
    
    def __init__(self, hass: HomeAssistant, name: str):
        """Initialize the sensor."""
        self.hass = hass
        self._name = name
        self._attr_name = f"{name.title()} Status"
        self._attr_unique_id = f"{name}_status"
        self._attr_icon = ICONS["status"]
        self._attr_device_class = None
        
        # Track relevant entities
        self._tracked_entities = []
        for feeding_type in FEEDING_TYPES:
            self._tracked_entities.append(f"input_boolean.{name}_feeding_{feeding_type}")
        self._tracked_entities.append(f"input_boolean.{name}_outside")
        self._tracked_entities.append(f"input_boolean.{name}_visitor_mode")
        
        self._update_state()
    
    async def async_added_to_hass(self):
        """Register callbacks."""
        @callback
        def sensor_state_listener(event):
            """Handle state changes."""
            self._update_state()
            self.async_write_ha_state()
        
        # Track state changes
        self.async_on_remove(
            async_track_state_change_event(
                self.hass, self._tracked_entities, sensor_state_listener
            )
        )
    
    def _update_state(self):
        """Update the sensor state."""
        fed_count = 0
        total_feedings = len(FEEDING_TYPES)
        
        for feeding_type in FEEDING_TYPES:
            entity_id = f"input_boolean.{self._name}_feeding_{feeding_type}"
            if self.hass.states.get(entity_id, {}).state == STATE_ON:
                fed_count += 1
        
        outside_state = self.hass.states.get(f"input_boolean.{self._name}_outside", {}).state
        visitor_mode = self.hass.states.get(f"input_boolean.{self._name}_visitor_mode", {}).state
        
        if visitor_mode == STATE_ON:
            self._attr_native_value = "Besuchsmodus"
        elif fed_count == total_feedings and outside_state == STATE_ON:
            self._attr_native_value = "Vollständig versorgt"
        elif fed_count == total_feedings:
            self._attr_native_value = "Gefüttert, war noch nicht draußen"
        elif outside_state == STATE_ON:
            self._attr_native_value = f"War draußen, {fed_count}/{total_feedings} Fütterungen"
        elif fed_count > 0:
            self._attr_native_value = f"{fed_count}/{total_feedings} Fütterungen erledigt"
        else:
            self._attr_native_value = "Noch nichts erledigt"
        
        # Set icon based on status
        if visitor_mode == STATE_ON:
            self._attr_icon = ICONS["visitor_mode"]
        elif fed_count == total_feedings and outside_state == STATE_ON:
            self._attr_icon = "mdi:heart"
        else:
            self._attr_icon = ICONS["dog"]

class HundeFeedingStatusSensor(SensorEntity):
    """Sensor for feeding status."""
    
    def __init__(self, hass: HomeAssistant, name: str):
        """Initialize the sensor."""
        self.hass = hass
        self._name = name
        self._attr_name = f"{name.title()} Fütterungsstatus"
        self._attr_unique_id = f"{name}_feeding_status"
        self._attr_icon = "mdi:food-variant"
        
        # Track feeding entities
        self._tracked_entities = []
        for feeding_type in FEEDING_TYPES:
            self._tracked_entities.append(f"input_boolean.{name}_feeding_{feeding_type}")
            self._tracked_entities.append(f"counter.{name}_feeding_{feeding_type}")
        
        self._update_state()
    
    async def async_added_to_hass(self):
        """Register callbacks."""
        @callback
        def sensor_state_listener(event):
            """Handle state changes."""
            self._update_state()
            self.async_write_ha_state()
        
        self.async_on_remove(
            async_track_state_change_event(
                self.hass, self._tracked_entities, sensor_state_listener
            )
        )
    
    def _update_state(self):
        """Update the sensor state."""
        fed_meals = []
        total_count = 0
        
        for feeding_type in FEEDING_TYPES:
            boolean_entity = f"input_boolean.{self._name}_feeding_{feeding_type}"
            counter_entity = f"counter.{self._name}_feeding_{feeding_type}"
            
            if self.hass.states.get(boolean_entity, {}).state == STATE_ON:
                meal_name = MEAL_TRANSLATIONS.get(feeding_type, feeding_type)
                fed_meals.append(meal_name)
            
            counter_state = self.hass.states.get(counter_entity, {})
            if counter_state.state and counter_state.state.isdigit():
                total_count += int(counter_state.state)
        
        if fed_meals:
            self._attr_native_value = f"{', '.join(fed_meals)} ({total_count} gesamt)"
        else:
            self._attr_native_value = f"Noch nicht gefüttert ({total_count} gesamt)"
        
        # Update attributes
        self._attr_extra_state_attributes = {
            "fed_meals": fed_meals,
            "total_count": total_count,
            "fed_count": len(fed_meals),
            "remaining_meals": len(FEEDING_TYPES) - len(fed_meals)
        }

class HundeActivitySensor(SensorEntity):
    """Sensor for activity status."""
    
    def __init__(self, hass: HomeAssistant, name: str):
        """Initialize the sensor."""
        self.hass = hass
        self._name = name
        self._attr_name = f"{name.title()} Aktivitäten"
        self._attr_unique_id = f"{name}_activity"
        self._attr_icon = ICONS["outside"]
        
        self._tracked_entities = [
            f"input_boolean.{name}_outside",
            f"counter.{name}_outside"
        ]
        
        self._update_state()
    
    async def async_added_to_hass(self):
        """Register callbacks."""
        @callback
        def sensor_state_listener(event):
            """Handle state changes."""
            self._update_state()
            self.async_write_ha_state()
        
        self.async_on_remove(
            async_track_state_change_event(
                self.hass, self._tracked_entities, sensor_state_listener
            )
        )
    
    def _update_state(self):
        """Update the sensor state."""
        outside_state = self.hass.states.get(f"input_boolean.{self._name}_outside", {}).state
        counter_state = self.hass.states.get(f"counter.{self._name}_outside", {})
        
        outside_count = 0
        if counter_state.state and counter_state.state.isdigit():
            outside_count = int(counter_state.state)
        
        if outside_state == STATE_ON:
            self._attr_native_value = f"War draußen ({outside_count} mal heute)"
        else:
            self._attr_native_value = f"War noch nicht draußen ({outside_count} mal heute)"
        
        self._attr_extra_state_attributes = {
            "outside_today": outside_count,
            "was_outside": outside_state == STATE_ON
        }

class HundeDailySummarySensor(SensorEntity):
    """Sensor for daily summary."""
    
    def __init__(self, hass: HomeAssistant, name: str):
        """Initialize the sensor."""
        self.hass = hass
        self._name = name
        self._attr_name = f"{name.title()} Tageszusammenfassung"
        self._attr_unique_id = f"{name}_daily_summary"
        self._attr_icon = "mdi:calendar-today"
        
        # Track all relevant entities
        self._tracked_entities = []
        for feeding_type in FEEDING_TYPES:
            self._tracked_entities.append(f"input_boolean.{name}_feeding_{feeding_type}")
            self._tracked_entities.append(f"counter.{name}_feeding_{feeding_type}")
        self._tracked_entities.extend([
            f"input_boolean.{name}_outside",
            f"counter.{name}_outside",
            f"input_boolean.{name}_visitor_mode"
        ])
        
        self._update_state()
    
    async def async_added_to_hass(self):
        """Register callbacks."""
        @callback
        def sensor_state_listener(event):
            """Handle state changes."""
            self._update_state()
            self.async_write_ha_state()
        
        self.async_on_remove(
            async_track_state_change_event(
                self.hass, self._tracked_entities, sensor_state_listener
            )
        )
    
    def _update_state(self):
        """Update the sensor state."""
        summary_data = {}
        total_activities = 0
        
        # Feeding data
        for feeding_type in FEEDING_TYPES:
            counter_entity = f"counter.{self._name}_feeding_{feeding_type}"
            counter_state = self.hass.states.get(counter_entity, {})
            count = 0
            if counter_state.state and counter_state.state.isdigit():
                count = int(counter_state.state)
            
            summary_data[f"feeding_{feeding_type}"] = count
            total_activities += count
        
        # Outside activity
        outside_counter = self.hass.states.get(f"counter.{self._name}_outside", {})
        outside_count = 0
        if outside_counter.state and outside_counter.state.isdigit():
            outside_count = int(outside_counter.state)
        
        summary_data["outside"] = outside_count
        total_activities += outside_count
        
        # Visitor mode
        visitor_mode = self.hass.states.get(f"input_boolean.{self._name}_visitor_mode", {}).state
        summary_data["visitor_mode"] = visitor_mode == STATE_ON
        
        self._attr_native_value = f"{total_activities} Aktivitäten heute"
        self._attr_extra_state_attributes = summary_data

class HundeLastActivitySensor(SensorEntity):
    """Sensor for last activity timestamp."""
    
    def __init__(self, hass: HomeAssistant, name: str):
        """Initialize the sensor."""
        self.hass = hass
        self._name = name
        self._attr_name = f"{name.title()} Letzte Aktivität"
        self._attr_unique_id = f"{name}_last_activity"
        self._attr_icon = "mdi:clock-outline"
        self._attr_device_class = SensorDeviceClass.TIMESTAMP
        
        # Track all activity entities
        self._tracked_entities = []
        for feeding_type in FEEDING_TYPES:
            self._tracked_entities.append(f"input_boolean.{name}_feeding_{feeding_type}")
        self._tracked_entities.append(f"input_boolean.{name}_outside")
        
        self._last_activity = None
        self._update_state()
    
    async def async_added_to_hass(self):
        """Register callbacks."""
        @callback
        def sensor_state_listener(event):
            """Handle state changes."""
            if event.data.get("new_state") and event.data["new_state"].state == STATE_ON:
                self._last_activity = datetime.now()
                self._update_state()
                self.async_write_ha_state()
        
        self.async_on_remove(
            async_track_state_change_event(
                self.hass, self._tracked_entities, sensor_state_listener
            )
        )
    
    def _update_state(self):
        """Update the sensor state."""
        if self._last_activity:
            self._attr_native_value = self._last_activity
        else:
            self._attr_native_value = None
        
        # Add time since last activity
        if self._last_activity:
            time_diff = datetime.now() - self._last_activity
            hours = int(time_diff.total_seconds() // 3600)
            minutes = int((time_diff.total_seconds() % 3600) // 60)
            
            self._attr_extra_state_attributes = {
                "hours_since": hours,
                "minutes_since": minutes,
                "last_activity_iso": self._last_activity.isoformat() if self._last_activity else None
            }
        else:
            self._attr_extra_state_attributes = {
                "hours_since": None,
                "minutes_since": None,
                "last_activity_iso": None
            }