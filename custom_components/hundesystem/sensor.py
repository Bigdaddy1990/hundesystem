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
                self._attr_extra_state_attributes = {
                    "priority": "medium",
                    "needs_attention": True,
                    "last_updated": datetime.now().isoformat(),
                }
                return

            # Check basic needs
            basic_needs_met = self._check_basic_needs()
            
            if basic_needs_met["all_met"]:
                self._attr_native_value = STATUS_MESSAGES["happy"]
                self._attr_icon = ICONS["happy"]
                priority = "low"
            else:
                unmet_needs = basic_needs_met["unmet_needs"]
                if len(unmet_needs) >= 3:
                    self._attr_native_value = STATUS_MESSAGES["needs_care"]
                    self._attr_icon = ICONS["attention"]
                    priority = "high"
                else:
                    self._attr_native_value = STATUS_MESSAGES["okay"]
                    self._attr_icon = ICONS["dog"]
                    priority = "medium"

            self._attr_extra_state_attributes = {
                "priority": priority,
                "basic_needs": basic_needs_met,
                "health_status": health_status,
                "visitor_mode": visitor_mode,
                "emergency_mode": False,
                "last_updated": datetime.now().isoformat(),
            }
            
        except Exception as e:
            _LOGGER.error("Error updating status for %s: %s", self._dog_name, e)
            self._attr_native_value = "Fehler"
            self._attr_icon = "mdi:alert-circle"
            self._attr_extra_state_attributes = {
                "error": str(e),
                "last_updated": datetime.now().isoformat(),
            }

    def _check_basic_needs(self) -> Dict[str, Any]:
        """Check if basic needs are met."""
        needs = {
            "fed": False,
            "outside": False,
            "poop": False,
        }
        
        unmet_needs = []
        
        # Check feeding (at least morning meal)
        morning_fed_state = self.hass.states.get(f"input_boolean.{self._dog_name}_feeding_morning")
        needs["fed"] = morning_fed_state.state == "on" if morning_fed_state else False
        if not needs["fed"]:
            unmet_needs.append("Frühstück")
        
        # Check outside activity
        outside_state = self.hass.states.get(f"input_boolean.{self._dog_name}_outside")
        needs["outside"] = outside_state.state == "on" if outside_state else False
        if not needs["outside"]:
            unmet_needs.append("Draußen")
            
        # Check bathroom needs
        poop_state = self.hass.states.get(f"input_boolean.{self._dog_name}_poop_done")
        needs["poop"] = poop_state.state == "on" if poop_state else False
        if not needs["poop"]:
            unmet_needs.append("Geschäft")
        
        return {
            "all_met": len(unmet_needs) == 0,
            "unmet_needs": unmet_needs,
            "needs_detail": needs,
            "met_count": sum(needs.values()),
            "total_count": len(needs),
        }


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
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_native_unit_of_measurement = "activities"
        
        self._activity_counters = [
            f"counter.{dog_name}_outside_count",
            f"counter.{dog_name}_walk_count",
            f"counter.{dog_name}_play_count",
            f"counter.{dog_name}_training_count",
        ]
        
        self._activity_times = [
            f"input_datetime.{dog_name}_last_outside",
            f"input_datetime.{dog_name}_last_walk",
            f"input_datetime.{dog_name}_last_play",
            f"input_datetime.{dog_name}_last_training",
        ]

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Track activity entities
        tracked_entities = self._activity_counters + self._activity_times
        self._track_entity_changes(tracked_entities, self._activity_changed)
        
        # Update every hour
        self._track_time_interval(self._periodic_update, timedelta(hours=1))
        
        # Initial update
        await self._async_update_activity()

    @callback
    def _activity_changed(self, event) -> None:
        """Handle activity changes - CORRECTED."""
        self.hass.async_create_task(self._async_update_activity())
        self.async_write_ha_state()

    @callback
    def _periodic_update(self, time) -> None:
        """Periodic update callback - CORRECTED."""
        self.hass.async_create_task(self._async_update_activity())

    async def _async_update_activity(self) -> None:
        """Update the activity status."""
        try:
            activity_counts = {}
            activity_times = {}
            total_activities = 0
            
            activity_types = ["outside", "walk", "play", "training"]
            
            for i, activity in enumerate(activity_types):
                # Get counter value
                counter_entity = self._activity_counters[i]
                counter_state = self.hass.states.get(counter_entity)
                count = int(counter_state.state) if counter_state and counter_state.state.isdigit() else 0
                activity_counts[activity] = count
                total_activities += count
                
                # Get last time
                time_entity = self._activity_times[i]
                time_state = self.hass.states.get(time_entity)
                if time_state and time_state.state not in ["unknown", "unavailable"]:
                    activity_times[f"last_{activity}"] = time_state.state
            
            # Calculate activity level
            activity_level = self._calculate_activity_level(activity_counts)
            
            # Find most recent activity
            most_recent_activity = self._get_most_recent_activity(activity_times)
            
            # Check if dog needs more activity
            needs_activity = self._check_activity_needs(activity_counts, activity_times)
            
            self._attr_native_value = total_activities
            
            self._attr_extra_state_attributes = {
                "activity_counts": activity_counts,
                "activity_times": activity_times,
                "activity_level": activity_level,
                "most_recent_activity": most_recent_activity,
                "needs_more_activity": needs_activity["needs_more"],
                "activity_recommendations": needs_activity["recommendations"],
                "total_today": total_activities,
                "last_updated": datetime.now().isoformat(),
            }
            
        except Exception as e:
            _LOGGER.error("Error updating activity for %s: %s", self._dog_name, e)
            self._attr_native_value = 0
            self._attr_extra_state_attributes = {
                "error": str(e),
                "last_updated": datetime.now().isoformat(),
            }

    def _calculate_activity_level(self, activity_counts: Dict[str, int]) -> str:
        """Calculate overall activity level."""
        total = sum(activity_counts.values())
        
        if total == 0:
            return "Sehr niedrig"
        elif total <= 2:
            return "Niedrig"
        elif total <= 5:
            return "Normal"
        elif total <= 8:
            return "Hoch"
        else:
            return "Sehr hoch"

    def _get_most_recent_activity(self, activity_times: Dict[str, str]) -> Optional[str]:
        """Get the most recent activity."""
        try:
            most_recent = None
            most_recent_time = None
            
            for activity, time_str in activity_times.items():
                if time_str and time_str not in ["unknown", "unavailable"]:
                    try:
                        activity_time = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
                        if most_recent_time is None or activity_time > most_recent_time:
                            most_recent = activity.replace("last_", "")
                            most_recent_time = activity_time
                    except ValueError:
                        continue
            
            if most_recent and most_recent_time:
                time_ago = datetime.now(most_recent_time.tzinfo) - most_recent_time
                hours_ago = time_ago.total_seconds() / 3600
                
                if hours_ago < 1:
                    time_desc = "vor weniger als 1 Stunde"
                elif hours_ago < 24:
                    time_desc = f"vor {int(hours_ago)} Stunden"
                else:
                    days_ago = int(hours_ago / 24)
                    time_desc = f"vor {days_ago} Tag(en)"
                
                return f"{ACTIVITY_TYPES.get(most_recent, most_recent)} {time_desc}"
            
            return "Keine Aktivität heute"
            
        except Exception as e:
            _LOGGER.error("Error calculating most recent activity: %s", e)
            return "Fehler bei Berechnung"

    def _check_activity_needs(self, activity_counts: Dict[str, int], activity_times: Dict[str, str]) -> Dict[str, Any]:
        """Check if dog needs more activity."""
        recommendations = []
        needs_more = False
        
        # Check minimum requirements
        if activity_counts.get("outside", 0) < 3:
            needs_more = True
            recommendations.append("Mehr Gartenbesuche")
        
        if activity_counts.get("walk", 0) < 1:
            needs_more = True
            recommendations.append("Spaziergang")
        
        # Check time since last activities
        now = datetime.now()
        
        # Check outside time
        last_outside = activity_times.get("last_outside")
        if last_outside:
            try:
                last_time = datetime.fromisoformat(last_outside.replace("Z", "+00:00"))
                hours_since = (now - last_time.replace(tzinfo=None)).total_seconds() / 3600
                if hours_since > 6:
                    needs_more = True
                    recommendations.append("War lange nicht draußen")
            except ValueError:
                pass
        
        return {
            "needs_more": needs_more,
            "recommendations": recommendations,
        }


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
        self._attr_icon = ICONS["status"]
        self._attr_native_unit_of_measurement = "points"

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Update every 30 minutes
        self._track_time_interval(self._periodic_summary_update, timedelta(minutes=30))
        
        # Initial update
        await self._async_update_daily_summary()

    @callback
    def _periodic_summary_update(self, time) -> None:
        """Periodic summary update - CORRECTED."""
        self.hass.async_create_task(self._async_update_daily_summary())

    async def _async_update_daily_summary(self) -> None:
        """Update the daily summary."""
        try:
            # Get feeding status
            feeding_score = self._calculate_feeding_score()
            
            # Get activity score
            activity_score = self._calculate_activity_score()
            
            # Get health score
            health_score = self._calculate_health_score()
            
            # Calculate overall score
            overall_score = (feeding_score + activity_score + health_score) / 3
            
            # Determine daily rating
            if overall_score >= 9:
                rating = "Perfekter Tag"
                icon = ICONS["happy"]
            elif overall_score >= 7:
                rating = "Guter Tag"
                icon = ICONS["dog"]
            elif overall_score >= 5:
                rating = "Durchschnittlicher Tag"
                icon = ICONS["status"]
            else:
                rating = "Verbesserungswürdiger Tag"
                icon = ICONS["attention"]
            
            self._attr_native_value = round(overall_score, 1)
            self._attr_icon = icon
            
            self._attr_extra_state_attributes = {
                "daily_rating": rating,
                "feeding_score": feeding_score,
                "activity_score": activity_score,
                "health_score": health_score,
                "overall_score": overall_score,
                "recommendations": self._get_daily_recommendations(feeding_score, activity_score, health_score),
                "date": datetime.now().date().isoformat(),
                "last_updated": datetime.now().isoformat(),
            }
            
        except Exception as e:
            _LOGGER.error("Error updating daily summary for %s: %s", self._dog_name, e)
            self._attr_native_value = 0
            self._attr_extra_state_attributes = {
                "error": str(e),
                "last_updated": datetime.now().isoformat(),
            }

    def _calculate_feeding_score(self) -> float:
        """Calculate feeding score (0-10)."""
        score = 0
        
        # Essential meals (7 points total)
        essential_meals = ["morning", "lunch", "evening"]
        for meal in essential_meals:
            state = self.hass.states.get(f"input_boolean.{self._dog_name}_feeding_{meal}")
            if state and state.state == "on":
                score += 2.33  # ~7 points for all 3 meals
        
        # Snack bonus (1 point)
        snack_state = self.hass.states.get(f"input_boolean.{self._dog_name}_feeding_snack")
        if snack_state and snack_state.state == "on":
            score += 1
        
        # Regularity bonus (2 points) - check if meals were on time
        score += 2  # Simplified - assume on time for now
        
        return min(score, 10)

    def _calculate_activity_score(self) -> float:
        """Calculate activity score (0-10)."""
        score = 0
        
        # Outside visits (4 points)
        outside_count_state = self.hass.states.get(f"counter.{self._dog_name}_outside_count")
        outside_count = int(outside_count_state.state) if outside_count_state and outside_count_state.state.isdigit() else 0
        score += min(outside_count * 1, 4)  # Max 4 points
        
        # Walks (3 points)
        walk_count_state = self.hass.states.get(f"counter.{self._dog_name}_walk_count")
        walk_count = int(walk_count_state.state) if walk_count_state and walk_count_state.state.isdigit() else 0
        score += min(walk_count * 1.5, 3)  # Max 3 points
        
        # Play time (2 points)
        play_count_state = self.hass.states.get(f"counter.{self._dog_name}_play_count")
        play_count = int(play_count_state.state) if play_count_state and play_count_state.state.isdigit() else 0
        score += min(play_count * 1, 2)  # Max 2 points
        
        # Training (1 point)
        training_count_state = self.hass.states.get(f"counter.{self._dog_name}_training_count")
        training_count = int(training_count_state.state) if training_count_state and training_count_state.state.isdigit() else 0
        score += min(training_count * 1, 1)  # Max 1 point
        
        return min(score, 10)

    def _calculate_health_score(self) -> float:
        """Calculate health score (0-10)."""
        score = 10  # Start with perfect score
        
        # Health status
        health_state = self.hass.states.get(f"input_select.{self._dog_name}_health_status")
        health_status = health_state.state if health_state else "Gut"
        
        health_scores = {
            "Ausgezeichnet": 10,
            "Gut": 8,
            "Normal": 6,
            "Schwach": 4,
            "Krank": 2,
            "Notfall": 0,
        }
        score = health_scores.get(health_status, 6)
        
        # Emergency mode penalty
        emergency_state = self.hass.states.get(f"input_boolean.{self._dog_name}_emergency_mode")
        if emergency_state and emergency_state.state == "on":
            score = min(score, 2)
        
        return score

    def _get_daily_recommendations(self, feeding_score: float, activity_score: float, health_score: float) -> List[str]:
        """Get recommendations for improving the day."""
        recommendations = []
        
        if feeding_score < 7:
            recommendations.append("Regelmäßigere Fütterung")
        
        if activity_score < 6:
            recommendations.append("Mehr Bewegung und Aktivität")
        
        if health_score < 8:
            recommendations.append("Gesundheit beobachten")
        
        if not recommendations:
            recommendations.append("Weiter so! Perfekte Pflege!")
        
        return recommendations


class HundesystemLastActivitySensor(HundesystemSensorBase):
    """Sensor for last activity tracking."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        dog_name: str,
    ) -> None:
        """Initialize the last activity sensor."""
        super().__init__(hass, config_entry, dog_name, ENTITIES["last_activity"])
        self._attr_icon = ICONS["status"]
        self._attr_device_class = SensorDeviceClass.TIMESTAMP
        
        self._activity_times = [
            f"input_datetime.{dog_name}_last_outside",
            f"input_datetime.{dog_name}_last_walk",
            f"input_datetime.{dog_name}_last_play",
            f"input_datetime.{dog_name}_last_training",
            f"input_datetime.{dog_name}_last_feeding_morning",
            f"input_datetime.{dog_name}_last_feeding_lunch",
            f"input_datetime.{dog_name}_last_feeding_evening",
            f"input_datetime.{dog_name}_last_feeding_snack",
        ]

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Track activity time entities
        self._track_entity_changes(self._activity_times, self._last_activity_changed)
        
        # Initial update
        await self._async_update_last_activity()

    @callback
    def _last_activity_changed(self, event) -> None:
        """Handle last activity changes - CORRECTED."""
        self.hass.async_create_task(self._async_update_last_activity())
        self.async_write_ha_state()

    async def _async_update_last_activity(self) -> None:
        """Update the last activity timestamp."""
        try:
            latest_activity = None
            latest_time = None
            activity_details = {}
            
            activity_names = {
                "last_outside": "Draußen",
                "last_walk": "Spaziergang", 
                "last_play": "Spielen",
                "last_training": "Training",
                "last_feeding_morning": "Frühstück",
                "last_feeding_lunch": "Mittagessen",
                "last_feeding_evening": "Abendessen",
                "last_feeding_snack": "Leckerli",
            }
            
            for entity_id in self._activity_times:
                state = self.hass.states.get(entity_id)
                if state and state.state not in ["unknown", "unavailable"]:
                    try:
                        activity_time = datetime.fromisoformat(state.state.replace("Z", "+00:00"))
                        
                        # Extract activity name from entity id
                        activity_key = entity_id.split(f"{self._dog_name}_")[1]
                        activity_name = activity_names.get(activity_key, activity_key)
                        
                        activity_details[activity_name] = {
                            "time": state.state,
                            "time_ago": self._get_time_ago(activity_time),
                        }
                        
                        if latest_time is None or activity_time > latest_time:
                            latest_activity = activity_name
                            latest_time = activity_time
                            
                    except ValueError as e:
                        _LOGGER.debug("Error parsing time for %s: %s", entity_id, e)
                        continue
            
            if latest_time:
                self._attr_native_value = latest_time.isoformat()
                time_ago = self._get_time_ago(latest_time)
            else:
                self._attr_native_value = None
                time_ago = "Keine Aktivität aufgezeichnet"
            
            self._attr_extra_state_attributes = {
                "last_activity_type": latest_activity,
                "time_ago": time_ago,
                "all_activities": activity_details,
                "total_activities_tracked": len(activity_details),
                "last_updated": datetime.now().isoformat(),
            }
            
        except Exception as e:
            _LOGGER.error("Error updating last activity for %s: %s", self._dog_name, e)
            self._attr_native_value = None
            self._attr_extra_state_attributes = {
                "error": str(e),
                "last_updated": datetime.now().isoformat(),
            }

    def _get_time_ago(self, activity_time: datetime) -> str:
        """Get human-readable time ago string."""
        try:
            now = datetime.now(activity_time.tzinfo)
            time_diff = now - activity_time
            
            total_seconds = time_diff.total_seconds()
            
            if total_seconds < 60:
                return "vor weniger als 1 Minute"
            elif total_seconds < 3600:
                minutes = int(total_seconds / 60)
                return f"vor {minutes} Minute(n)"
            elif total_seconds < 86400:
                hours = int(total_seconds / 3600)
                return f"vor {hours} Stunde(n)"
            else:
                days = int(total_seconds / 86400)
                return f"vor {days} Tag(en)"
                
        except Exception:
            return "Unbekannt"


class HundesystemHealthScoreSensor(HundesystemSensorBase):
    """Sensor for health score calculation."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        dog_name: str,
    ) -> None:
        """Initialize the health score sensor."""
        super().__init__(hass, config_entry, dog_name, ENTITIES["health_score"])
        self._attr_icon = ICONS["health"]
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = "points"
        
        self._health_entities = [
            f"input_select.{dog_name}_health_status",
            f"input_select.{dog_name}_mood",
            f"input_select.{dog_name}_energy_level_category",
            f"input_select.{dog_name}_appetite_level",
            f"input_number.{dog_name}_health_score",
            f"input_boolean.{dog_name}_emergency_mode",
        ]

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Track health entities
        self._track_entity_changes(self._health_entities, self._health_score_changed)
        
        # Initial update
        await self._async_update_health_score()

    @callback
    def _health_score_changed(self, event) -> None:
        """Handle health score changes - CORRECTED."""
        self.hass.async_create_task(self._async_update_health_score())
        self.async_write_ha_state()

    async def _async_update_health_score(self) -> None:
        """Update the health score."""
        try:
            health_metrics = self._get_health_metrics()
            calculated_score = self._calculate_comprehensive_health_score(health_metrics)
            
            # Determine health status
            if calculated_score >= 9:
                status = "Ausgezeichnet"
                concerns = []
            elif calculated_score >= 7:
                status = "Gut"
                concerns = self._identify_minor_concerns(health_metrics)
            elif calculated_score >= 5:
                status = "Durchschnittlich"
                concerns = self._identify_moderate_concerns(health_metrics)
            else:
                status = "Bedenklich"
                concerns = self._identify_major_concerns(health_metrics)
            
            self._attr_native_value = calculated_score
            
            self._attr_extra_state_attributes = {
                "health_status": status,
                "health_metrics": health_metrics,
                "concerns": concerns,
                "recommendations": self._get_health_recommendations(health_metrics, concerns),
                "last_calculation": datetime.now().isoformat(),
            }
            
        except Exception as e:
            _LOGGER.error("Error updating health score for %s: %s", self._dog_name, e)
            self._attr_native_value = 0
            self._attr_extra_state_attributes = {
                "error": str(e),
                "last_updated": datetime.now().isoformat(),
            }

    def _get_health_metrics(self) -> Dict[str, Any]:
        """Get all health-related metrics."""
        metrics = {}
        
        # Health status
        health_state = self.hass.states.get(f"input_select.{self._dog_name}_health_status")
        metrics["health_status"] = health_state.state if health_state else "Gut"
        
        # Mood
        mood_state = self.hass.states.get(f"input_select.{self._dog_name}_mood")
        metrics["mood"] = mood_state.state if mood_state else "Glücklich"
        
        # Energy level
        energy_state = self.hass.states.get(f"input_select.{self._dog_name}_energy_level_category")
        metrics["energy_level"] = energy_state.state if energy_state else "Normal"
        
        # Appetite
        appetite_state = self.hass.states.get(f"input_select.{self._dog_name}_appetite_level")
        metrics["appetite"] = appetite_state.state if appetite_state else "Normal"
        
        # Manual health score
        health_score_state = self.hass.states.get(f"input_number.{self._dog_name}_health_score")
        if health_score_state and health_score_state.state not in ["unknown", "unavailable"]:
            try:
                metrics["manual_score"] = float(health_score_state.state)
            except ValueError:
                metrics["manual_score"] = None
        else:
            metrics["manual_score"] = None
        
        # Emergency mode
        emergency_state = self.hass.states.get(f"input_boolean.{self._dog_name}_emergency_mode")
        metrics["emergency_mode"] = emergency_state.state == "on" if emergency_state else False
        
        return metrics

    def _calculate_comprehensive_health_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate comprehensive health score."""
        if metrics.get("emergency_mode", False):
            return 0.0
        
        # Start with manual score if available
        if metrics.get("manual_score") is not None:
            base_score = metrics["manual_score"]
        else:
            # Calculate based on status indicators
            status_scores = {
                "Ausgezeichnet": 10,
                "Gut": 8,
                "Normal": 6,
                "Schwach": 4,
                "Krank": 2,
                "Notfall": 0,
            }
            base_score = status_scores.get(metrics.get("health_status", "Gut"), 6)
        
        # Adjust based on mood
        mood_adjustments = {
            "Sehr glücklich": 1.0,
            "Glücklich": 0.5,
            "Neutral": 0.0,
            "Gestresst": -1.0,
            "Ängstlich": -1.5,
            "Krank": -3.0,
        }
        base_score += mood_adjustments.get(metrics.get("mood", "Glücklich"), 0)
        
        # Adjust based on energy level
        energy_adjustments = {
            "Hyperaktiv": -0.5,  # Might indicate stress
            "Energiegeladen": 0.5,
            "Normal": 0.0,
            "Müde": -0.5,
            "Sehr müde": -1.5,
        }
        base_score += energy_adjustments.get(metrics.get("energy_level", "Normal"), 0)
        
        # Adjust based on appetite
        appetite_adjustments = {
            "Sehr hungrig": 0.0,  # Normal for healthy dogs
            "Guter Appetit": 0.5,
            "Normal": 0.0,
            "Wenig Appetit": -1.0,
            "Kein Appetit": -2.0,
        }
        base_score += appetite_adjustments.get(metrics.get("appetite", "Normal"), 0)
        
        return max(0.0, min(10.0, base_score))

    def _identify_minor_concerns(self, metrics: Dict[str, Any]) -> List[str]:
        """Identify minor health concerns."""
        concerns = []
        
        if metrics.get("energy_level") in ["Müde", "Sehr müde"]:
            concerns.append("Niedrige Energie")
        
        if metrics.get("mood") == "Gestresst":
            concerns.append("Leichter Stress")
        
        if metrics.get("appetite") == "Wenig Appetit":
            concerns.append("Reduzierter Appetit")
        
        return concerns

    def _identify_moderate_concerns(self, metrics: Dict[str, Any]) -> List[str]:
        """Identify moderate health concerns."""
        concerns = []
        
        if metrics.get("health_status") in ["Normal", "Schwach"]:
            concerns.append("Gesundheitsstatus unter optimal")
        
        if metrics.get("mood") == "Ängstlich":
            concerns.append("Anzeichen von Angst")
        
        if metrics.get("appetite") == "Kein Appetit":
            concerns.append("Appetitlosigkeit")
        
        if metrics.get("energy_level") == "Sehr müde":
            concerns.append("Extreme Müdigkeit")
        
        return concerns

    def _identify_major_concerns(self, metrics: Dict[str, Any]) -> List[str]:
        """Identify major health concerns."""
        concerns = []
        
        if metrics.get("health_status") in ["Krank", "Notfall"]:
            concerns.append("Ernste Gesundheitsprobleme")
        
        if metrics.get("mood") == "Krank":
            concerns.append("Krankheitsanzeichen")
        
        if metrics.get("emergency_mode", False):
            concerns.append("Notfallsituation")
        
        return concerns

    def _get_health_recommendations(self, metrics: Dict[str, Any], concerns: List[str]) -> List[str]:
        """Get health recommendations based on metrics and concerns."""
        recommendations = []
        
        if "Niedrige Energie" in concerns:
            recommendations.append("Mehr Ruhe und sanfte Aktivitäten")
        
        if "Leichter Stress" in concerns or "Anzeichen von Angst" in concerns:
            recommendations.append("Stressreduktion und beruhigende Umgebung")
        
        if "Reduzierter Appetit" in concerns or "Appetitlosigkeit" in concerns:
            recommendations.append("Tierarzt konsultieren für Appetitprobleme")
        
        if "Ernste Gesundheitsprobleme" in concerns:
            recommendations.append("Sofortige tierärztliche Behandlung erforderlich")
        
        if "Notfallsituation" in concerns:
            recommendations.append("Notfall-Tierarzt kontaktieren")
        
        if not concerns:
            recommendations.append("Weiterhin gute Pflege beibehalten")
        
        return recommendations


class HundesystemMoodSensor(HundesystemSensorBase):
    """Sensor for mood tracking."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        dog_name: str,
    ) -> None:
        """Initialize the mood sensor."""
        super().__init__(hass, config_entry, dog_name, ENTITIES["mood"])
        self._attr_icon = ICONS["happy"]
        
        self._mood_entities = [
            f"input_select.{dog_name}_mood",
            f"input_select.{dog_name}_energy_level_category",
            f"input_boolean.{dog_name}_feeling_well",
            f"input_boolean.{dog_name}_played_today",
            f"input_boolean.{dog_name}_socialized_today",
        ]

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Track mood entities
        self._track_entity_changes(self._mood_entities, self._mood_changed)
        
        # Initial update
        await self._async_update_mood()

    @callback
    def _mood_changed(self, event) -> None:
        """Handle mood changes - CORRECTED."""
        self.hass.async_create_task(self._async_update_mood())
        self.async_write_ha_state()

    async def _async_update_mood(self) -> None:
        """Update the mood status."""
        try:
            # Get primary mood
            mood_state = self.hass.states.get(f"input_select.{self._dog_name}_mood")
            primary_mood = mood_state.state if mood_state else "Glücklich"
            
            # Get supporting indicators
            energy_state = self.hass.states.get(f"input_select.{self._dog_name}_energy_level_category")
            energy_level = energy_state.state if energy_state else "Normal"
            
            feeling_well_state = self.hass.states.get(f"input_boolean.{self._dog_name}_feeling_well")
            feeling_well = feeling_well_state.state == "on" if feeling_well_state else True
            
            played_state = self.hass.states.get(f"input_boolean.{self._dog_name}_played_today")
            played_today = played_state.state == "on" if played_state else False
            
            socialized_state = self.hass.states.get(f"input_boolean.{self._dog_name}_socialized_today")
            socialized_today = socialized_state.state == "on" if socialized_state else False
            
            # Calculate mood score (0-10)
            mood_score = self._calculate_mood_score(primary_mood, energy_level, feeling_well, played_today, socialized_today)
            
            # Determine mood description and icon
            mood_description, mood_icon = self._get_mood_description_and_icon(primary_mood, mood_score)
            
            self._attr_native_value = primary_mood
            self._attr_icon = mood_icon
            
            self._attr_extra_state_attributes = {
                "mood_score": mood_score,
                "mood_description": mood_description,
                "energy_level": energy_level,
                "feeling_well": feeling_well,
                "played_today": played_today,
                "socialized_today": socialized_today,
                "mood_factors": self._analyze_mood_factors(primary_mood, energy_level, feeling_well, played_today, socialized_today),
                "last_updated": datetime.now().isoformat(),
            }
            
        except Exception as e:
            _LOGGER.error("Error updating mood for %s: %s", self._dog_name, e)
            self._attr_native_value = "Unbekannt"
            self._attr_extra_state_attributes = {
                "error": str(e),
                "last_updated": datetime.now().isoformat(),
            }

    def _calculate_mood_score(self, mood: str, energy: str, feeling_well: bool, played: bool, socialized: bool) -> float:
        """Calculate numeric mood score."""
        mood_scores = {
            "Sehr glücklich": 10,
            "Glücklich": 8,
            "Neutral": 6,
            "Gestresst": 4,
            "Ängstlich": 2,
            "Krank": 1,
        }
        
        base_score = mood_scores.get(mood, 6)
        
        # Adjust based on other factors
        if not feeling_well:
            base_score -= 2
        
        if played:
            base_score += 0.5
        
        if socialized:
            base_score += 0.5
        
        # Energy level adjustments
        energy_adjustments = {
            "Hyperaktiv": -0.5,
            "Energiegeladen": 0.5,
            "Normal": 0,
            "Müde": -0.5,
            "Sehr müde": -1,
        }
        base_score += energy_adjustments.get(energy, 0)
        
        return max(0, min(10, base_score))

    def _get_mood_description_and_icon(self, primary_mood: str, score: float) -> tuple:
        """Get mood description and appropriate icon."""
        if score >= 9:
            return "Fantastische Stimmung", ICONS["happy"]
        elif score >= 7:
            return "Gute Stimmung", ICONS["dog"]
        elif score >= 5:
            return "Durchschnittliche Stimmung", ICONS["status"]
        elif score >= 3:
            return "Schlechte Stimmung", ICONS["attention"]
        else:
            return "Sehr schlechte Stimmung", ICONS["emergency"]

    def _analyze_mood_factors(self, mood: str, energy: str, feeling_well: bool, played: bool, socialized: bool) -> Dict[str, Any]:
        """Analyze factors affecting mood."""
        positive_factors = []
        negative_factors = []
        
        if mood in ["Sehr glücklich", "Glücklich"]:
            positive_factors.append("Positive Grundstimmung")
        elif mood in ["Gestresst", "Ängstlich", "Krank"]:
            negative_factors.append(f"Beeinträchtigte Stimmung: {mood}")
        
        if feeling_well:
            positive_factors.append("Fühlt sich wohl")
        else:
            negative_factors.append("Fühlt sich nicht wohl")
        
        if played:
            positive_factors.append("Hat heute gespielt")
        else:
            negative_factors.append("Hat heute noch nicht gespielt")
        
        if socialized:
            positive_factors.append("Sozialer Kontakt heute")
        else:
            negative_factors.append("Kein sozialer Kontakt heute")
        
        if energy in ["Energiegeladen", "Normal"]:
            positive_factors.append(f"Gutes Energielevel: {energy}")
        else:
            negative_factors.append(f"Niedriges Energielevel: {energy}")
        
        return {
            "positive_factors": positive_factors,
            "negative_factors": negative_factors,
            "overall_assessment": "Positiv" if len(positive_factors) > len(negative_factors) else "Verbesserungswürdig"
        }


class HundesystemWeeklySummarySensor(HundesystemSensorBase):
    """Sensor for weekly summary and trends."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        dog_name: str,
    ) -> None:
        """Initialize the weekly summary sensor."""
        super().__init__(hass, config_entry, dog_name, ENTITIES["weekly_summary"])
        self._attr_icon = ICONS["status"]
        self._attr_native_unit_of_measurement = "score"

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Update daily at midnight
        self._track_time_interval(self._daily_summary_update, timedelta(days=1))
        
        # Initial update
        await self._async_update_weekly_summary()

    @callback
    def _daily_summary_update(self, time) -> None:
        """Daily summary update - CORRECTED."""
        self.hass.async_create_task(self._async_update_weekly_summary())

    async def _async_update_weekly_summary(self) -> None:
        """Update the weekly summary."""
        try:
            # Get daily summary sensor for trend analysis
            daily_sensor = self.hass.states.get(f"sensor.{self._dog_name}_daily_summary")
            current_daily_score = float(daily_sensor.state) if daily_sensor and daily_sensor.state.replace('.', '').isdigit() else 0
            
            # Calculate weekly metrics (simplified for demo)
            weekly_metrics = {
                "average_daily_score": current_daily_score,  # In real implementation, would track 7 days
                "feeding_consistency": self._calculate_feeding_consistency(),
                "activity_trend": self._calculate_activity_trend(),
                "health_trend": self._calculate_health_trend(),
            }
            
            # Calculate overall weekly score
            weekly_score = self._calculate_weekly_score(weekly_metrics)
            
            # Generate weekly assessment
            assessment = self._generate_weekly_assessment(weekly_score, weekly_metrics)
            
            self._attr_native_value = weekly_score
            
            self._attr_extra_state_attributes = {
                "weekly_score": weekly_score,
                "weekly_assessment": assessment,
                "metrics": weekly_metrics,
                "recommendations": self._get_weekly_recommendations(weekly_metrics),
                "week_start": (datetime.now() - timedelta(days=datetime.now().weekday())).date().isoformat(),
                "last_updated": datetime.now().isoformat(),
            }
            
        except Exception as e:
            _LOGGER.error("Error updating weekly summary for %s: %s", self._dog_name, e)
            self._attr_native_value = 0
            self._attr_extra_state_attributes = {
                "error": str(e),
                "last_updated": datetime.now().isoformat(),
            }

    def _calculate_feeding_consistency(self) -> float:
        """Calculate feeding consistency score."""
        # Simplified - in real implementation would track daily patterns
        feeding_entities = [f"input_boolean.{self._dog_name}_feeding_{meal}" for meal in FEEDING_TYPES]
        
        fed_count = 0
        total_count = len(feeding_entities)
        
        for entity_id in feeding_entities:
            state = self.hass.states.get(entity_id)
            if state and state.state == "on":
                fed_count += 1
        
        return (fed_count / total_count) * 10 if total_count > 0 else 0

    def _calculate_activity_trend(self) -> str:
        """Calculate activity trend."""
        # Simplified trend calculation
        activity_sensor = self.hass.states.get(f"sensor.{self._dog_name}_activity")
        current_activities = int(activity_sensor.state) if activity_sensor and activity_sensor.state.isdigit() else 0
        
        if current_activities >= 8:
            return "Steigend"
        elif current_activities >= 4:
            return "Stabil"
        else:
            return "Sinkend"

    def _calculate_health_trend(self) -> str:
        """Calculate health trend."""
        health_sensor = self.hass.states.get(f"sensor.{self._dog_name}_health_score")
        current_health = float(health_sensor.state) if health_sensor and health_sensor.state.replace('.', '').isdigit() else 5
        
        if current_health >= 8:
            return "Ausgezeichnet"
        elif current_health >= 6:
            return "Gut"
        else:
            return "Verbesserungswürdig"

    def _calculate_weekly_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate overall weekly score."""
        daily_score = metrics.get("average_daily_score", 0)
        feeding_score = metrics.get("feeding_consistency", 0)
        
        # Weight the scores
        weighted_score = (daily_score * 0.6) + (feeding_score * 0.4)
        
        return round(weighted_score, 1)

    def _generate_weekly_assessment(self, score: float, metrics: Dict[str, Any]) -> str:
        """Generate weekly assessment text."""
        if score >= 8.5:
            return "Ausgezeichnete Woche! Alle Aspekte der Hundepflege sind optimal."
        elif score >= 7:
            return "Gute Woche mit konstanter Pflege und Aufmerksamkeit."
        elif score >= 5:
            return "Durchschnittliche Woche, einige Bereiche könnten verbessert werden."
        else:
            return "Herausfordernde Woche, mehr Aufmerksamkeit für Grundbedürfnisse nötig."

    def _get_weekly_recommendations(self, metrics: Dict[str, Any]) -> List[str]:
        """Get weekly recommendations."""
        recommendations = []
        
        feeding_consistency = metrics.get("feeding_consistency", 0)
        if feeding_consistency < 8:
            recommendations.append("Regelmäßigere Fütterungszeiten etablieren")
        
        activity_trend = metrics.get("activity_trend", "")
        if activity_trend == "Sinkend":
            recommendations.append("Mehr tägliche Aktivitäten einplanen")
        
        health_trend = metrics.get("health_trend", "")
        if health_trend == "Verbesserungswürdig":
            recommendations.append("Gesundheitsstatus genauer beobachten")
        
        if not recommendations:
            recommendations.append("Weiterhin exzellente Pflege!")
        
        return recommendations
