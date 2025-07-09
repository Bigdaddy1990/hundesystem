"""Sensor platform for Hundesystem integration."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    CONF_DOG_NAME,
    ICONS,
    ENTITIES,
    STATUS_MESSAGES,
    MEAL_TYPES,
    ACTIVITY_TYPES,
    FEEDING_TYPES,
    HEALTH_THRESHOLDS,
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
        HundesystemHealthScoreSensor(hass, config_entry, dog_name),
        HundesystemMoodSensor(hass, config_entry, dog_name),
        HundesystemWeeklySummarySensor(hass, config_entry, dog_name),
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
            "sw_version": "2.0.2",
        }

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Restore previous state
        if (old_state := await self.async_get_last_state()) is not None:
            self._attr_native_value = old_state.state
            if old_state.attributes:
                self._attr_extra_state_attributes = dict(old_state.attributes)


class HundesystemFeedingStatusSensor(HundesystemSensorBase):
    """Sensor for detailed feeding status."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        dog_name: str,
    ) -> None:
        """Initialize the feeding status sensor."""
        super().__init__(hass, config_entry, dog_name, ENTITIES["feeding_status"])
        self._attr_icon = ICONS["food"]
        self._attr_state_class = SensorStateClass.MEASUREMENT
        
        self._feeding_entities = [f"input_boolean.{dog_name}_feeding_{meal}" for meal in FEEDING_TYPES]
        self._feeding_counters = [f"counter.{dog_name}_feeding_{meal}_count" for meal in FEEDING_TYPES]
        self._feeding_times = [f"input_datetime.{dog_name}_feeding_{meal}_time" for meal in FEEDING_TYPES]

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Track feeding entities
        tracked_entities = self._feeding_entities + self._feeding_counters + self._feeding_times
        async_track_state_change_event(
            self.hass, tracked_entities, self._async_feeding_status_changed
        )
        
        # Initial update
        await self._async_update_feeding_status()

    @callback
    def _async_feeding_status_changed(self, event) -> None:
        """Handle feeding status changes."""
        # KORRIGIERT: @callback kann nicht mit async def verwendet werden
        self.hass.async_create_task(self._async_update_feeding_status())
        self.async_write_ha_state()

    async def _async_update_feeding_status(self) -> None:
        """Update the feeding status."""
        feeding_status = {}
        feeding_counts = {}
        feeding_times = {}
        total_fed = 0
        total_feedings = 0
        
        # Process each meal type
        for i, meal in enumerate(FEEDING_TYPES):
            # Check if meal was given
            boolean_entity = self._feeding_entities[i]
            state = self.hass.states.get(boolean_entity)
            is_fed = state.state == "on" if state else False
            feeding_status[meal] = is_fed
            
            if is_fed:
                total_fed += 1
            
            # Get feeding count
            counter_entity = self._feeding_counters[i]
            counter_state = self.hass.states.get(counter_entity)
            count = int(counter_state.state) if counter_state else 0
            feeding_counts[meal] = count
            total_feedings += count
            
            # Get scheduled time
            time_entity = self._feeding_times[i]
            time_state = self.hass.states.get(time_entity)
            if time_state and time_state.state not in ["unknown", "unavailable"]:
                feeding_times[meal] = time_state.state
        
        # Determine status message
        essential_meals = ["morning", "lunch", "evening"]
        essential_fed = sum(1 for meal in essential_meals if feeding_status.get(meal, False))
        
        if essential_fed == 0:
            status = "Noch nicht gefüttert"
            urgency = "high"
        elif essential_fed < 3:
            status = f"Teilweise gefüttert ({essential_fed}/3)"
            urgency = "medium"
        else:
            status = "Vollständig gefüttert"
            urgency = "low"
            
        if feeding_status.get("snack", False):
            status += " (mit Leckerli)"
        
        self._attr_native_value = total_feedings
        
        # Calculate next meal time
        next_meal = self._get_next_meal(feeding_status, feeding_times)
        
        # Check for overfeeding
        overfeeding_warning = total_feedings > 6  # More than 6 feedings per day
        
        self._attr_extra_state_attributes = {
            "status_text": status,
            "urgency": urgency,
            "meals_completed": total_fed,
            "essential_meals_completed": essential_fed,
            "feeding_details": feeding_status,
            "feeding_counts": feeding_counts,
            "total_feedings_today": total_feedings,
            "next_meal": next_meal,
            "scheduled_times": feeding_times,
            "overfeeding_warning": overfeeding_warning,
            "last_updated": datetime.now().isoformat(),
        }

    def _get_next_meal(self, feeding_status: dict, feeding_times: dict) -> str | None:
        """Get the next scheduled meal."""
        now = datetime.now()
        current_time = now.time()
        
        # Check each meal in order
        meal_order = ["morning", "lunch", "evening", "snack"]
        
        for meal in meal_order:
            if not feeding_status.get(meal, False):  # Meal not yet given
                scheduled_time = feeding_times.get(meal)
                if scheduled_time:
                    try:
                        meal_time = datetime.strptime(scheduled_time, "%H:%M:%S").time()
                        if current_time <= meal_time:
                            return f"{MEAL_TYPES[meal]} um {scheduled_time[:5]}"
                    except ValueError:
                        continue
        
        # If all meals are done or we're past all scheduled times
        if all(feeding_status.get(meal, False) for meal in ["morning", "lunch", "evening"]):
            return "Alle Hauptmahlzeiten erledigt"
        else:
            # Find first incomplete meal for tomorrow
            for meal in meal_order:
                if not feeding_status.get(meal, False):
                    scheduled_time = feeding_times.get(meal)
                    if scheduled_time:
                        return f"{MEAL_TYPES[meal]} morgen um {scheduled_time[:5]}"
        
        return None


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
        self._feeding_entities = [f"input_boolean.{dog_name}_feeding_{meal}" for meal in FEEDING_TYPES]
        self._activity_entities = [
            f"input_boolean.{dog_name}_outside",
            f"input_boolean.{dog_name}_poop_done",
        ]
        self._status_entities = [
            f"input_boolean.{dog_name}_visitor_mode_input",
            f"input_boolean.{dog_name}_emergency_mode",
            f"input_select.{dog_name}_health_status",
            f"binary_sensor.{dog_name}_needs_attention",
        ]

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Track all relevant entities
        tracked_entities = self._feeding_entities + self._activity_entities + self._status_entities
        async_track_state_change_event(
            self.hass, tracked_entities, self._async_status_changed
        )
        
        # Initial update
        await self._async_update_status()

    @callback
    def _async_status_changed(self, event) -> None:
        """Handle state changes that affect overall status."""
        # KORRIGIERT: @callback kann nicht mit async def verwendet werden
        self.hass.async_create_task(self._async_update_status())
        self.async_write_ha_state()

    async def _async_update_status(self) -> None:
        """Update the overall status."""
        # Check emergency mode first
        emergency_state = self.hass.states.get(f"input_boolean.{self._dog_name}_emergency_mode")
        if emergency_state and emergency_state.state == "on":
            self._attr_native_value = STATUS_MESSAGES["emergency"]
            self._attr_icon = ICONS["emergency"]
            self._attr_extra_state_attributes = {
                "priority": "critical",
                "emergency_mode": True,
                "last_updated": datetime.now().isoformat(),
            }
            return

        # Check health status
        health_state = self.hass.states.get(f"input_select.{self._dog_name}_health_status")
        health_status = health_state.state if health_state else "Gut"
        
        if health_status in ["Krank", "Notfall"]:
            self._attr_native_value = STATUS_MESSAGES["sick"]
            self._attr_icon = ICONS["health"]
            self._attr_extra_state_attributes = {
                "priority": "high",
                "health_issue": True,
                "health_status": health_status,
                "last_updated": datetime.now().isoformat(),
            }
            return

        # Check visitor mode
        visitor_state = self.hass.states.get(f"input_boolean.{self._dog_name}_visitor_mode_input")
        visitor_mode = visitor_state.state == "on" if visitor_state else False
        
        if visitor_mode:
            visitor_name_state = self.hass.states.get(f"input_text.{self._dog_name}_visitor_name")
            visitor_name = visitor_name_state.state if visitor_name_state else ""
            
            self._attr_native_value = STATUS_MESSAGES["visitor_mode"]
            self._attr_icon = ICONS["visitor"]
            self._attr_extra_state_attributes = {
                "priority": "normal",
                "visitor_mode": True,
                "visitor_name": visitor_name,
                "last_updated": datetime.now().isoformat(),
            }
            return

        # Check if attention is needed
        attention_state = self.hass.states.get(f"binary_sensor.{self._dog_name}_needs_attention")
        needs_attention = attention_state.state == "on" if attention_state else False
        
        if needs_attention:
            self._attr_native_value = STATUS_MESSAGES["attention_needed"]
            self._attr_icon = ICONS["attention"]
            
            # Get attention reasons
            attention_reasons = []
            if attention_state and attention_state.attributes:
                attention_reasons = attention_state.attributes.get("reasons", [])
            
            self._attr_extra_state_attributes = {
                "priority": "medium",
                "needs_attention": True,
                "attention_reasons": attention_reasons,
                "last_updated": datetime.now().isoformat(),
            }
            return

        # Check feeding and activity progress
        fed_count = sum(
            1 for entity_id in self._feeding_entities
            if self.hass.states.get(entity_id) and self.hass.states.get(entity_id).state == "on"
        )
        
        outside_state = self.hass.states.get(f"input_boolean.{self._dog_name}_outside")
        was_outside = outside_state.state == "on" if outside_state else False
        
        poop_state = self.hass.states.get(f"input_boolean.{self._dog_name}_poop_done")
        poop_done = poop_state.state == "on" if poop_state else False

        # Determine status based on completion
        total_main_meals = 3  # morning, lunch, evening
        if fed_count >= total_main_meals and was_outside and poop_done:
            self._attr_native_value = STATUS_MESSAGES["all_good"]
            self._attr_icon = ICONS["complete"]
            mood = "happy"
        elif fed_count < total_main_meals:
            self._attr_native_value = STATUS_MESSAGES["needs_feeding"]
            self._attr_icon = ICONS["food"]
            mood = "neutral"
        elif not was_outside:
            self._attr_native_value = STATUS_MESSAGES["needs_outside"]
            self._attr_icon = ICONS["walk"]
            mood = "bored"
        else:
            self._attr_native_value = STATUS_MESSAGES["happy"]
            self._attr_icon = ICONS["happy"]
            mood = "happy"
        
        # Calculate completion percentage
        total_tasks = 5  # 3 meals + outside + poop
        completed_tasks = min(fed_count, 3) + (1 if was_outside else 0) + (1 if poop_done else 0)
        completion_percentage = round((completed_tasks / total_tasks) * 100)
        
        self._attr_extra_state_attributes = {
            "priority": "low",
            "feeding_progress": f"{fed_count}/{len(self._feeding_entities)}",
            "was_outside": was_outside,
            "poop_done": poop_done,
            "completion_percentage": completion_percentage,
            "mood": mood,
            "health_status": health_status,
            "last_updated": datetime.now().isoformat(),
        }


# Weitere Sensor-Klassen hier mit den gleichen @callback Korrekturen...
class HundesystemActivitySensor(HundesystemSensorBase):
    """Sensor for activity tracking and analysis."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        dog_name: str,
    ) -> None:
        """Initialize the activity sensor."""
        super().__init__(hass, config_entry, dog_name, ENTITIES["activity"])
        self._attr_icon = ICONS["walk"]
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @callback
    def _async_activity_changed(self, event) -> None:
        """Handle activity changes."""
        # KORRIGIERT: @callback kann nicht mit async def verwendet werden
        self.hass.async_create_task(self._async_update_activity())
        self.async_write_ha_state()

    async def _async_update_activity(self) -> None:
        """Update the activity status."""
        self._attr_native_value = "Aktivität wird berechnet..."
        # Implementierung hier...


class HundesystemDailySummarySensor(HundesystemSensorBase):
    """Sensor for comprehensive daily summary."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        dog_name: str,
    ) -> None:
        """Initialize the daily summary sensor."""
        super().__init__(hass, config_entry, dog_name, ENTITIES["daily_summary"])
        self._attr_icon = ICONS["notes"]

    @callback
    def _async_summary_changed(self, event) -> None:
        """Handle summary relevant changes."""
        # KORRIGIERT: @callback kann nicht mit async def verwendet werden
        self.hass.async_create_task(self._async_update_summary())
        self.async_write_ha_state()

    async def _async_update_summary(self) -> None:
        """Update the daily summary."""
        self._attr_native_value = "Zusammenfassung wird erstellt..."
        # Implementierung hier...


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
        self._attr_device_class = SensorDeviceClass.TIMESTAMP

    @callback
    def _async_activity_tracked(self, event) -> None:
        """Handle activity tracking."""
        # KORRIGIERT: @callback kann nicht mit async def verwendet werden
        if event.data.get("new_state") and event.data["new_state"].state == "on":
            self.hass.async_create_task(self._async_update_last_activity(event.data["entity_id"]))
            self.async_write_ha_state()

    async def _async_update_last_activity(self, triggered_entity: str = None) -> None:
        """Update the last activity timestamp."""
        now = dt_util.now()
        self._attr_native_value = now.isoformat()
        # Weitere Implementierung...


class HundesystemHealthScoreSensor(HundesystemSensorBase):
    """Sensor for health score calculation."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry, dog_name: str) -> None:
        """Initialize the health score sensor."""
        super().__init__(hass, config_entry, dog_name, ENTITIES["health_score"])
        self._attr_icon = ICONS["health"]
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = "points"

    @callback
    def _async_health_changed(self, event) -> None:
        """Handle health-related changes."""
        # KORRIGIERT: @callback kann nicht mit async def verwendet werden
        self.hass.async_create_task(self._async_update_health_score())
        self.async_write_ha_state()

    async def _async_update_health_score(self) -> None:
        """Update the health score."""
        self._attr_native_value = 8.0  # Placeholder
        # Implementierung hier...


class HundesystemMoodSensor(HundesystemSensorBase):
    """Sensor for mood tracking."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry, dog_name: str) -> None:
        """Initialize the mood sensor."""
        super().__init__(hass, config_entry, dog_name, ENTITIES["mood"])
        self._attr_icon = ICONS["happy"]

    @callback
    def _async_mood_changed(self, event) -> None:
        """Handle mood-related changes."""
        # KORRIGIERT: @callback kann nicht mit async def verwendet werden
        self.hass.async_create_task(self._async_update_mood())
        self.async_write_ha_state()

    async def _async_update_mood(self) -> None:
        """Update the mood sensor."""
        self._attr_native_value = "Glücklich"  # Placeholder
        # Implementierung hier...


class HundesystemWeeklySummarySensor(HundesystemSensorBase):
    """Sensor for weekly summary."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry, dog_name: str) -> None:
        """Initialize the weekly summary sensor."""
        super().__init__(hass, config_entry, dog_name, ENTITIES["weekly_summary"])
        self._attr_icon = ICONS["status"]

    async def _async_update_weekly_summary(self) -> None:
        """Update the weekly summary."""
        now = datetime.now()
        week_start = now - timedelta(days=now.weekday())
        
        summary_text = f"Woche vom {week_start.strftime('%d.%m')} - {now.strftime('%d.%m')}"
        
        self._attr_native_value = summary_text
        
        self._attr_extra_state_attributes = {
            "week_start": week_start.isoformat(),
            "week_end": now.isoformat(),
            "days_in_week": now.weekday() + 1,
            "note": "Vollständige Implementierung folgt mit historischen Daten",
            "last_updated": now.isoformat(),
        }
