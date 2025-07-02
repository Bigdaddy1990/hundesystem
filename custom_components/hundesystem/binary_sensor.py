"""Binary sensor platform for Hundesystem integration."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    DOMAIN,
    CONF_DOG_NAME,
    ICONS,
    ENTITIES,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Hundesystem binary sensors based on a config entry."""
    dog_name = config_entry.data[CONF_DOG_NAME]
    
    entities = [
        HundesystemFeedingCompleteBinarySensor(hass, config_entry, dog_name),
        HundesystemDailyTasksCompleteBinarySensor(hass, config_entry, dog_name),
        HundesystemVisitorModeBinarySensor(hass, config_entry, dog_name),
        HundesystemOutsideStatusBinarySensor(hass, config_entry, dog_name),
        HundesystemNeedsAttentionBinarySensor(hass, config_entry, dog_name),
    ]
    
    async_add_entities(entities, True)


class HundesystemBinarySensorBase(BinarySensorEntity, RestoreEntity):
    """Base class for Hundesystem binary sensors."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        dog_name: str,
        sensor_type: str,
    ) -> None:
        """Initialize the binary sensor."""
        self.hass = hass
        self._config_entry = config_entry
        self._dog_name = dog_name
        self._sensor_type = sensor_type
        self._attr_unique_id = f"{DOMAIN}_{dog_name}_{sensor_type}"
        self._attr_name = f"{dog_name.title()} {sensor_type.replace('_', ' ').title()}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, dog_name)},
            "name": f"Hundesystem {dog_name.title()}",
            "manufacturer": "Hundesystem",
            "model": "Dog Management System",
            "sw_version": "1.0.0",
        }

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Restore previous state
        if (old_state := await self.async_get_last_state()) is not None:
            self._attr_is_on = old_state.state == "on"


class HundesystemFeedingCompleteBinarySensor(HundesystemBinarySensorBase):
    """Binary sensor for feeding completion status."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        dog_name: str,
    ) -> None:
        """Initialize the feeding complete binary sensor."""
        super().__init__(hass, config_entry, dog_name, ENTITIES["feeding_complete"])
        self._attr_icon = ICONS["complete"]
        self._attr_device_class = BinarySensorDeviceClass.PROBLEM
        self._tracked_entities = [
            f"input_boolean.{dog_name}_feeding_morning",
            f"input_boolean.{dog_name}_feeding_lunch",
            f"input_boolean.{dog_name}_feeding_evening",
        ]

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Track state changes of feeding input_booleans
        async_track_state_change_event(
            self.hass, self._tracked_entities, self._async_feeding_state_changed
        )
        
        # Initial update
        await self._async_update_state()

    @callback
    async def _async_feeding_state_changed(self, event) -> None:
        """Handle state changes of feeding entities."""
        await self._async_update_state()
        self.async_write_ha_state()

    async def _async_update_state(self) -> None:
        """Update the binary sensor state."""
        all_fed = True
        
        for entity_id in self._tracked_entities:
            state = self.hass.states.get(entity_id)
            if not state or state.state != "on":
                all_fed = False
                break
        
        self._attr_is_on = all_fed
        
        # Add extra attributes
        feeding_status = {}
        for entity_id in self._tracked_entities:
            meal_type = entity_id.split("_")[-1]
            state = self.hass.states.get(entity_id)
            feeding_status[meal_type] = state.state == "on" if state else False
        
        self._attr_extra_state_attributes = {
            "feeding_status": feeding_status,
            "total_meals": len(self._tracked_entities),
            "completed_meals": sum(feeding_status.values()),
        }


class HundesystemDailyTasksCompleteBinarySensor(HundesystemBinarySensorBase):
    """Binary sensor for daily tasks completion status."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        dog_name: str,
    ) -> None:
        """Initialize the daily tasks complete binary sensor."""
        super().__init__(hass, config_entry, dog_name, ENTITIES["daily_tasks_complete"])
        self._attr_icon = ICONS["complete"]
        self._attr_device_class = BinarySensorDeviceClass.PROBLEM
        self._tracked_entities = [
            f"input_boolean.{dog_name}_feeding_morning",
            f"input_boolean.{dog_name}_feeding_lunch",
            f"input_boolean.{dog_name}_feeding_evening",
            f"input_boolean.{dog_name}_outside",
        ]

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Track state changes
        async_track_state_change_event(
            self.hass, self._tracked_entities, self._async_tasks_state_changed
        )
        
        # Initial update
        await self._async_update_state()

    @callback
    async def _async_tasks_state_changed(self, event) -> None:
        """Handle state changes of task entities."""
        await self._async_update_state()
        self.async_write_ha_state()

    async def _async_update_state(self) -> None:
        """Update the binary sensor state."""
        all_complete = True
        completed_tasks = []
        pending_tasks = []
        
        for entity_id in self._tracked_entities:
            state = self.hass.states.get(entity_id)
            task_name = entity_id.split("_")[-1]
            
            if state and state.state == "on":
                completed_tasks.append(task_name)
            else:
                pending_tasks.append(task_name)
                all_complete = False
        
        self._attr_is_on = all_complete
        
        self._attr_extra_state_attributes = {
            "completed_tasks": completed_tasks,
            "pending_tasks": pending_tasks,
            "completion_percentage": round(len(completed_tasks) / len(self._tracked_entities) * 100),
        }


class HundesystemVisitorModeBinarySensor(HundesystemBinarySensorBase):
    """Binary sensor for visitor mode status."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        dog_name: str,
    ) -> None:
        """Initialize the visitor mode binary sensor."""
        super().__init__(hass, config_entry, dog_name, ENTITIES["visitor_mode"])
        self._attr_icon = ICONS["visitor"]
        self._tracked_entity = f"input_boolean.{dog_name}_visitor_mode_input"
        self._visitor_name_entity = f"input_text.{dog_name}_visitor_name"

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Track state changes
        async_track_state_change_event(
            self.hass, [self._tracked_entity, self._visitor_name_entity], 
            self._async_visitor_state_changed
        )
        
        # Initial update
        await self._async_update_state()

    @callback
    async def _async_visitor_state_changed(self, event) -> None:
        """Handle state changes of visitor mode entities."""
        await self._async_update_state()
        self.async_write_ha_state()

    async def _async_update_state(self) -> None:
        """Update the binary sensor state."""
        state = self.hass.states.get(self._tracked_entity)
        name_state = self.hass.states.get(self._visitor_name_entity)
        
        self._attr_is_on = state.state == "on" if state else False
        
        visitor_name = name_state.state if name_state else ""
        
        self._attr_extra_state_attributes = {
            "visitor_name": visitor_name,
            "enabled_since": datetime.now().isoformat() if self._attr_is_on else None,
        }


class HundesystemOutsideStatusBinarySensor(HundesystemBinarySensorBase):
    """Binary sensor for outside status."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        dog_name: str,
    ) -> None:
        """Initialize the outside status binary sensor."""
        super().__init__(hass, config_entry, dog_name, ENTITIES["outside_status"])
        self._attr_icon = ICONS["outside"]
        self._tracked_entity = f"input_boolean.{dog_name}_outside"
        self._datetime_entity = f"input_datetime.{dog_name}_last_outside"

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Track state changes
        async_track_state_change_event(
            self.hass, [self._tracked_entity], self._async_outside_state_changed
        )
        
        # Initial update
        await self._async_update_state()

    @callback
    async def _async_outside_state_changed(self, event) -> None:
        """Handle state changes of outside status."""
        await self._async_update_state()
        self.async_write_ha_state()

    async def _async_update_state(self) -> None:
        """Update the binary sensor state."""
        state = self.hass.states.get(self._tracked_entity)
        datetime_state = self.hass.states.get(self._datetime_entity)
        
        was_outside_today = state.state == "on" if state else False
        
        # Check if last outside time was today
        last_outside = None
        if datetime_state and datetime_state.state not in ["unknown", "unavailable"]:
            try:
                last_outside = datetime.fromisoformat(datetime_state.state.replace("Z", "+00:00"))
                today = datetime.now().date()
                was_outside_today = was_outside_today or last_outside.date() == today
            except (ValueError, AttributeError):
                pass
        
        self._attr_is_on = was_outside_today
        
        self._attr_extra_state_attributes = {
            "last_outside": last_outside.isoformat() if last_outside else None,
            "currently_outside": state.state == "on" if state else False,
        }


class HundesystemNeedsAttentionBinarySensor(HundesystemBinarySensorBase):
    """Binary sensor for attention needs."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        dog_name: str,
    ) -> None:
        """Initialize the needs attention binary sensor."""
        super().__init__(hass, config_entry, dog_name, ENTITIES["needs_attention"])
        self._attr_icon = ICONS["attention"]
        self._attr_device_class = BinarySensorDeviceClass.PROBLEM
        
        # Entities to monitor for attention needs
        self._feeding_entities = [
            f"input_boolean.{dog_name}_feeding_morning",
            f"input_boolean.{dog_name}_feeding_lunch",
            f"input_boolean.{dog_name}_feeding_evening",
        ]
        self._outside_entity = f"input_boolean.{dog_name}_outside"
        self._visitor_entity = f"input_boolean.{dog_name}_visitor_mode_input"

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Track all relevant entities
        tracked_entities = self._feeding_entities + [self._outside_entity, self._visitor_entity]
        async_track_state_change_event(
            self.hass, tracked_entities, self._async_attention_state_changed
        )
        
        # Initial update
        await self._async_update_state()

    @callback
    async def _async_attention_state_changed(self, event) -> None:
        """Handle state changes that might affect attention needs."""
        await self._async_update_state()
        self.async_write_ha_state()

    async def _async_update_state(self) -> None:
        """Update the attention needs state."""
        reasons = []
        now = datetime.now()
        
        # Check if visitor mode is active (lower priority for attention)
        visitor_state = self.hass.states.get(self._visitor_entity)
        visitor_mode = visitor_state.state == "on" if visitor_state else False
        
        if not visitor_mode:
            # Check feeding status
            for entity_id in self._feeding_entities:
                state = self.hass.states.get(entity_id)
                meal_type = entity_id.split("_")[-1]
                
                if not state or state.state != "on":
                    # Check if it's time for this meal
                    if self._is_meal_time(meal_type, now):
                        reasons.append(f"Zeit für {meal_type}")
            
            # Check if dog was outside today
            outside_state = self.hass.states.get(self._outside_entity)
            if not outside_state or outside_state.state != "on":
                reasons.append("War noch nicht draußen")
        
        self._attr_is_on = len(reasons) > 0
        
        self._attr_extra_state_attributes = {
            "reasons": reasons,
            "visitor_mode": visitor_mode,
            "attention_level": "high" if len(reasons) > 2 else "medium" if len(reasons) > 0 else "low",
        }

    def _is_meal_time(self, meal_type: str, current_time: datetime) -> bool:
        """Check if it's time for a specific meal."""
        hour = current_time.hour
        
        meal_times = {
            "morning": (6, 10),    # 6:00 - 10:00
            "lunch": (11, 14),     # 11:00 - 14:00  
            "evening": (17, 20),   # 17:00 - 20:00
        }
        
        if meal_type in meal_times:
            start_hour, end_hour = meal_times[meal_type]
            return start_hour <= hour <= end_hour
        
        return False
