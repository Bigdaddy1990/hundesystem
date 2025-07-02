"""Sensor platform for Hundesystem integration."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.sensor import SensorEntity
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
    STATUS_MESSAGES,
    MEAL_TYPES,
    ACTIVITY_TYPES,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Hundesystem sensors based on a config entry."""
    dog_name = config_entry.data[CONF_DOG_NAME]
    
    entities = [
        HundesystemStatusSensor(hass, config_entry, dog_name),
        HundesystemFeedingStatusSensor(hass, config_entry, dog_name),
        HundesystemActivitySensor(hass, config_entry, dog_name),
        HundesystemDailySummarySensor(hass, config_entry, dog_name),
        HundesystemLastActivitySensor(hass, config_entry, dog_name),
    ]
    
    async_add_entities(entities, True)


class HundesystemSensorBase(SensorEntity, RestoreEntity):
    """Base class for Hundesystem sensors."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        dog_name: str,
        sensor_type: str,
    ) -> None:
        """Initialize the sensor."""
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
            self._attr_native_value = old_state.state


class HundesystemStatusSensor(HundesystemSensorBase):
    """Sensor for overall dog status."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        dog_name: str,
    ) -> None:
        """Initialize the status sensor."""
        super().__init__(hass, config_entry, dog_name, ENTITIES["status"])
        self._attr_icon = ICONS["dog"]
        
        # Entities to monitor for status calculation
        self._feeding_entities = [
            f"input_boolean.{dog_name}_feeding_morning",
            f"input_boolean.{dog_name}_feeding_lunch",
            f"input_boolean.{dog_name}_feeding_evening",
        ]
        self._outside_entity = f"input_boolean.{dog_name}_outside"
        self._visitor_entity = f"input_boolean.{dog_name}_visitor_mode_input"
        self._needs_attention_entity = f"binary_sensor.{dog_name}_needs_attention"

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Track all relevant entities
        tracked_entities = (
            self._feeding_entities + 
            [self._outside_entity, self._visitor_entity, self._needs_attention_entity]
        )
        async_track_state_change_event(
            self.hass, tracked_entities, self._async_status_changed
        )
        
        # Initial update
        await self._async_update_status()

    @callback
    async def _async_status_changed(self, event) -> None:
        """Handle state changes that affect overall status."""
        await self._async_update_status()
        self.async_write_ha_state()

    async def _async_update_status(self) -> None:
        """Update the overall status."""
        # Check visitor mode
        visitor_state = self.hass.states.get(self._visitor_entity)
        visitor_mode = visitor_state.state == "on" if visitor_state else False
        
        if visitor_mode:
            self._attr_native_value = STATUS_MESSAGES["visitor_mode"]
            self._attr_icon = ICONS["visitor"]
        else:
            # Check if attention is needed
            attention_state = self.hass.states.get(self._needs_attention_entity)
            needs_attention = attention_state.state == "on" if attention_state else False
            
            if needs_attention:
                self._attr_native_value = STATUS_MESSAGES["attention_needed"]
                self._attr_icon = ICONS["attention"]
            else:
                # Check feeding status
                fed_count = 0
                for entity_id in self._feeding_entities:
                    state = self.hass.states.get(entity_id)
                    if state and state.state == "on":
                        fed_count += 1
                
                # Check outside status
                outside_state = self.hass.states.get(self._outside_entity)
                was_outside = outside_state.state == "on" if outside_state else False
                
                if fed_count == len(self._feeding_entities) and was_outside:
                    self._attr_native_value = STATUS_MESSAGES["all_good"]
                    self._attr_icon = ICONS["complete"]
                elif fed_count < len(self._feeding_entities):
                    self._attr_native_value = STATUS_MESSAGES["needs_feeding"]
                    self._attr_icon = ICONS["food"]
                elif not was_outside:
                    self._attr_native_value = STATUS_MESSAGES["needs_outside"]
                    self._attr_icon = ICONS["walk"]
                else:
                    self._attr_native_value = STATUS_MESSAGES["all_good"]
                    self._attr_icon = ICONS["dog"]
        
        # Update attributes
        self._attr_extra_state_attributes = {
            "visitor_mode": visitor_mode,
            "feeding_progress": f"{fed_count}/{len(self._feeding_entities)}",
            "was_outside": outside_state.state == "on" if outside_state else False,
            "last_updated": datetime.now().isoformat(),
        }


class HundesystemFeedingStatusSensor(HundesystemSensorBase):
    """Sensor for feeding status."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        dog_name: str,
    ) -> None:
        """Initialize the feeding status sensor."""
        super().__init__(hass, config_entry, dog_name, ENTITIES["feeding_status"])
        self._attr_icon = ICONS["food"]
        
        self._feeding_entities = [
            f"input_boolean.{dog_name}_feeding_morning",
            f"input_boolean.{dog_name}_feeding_lunch",
            f"input_boolean.{dog_name}_feeding_evening",
            f"input_boolean.{dog_name}_feeding_snack",
        ]
        self._feeding_counters = [
            f"counter.{dog_name}_feeding_count",
        ]

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Track feeding entities
        tracked_entities = self._feeding_entities + self._feeding_counters
        async_track_state_change_event(
            self.hass, tracked_entities, self._async_feeding_status_changed
        )
        
        # Initial update
        await self._async_update_feeding_status()

    @callback
    async def _async_feeding_status_changed(self, event) -> None:
        """Handle feeding status changes."""
        await self._async_update_feeding_status()
        self.async_write_ha_state()

    async def _async_update_feeding_status(self) -> None:
        """Update the feeding status."""
        feeding_status = {}
        total_fed = 0
        
        for entity_id in self._feeding_entities:
            meal_type = entity_id.split("_")[-1]
            state = self.hass.states.get(entity_id)
            is_fed = state.state == "on" if state else False
            feeding_status[meal_type] = is_fed
            if is_fed:
                total_fed += 1
        
        # Get feeding counter
        counter_state = self.hass.states.get(self._feeding_counters[0])
        total_feedings = int(counter_state.state) if counter_state else 0
        
        # Determine status message
        if total_fed == 0:
            status = "Noch nicht gefüttert"
        elif total_fed < 3:  # Morning, lunch, evening are essential
            status = f"Teilweise gefüttert ({total_fed}/3)"
        else:
            status = "Vollständig gefüttert"
        
        self._attr_native_value = status
        
        # Update attributes
        self._attr_extra_state_attributes = {
            "meals_today": feeding_status,
            "total_meals_completed": total_fed,
            "total_feedings_count": total_feedings,
            "next_meal": self._get_next_meal_time(),
        }

    def _get_next_meal_time(self) -> str | None:
        """Get the next scheduled meal time."""
        now = datetime.now()
        hour = now.hour
        
        if hour < 8:
            return "Frühstück (08:00)"
        elif hour < 12:
            return "Mittagessen (12:00)"
        elif hour < 18:
            return "Abendessen (18:00)"
        else:
            return "Frühstück (08:00 morgen)"


class HundesystemActivitySensor(HundesystemSensorBase):
    """Sensor for activity tracking."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        dog_name: str,
    ) -> None:
        """Initialize the activity sensor."""
        super().__init__(hass, config_entry, dog_name, ENTITIES["activity"])
        self._attr_icon = ICONS["walk"]
        
        self._outside_entity = f"input_boolean.{dog_name}_outside"
        self._activity_counter = f"counter.{dog_name}_activity_count"
        self._outside_counter = f"counter.{dog_name}_outside_count"
        self._last_outside_entity = f"input_datetime.{dog_name}_last_outside"

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Track activity entities
        tracked_entities = [
            self._outside_entity,
            self._activity_counter,
            self._outside_counter,
            self._last_outside_entity,
        ]
        async_track_state_change_event(
            self.hass, tracked_entities, self._async_activity_changed
        )
        
        # Initial update
        await self._async_update_activity()

    @callback
    async def _async_activity_changed(self, event) -> None:
        """Handle activity changes."""
        await self._async_update_activity()
        self.async_write_ha_state()

    async def _async_update_activity(self) -> None:
        """Update the activity status."""
        # Check if currently outside
        outside_state = self.hass.states.get(self._outside_entity)
        currently_outside = outside_state.state == "on" if outside_state else False
        
        # Get activity counters
        activity_count_state = self.hass.states.get(self._activity_counter)
        outside_count_state = self.hass.states.get(self._outside_counter)
        
        activity_count = int(activity_count_state.state) if activity_count_state else 0
        outside_count = int(outside_count_state.state) if outside_count_state else 0
        
        # Get last outside time
        last_outside_state = self.hass.states.get(self._last_outside_entity)
        last_outside = None
        if last_outside_state and last_outside_state.state not in ["unknown", "unavailable"]:
            try:
                last_outside = datetime.fromisoformat(last_outside_state.state.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                pass
        
        # Determine activity status
        if currently_outside:
            status = "Gerade draußen"
        elif outside_count > 0:
            status = f"War {outside_count}x draußen heute"
        else:
            status = "War noch nicht draußen"
        
        self._attr_native_value = status
        
        # Update attributes
        self._attr_extra_state_attributes = {
            "currently_outside": currently_outside,
            "times_outside_today": outside_count,
            "total_activities_today": activity_count,
            "last_outside": last_outside.isoformat() if last_outside else None,
            "activity_level": self._calculate_activity_level(activity_count, outside_count),
        }

    def _calculate_activity_level(self, activity_count: int, outside_count: int) -> str:
        """Calculate activity level based on counts."""
        total_activities = activity_count + outside_count
        
        if total_activities >= 5:
            return "Sehr aktiv"
        elif total_activities >= 3:
            return "Aktiv"
        elif total_activities >= 1:
            return "Wenig aktiv"
        else:
            return "Inaktiv"


class HundesystemDailySummarySensor(HundesystemSensorBase):
    """Sensor for daily summary."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        dog_name: str,
    ) -> None:
        """Initialize the daily summary sensor."""
        super().__init__(hass, config_entry, dog_name, ENTITIES["daily_summary"])
        self._attr_icon = ICONS["notes"]
        
        # All entities to include in summary
        self._feeding_entities = [
            f"input_boolean.{dog_name}_feeding_morning",
            f"input_boolean.{dog_name}_feeding_lunch",
            f"input_boolean.{dog_name}_feeding_evening",
            f"input_boolean.{dog_name}_feeding_snack",
        ]
        self._counters = [
            f"counter.{dog_name}_feeding_count",
            f"counter.{dog_name}_outside_count", 
            f"counter.{dog_name}_activity_count",
        ]
        self._other_entities = [
            f"input_boolean.{dog_name}_outside",
            f"input_boolean.{dog_name}_visitor_mode_input",
        ]

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Track all relevant entities
        tracked_entities = self._feeding_entities + self._counters + self._other_entities
        async_track_state_change_event(
            self.hass, tracked_entities, self._async_summary_changed
        )
        
        # Initial update
        await self._async_update_summary()

    @callback
    async def _async_summary_changed(self, event) -> None:
        """Handle summary relevant changes."""
        await self._async_update_summary()
        self.async_write_ha_state()

    async def _async_update_summary(self) -> None:
        """Update the daily summary."""
        # Count completed meals
        meals_completed = 0
        meal_details = {}
        
        for entity_id in self._feeding_entities:
            meal_type = entity_id.split("_")[-1]
            state = self.hass.states.get(entity_id)
            is_completed = state.state == "on" if state else False
            meal_details[meal_type] = is_completed
            if is_completed:
                meals_completed += 1
        
        # Get counter values
        feeding_count = 0
        outside_count = 0
        activity_count = 0
        
        for counter_id in self._counters:
            state = self.hass.states.get(counter_id)
            count = int(state.state) if state else 0
            
            if "feeding" in counter_id:
                feeding_count = count
            elif "outside" in counter_id:
                outside_count = count
            elif "activity" in counter_id:
                activity_count = count
        
        # Check other status
        outside_state = self.hass.states.get(self._other_entities[0])
        visitor_state = self.hass.states.get(self._other_entities[1])
        
        was_outside = outside_state.state == "on" if outside_state else False
        visitor_mode = visitor_state.state == "on" if visitor_state else False
        
        # Generate summary text
        summary_parts = []
        
        if visitor_mode:
            summary_parts.append("🏠 Besuchsmodus aktiv")
        
        summary_parts.append(f"🍽️ Mahlzeiten: {meals_completed}/4")
        
        if was_outside or outside_count > 0:
            summary_parts.append(f"🚶 Draußen: {outside_count}x")
        else:
            summary_parts.append("🚶 Noch nicht draußen")
        
        if activity_count > 0:
            summary_parts.append(f"🎾 Aktivitäten: {activity_count}")
        
        summary = " | ".join(summary_parts)
        self._attr_native_value = summary
        
        # Calculate completion percentage
        total_tasks = 4  # 3 main meals + outside
        completed_tasks = min(meals_completed, 3) + (1 if was_outside else 0)
        completion_percentage = round((completed_tasks / total_tasks) * 100)
        
        # Update attributes
        self._attr_extra_state_attributes = {
            "meals_completed": meals_completed,
            "meal_details": meal_details,
            "feeding_count": feeding_count,
            "outside_count": outside_count,
            "activity_count": activity_count,
            "was_outside": was_outside,
            "visitor_mode": visitor_mode,
            "completion_percentage": completion_percentage,
            "day_rating": self._calculate_day_rating(completion_percentage, activity_count),
            "generated_at": datetime.now().isoformat(),
        }

    def _calculate_day_rating(self, completion_percentage: int, activity_count: int) -> str:
        """Calculate a rating for the day."""
        if completion_percentage >= 100 and activity_count >= 3:
            return "🌟 Perfekter Tag"
        elif completion_percentage >= 75:
            return "😊 Guter Tag"
        elif completion_percentage >= 50:
            return "😐 Durchschnittlicher Tag"
        else:
            return "😔 Verbesserungsbedarf"


class HundesystemLastActivitySensor(HundesystemSensorBase):
    """Sensor for last activity timestamp."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        dog_name: str,
    ) -> None:
        """Initialize the last activity sensor."""
        super().__init__(hass, config_entry, dog_name, ENTITIES["last_activity"])
        self._attr_icon = ICONS["notes"]
        self._attr_device_class = "timestamp"
        
        # Entities that count as activities
        self._activity_entities = [
            f"input_boolean.{dog_name}_feeding_morning",
            f"input_boolean.{dog_name}_feeding_lunch",
            f"input_boolean.{dog_name}_feeding_evening",
            f"input_boolean.{dog_name}_feeding_snack",
            f"input_boolean.{dog_name}_outside",
        ]
        
        self._notes_entity = f"input_text.{dog_name}_last_activity_notes"

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Track activity entities
        async_track_state_change_event(
            self.hass, self._activity_entities, self._async_activity_tracked
        )
        
        # Initial update
        await self._async_update_last_activity()

    @callback
    async def _async_activity_tracked(self, event) -> None:
        """Handle activity tracking."""
        # Only update if state changed to 'on'
        if event.data.get("new_state") and event.data["new_state"].state == "on":
            await self._async_update_last_activity()
            self.async_write_ha_state()

    async def _async_update_last_activity(self) -> None:
        """Update the last activity timestamp."""
        now = datetime.now()
        self._attr_native_value = now.isoformat()
        
        # Get notes if available
        notes_state = self.hass.states.get(self._notes_entity)
        notes = notes_state.state if notes_state else ""
        
        # Find which activity was last triggered
        last_activity = "Unbekannt"
        for entity_id in self._activity_entities:
            state = self.hass.states.get(entity_id)
            if state and state.state == "on":
                activity_type = entity_id.split("_")[-1]
                if "feeding" in entity_id:
                    meal_type = activity_type
                    last_activity = f"Fütterung: {MEAL_TYPES.get(meal_type, meal_type)}"
                elif "outside" in entity_id:
                    last_activity = "Draußen"
                break
        
        self._attr_extra_state_attributes = {
            "last_activity_type": last_activity,
            "timestamp": now.isoformat(),
            "notes": notes,
            "time_ago": self._format_time_ago(now),
        }

    def _format_time_ago(self, timestamp: datetime) -> str:
        """Format time ago in human readable format."""
        now = datetime.now()
        diff = now - timestamp
        
        if diff.total_seconds() < 60:
            return "Gerade eben"
        elif diff.total_seconds() < 3600:
            minutes = int(diff.total_seconds() / 60)
            return f"Vor {minutes} Minute{'n' if minutes != 1 else ''}"
        elif diff.total_seconds() < 86400:
            hours = int(diff.total_seconds() / 3600)
            return f"Vor {hours} Stunde{'n' if hours != 1 else ''}"
        else:
            days = int(diff.total_seconds() / 86400)
            return f"Vor {days} Tag{'en' if days != 1 else ''}"
