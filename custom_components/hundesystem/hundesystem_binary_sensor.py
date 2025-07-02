"""Binary sensor platform for Hundesystem."""
import logging
from datetime import datetime

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.const import STATE_ON, STATE_OFF

from .const import DOMAIN, CONF_NAME, FEEDING_TYPES, ICONS

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Hundesystem binary sensors."""
    name = config_entry.data.get(CONF_NAME, "hund")
    
    entities = []
    
    # Feeding complete sensor
    entities.append(HundeFeedingCompleteBinarySensor(hass, name))
    
    # Daily tasks complete sensor
    entities.append(HundeDailyTasksCompleteBinarySensor(hass, name))
    
    # Visitor mode sensor
    entities.append(HundeVisitorModeBinarySensor(hass, name))
    
    # Outside status sensor
    entities.append(HundeOutsideStatusBinarySensor(hass, name))
    
    # Need attention sensor
    entities.append(HundeNeedAttentionBinarySensor(hass, name))
    
    async_add_entities(entities)

class HundeFeedingCompleteBinarySensor(BinarySensorEntity):
    """Binary sensor for feeding completion status."""
    
    def __init__(self, hass: HomeAssistant, name: str):
        """Initialize the binary sensor."""
        self.hass = hass
        self._name = name
        self._attr_name = f"{name.title()} Fütterung komplett"
        self._attr_unique_id = f"{name}_feeding_complete"
        self._attr_icon = "mdi:check-circle"
        self._attr_device_class = None
        
        # Track feeding entities
        self._tracked_entities = []
        for feeding_type in FEEDING_TYPES:
            self._tracked_entities.append(f"input_boolean.{name}_feeding_{feeding_type}")
        
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
        """Update the binary sensor state."""
        all_fed = True
        fed_count = 0
        
        for feeding_type in FEEDING_TYPES:
            entity_id = f"input_boolean.{self._name}_feeding_{feeding_type}"
            state = self.hass.states.get(entity_id, {}).state
            if state == STATE_ON:
                fed_count += 1
            else:
                all_fed = False
        
        self._attr_is_on = all_fed
        self._attr_extra_state_attributes = {
            "fed_count": fed_count,
            "total_meals": len(FEEDING_TYPES),
            "completion_percentage": round((fed_count / len(FEEDING_TYPES)) * 100, 1)
        }

class HundeDailyTasksCompleteBinarySensor(BinarySensorEntity):
    """Binary sensor for daily tasks completion."""
    
    def __init__(self, hass: HomeAssistant, name: str):
        """Initialize the binary sensor."""
        self.hass = hass
        self._name = name
        self._attr_name = f"{name.title()} Tagesaufgaben komplett"
        self._attr_unique_id = f"{name}_daily_tasks_complete"
        self._attr_icon = "mdi:calendar-check"
        
        # Track all relevant entities
        self._tracked_entities = []
        for feeding_type in FEEDING_TYPES:
            self._tracked_entities.append(f"input_boolean.{name}_feeding_{feeding_type}")
        self._tracked_entities.append(f"input_boolean.{name}_outside")
        
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
        """Update the binary sensor state."""
        all_fed = True
        fed_count = 0
        
        # Check feeding status
        for feeding_type in FEEDING_TYPES:
            entity_id = f"input_boolean.{self._name}_feeding_{feeding_type}"
            if self.hass.states.get(entity_id, {}).state == STATE_ON:
                fed_count += 1
            else:
                all_fed = False
        
        # Check outside status
        outside_state = self.hass.states.get(f"input_boolean.{self._name}_outside", {}).state
        was_outside = outside_state == STATE_ON
        
        # All tasks complete if fed and was outside
        all_complete = all_fed and was_outside
        
        self._attr_is_on = all_complete
        self._attr_extra_state_attributes = {
            "feeding_complete": all_fed,
            "was_outside": was_outside,
            "fed_count": fed_count,
            "total_meals": len(FEEDING_TYPES)
        }

class HundeVisitorModeBinarySensor(BinarySensorEntity):
    """Binary sensor for visitor mode status."""
    
    def __init__(self, hass: HomeAssistant, name: str):
        """Initialize the binary sensor."""
        self.hass = hass
        self._name = name
        self._attr_name = f"{name.title()} Besuchsmodus"
        self._attr_unique_id = f"{name}_visitor_mode"
        self._attr_icon = ICONS["visitor_mode"]
        self._attr_device_class = None
        
        self._tracked_entities = [f"input_boolean.{name}_visitor_mode"]
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
        """Update the binary sensor state."""
        visitor_state = self.hass.states.get(f"input_boolean.{self._name}_visitor_mode", {}).state
        self._attr_is_on = visitor_state == STATE_ON

class HundeOutsideStatusBinarySensor(BinarySensorEntity):
    """Binary sensor for outside status."""
    
    def __init__(self, hass: HomeAssistant, name: str):
        """Initialize the binary sensor."""
        self.hass = hass
        self._name = name
        self._attr_name = f"{name.title()} War draußen"
        self._attr_unique_id = f"{name}_outside_status"
        self._attr_icon = ICONS["outside"]
        self._attr_device_class = None
        
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
        """Update the binary sensor state."""
        outside_state = self.hass.states.get(f"input_boolean.{self._name}_outside", {}).state
        counter_state = self.hass.states.get(f"counter.{self._name}_outside", {})
        
        outside_count = 0
        if counter_state.state and counter_state.state.isdigit():
            outside_count = int(counter_state.state)
        
        self._attr_is_on = outside_state == STATE_ON
        self._attr_extra_state_attributes = {
            "times_outside_today": outside_count
        }

class HundeNeedAttentionBinarySensor(BinarySensorEntity):
    """Binary sensor that indicates if dog needs attention."""
    
    def __init__(self, hass: HomeAssistant, name: str):
        """Initialize the binary sensor."""
        self.hass = hass
        self._name = name
        self._attr_name = f"{name.title()} Braucht Aufmerksamkeit"
        self._attr_unique_id = f"{name}_needs_attention"
        self._attr_icon = "mdi:alert-circle"
        self._attr_device_class = None
        
        # Track all relevant entities
        self._tracked_entities = []
        for feeding_type in FEEDING_TYPES:
            self._tracked_entities.append(f"input_boolean.{name}_feeding_{feeding_type}")
        self._tracked_entities.extend([
            f"input_boolean.{name}_outside",
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
        """Update the binary sensor state."""
        visitor_mode = self.hass.states.get(f"input_boolean.{self._name}_visitor_mode", {}).state
        
        # If in visitor mode, no attention needed from regular routine
        if visitor_mode == STATE_ON:
            self._attr_is_on = False
            self._attr_extra_state_attributes = {"reason": "Besuchsmodus aktiv"}
            return
        
        needs_attention = False
        reasons = []
        
        # Check feeding status
        fed_count = 0
        for feeding_type in FEEDING_TYPES:
            entity_id = f"input_boolean.{self._name}_feeding_{feeding_type}"
            if self.hass.states.get(entity_id, {}).state == STATE_ON:
                fed_count += 1
        
        if fed_count < len(FEEDING_TYPES):
            needs_attention = True
            missing = len(FEEDING_TYPES) - fed_count
            reasons.append(f"{missing} Fütterung(en) fehlen")
        
        # Check outside status
        outside_state = self.hass.states.get(f"input_boolean.{self._name}_outside", {}).state
        if outside_state != STATE_ON:
            needs_attention = True
            reasons.append("War noch nicht draußen")
        
        self._attr_is_on = needs_attention
        self._attr_extra_state_attributes = {
            "reasons": reasons,
            "fed_count": fed_count,
            "total_meals": len(FEEDING_TYPES)
        }