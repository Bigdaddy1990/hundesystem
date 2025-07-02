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
        HundesystemFeedingProgressSensor(hass, config_entry, dog_name),
        HundesystemActivityLevelSensor(hass, config_entry, dog_name),
        HundesystemHealthTrendSensor(hass, config_entry, dog_name),
        HundesystemNextEventSensor(hass, config_entry, dog_name),
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
            "sw_version": "2.0.0",
        }

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Restore previous state
        if (old_state := await self.async_get_last_state()) is not None:
            self._attr_native_value = old_state.state
            if old_state.attributes:
                self._attr_extra_state_attributes = dict(old_state.attributes)


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
    async def _async_status_changed(self, event) -> None:
        """Handle state changes that affect overall status."""
        await self._async_update_status()
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
    async def _async_feeding_status_changed(self, event) -> None:
        """Handle feeding status changes."""
        await self._async_update_feeding_status()
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
        
        # Activity tracking entities
        self._activity_entities = [
            f"input_boolean.{dog_name}_outside",
            f"input_boolean.{dog_name}_poop_done",
        ]
        
        self._activity_counters = [
            f"counter.{dog_name}_outside_count",
            f"counter.{dog_name}_walk_count",
            f"counter.{dog_name}_play_count",
            f"counter.{dog_name}_training_count",
            f"counter.{dog_name}_poop_count",
            f"counter.{dog_name}_activity_count",
        ]
        
        self._datetime_entities = [
            f"input_datetime.{dog_name}_last_outside",
            f"input_datetime.{dog_name}_last_walk",
            f"input_datetime.{dog_name}_last_play",
            f"input_datetime.{dog_name}_last_activity",
        ]

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Track activity entities
        tracked_entities = self._activity_entities + self._activity_counters + self._datetime_entities
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
        # Get current activity status
        outside_state = self.hass.states.get(f"input_boolean.{self._dog_name}_outside")
        currently_outside = outside_state.state == "on" if outside_state else False
        
        poop_state = self.hass.states.get(f"input_boolean.{self._dog_name}_poop_done")
        poop_done = poop_state.state == "on" if poop_state else False
        
        # Get activity counters
        activity_counts = {}
        total_activities = 0
        
        counter_names = ["outside", "walk", "play", "training", "poop", "activity"]
        for counter_name in counter_names:
            counter_state = self.hass.states.get(f"counter.{self._dog_name}_{counter_name}_count")
            count = int(counter_state.state) if counter_state else 0
            activity_counts[counter_name] = count
            
            if counter_name != "activity":  # Don't double-count the general activity counter
                total_activities += count
        
        # Get last activity times
        last_times = {}
        for entity in self._datetime_entities:
            state = self.hass.states.get(entity)
            if state and state.state not in ["unknown", "unavailable"]:
                try:
                    last_time = datetime.fromisoformat(state.state.replace("Z", "+00:00"))
                    activity_type = entity.split("_")[-1]
                    last_times[activity_type] = last_time
                except (ValueError, AttributeError):
                    continue
        
        # Calculate activity level
        activity_level = self._calculate_activity_level(activity_counts)
        
        # Determine status message
        if currently_outside:
            status = "Gerade draußen"
        elif activity_counts["outside"] > 0:
            status = f"War {activity_counts['outside']}x draußen"
        else:
            status = "War noch nicht draußen"
        
        # Check for inactivity warning
        hours_since_last_activity = self._hours_since_last_activity(last_times)
        inactivity_warning = hours_since_last_activity > HEALTH_THRESHOLDS["max_hours_without_outside"]
        
        self._attr_native_value = total_activities
        
        # Generate activity summary
        activity_summary = []
        if activity_counts["walk"] > 0:
            activity_summary.append(f"{activity_counts['walk']}x Gassi")
        if activity_counts["play"] > 0:
            activity_summary.append(f"{activity_counts['play']}x Spielen")
        if activity_counts["training"] > 0:
            activity_summary.append(f"{activity_counts['training']}x Training")
        
        self._attr_extra_state_attributes = {
            "status_text": status,
            "activity_level": activity_level,
            "currently_outside": currently_outside,
            "poop_done": poop_done,
            "activity_counts": activity_counts,
            "total_activities": total_activities,
            "activity_summary": activity_summary,
            "last_activity_times": {k: v.isoformat() for k, v in last_times.items()},
            "hours_since_last_activity": hours_since_last_activity,
            "inactivity_warning": inactivity_warning,
            "recommendations": self._get_activity_recommendations(activity_counts, hours_since_last_activity),
            "last_updated": datetime.now().isoformat(),
        }

    def _calculate_activity_level(self, activity_counts: dict) -> str:
        """Calculate activity level based on counts."""
        total = sum(activity_counts[key] for key in ["outside", "walk", "play", "training"])
        
        if total >= 8:
            return "Sehr aktiv"
        elif total >= 5:
            return "Aktiv"
        elif total >= 3:
            return "Mäßig aktiv"
        elif total >= 1:
            return "Wenig aktiv"
        else:
            return "Inaktiv"

    def _hours_since_last_activity(self, last_times: dict) -> float:
        """Calculate hours since last activity."""
        if not last_times:
            return 24.0  # Assume 24 hours if no data
        
        most_recent = max(last_times.values())
        now = dt_util.now()
        
        # Handle timezone-aware vs naive datetime
        if most_recent.tzinfo is None:
            most_recent = dt_util.as_local(most_recent)
        
        diff = now - most_recent
        return diff.total_seconds() / 3600

    def _get_activity_recommendations(self, activity_counts: dict, hours_since_last: float) -> list[str]:
        """Get activity recommendations based on current status."""
        recommendations = []
        
        if hours_since_last > 6:
            recommendations.append("Zeit für einen Spaziergang")
        
        if activity_counts["play"] == 0:
            recommendations.append("Etwas Spielzeit einplanen")
        
        if activity_counts["training"] == 0:
            recommendations.append("Kurze Trainingseinheit")
        
        if activity_counts["outside"] == 0:
            recommendations.append("Dringend nach draußen gehen")
        
        if not activity_counts["poop"]:
            recommendations.append("Auf Geschäfte achten")
        
        return recommendations


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
        
        # All relevant entities for daily summary
        self._all_entities = []
        
        # Add feeding entities
        for meal in FEEDING_TYPES:
            self._all_entities.extend([
                f"input_boolean.{dog_name}_feeding_{meal}",
                f"counter.{dog_name}_feeding_{meal}_count",
            ])
        
        # Add activity entities
        activity_types = ["outside", "walk", "play", "training", "poop", "activity"]
        for activity in activity_types:
            self._all_entities.append(f"counter.{dog_name}_{activity}_count")
        
        # Add status entities
        self._all_entities.extend([
            f"input_boolean.{dog_name}_outside",
            f"input_boolean.{dog_name}_poop_done",
            f"input_boolean.{dog_name}_visitor_mode_input",
            f"input_select.{dog_name}_health_status",
            f"input_select.{dog_name}_mood",
        ])

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Track all relevant entities
        async_track_state_change_event(
            self.hass, self._all_entities, self._async_summary_changed
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
        # Collect all data
        feeding_data = self._collect_feeding_data()
        activity_data = self._collect_activity_data()
        health_data = self._collect_health_data()
        
        # Generate summary text
        summary_parts = []
        
        # Feeding summary
        meals_completed = sum(1 for meal in FEEDING_TYPES if feeding_data["status"].get(meal, False))
        summary_parts.append(f"🍽️ {meals_completed}/4 Mahlzeiten")
        
        # Activity summary
        if activity_data["outside_count"] > 0:
            summary_parts.append(f"🚶 {activity_data['outside_count']}x draußen")
        else:
            summary_parts.append("🚶 Noch nicht draußen")
        
        # Health status
        health_status = health_data.get("health_status", "Gut")
        if health_status in ["Ausgezeichnet", "Gut"]:
            summary_parts.append("❤️ Gesund")
        elif health_status == "Normal":
            summary_parts.append("❤️ Normal")
        else:
            summary_parts.append(f"⚠️ {health_status}")
        
        # Visitor mode
        if health_data.get("visitor_mode", False):
            visitor_name = health_data.get("visitor_name", "")
            if visitor_name:
                summary_parts.append(f"🏠 Besuch: {visitor_name}")
            else:
                summary_parts.append("🏠 Besuchsmodus")
        
        summary_text = " | ".join(summary_parts)
        self._attr_native_value = summary_text
        
        # Calculate scores
        nutrition_score = self._calculate_nutrition_score(feeding_data)
        activity_score = self._calculate_activity_score(activity_data)
        health_score = self._calculate_health_score(health_data)
        overall_score = round((nutrition_score + activity_score + health_score) / 3, 1)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(feeding_data, activity_data, health_data)
        
        # Calculate day rating
        day_rating = self._calculate_day_rating(overall_score, recommendations)
        
        self._attr_extra_state_attributes = {
            "feeding_data": feeding_data,
            "activity_data": activity_data,
            "health_data": health_data,
            "scores": {
                "nutrition": nutrition_score,
                "activity": activity_score,
                "health": health_score,
                "overall": overall_score,
            },
            "day_rating": day_rating,
            "recommendations": recommendations,
            "summary_date": datetime.now().strftime("%Y-%m-%d"),
            "last_updated": datetime.now().isoformat(),
        }

    def _collect_feeding_data(self) -> dict:
        """Collect feeding-related data."""
        feeding_status = {}
        feeding_counts = {}
        total_feedings = 0
        
        for meal in FEEDING_TYPES:
            # Status
            boolean_state = self.hass.states.get(f"input_boolean.{self._dog_name}_feeding_{meal}")
            feeding_status[meal] = boolean_state.state == "on" if boolean_state else False
            
            # Count
            counter_state = self.hass.states.get(f"counter.{self._dog_name}_feeding_{meal}_count")
            count = int(counter_state.state) if counter_state else 0
            feeding_counts[meal] = count
            total_feedings += count
        
        return {
            "status": feeding_status,
            "counts": feeding_counts,
            "total_feedings": total_feedings,
            "meals_completed": sum(feeding_status.values()),
        }

    def _collect_activity_data(self) -> dict:
        """Collect activity-related data."""
        activity_counts = {}
        total_activities = 0
        
        activity_types = ["outside", "walk", "play", "training", "poop"]
        for activity in activity_types:
            counter_state = self.hass.states.get(f"counter.{self._dog_name}_{activity}_count")
            count = int(counter_state.state) if counter_state else 0
            activity_counts[activity] = count
            total_activities += count
        
        # Current status
        outside_state = self.hass.states.get(f"input_boolean.{self._dog_name}_outside")
        poop_state = self.hass.states.get(f"input_boolean.{self._dog_name}_poop_done")
        
        return {
            "counts": activity_counts,
            "total_activities": total_activities,
            "currently_outside": outside_state.state == "on" if outside_state else False,
            "poop_done": poop_state.state == "on" if poop_state else False,
            "outside_count": activity_counts.get("outside", 0),
            "walk_count": activity_counts.get("walk", 0),
            "play_count": activity_counts.get("play", 0),
        }

    def _collect_health_data(self) -> dict:
        """Collect health and status data."""
        # Health status
        health_state = self.hass.states.get(f"input_select.{self._dog_name}_health_status")
        health_status = health_state.state if health_state else "Gut"
        
        # Mood
        mood_state = self.hass.states.get(f"input_select.{self._dog_name}_mood")
        mood = mood_state.state if mood_state else "Glücklich"
        
        # Visitor mode
        visitor_state = self.hass.states.get(f"input_boolean.{self._dog_name}_visitor_mode_input")
        visitor_mode = visitor_state.state == "on" if visitor_state else False
        
        visitor_name = ""
        if visitor_mode:
            name_state = self.hass.states.get(f"input_text.{self._dog_name}_visitor_name")
            visitor_name = name_state.state if name_state else ""
        
        return {
            "health_status": health_status,
            "mood": mood,
            "visitor_mode": visitor_mode,
            "visitor_name": visitor_name,
        }

    def _calculate_nutrition_score(self, feeding_data: dict) -> float:
        """Calculate nutrition score (0-10)."""
        # Base score from completed meals
        essential_meals = sum(1 for meal in ["morning", "lunch", "evening"] 
                            if feeding_data["status"].get(meal, False))
        base_score = (essential_meals / 3) * 8  # Max 8 points for essential meals
        
        # Bonus for snack
        if feeding_data["status"].get("snack", False):
            base_score += 1
        
        # Penalty for overfeeding
        if feeding_data["total_feedings"] > 6:
            base_score -= 1
        
        return max(0, min(10, base_score))

    def _calculate_activity_score(self, activity_data: dict) -> float:
        """Calculate activity score (0-10)."""
        score = 0
        
        # Outside activity (essential)
        if activity_data["outside_count"] >= 3:
            score += 4
        elif activity_data["outside_count"] >= 1:
            score += 2
        
        # Walk activity
        if activity_data["walk_count"] >= 2:
            score += 3
        elif activity_data["walk_count"] >= 1:
            score += 1.5
        
        # Play activity
        if activity_data["play_count"] >= 1:
            score += 2
        
        # Poop (health indicator)
        if activity_data["poop_done"]:
            score += 1
        
        return min(10, score)

    def _calculate_health_score(self, health_data: dict) -> float:
        """Calculate health score (0-10)."""
        health_mapping = {
            "Ausgezeichnet": 10,
            "Gut": 8,
            "Normal": 6,
            "Schwach": 4,
            "Krank": 2,
            "Notfall": 0,
        }
        
        health_score = health_mapping.get(health_data["health_status"], 8)
        
        # Mood adjustment
        mood_adjustment = {
            "Sehr glücklich": 0,
            "Glücklich": 0,
            "Neutral": -0.5,
            "Gestresst": -1,
            "Ängstlich": -1.5,
            "Krank": -2,
        }
        
        mood_adj = mood_adjustment.get(health_data["mood"], 0)
        
        return max(0, min(10, health_score + mood_adj))

    def _generate_recommendations(self, feeding_data: dict, activity_data: dict, health_data: dict) -> list[str]:
        """Generate recommendations based on current status."""
        recommendations = []
        
        # Feeding recommendations
        essential_meals = ["morning", "lunch", "evening"]
        missing_meals = [meal for meal in essential_meals if not feeding_data["status"].get(meal, False)]
        
        if missing_meals:
            meal_names = [MEAL_TYPES[meal] for meal in missing_meals]
            recommendations.append(f"Noch füttern: {', '.join(meal_names)}")
        
        # Activity recommendations
        if activity_data["outside_count"] == 0:
            recommendations.append("Dringend nach draußen gehen")
        elif activity_data["outside_count"] < 2:
            recommendations.append("Weitere Runde nach draußen")
        
        if activity_data["walk_count"] == 0:
            recommendations.append("Spaziergang einplanen")
        
        if activity_data["play_count"] == 0:
            recommendations.append("Spielzeit einbauen")
        
        if not activity_data["poop_done"]:
            recommendations.append("Auf Geschäfte achten")
        
        # Health recommendations
        if health_data["health_status"] in ["Schwach", "Krank"]:
            recommendations.append("Gesundheit beobachten, evtl. Tierarzt")
        
        if health_data["mood"] in ["Gestresst", "Ängstlich"]:
            recommendations.append("Beruhigende Aktivitäten")
        
        return recommendations

    def _calculate_day_rating(self, overall_score: float, recommendations: list) -> str:
        """Calculate overall day rating."""
        if overall_score >= 9 and len(recommendations) == 0:
            return "🌟 Perfekter Tag"
        elif overall_score >= 8:
            return "😊 Sehr guter Tag"
        elif overall_score >= 7:
            return "🙂 Guter Tag"
        elif overall_score >= 6:
            return "😐 Durchschnittlicher Tag"
        elif overall_score >= 4:
            return "😟 Verbesserungsbedarf"
        else:
            return "😔 Schwieriger Tag"


class HundesystemLastActivitySensor(HundesystemSensorBase):
    """Sensor for last activity timestamp with detailed tracking."""

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
        
        # Entities that count as activities
        self._activity_entities = []
        for meal in FEEDING_TYPES:
            self._activity_entities.append(f"input_boolean.{dog_name}_feeding_{meal}")
        
        self._activity_entities.extend([
            f"input_boolean.{dog_name}_outside",
            f"input_boolean.{dog_name}_poop_done",
        ])
        
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
            await self._async_update_last_activity(event.data["entity_id"])
            self.async_write_ha_state()

    async def _async_update_last_activity(self, triggered_entity: str = None) -> None:
        """Update the last activity timestamp."""
        now = dt_util.now()
        self._attr_native_value = now.isoformat()
        
        # Get notes if available
        notes_state = self.hass.states.get(self._notes_entity)
        notes = notes_state.state if notes_state else ""
        
        # Determine activity type from triggered entity
        last_activity_type = "Unbekannt"
        if triggered_entity:
            if "feeding_" in triggered_entity:
                meal_type = triggered_entity.split("_")[-1]
                last_activity_type = f"Fütterung: {MEAL_TYPES.get(meal_type, meal_type)}"
            elif "outside" in triggered_entity:
                last_activity_type = "Draußen"
            elif "poop" in triggered_entity:
                last_activity_type = "Geschäft gemacht"
        else:
            # Find most recent activity
            for entity_id in self._activity_entities:
                state = self.hass.states.get(entity_id)
                if state and state.state == "on":
                    if "feeding_" in entity_id:
                        meal_type = entity_id.split("_")[-1]
                        last_activity_type = f"Fütterung: {MEAL_TYPES.get(meal_type, meal_type)}"
                    elif "outside" in entity_id:
                        last_activity_type = "Draußen"
                    elif "poop" in entity_id:
                        last_activity_type = "Geschäft gemacht"
                    break
        
        # Calculate time since last activity
        time_ago = self._format_time_ago(now)
        
        self._attr_extra_state_attributes = {
            "activity_type": last_activity_type,
            "timestamp": now.isoformat(),
            "time_ago": time_ago,
            "notes": notes,
            "triggered_by": triggered_entity,
        }

    def _format_time_ago(self, timestamp: datetime) -> str:
        """Format time ago in human readable format."""
        # Since this is "last activity", it just happened
        return "Gerade eben"


# Additional specialized sensors continue here...
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
            f"input_number.{self._dog_name}_health_score",
            f"input_boolean.{self._dog_name}_medication_given",
        ]
        
        async_track_state_change_event(
            self.hass, health_entities, self._async_health_changed
        )
        
        await self._async_update_health_score()

    @callback
    async def _async_health_changed(self, event) -> None:
        """Handle health-related changes."""
        await self._async_update_health_score()
        self.async_write_ha_state()

    async def _async_update_health_score(self) -> None:
        """Update the health score."""
        # Get health status
        health_state = self.hass.states.get(f"input_select.{self._dog_name}_health_status")
        health_status = health_state.state if health_state else "Gut"
        
        # Get mood
        mood_state = self.hass.states.get(f"input_select.{self._dog_name}_mood")
        mood = mood_state.state if mood_state else "Glücklich"
        
        # Get manual health score if set
        manual_score_state = self.hass.states.get(f"input_number.{self._dog_name}_health_score")
        manual_score = float(manual_score_state.state) if manual_score_state else None
        
        # Calculate automatic score if no manual score
        if manual_score is not None and manual_score > 0:
            calculated_score = manual_score
        else:
            calculated_score = self._calculate_health_score(health_status, mood)
        
        self._attr_native_value = calculated_score
        
        # Determine health trend and recommendations
        health_trend = self._determine_health_trend(calculated_score)
        recommendations = self._get_health_recommendations(health_status, mood, calculated_score)
        
        self._attr_extra_state_attributes = {
            "health_status": health_status,
            "mood": mood,
            "score_source": "manual" if manual_score is not None else "calculated",
            "health_trend": health_trend,
            "recommendations": recommendations,
            "last_updated": datetime.now().isoformat(),
        }

    def _calculate_health_score(self, health_status: str, mood: str) -> float:
        """Calculate health score based on status and mood."""
        # Base score from health status
        health_scores = {
            "Ausgezeichnet": 10.0,
            "Gut": 8.5,
            "Normal": 7.0,
            "Schwach": 5.0,
            "Krank": 3.0,
            "Notfall": 1.0,
        }
        
        base_score = health_scores.get(health_status, 7.0)
        
        # Mood adjustments
        mood_adjustments = {
            "Sehr glücklich": 0.5,
            "Glücklich": 0.0,
            "Neutral": -0.5,
            "Gestresst": -1.0,
            "Ängstlich": -1.5,
            "Krank": -2.0,
        }
        
        mood_adj = mood_adjustments.get(mood, 0.0)
        
        final_score = base_score + mood_adj
        return max(0.0, min(10.0, round(final_score, 1)))

    def _determine_health_trend(self, score: float) -> str:
        """Determine health trend based on score."""
        if score >= 9:
            return "Excellent"
        elif score >= 8:
            return "Very Good"
        elif score >= 7:
            return "Good"
        elif score >= 6:
            return "Fair"
        elif score >= 4:
            return "Poor"
        else:
            return "Critical"

    def _get_health_recommendations(self, health_status: str, mood: str, score: float) -> list[str]:
        """Get health recommendations."""
        recommendations = []
        
        if score < 6:
            recommendations.append("Tierarzt konsultieren")
        
        if health_status in ["Krank", "Notfall"]:
            recommendations.append("Sofortige medizinische Betreuung")
        elif health_status == "Schwach":
            recommendations.append("Gesundheit genau beobachten")
        
        if mood in ["Gestresst", "Ängstlich"]:
            recommendations.append("Stressreduzierende Maßnahmen")
        
        if score < 8:
            recommendations.append("Mehr Aufmerksamkeit für Wohlbefinden")
        
        return recommendations


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
            f"input_select.{self._dog_name}_energy_level_category",
            f"counter.{self._dog_name}_play_count",
            f"counter.{self._dog_name}_training_count",
        ]
        
        async_track_state_change_event(
            self.hass, mood_entities, self._async_mood_changed
        )
        
        await self._async_update_mood()

    @callback
    async def _async_mood_changed(self, event) -> None:
        """Handle mood-related changes."""
        await self._async_update_mood()
        self.async_write_ha_state()

    async def _async_update_mood(self) -> None:
        """Update the mood sensor."""
        # Get current mood setting
        mood_state = self.hass.states.get(f"input_select.{self._dog_name}_mood")
        current_mood = mood_state.state if mood_state else "Glücklich"
        
        # Get energy level
        energy_state = self.hass.states.get(f"input_select.{self._dog_name}_energy_level_category")
        energy_level = energy_state.state if energy_state else "Normal"
        
        # Get activity counts for mood analysis
        play_count_state = self.hass.states.get(f"counter.{self._dog_name}_play_count")
        play_count = int(play_count_state.state) if play_count_state else 0
        
        training_count_state = self.hass.states.get(f"counter.{self._dog_name}_training_count")
        training_count = int(training_count_state.state) if training_count_state else 0
        
        # Analyze mood based on activities
        mood_analysis = self._analyze_mood(current_mood, energy_level, play_count, training_count)
        
        self._attr_native_value = current_mood
        self._attr_icon = self._get_mood_icon(current_mood)
        
        self._attr_extra_state_attributes = {
            "current_mood": current_mood,
            "energy_level": energy_level,
            "play_count": play_count,
            "training_count": training_count,
            "mood_analysis": mood_analysis,
            "mood_suggestions": self._get_mood_suggestions(current_mood, energy_level, play_count),
            "last_updated": datetime.now().isoformat(),
        }

    def _analyze_mood(self, mood: str, energy: str, play_count: int, training_count: int) -> str:
        """Analyze mood based on various factors."""
        if mood in ["Sehr glücklich", "Glücklich"] and play_count > 0:
            return "Ausgeglichen und aktiv"
        elif mood == "Gestresst" and training_count == 0:
            return "Möglicherweise unterfordert"
        elif mood == "Ängstlich":
            return "Braucht Beruhigung und Sicherheit"
        elif energy == "Hyperaktiv" and play_count < 2:
            return "Zu wenig Auslastung"
        elif energy == "Sehr müde" and play_count > 3:
            return "Möglicherweise überanstrengt"
        else:
            return "Normal entwickelt"

    def _get_mood_icon(self, mood: str) -> str:
        """Get appropriate icon for mood."""
        mood_icons = {
            "Sehr glücklich": ICONS["excited"],
            "Glücklich": ICONS["happy"],
            "Neutral": ICONS["neutral"],
            "Gestresst": ICONS["sad"],
            "Ängstlich": ICONS["sad"],
            "Krank": ICONS["health"],
        }
        return mood_icons.get(mood, ICONS["happy"])

    def _get_mood_suggestions(self, mood: str, energy: str, play_count: int) -> list[str]:
        """Get suggestions to improve mood."""
        suggestions = []
        
        if mood == "Gestresst":
            suggestions.extend(["Ruhige Umgebung schaffen", "Entspannungsübungen"])
        
        if mood == "Ängstlich":
            suggestions.extend(["Sicherheit vermitteln", "Bekannte Routinen"])
        
        if energy == "Hyperaktiv" and play_count < 2:
            suggestions.append("Mehr Spielzeit einplanen")
        
        if mood == "Neutral" and play_count == 0:
            suggestions.append("Interaktive Spiele probieren")
        
        return suggestions


class HundesystemWeeklySummarySensor(HundesystemSensorBase):
    """Sensor for weekly summary and trends."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry, dog_name: str) -> None:
        """Initialize the weekly summary sensor."""
        super().__init__(hass, config_entry, dog_name, ENTITIES["weekly_summary"])
        self._attr_icon = ICONS["status"]

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Update weekly summary daily
        await self._async_update_weekly_summary()

    async def _async_update_weekly_summary(self) -> None:
        """Update the weekly summary."""
        # For now, provide a placeholder implementation
        # In a full implementation, this would analyze historical data
        
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


# Additional sensor classes would continue here for:
# - HundesystemFeedingProgressSensor
# - HundesystemActivityLevelSensor 
# - HundesystemHealthTrendSensor
# - HundesystemNextEventSensor

# These would follow similar patterns to the sensors above

# === Erweiterung: Statistik-Sensoren automatisch erzeugen ===
import logging
_LOGGER = logging.getLogger(__name__)
from homeassistant.core import HomeAssistant

async def async_setup_statistics(hass: HomeAssistant, dog_name: str):
    dog_id = dog_name.lower().replace(" ", "_")
    activities = ["walk", "feeding", "potty"]
    cycles = ["daily", "weekly"]

    for activity in activities:
        counter_entity = f"counter.{activity}_{dog_id}"
        if not hass.states.get(counter_entity):
            _LOGGER.warning("Zähler %s nicht gefunden – übersprungen", counter_entity)
            continue

        for cycle in cycles:
            sensor_id = f"sensor.{activity}s_{cycle}_{dog_id}"
            await hass.services.async_call(
                "utility_meter",
                "calibrate",
                {
                    "entity_id": sensor_id,
                    "value": hass.states.get(counter_entity).state
                },
                blocking=True,
            )
            _LOGGER.info("Utility-Meter erzeugt: %s", sensor_id)


class HundesystemFeedingProgressSensor(SensorEntity):
    def __init__(self, hass, config_entry, dog_name):
        self._attr_name = f"{dog_name} Fütterungsfortschritt"
        self._attr_unique_id = f"{dog_name}_feeding_progress"
        self._state = "unbekannt"

    @property
    def name(self):
        return self._attr_name

    @property
    def unique_id(self):
        return self._attr_unique_id

    @property
    def state(self):
        return self._state
