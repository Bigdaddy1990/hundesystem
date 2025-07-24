"""Sensor platform for Hundesystem integration - CORRECTED VERSION."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback, State
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_interval
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.entity import DeviceInfo
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
    """Base class for Hundesystem sensors with proper cleanup."""

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
        
        # Track event listeners for cleanup
        self._listeners: List[Callable[[], None]] = []
        
        # Device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, dog_name)},
            name=f"Hundesystem {dog_name.title()}",
            manufacturer="Hundesystem",
            model="Dog Management System",
            sw_version="2.0.3",
        )

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Restore previous state
        if (old_state := await self.async_get_last_state()) is not None:
            self._attr_native_value = old_state.state
            if old_state.attributes:
                self._attr_extra_state_attributes = dict(old_state.attributes)

    async def async_will_remove_from_hass(self) -> None:
        """Clean up when entity is removed."""
        # Remove all event listeners
        for remove_listener in self._listeners:
            try:
                remove_listener()
            except Exception as e:
                _LOGGER.warning("Error removing listener: %s", e)
        self._listeners.clear()
        
        await super().async_will_remove_from_hass()

    def _track_entity_changes(self, entities: List[str], callback_func: Callable) -> None:
        """Track entity changes with cleanup registration."""
        if not entities:
            return
            
        remove_listener = async_track_state_change_event(
            self.hass, entities, callback_func
        )
        self._listeners.append(remove_listener)

    def _track_time_interval(self, callback_func: Callable, interval: timedelta) -> None:
        """Track time intervals with cleanup registration."""
        remove_listener = async_track_time_interval(
            self.hass, callback_func, interval
        )
        self._listeners.append(remove_listener)


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
        self._attr_native_unit_of_measurement = "feedings"
        
        self._feeding_entities = [f"input_boolean.{dog_name}_feeding_{meal}" for meal in FEEDING_TYPES]
        self._feeding_counters = [f"counter.{dog_name}_feeding_{meal}_count" for meal in FEEDING_TYPES]
        self._feeding_times = [f"input_datetime.{dog_name}_feeding_{meal}_time" for meal in FEEDING_TYPES]

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Track feeding entities
        tracked_entities = self._feeding_entities + self._feeding_counters + self._feeding_times
        self._track_entity_changes(tracked_entities, self._feeding_status_changed)
        
        # Initial update
        await self._async_update_feeding_status()

    @callback
    def _feeding_status_changed(self, event) -> None:
        """Handle feeding status changes - CORRECTED: callback without async."""
        self.hass.async_create_task(self._async_update_feeding_status())
        self.async_write_ha_state()

    async def _async_update_feeding_status(self) -> None:
        """Update the feeding status."""
        try:
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
                count = int(counter_state.state) if counter_state and counter_state.state.isdigit() else 0
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
            
        except Exception as e:
            _LOGGER.error("Error updating feeding status for %s: %s", self._dog_name, e)
            self._attr_native_value = 0
            self._attr_extra_state_attributes = {
                "error": str(e),
                "last_updated": datetime.now().isoformat(),
            }

    def _get_next_meal(self, feeding_status: Dict[str, bool], feeding_times: Dict[str, str]) -> Optional[str]:
        """Get the next scheduled meal."""
        try:
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
            
        except Exception as e:
            _LOGGER.error("Error calculating next meal for %s: %s", self._dog_name, e)
            return "Fehler bei Berechnung"


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
        self._track_entity_changes(tracked_entities, self._status_changed)
        
        # Initial update
        await self._async_update_status()

    @callback
    def _status_changed(self, event) -> None:
        """Handle state changes that affect overall status - CORRECTED."""
        self.hass.async_create_task(self._async_update_status())
        self.async_write_ha_state()

    async def _async_update_status(self) -> None:
        """Update the overall status."""
        try:
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
            
        except Exception as e:
            _LOGGER.error("Error updating status for %s: %s", self._dog_name, e)
            self._attr_native_value = "Fehler"
            self._attr_extra_state_attributes = {
                "error": str(e),
                "last_updated": datetime.now().isoformat(),
            }


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
        self._attr_native_unit_of_measurement = "activities"
        
        # Track activity counters
        self._activity_counters = [
            f"counter.{dog_name}_outside_count",
            f"counter.{dog_name}_walk_count",
            f"counter.{dog_name}_play_count",
            f"counter.{dog_name}_training_count",
        ]

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Track activity counters
        self._track_entity_changes(self._activity_counters, self._activity_changed)
        
        # Initial update
        await self._async_update_activity()

    @callback
    def _activity_changed(self, event) -> None:
        """Handle activity changes - CORRECTED."""
        self.hass.async_create_task(self._async_update_activity())
        self.async_write_ha_state()

    async def _async_update_activity(self) -> None:
        """Update the activity status."""
        try:
            total_activities = 0
            activity_breakdown = {}
            
            # Sum all activity counters
            for counter_entity in self._activity_counters:
                state = self.hass.states.get(counter_entity)
                count = int(state.state) if state and state.state.isdigit() else 0
                
                # Extract activity type from entity name
                activity_type = counter_entity.split("_")[-2]  # e.g., "walk" from "counter.dog_walk_count"
                activity_breakdown[activity_type] = count
                total_activities += count
            
            self._attr_native_value = total_activities
            
            # Determine activity level
            if total_activities == 0:
                activity_level = "Keine Aktivität"
                recommendation = "Aktivität erforderlich"
            elif total_activities < 3:
                activity_level = "Wenig aktiv"
                recommendation = "Mehr Bewegung empfohlen"
            elif total_activities < 6:
                activity_level = "Normal aktiv"
                recommendation = "Gute Aktivität"
            else:
                activity_level = "Sehr aktiv"
                recommendation = "Ausgezeichnete Aktivität"
            
            self._attr_extra_state_attributes = {
                "activity_level": activity_level,
                "recommendation": recommendation,
                "activity_breakdown": activity_breakdown,
                "total_activities": total_activities,
                "last_updated": datetime.now().isoformat(),
            }
            
        except Exception as e:
            _LOGGER.error("Error updating activity for %s: %s", self._dog_name, e)
            self._attr_native_value = 0
            self._attr_extra_state_attributes = {
                "error": str(e),
                "last_updated": datetime.now().isoformat(),
            }


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

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Track relevant entities for summary
        summary_entities = [
            f"sensor.{self._dog_name}_feeding_status",
            f"sensor.{self._dog_name}_activity",
            f"input_select.{self._dog_name}_health_status",
            f"input_select.{self._dog_name}_mood",
        ]
        self._track_entity_changes(summary_entities, self._summary_changed)
        
        # Update summary every hour
        self._track_time_interval(self._periodic_summary_update, timedelta(hours=1))
        
        # Initial update
        await self._async_update_summary()

    @callback
    def _summary_changed(self, event) -> None:
        """Handle summary relevant changes - CORRECTED."""
        self.hass.async_create_task(self._async_update_summary())
        self.async_write_ha_state()

    @callback
    def _periodic_summary_update(self, now) -> None:
        """Periodic summary update - CORRECTED."""
        self.hass.async_create_task(self._async_update_summary())
        self.async_write_ha_state()

    async def _async_update_summary(self) -> None:
        """Update the daily summary."""
        try:
            now = datetime.now()
            
            # Get feeding status
            feeding_sensor = self.hass.states.get(f"sensor.{self._dog_name}_feeding_status")
            feeding_info = "Unbekannt"
            if feeding_sensor and feeding_sensor.attributes:
                feeding_info = feeding_sensor.attributes.get("status_text", "Unbekannt")
            
            # Get activity status
            activity_sensor = self.hass.states.get(f"sensor.{self._dog_name}_activity")
            activity_info = "Unbekannt"
            if activity_sensor and activity_sensor.attributes:
                activity_info = activity_sensor.attributes.get("activity_level", "Unbekannt")
            
            # Get health and mood
            health_state = self.hass.states.get(f"input_select.{self._dog_name}_health_status")
            health_status = health_state.state if health_state else "Gut"
            
            mood_state = self.hass.states.get(f"input_select.{self._dog_name}_mood")
            mood = mood_state.state if mood_state else "Glücklich"
            
            # Create summary text
            summary = f"Fütterung: {feeding_info}, Aktivität: {activity_info}, Gesundheit: {health_status}, Stimmung: {mood}"
            
            self._attr_native_value = summary
            
            # Detailed attributes
            self._attr_extra_state_attributes = {
                "date": now.date().isoformat(),
                "feeding_status": feeding_info,
                "activity_level": activity_info,
                "health_status": health_status,
                "mood": mood,
                "summary_time": now.strftime("%H:%M"),
                "last_updated": now.isoformat(),
            }
            
        except Exception as e:
            _LOGGER.error("Error updating daily summary for %s: %s", self._dog_name, e)
            self._attr_native_value = "Fehler bei Zusammenfassung"
            self._attr_extra_state_attributes = {
                "error": str(e),
                "last_updated": datetime.now().isoformat(),
            }


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

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Track activity datetime entities
        activity_entities = [
            f"input_datetime.{self._dog_name}_last_outside",
            f"input_datetime.{self._dog_name}_last_walk",
            f"input_datetime.{self._dog_name}_last_play",
            f"input_datetime.{self._dog_name}_last_activity",
        ]
        self._track_entity_changes(activity_entities, self._activity_tracked)
        
        # Initial update
        await self._async_update_last_activity()

    @callback
    def _activity_tracked(self, event) -> None:
        """Handle activity tracking - CORRECTED."""
        # Only update if state changed to a valid datetime
        if (event.data.get("new_state") and 
            event.data["new_state"].state not in ["unknown", "unavailable"]):
            self.hass.async_create_task(self._async_update_last_activity(event.data["entity_id"]))
            self.async_write_ha_state()

    async def _async_update_last_activity(self, triggered_entity: Optional[str] = None) -> None:
        """Update the last activity timestamp."""
        try:
            latest_activity = None
            latest_activity_type = "Unbekannt"
            
            # Check all activity datetime entities
            activity_types = {
                f"input_datetime.{self._dog_name}_last_outside": "Draußen",
                f"input_datetime.{self._dog_name}_last_walk": "Gassi",
                f"input_datetime.{self._dog_name}_last_play": "Spielen",
                f"input_datetime.{self._dog_name}_last_activity": "Allgemeine Aktivität",
            }
            
            for entity_id, activity_name in activity_types.items():
                state = self.hass.states.get(entity_id)
                if state and state.state not in ["unknown", "unavailable"]:
                    try:
                        activity_time = datetime.fromisoformat(state.state.replace("Z", "+00:00"))
                        if latest_activity is None or activity_time > latest_activity:
                            latest_activity = activity_time
                            latest_activity_type = activity_name
                    except ValueError:
                        continue
            
            if latest_activity:
                self._attr_native_value = latest_activity.isoformat()
                
                # Calculate time since
                now = dt_util.now()
                if latest_activity.tzinfo is None:
                    latest_activity = dt_util.as_local(latest_activity)
                
                time_since = now - latest_activity
                hours_since = time_since.total_seconds() / 3600
                
                if hours_since < 1:
                    time_ago = f"{int(time_since.total_seconds() / 60)} Minuten"
                elif hours_since < 24:
                    time_ago = f"{int(hours_since)} Stunden"
                else:
                    time_ago = f"{int(hours_since / 24)} Tage"
                
                self._attr_extra_state_attributes = {
                    "activity_type": latest_activity_type,
                    "time_ago": time_ago,
                    "hours_since": round(hours_since, 1),
                    "triggered_by": triggered_entity,
                    "last_updated": now.isoformat(),
                }
            else:
                self._attr_native_value = None
                self._attr_extra_state_attributes = {
                    "activity_type": "Keine Aktivität aufgezeichnet",
                    "last_updated": datetime.now().isoformat(),
                }
                
        except Exception as e:
            _LOGGER.error("Error updating last activity for %s: %s", self._dog_name, e)
            self._attr_native_value = None
            self._attr_extra_state_attributes = {
                "error": str(e),
                "last_updated": datetime.now().isoformat(),
            }


class HundesystemHealthScoreSensor(HundesystemSensorBase):
    """Sensor for health score calculation."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry, dog_name: str) -> None:
        """Initialize the health score sensor."""
        super().__init__(hass, config_entry, dog_name, ENTITIES["health_score"])
        self._attr_icon = ICONS["health"]
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = "points"

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Track health-related entities
        health_entities = [
            f"input_select.{self._dog_name}_health_status",
            f"input_select.{self._dog_name}_mood",
            f"input_number.{self._dog_name}_temperature",
            f"input_number.{self._dog_name}_weight",
            f"input_boolean.{self._dog_name}_medication_given",
            f"sensor.{self._dog_name}_feeding_status",
            f"sensor.{self._dog_name}_activity",
        ]
        self._track_entity_changes(health_entities, self._health_changed)
        
        # Update health score every 30 minutes
        self._track_time_interval(self._periodic_health_update, timedelta(minutes=30))
        
        # Initial update
        await self._async_update_health_score()

    @callback
    def _health_changed(self, event) -> None:
        """Handle health-related changes - CORRECTED."""
        self.hass.async_create_task(self._async_update_health_score())
        self.async_write_ha_state()

    @callback
    def _periodic_health_update(self, now) -> None:
        """Periodic health update - CORRECTED."""
        self.hass.async_create_task(self._async_update_health_score())
        self.async_write_ha_state()

    async def _async_update_health_score(self) -> None:
        """Update the health score based on various factors."""
        try:
            base_score = 10.0  # Start with perfect score
            factors = {}
            
            # Health status factor (most important)
            health_state = self.hass.states.get(f"input_select.{self._dog_name}_health_status")
            health_status = health_state.state if health_state else "Gut"
            
            health_multipliers = {
                "Ausgezeichnet": 1.0,
                "Gut": 0.9,
                "Normal": 0.8,
                "Schwach": 0.6,
                "Krank": 0.4,
                "Notfall": 0.1
            }
            health_factor = health_multipliers.get(health_status, 0.8)
            factors["health_status"] = {"value": health_status, "factor": health_factor}
            
            # Mood factor
            mood_state = self.hass.states.get(f"input_select.{self._dog_name}_mood")
            mood = mood_state.state if mood_state else "Glücklich"
            
            mood_multipliers = {
                "Sehr glücklich": 1.0,
                "Glücklich": 0.95,
                "Neutral": 0.85,
                "Gestresst": 0.7,
                "Ängstlich": 0.6,
                "Krank": 0.3
            }
            mood_factor = mood_multipliers.get(mood, 0.85)
            factors["mood"] = {"value": mood, "factor": mood_factor}
            
            # Temperature factor
            temp_state = self.hass.states.get(f"input_number.{self._dog_name}_temperature")
            if temp_state and temp_state.state not in ["unknown", "unavailable"]:
                try:
                    temperature = float(temp_state.state)
                    # Normal dog temperature: 37.5-39.0°C
                    if 37.5 <= temperature <= 39.0:
                        temp_factor = 1.0
                    elif 37.0 <= temperature < 37.5 or 39.0 < temperature <= 39.5:
                        temp_factor = 0.9
                    elif 36.5 <= temperature < 37.0 or 39.5 < temperature <= 40.0:
                        temp_factor = 0.7
                    else:
                        temp_factor = 0.5
                    factors["temperature"] = {"value": temperature, "factor": temp_factor}
                except ValueError:
                    pass
            
            # Activity factor
            activity_sensor = self.hass.states.get(f"sensor.{self._dog_name}_activity")
            if activity_sensor and activity_sensor.state not in ["unknown", "unavailable"]:
                try:
                    activity_count = int(activity_sensor.state)
                    if activity_count >= 5:
                        activity_factor = 1.0
                    elif activity_count >= 3:
                        activity_factor = 0.9
                    elif activity_count >= 1:
                        activity_factor = 0.8
                    else:
                        activity_factor = 0.6
                    factors["activity"] = {"value": activity_count, "factor": activity_factor}
                except ValueError:
                    pass
            
            # Feeding factor
            feeding_sensor = self.hass.states.get(f"sensor.{self._dog_name}_feeding_status")
            if feeding_sensor and feeding_sensor.attributes:
                urgency = feeding_sensor.attributes.get("urgency", "medium")
                if urgency == "low":
                    feeding_factor = 1.0
                elif urgency == "medium":
                    feeding_factor = 0.85
                else:
                    feeding_factor = 0.7
                factors["feeding"] = {"value": urgency, "factor": feeding_factor}
            
            # Calculate weighted score
            weights = {
                "health_status": 0.4,
                "mood": 0.2,
                "temperature": 0.15,
                "activity": 0.15,
                "feeding": 0.1
            }
            
            calculated_score = base_score
            for factor_name, factor_data in factors.items():
                weight = weights.get(factor_name, 0.1)
                calculated_score *= (1 - weight + weight * factor_data["factor"])
            
            # Round to one decimal place
            final_score = round(calculated_score, 1)
            
            self._attr_native_value = final_score
            
            # Determine score category
            if final_score >= 9.0:
                score_category = "Ausgezeichnet"
                score_color = "green"
            elif final_score >= 7.5:
                score_category = "Gut"
                score_color = "lightgreen"
            elif final_score >= 6.0:
                score_category = "Normal"
                score_color = "yellow"
            elif final_score >= 4.0:
                score_category = "Bedenklich"
                score_color = "orange"
            else:
                score_category = "Kritisch"
                score_color = "red"
            
            self._attr_extra_state_attributes = {
                "score_category": score_category,
                "score_color": score_color,
                "factors": factors,
                "calculation_method": "weighted_average",
                "max_score": base_score,
                "last_updated": datetime.now().isoformat(),
            }
            
        except Exception as e:
            _LOGGER.error("Error updating health score for %s: %s", self._dog_name, e)
            self._attr_native_value = 5.0  # Default to middle score
            self._attr_extra_state_attributes = {
                "error": str(e),
                "last_updated": datetime.now().isoformat(),
            }


class HundesystemMoodSensor(HundesystemSensorBase):
    """Sensor for mood tracking and analysis."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry, dog_name: str) -> None:
        """Initialize the mood sensor."""
        super().__init__(hass, config_entry, dog_name, ENTITIES["mood"])
        self._attr_icon = ICONS["happy"]

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Track mood-related entities
        mood_entities = [
            f"input_select.{self._dog_name}_mood",
            f"input_select.{self._dog_name}_health_status",
            f"sensor.{self._dog_name}_activity",
            f"input_boolean.{self._dog_name}_visitor_mode_input",
            f"input_boolean.{self._dog_name}_emergency_mode",
        ]
        self._track_entity_changes(mood_entities, self._mood_changed)
        
        # Initial update
        await self._async_update_mood()

    @callback
    def _mood_changed(self, event) -> None:
        """Handle mood-related changes - CORRECTED."""
        self.hass.async_create_task(self._async_update_mood())
        self.async_write_ha_state()

    async def _async_update_mood(self) -> None:
        """Update the mood sensor with analysis."""
        try:
            # Get base mood
            mood_state = self.hass.states.get(f"input_select.{self._dog_name}_mood")
            base_mood = mood_state.state if mood_state else "Glücklich"
            
            # Get influencing factors
            health_state = self.hass.states.get(f"input_select.{self._dog_name}_health_status")
            health_status = health_state.state if health_state else "Gut"
            
            emergency_state = self.hass.states.get(f"input_boolean.{self._dog_name}_emergency_mode")
            emergency_mode = emergency_state.state == "on" if emergency_state else False
            
            visitor_state = self.hass.states.get(f"input_boolean.{self._dog_name}_visitor_mode_input")
            visitor_mode = visitor_state.state == "on" if visitor_state else False
            
            # Get activity level
            activity_sensor = self.hass.states.get(f"sensor.{self._dog_name}_activity")
            activity_count = 0
            if activity_sensor and activity_sensor.state not in ["unknown", "unavailable"]:
                try:
                    activity_count = int(activity_sensor.state)
                except ValueError:
                    pass
            
            # Analyze mood influences
            mood_influences = []
            adjusted_mood = base_mood
            
            if emergency_mode:
                adjusted_mood = "Notfall/Gestresst"
                mood_influences.append("Notfallmodus aktiv")
                
            elif health_status in ["Krank", "Notfall"]:
                if base_mood not in ["Krank", "Ängstlich"]:
                    adjusted_mood = "Krank"
                mood_influences.append(f"Gesundheit: {health_status}")
                
            elif health_status == "Schwach":
                if base_mood in ["Sehr glücklich", "Glücklich"]:
                    adjusted_mood = "Neutral"
                mood_influences.append("Gesundheit schwach")
                
            elif activity_count == 0:
                if base_mood in ["Sehr glücklich", "Glücklich"]:
                    adjusted_mood = "Gelangweilt"
                mood_influences.append("Keine Aktivität heute")
                
            elif activity_count >= 5:
                if base_mood in ["Neutral", "Gestresst"]:
                    adjusted_mood = "Glücklich"
                mood_influences.append("Sehr aktiv")
            
            if visitor_mode:
                mood_influences.append("Besuchsmodus")
            
            # Set icon based on mood
            mood_icons = {
                "Sehr glücklich": "mdi:emoticon-excited",
                "Glücklich": "mdi:emoticon-happy",
                "Neutral": "mdi:emoticon-neutral",
                "Gelangweilt": "mdi:emoticon-sad",
                "Gestresst": "mdi:emoticon-confused",
                "Ängstlich": "mdi:emoticon-cry",
                "Krank": "mdi:emoticon-sick",
                "Notfall/Gestresst": "mdi:alert-circle"
            }
            self._attr_icon = mood_icons.get(adjusted_mood, ICONS["happy"])
            
            self._attr_native_value = adjusted_mood
            
            # Mood recommendations
            recommendations = []
            if adjusted_mood in ["Gestresst", "Ängstlich"]:
                recommendations.append("Ruhige Umgebung schaffen")
                recommendations.append("Entspannungsübungen")
            elif adjusted_mood == "Gelangweilt":
                recommendations.append("Mehr Spielzeit")
                recommendations.append("Neue Aktivitäten einführen")
            elif adjusted_mood == "Krank":
                recommendations.append("Tierarzt konsultieren")
                recommendations.append("Ruhe und Beobachtung")
            elif adjusted_mood == "Sehr glücklich":
                recommendations.append("Aktivitätslevel beibehalten")
            
            self._attr_extra_state_attributes = {
                "base_mood": base_mood,
                "adjusted_mood": adjusted_mood,
                "influences": mood_influences,
                "recommendations": recommendations,
                "health_status": health_status,
                "activity_count": activity_count,
                "visitor_mode": visitor_mode,
                "emergency_mode": emergency_mode,
                "last_updated": datetime.now().isoformat(),
            }
            
        except Exception as e:
            _LOGGER.error("Error updating mood for %s: %s", self._dog_name, e)
            self._attr_native_value = "Unbekannt"
            self._attr_extra_state_attributes = {
                "error": str(e),
                "last_updated": datetime.now().isoformat(),
            }


class HundesystemWeeklySummarySensor(HundesystemSensorBase):
    """Sensor for weekly summary and trends."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry, dog_name: str) -> None:
        """Initialize the weekly summary sensor."""
        super().__init__(hass, config_entry, dog_name, ENTITIES["weekly_summary"])
        self._attr_icon = ICONS["status"]

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Update weekly summary once daily at midnight
        self._track_time_interval(self._daily_summary_update, timedelta(hours=24))
        
        # Initial update
        await self._async_update_weekly_summary()

    @callback
    def _daily_summary_update(self, now) -> None:
        """Daily summary update - CORRECTED."""
        # Only update if it's close to midnight (within 1 hour)
        if now.hour == 0:
            self.hass.async_create_task(self._async_update_weekly_summary())
            self.async_write_ha_state()

    async def _async_update_weekly_summary(self) -> None:
        """Update the weekly summary with trends."""
        try:
            now = datetime.now()
            week_start = now - timedelta(days=now.weekday())
            
            # Create summary text
            summary_text = f"Woche vom {week_start.strftime('%d.%m')} - {now.strftime('%d.%m')}"
            
            # Get current week statistics (simplified as we don't have historical data)
            current_stats = {}
            
            # Get current counters as week summary
            counter_entities = [
                f"counter.{self._dog_name}_feeding_morning_count",
                f"counter.{self._dog_name}_feeding_lunch_count",
                f"counter.{self._dog_name}_feeding_evening_count",
                f"counter.{self._dog_name}_outside_count",
                f"counter.{self._dog_name}_walk_count",
                f"counter.{self._dog_name}_play_count",
            ]
            
            for entity_id in counter_entities:
                state = self.hass.states.get(entity_id)
                if state and state.state.isdigit():
                    counter_name = entity_id.split("_")[-2]  # Extract activity type
                    current_stats[counter_name] = int(state.state)
            
            # Calculate totals
            total_feedings = sum(current_stats.get(meal, 0) for meal in ["morning", "lunch", "evening"])
            total_activities = sum(current_stats.get(activity, 0) for activity in ["outside", "walk", "play"])
            
            # Weekly assessment
            if total_feedings >= 18:  # 3 meals * 6 days (assuming some flexibility)
                feeding_assessment = "Ausgezeichnet"
            elif total_feedings >= 12:
                feeding_assessment = "Gut"
            else:
                feeding_assessment = "Verbesserungsbedarf"
            
            if total_activities >= 14:  # 2 activities per day
                activity_assessment = "Sehr aktiv"
            elif total_activities >= 7:
                activity_assessment = "Aktiv"
            else:
                activity_assessment = "Mehr Bewegung nötig"
            
            self._attr_native_value = summary_text
            
            self._attr_extra_state_attributes = {
                "week_start": week_start.isoformat(),
                "week_end": now.isoformat(),
                "days_in_week": now.weekday() + 1,
                "current_stats": current_stats,
                "total_feedings": total_feedings,
                "total_activities": total_activities,
                "feeding_assessment": feeding_assessment,
                "activity_assessment": activity_assessment,
                "note": "Basiert auf aktuellen Tagesstatistiken",
                "last_updated": now.isoformat(),
            }
            
        except Exception as e:
            _LOGGER.error("Error updating weekly summary for %s: %s", self._dog_name, e)
            self._attr_native_value = "Fehler bei Wochenzusammenfassung"
            self._attr_extra_state_attributes = {
                "error": str(e),
                "last_updated": datetime.now().isoformat(),
            }
