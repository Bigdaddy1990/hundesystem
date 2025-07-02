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
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_interval
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    CONF_DOG_NAME,
    ICONS,
    ENTITIES,
    FEEDING_TYPES,
    HEALTH_THRESHOLDS,
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
        HundesystemHealthStatusBinarySensor(hass, config_entry, dog_name),
        HundesystemEmergencyStatusBinarySensor(hass, config_entry, dog_name),
        HundesystemOverdueFeedingBinarySensor(hass, config_entry, dog_name),
        HundesystemInactivityWarningBinarySensor(hass, config_entry, dog_name),
        HundesystemMedicationDueBinarySensor(hass, config_entry, dog_name),
        HundesystemVetAppointmentReminderBinarySensor(hass, config_entry, dog_name),
        HundesystemWeatherAlertBinarySensor(hass, config_entry, dog_name),
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
            "sw_version": "2.0.0",
        }

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Restore previous state
        if (old_state := await self.async_get_last_state()) is not None:
            self._attr_is_on = old_state.state == "on"
            if old_state.attributes:
                self._attr_extra_state_attributes = dict(old_state.attributes)


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
        
        # Track essential meals (morning, lunch, evening)
        self._essential_meals = ["morning", "lunch", "evening"]
        self._tracked_entities = [f"input_boolean.{dog_name}_feeding_{meal}" for meal in self._essential_meals]

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
        feeding_status = {}
        all_fed = True
        completed_count = 0
        
        for meal in self._essential_meals:
            entity_id = f"input_boolean.{self._dog_name}_feeding_{meal}"
            state = self.hass.states.get(entity_id)
            is_fed = state.state == "on" if state else False
            feeding_status[meal] = is_fed
            
            if is_fed:
                completed_count += 1
            else:
                all_fed = False
        
        # Check if snack was given
        snack_state = self.hass.states.get(f"input_boolean.{self._dog_name}_feeding_snack")
        snack_given = snack_state.state == "on" if snack_state else False
        feeding_status["snack"] = snack_given
        
        self._attr_is_on = all_fed
        
        # Get feeding counters for total count
        total_feedings = 0
        for meal in FEEDING_TYPES:
            counter_state = self.hass.states.get(f"counter.{self._dog_name}_feeding_{meal}_count")
            if counter_state:
                total_feedings += int(counter_state.state)
        
        self._attr_extra_state_attributes = {
            "feeding_status": feeding_status,
            "essential_meals_completed": completed_count,
            "total_meals": len(self._essential_meals),
            "completion_percentage": round((completed_count / len(self._essential_meals)) * 100),
            "snack_given": snack_given,
            "total_feedings_today": total_feedings,
            "last_updated": datetime.now().isoformat(),
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
        
        # Essential daily tasks
        self._task_entities = {
            "morning_feeding": f"input_boolean.{dog_name}_feeding_morning",
            "lunch_feeding": f"input_boolean.{dog_name}_feeding_lunch",
            "evening_feeding": f"input_boolean.{dog_name}_feeding_evening",
            "outside": f"input_boolean.{dog_name}_outside",
            "poop": f"input_boolean.{dog_name}_poop_done",
        }

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Track state changes
        async_track_state_change_event(
            self.hass, list(self._task_entities.values()), self._async_tasks_state_changed
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
        completed_tasks = []
        pending_tasks = []
        
        for task_name, entity_id in self._task_entities.items():
            state = self.hass.states.get(entity_id)
            
            if state and state.state == "on":
                completed_tasks.append(task_name)
            else:
                pending_tasks.append(task_name)
        
        all_complete = len(pending_tasks) == 0
        completion_percentage = round(len(completed_tasks) / len(self._task_entities) * 100)
        
        self._attr_is_on = all_complete
        
        # Determine urgency level
        if completion_percentage >= 80:
            urgency = "low"
        elif completion_percentage >= 60:
            urgency = "medium"
        else:
            urgency = "high"
        
        # Create readable task names
        task_translations = {
            "morning_feeding": "Frühstück",
            "lunch_feeding": "Mittagessen", 
            "evening_feeding": "Abendessen",
            "outside": "Draußen",
            "poop": "Geschäft",
        }
        
        completed_readable = [task_translations.get(task, task) for task in completed_tasks]
        pending_readable = [task_translations.get(task, task) for task in pending_tasks]
        
        self._attr_extra_state_attributes = {
            "completed_tasks": completed_readable,
            "pending_tasks": pending_readable,
            "completion_percentage": completion_percentage,
            "urgency": urgency,
            "total_tasks": len(self._task_entities),
            "completed_count": len(completed_tasks),
            "next_priority_task": pending_readable[0] if pending_readable else None,
            "last_updated": datetime.now().isoformat(),
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
        self._visitor_start_entity = f"input_datetime.{dog_name}_visitor_start"
        self._visitor_end_entity = f"input_datetime.{dog_name}_visitor_end"

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Track state changes
        tracked_entities = [
            self._tracked_entity,
            self._visitor_name_entity,
            self._visitor_start_entity,
            self._visitor_end_entity,
        ]
        async_track_state_change_event(
            self.hass, tracked_entities, self._async_visitor_state_changed
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
        visitor_mode_active = state.state == "on" if state else False
        
        # Get visitor information
        name_state = self.hass.states.get(self._visitor_name_entity)
        visitor_name = name_state.state if name_state else ""
        
        # Get visitor timeframe
        start_state = self.hass.states.get(self._visitor_start_entity)
        end_state = self.hass.states.get(self._visitor_end_entity)
        
        visitor_start = None
        visitor_end = None
        
        if start_state and start_state.state not in ["unknown", "unavailable"]:
            try:
                visitor_start = datetime.fromisoformat(start_state.state.replace("Z", "+00:00"))
            except ValueError:
                pass
        
        if end_state and end_state.state not in ["unknown", "unavailable"]:
            try:
                visitor_end = datetime.fromisoformat(end_state.state.replace("Z", "+00:00"))
            except ValueError:
                pass
        
        self._attr_is_on = visitor_mode_active
        
        # Calculate duration if both start and end are set
        duration_info = {}
        if visitor_start and visitor_end and visitor_end > visitor_start:
            duration = visitor_end - visitor_start
            duration_info = {
                "planned_duration_hours": round(duration.total_seconds() / 3600, 1),
                "planned_duration_text": self._format_duration(duration),
            }
        
        # Check if visitor period is currently active
        now = dt_util.now()
        currently_in_timeframe = False
        
        if visitor_start and visitor_end:
            # Handle timezone-aware comparison
            if visitor_start.tzinfo is None:
                visitor_start = dt_util.as_local(visitor_start)
            if visitor_end.tzinfo is None:
                visitor_end = dt_util.as_local(visitor_end)
            
            currently_in_timeframe = visitor_start <= now <= visitor_end
        
        self._attr_extra_state_attributes = {
            "visitor_name": visitor_name,
            "visitor_start": visitor_start.isoformat() if visitor_start else None,
            "visitor_end": visitor_end.isoformat() if visitor_end else None,
            "currently_in_timeframe": currently_in_timeframe,
            "mode_active": visitor_mode_active,
            **duration_info,
            "reduced_notifications": visitor_mode_active,
            "last_updated": datetime.now().isoformat(),
        }

    def _format_duration(self, duration: timedelta) -> str:
        """Format duration in human readable format."""
        hours = int(duration.total_seconds() // 3600)
        minutes = int((duration.total_seconds() % 3600) // 60)
        
        if hours > 0:
            return f"{hours}h {minutes}min"
        else:
            return f"{minutes}min"


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
        self._counter_entity = f"counter.{dog_name}_outside_count"

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Track state changes
        tracked_entities = [self._tracked_entity, self._datetime_entity, self._counter_entity]
        async_track_state_change_event(
            self.hass, tracked_entities, self._async_outside_state_changed
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
        counter_state = self.hass.states.get(self._counter_entity)
        
        was_outside_today = state.state == "on" if state else False
        outside_count = int(counter_state.state) if counter_state else 0
        
        # Check if last outside time was today
        last_outside = None
        last_outside_today = False
        
        if datetime_state and datetime_state.state not in ["unknown", "unavailable"]:
            try:
                last_outside = datetime.fromisoformat(datetime_state.state.replace("Z", "+00:00"))
                today = datetime.now().date()
                last_outside_today = last_outside.date() == today
            except (ValueError, AttributeError):
                pass
        
        # Sensor is on if dog was outside today (either manually set or last time was today)
        sensor_active = was_outside_today or last_outside_today or outside_count > 0
        
        # Calculate time since last outside
        hours_since_outside = None
        if last_outside:
            now = dt_util.now()
            if last_outside.tzinfo is None:
                last_outside = dt_util.as_local(last_outside)
            
            time_diff = now - last_outside
            hours_since_outside = time_diff.total_seconds() / 3600
        
        # Determine urgency for going outside
        urgency = "low"
        if not sensor_active:
            urgency = "critical"
        elif hours_since_outside and hours_since_outside > 8:
            urgency = "high"
        elif hours_since_outside and hours_since_outside > 4:
            urgency = "medium"
        
        self._attr_is_on = sensor_active
        
        self._attr_extra_state_attributes = {
            "manually_set": was_outside_today,
            "last_outside": last_outside.isoformat() if last_outside else None,
            "last_outside_today": last_outside_today,
            "outside_count_today": outside_count,
            "hours_since_outside": round(hours_since_outside, 1) if hours_since_outside else None,
            "urgency": urgency,
            "needs_outside": not sensor_active,
            "overdue": hours_since_outside and hours_since_outside > HEALTH_THRESHOLDS["max_hours_without_outside"],
            "last_updated": datetime.now().isoformat(),
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
        self._feeding_entities = [f"input_boolean.{dog_name}_feeding_{meal}" for meal in ["morning", "lunch", "evening"]]
        self._activity_entities = [
            f"input_boolean.{dog_name}_outside",
            f"input_boolean.{dog_name}_poop_done",
        ]
        self._status_entities = [
            f"input_boolean.{dog_name}_visitor_mode_input",
            f"input_boolean.{dog_name}_emergency_mode",
            f"input_select.{dog_name}_health_status",
        ]
        
        # Time-sensitive entities
        self._datetime_entities = [
            f"input_datetime.{dog_name}_last_outside",
            f"input_datetime.{dog_name}_last_feeding_morning",
            f"input_datetime.{dog_name}_last_feeding_lunch",
            f"input_datetime.{dog_name}_last_feeding_evening",
        ]

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Track all relevant entities
        tracked_entities = (
            self._feeding_entities + 
            self._activity_entities + 
            self._status_entities +
            self._datetime_entities
        )
        async_track_state_change_event(
            self.hass, tracked_entities, self._async_attention_state_changed
        )
        
        # Also track time for time-based attention needs
        async_track_time_interval(
            self.hass, self._async_time_based_check, timedelta(minutes=15)
        )
        
        # Initial update
        await self._async_update_state()

    @callback
    async def _async_attention_state_changed(self, event) -> None:
        """Handle state changes that might affect attention needs."""
        await self._async_update_state()
        self.async_write_ha_state()

    @callback
    async def _async_time_based_check(self, now) -> None:
        """Periodic check for time-based attention needs."""
        await self._async_update_state()
        self.async_write_ha_state()

    async def _async_update_state(self) -> None:
        """Update the attention needs state."""
        reasons = []
        priority = "low"
        
        # Check if emergency mode is active
        emergency_state = self.hass.states.get(f"input_boolean.{self._dog_name}_emergency_mode")
        if emergency_state and emergency_state.state == "on":
            reasons.append("Notfallmodus aktiv")
            priority = "critical"
            self._attr_is_on = True
            self._attr_extra_state_attributes = {
                "reasons": reasons,
                "priority": priority,
                "emergency_active": True,
                "last_updated": datetime.now().isoformat(),
            }
            return
        
        # Check if visitor mode is active (lower priority for attention)
        visitor_state = self.hass.states.get(f"input_boolean.{self._dog_name}_visitor_mode_input")
        visitor_mode = visitor_state.state == "on" if visitor_state else False
        
        # Check health status
        health_state = self.hass.states.get(f"input_select.{self._dog_name}_health_status")
        health_status = health_state.state if health_state else "Gut"
        
        if health_status in ["Krank", "Notfall"]:
            reasons.append(f"Gesundheitsstatus: {health_status}")
            priority = "critical" if health_status == "Notfall" else "high"
        elif health_status == "Schwach":
            reasons.append("Gesundheit beobachten")
            priority = max(priority, "medium")
        
        # Only check feeding and activity if not in visitor mode
        if not visitor_mode:
            # Check feeding status
            current_time = datetime.now()
            feeding_issues = self._check_feeding_issues(current_time)
            reasons.extend(feeding_issues["reasons"])
            if feeding_issues["priority"] and feeding_issues["priority"] != "low":
                priority = max(priority, feeding_issues["priority"])
            
            # Check activity status
            activity_issues = self._check_activity_issues()
            reasons.extend(activity_issues["reasons"])
            if activity_issues["priority"] and activity_issues["priority"] != "low":
                priority = max(priority, activity_issues["priority"])
        
        # Check for overdue medication or vet appointments
        medical_issues = self._check_medical_issues()
        reasons.extend(medical_issues["reasons"])
        if medical_issues["priority"] and medical_issues["priority"] != "low":
            priority = max(priority, medical_issues["priority"])
        
        needs_attention = len(reasons) > 0
        self._attr_is_on = needs_attention
        
        # Determine attention level
        if priority == "critical":
            attention_level = "Critical - Immediate Action Required"
        elif priority == "high":
            attention_level = "High - Attention Needed Soon"
        elif priority == "medium":
            attention_level = "Medium - Should Address"
        else:
            attention_level = "Low - All Good"
        
        self._attr_extra_state_attributes = {
            "reasons": reasons,
            "priority": priority,
            "attention_level": attention_level,
            "visitor_mode": visitor_mode,
            "health_status": health_status,
            "total_issues": len(reasons),
            "emergency_active": False,
            "last_updated": datetime.now().isoformat(),
        }

    def _check_feeding_issues(self, current_time: datetime) -> dict:
        """Check for feeding-related attention needs."""
        reasons = []
        priority = "low"
        
        # Define meal time windows
        meal_windows = {
            "morning": (6, 10),    # 6:00 - 10:00
            "lunch": (11, 14),     # 11:00 - 14:00  
            "evening": (17, 21),   # 17:00 - 21:00
        }
        
        current_hour = current_time.hour
        
        for meal, (start_hour, end_hour) in meal_windows.items():
            # Check if it's time for this meal
            if start_hour <= current_hour <= end_hour:
                meal_state = self.hass.states.get(f"input_boolean.{self._dog_name}_feeding_{meal}")
                if not meal_state or meal_state.state != "on":
                    if meal == "morning":
                        meal_name = "Frühstück"
                    elif meal == "lunch":
                        meal_name = "Mittagessen"
                    elif meal == "evening":
                        meal_name = "Abendessen"
                    
                    reasons.append(f"Zeit für {meal_name}")
                    
                    # Higher priority if it's late in the meal window
                    if current_hour > (start_hour + end_hour) / 2:
                        priority = max(priority, "medium")
                    else:
                        priority = max(priority, "low")
        
        # Check for completely missed meals (past time window)
        for meal, (start_hour, end_hour) in meal_windows.items():
            if current_hour > end_hour:
                meal_state = self.hass.states.get(f"input_boolean.{self._dog_name}_feeding_{meal}")
                if not meal_state or meal_state.state != "on":
                    if meal == "morning":
                        meal_name = "Frühstück"
                    elif meal == "lunch":
                        meal_name = "Mittagessen"
                    
                    reasons.append(f"{meal_name} verpasst")
                    priority = max(priority, "high")
        
        return {"reasons": reasons, "priority": priority}

    def _check_activity_issues(self) -> dict:
        """Check for activity-related attention needs."""
        reasons = []
        priority = "low"
        
        # Check if dog was outside today
        outside_state = self.hass.states.get(f"input_boolean.{self._dog_name}_outside")
        if not outside_state or outside_state.state != "on":
            reasons.append("War noch nicht draußen")
            
            # Check time to determine urgency
            current_hour = datetime.now().hour
            if current_hour >= 20:  # After 8 PM
                priority = max(priority, "high")
            elif current_hour >= 16:  # After 4 PM
                priority = max(priority, "medium")
            else:
                priority = max(priority, "low")
        
        # Check poop status
        poop_state = self.hass.states.get(f"input_boolean.{self._dog_name}_poop_done")
        if not poop_state or poop_state.state != "on":
            # Check last outside time
            last_outside_state = self.hass.states.get(f"input_datetime.{self._dog_name}_last_outside")
            if last_outside_state and last_outside_state.state not in ["unknown", "unavailable"]:
                try:
                    last_outside = datetime.fromisoformat(last_outside_state.state.replace("Z", "+00:00"))
                    hours_since = (datetime.now() - last_outside).total_seconds() / 3600
                    
                    if hours_since > 12:
                        reasons.append("Geschäft überfällig")
                        priority = max(priority, "medium")
                except ValueError:
                    pass
        
        return {"reasons": reasons, "priority": priority}

    def _check_medical_issues(self) -> dict:
        """Check for medical attention needs."""
        reasons = []
        priority = "low"
        
        # Check if medication is due
        medication_time_state = self.hass.states.get(f"input_datetime.{self._dog_name}_medication_time")
        medication_given_state = self.hass.states.get(f"input_boolean.{self._dog_name}_medication_given")
        
        if (medication_time_state and medication_time_state.state not in ["unknown", "unavailable"] and
            medication_given_state and medication_given_state.state != "on"):
            # Parse medication time
            try:
                med_time = datetime.strptime(medication_time_state.state, "%H:%M:%S").time()
                current_time = datetime.now().time()
                
                if current_time >= med_time:
                    reasons.append("Medikament fällig")
                    priority = max(priority, "medium")
            except ValueError:
                pass
        
        # Check for upcoming vet appointments
        next_vet_state = self.hass.states.get(f"input_datetime.{self._dog_name}_next_vet_appointment")
        if next_vet_state and next_vet_state.state not in ["unknown", "unavailable"]:
            try:
                next_vet = datetime.fromisoformat(next_vet_state.state.replace("Z", "+00:00"))
                now = datetime.now()
                
                # If timezone naive, make it local
                if next_vet.tzinfo is None:
                    next_vet = dt_util.as_local(next_vet)
                    now = dt_util.as_local(now)
                
                time_until = next_vet - now
                
                if time_until.days == 0:
                    reasons.append("Tierarzttermin heute")
                    priority = max(priority, "high")
                elif time_until.days == 1:
                    reasons.append("Tierarzttermin morgen")
                    priority = max(priority, "medium")
                elif 0 < time_until.days <= 3:
                    reasons.append(f"Tierarzttermin in {time_until.days} Tagen")
                    priority = max(priority, "low")
            except ValueError:
                pass
        
        return {"reasons": reasons, "priority": priority}


class HundesystemHealthStatusBinarySensor(HundesystemBinarySensorBase):
    """Binary sensor for health status monitoring."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        dog_name: str,
    ) -> None:
        """Initialize the health status binary sensor."""
        super().__init__(hass, config_entry, dog_name, ENTITIES["health_status"])
        self._attr_icon = ICONS["health"]
        self._attr_device_class = BinarySensorDeviceClass.PROBLEM

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Track health-related entities
        health_entities = [
            f"input_select.{self._dog_name}_health_status",
            f"input_select.{self._dog_name}_mood",
            f"input_number.{self._dog_name}_temperature",
            f"input_boolean.{self._dog_name}_medication_given",
        ]
        
        async_track_state_change_event(
            self.hass, health_entities, self._async_health_changed
        )
        
        await self._async_update_state()

    @callback
    async def _async_health_changed(self, event) -> None:
        """Handle health-related changes."""
        await self._async_update_state()
        self.async_write_ha_state()

    async def _async_update_state(self) -> None:
        """Update the health status."""
        # Get health status
        health_state = self.hass.states.get(f"input_select.{self._dog_name}_health_status")
        health_status = health_state.state if health_state else "Gut"
        
        # Get mood
        mood_state = self.hass.states.get(f"input_select.{self._dog_name}_mood")
        mood = mood_state.state if mood_state else "Glücklich"
        
        # Get temperature if available
        temp_state = self.hass.states.get(f"input_number.{self._dog_name}_temperature")
        temperature = float(temp_state.state) if temp_state else None
        
        # Determine if there's a health issue
        health_issue = (
            health_status in ["Schwach", "Krank", "Notfall"] or
            mood in ["Gestresst", "Ängstlich", "Krank"] or
            (temperature and (temperature < 37.5 or temperature > 39.5))
        )
        
        self._attr_is_on = health_issue
        
        # Determine severity
        if health_status == "Notfall" or (temperature and temperature > 40.0):
            severity = "critical"
        elif health_status == "Krank" or mood == "Krank":
            severity = "high"
        elif health_status == "Schwach" or mood in ["Gestresst", "Ängstlich"]:
            severity = "medium"
        else:
            severity = "low"
        
        self._attr_extra_state_attributes = {
            "health_status": health_status,
            "mood": mood,
            "temperature": temperature,
            "severity": severity,
            "recommendations": self._get_health_recommendations(health_status, mood, temperature),
            "last_updated": datetime.now().isoformat(),
        }

    def _get_health_recommendations(self, health_status: str, mood: str, temperature: float) -> list[str]:
        """Get health recommendations."""
        recommendations = []
        
        if health_status in ["Notfall", "Krank"]:
            recommendations.append("Sofort zum Tierarzt")
        elif health_status == "Schwach":
            recommendations.append("Gesundheit beobachten")
        
        if mood in ["Gestresst", "Ängstlich"]:
            recommendations.append("Beruhigende Umgebung schaffen")
        elif mood == "Krank":
            recommendations.append("Auf Krankheitssymptome achten")
        
        if temperature:
            if temperature > 39.5:
                recommendations.append("Fieber - Tierarzt kontaktieren")
            elif temperature < 37.5:
                recommendations.append("Niedrige Temperatur - beobachten")
        
        return recommendations


class HundesystemEmergencyStatusBinarySensor(HundesystemBinarySensorBase):
    """Binary sensor for emergency status."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        dog_name: str,
    ) -> None:
        """Initialize the emergency status binary sensor."""
        super().__init__(hass, config_entry, dog_name, ENTITIES["emergency_status"])
        self._attr_icon = ICONS["emergency"]
        self._attr_device_class = BinarySensorDeviceClass.SAFETY

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Track emergency-related entities
        emergency_entities = [
            f"input_boolean.{self._dog_name}_emergency_mode",
            f"input_select.{self._dog_name}_health_status",
        ]
        
        async_track_state_change_event(
            self.hass, emergency_entities, self._async_emergency_changed
        )
        
        await self._async_update_state()

    @callback
    async def _async_emergency_changed(self, event) -> None:
        """Handle emergency-related changes."""
        await self._async_update_state()
        self.async_write_ha_state()

    async def _async_update_state(self) -> None:
        """Update the emergency status."""
        # Check emergency mode
        emergency_state = self.hass.states.get(f"input_boolean.{self._dog_name}_emergency_mode")
        emergency_mode = emergency_state.state == "on" if emergency_state else False
        
        # Check health status for emergency conditions
        health_state = self.hass.states.get(f"input_select.{self._dog_name}_health_status")
        health_status = health_state.state if health_state else "Gut"
        health_emergency = health_status == "Notfall"
        
        emergency_active = emergency_mode or health_emergency
        
        self._attr_is_on = emergency_active
        
        # Determine emergency type
        emergency_type = None
        if emergency_mode and health_emergency:
            emergency_type = "Manual + Health Emergency"
        elif emergency_mode:
            emergency_type = "Manual Emergency"
        elif health_emergency:
            emergency_type = "Health Emergency"
        
        self._attr_extra_state_attributes = {
            "emergency_mode": emergency_mode,
            "health_emergency": health_emergency,
            "emergency_type": emergency_type,
            "activated_at": datetime.now().isoformat() if emergency_active else None,
            "action_required": emergency_active,
            "last_updated": datetime.now().isoformat(),
        }


# Additional binary sensor classes continue with the same pattern:
# - HundesystemOverdueFeedingBinarySensor
# - HundesystemInactivityWarningBinarySensor 
# - HundesystemMedicationDueBinarySensor
# - HundesystemVetAppointmentReminderBinarySensor
# - HundesystemWeatherAlertBinarySensor

# These would follow similar patterns to implement specific monitoring for:
# - Overdue feeding times
# - Inactivity warnings
# - Medication schedules
# - Vet appointment reminders
# - Weather-based alerts

class HundesystemOverdueFeedingBinarySensor(HundesystemBinarySensorBase):
    """Binary sensor for overdue feeding detection."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry, dog_name: str) -> None:
        """Initialize the overdue feeding binary sensor."""
        super().__init__(hass, config_entry, dog_name, "overdue_feeding")
        self._attr_icon = ICONS["attention"]
        self._attr_device_class = BinarySensorDeviceClass.PROBLEM

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Track feeding times and status
        feeding_entities = []
        for meal in FEEDING_TYPES:
            feeding_entities.extend([
                f"input_boolean.{self._dog_name}_feeding_{meal}",
                f"input_datetime.{self._dog_name}_feeding_{meal}_time",
            ])
        
        async_track_state_change_event(
            self.hass, feeding_entities, self._async_feeding_changed
        )
        
        # Check every 30 minutes for overdue feedings
        async_track_time_interval(
            self.hass, self._async_check_overdue, timedelta(minutes=30)
        )
        
        await self._async_update_state()

    @callback
    async def _async_feeding_changed(self, event) -> None:
        """Handle feeding-related changes."""
        await self._async_update_state()
        self.async_write_ha_state()

    @callback
    async def _async_check_overdue(self, now) -> None:
        """Periodic check for overdue feedings."""
        await self._async_update_state()
        self.async_write_ha_state()

    async def _async_update_state(self) -> None:
        """Update the overdue feeding status."""
        now = datetime.now()
        overdue_meals = []
        
        # Check each meal type
        for meal in FEEDING_TYPES:
            # Check if meal was already given
            status_entity = f"input_boolean.{self._dog_name}_feeding_{meal}"
            status_state = self.hass.states.get(status_entity)
            if status_state and status_state.state == "on":
                continue  # Meal already given
            
            # Check scheduled time
            time_entity = f"input_datetime.{self._dog_name}_feeding_{meal}_time"
            time_state = self.hass.states.get(time_entity)
            
            if time_state and time_state.state not in ["unknown", "unavailable"]:
                try:
                    scheduled_time = datetime.strptime(time_state.state, "%H:%M:%S").time()
                    current_time = now.time()
                    
                    # Calculate grace period (30 minutes for main meals, 60 for snacks)
                    grace_minutes = 60 if meal == "snack" else 30
                    grace_time = (datetime.combine(now.date(), scheduled_time) + 
                                 timedelta(minutes=grace_minutes)).time()
                    
                    if current_time > grace_time:
                        minutes_overdue = int((datetime.combine(now.date(), current_time) - 
                                            datetime.combine(now.date(), grace_time)).total_seconds() / 60)
                        
                        overdue_meals.append({
                            "meal": meal,
                            "meal_name": MEAL_TYPES[meal],
                            "scheduled_time": scheduled_time.strftime("%H:%M"),
                            "minutes_overdue": minutes_overdue
                        })
                
                except ValueError:
                    continue
        
        has_overdue = len(overdue_meals) > 0
        self._attr_is_on = has_overdue
        
        # Determine urgency based on how overdue
        max_overdue = max((meal["minutes_overdue"] for meal in overdue_meals), default=0)
        if max_overdue > 120:  # More than 2 hours
            urgency = "critical"
        elif max_overdue > 60:  # More than 1 hour
            urgency = "high"
        else:
            urgency = "medium"
        
        self._attr_extra_state_attributes = {
            "overdue_meals": overdue_meals,
            "total_overdue": len(overdue_meals),
            "max_minutes_overdue": max_overdue,
            "urgency": urgency,
            "last_checked": now.isoformat(),
        }


class HundesystemInactivityWarningBinarySensor(HundesystemBinarySensorBase):
    """Binary sensor for inactivity warnings."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry, dog_name: str) -> None:
        """Initialize the inactivity warning binary sensor."""
        super().__init__(hass, config_entry, dog_name, "inactivity_warning")
        self._attr_icon = ICONS["attention"]
        self._attr_device_class = BinarySensorDeviceClass.PROBLEM

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Track activity entities
        activity_entities = [
            f"input_datetime.{self._dog_name}_last_outside",
            f"input_datetime.{self._dog_name}_last_walk",
            f"input_datetime.{self._dog_name}_last_play",
            f"input_datetime.{self._dog_name}_last_activity",
        ]
        
        async_track_state_change_event(
            self.hass, activity_entities, self._async_activity_changed
        )
        
        # Check every hour for inactivity
        async_track_time_interval(
            self.hass, self._async_check_inactivity, timedelta(hours=1)
        )
        
        await self._async_update_state()

    @callback
    async def _async_activity_changed(self, event) -> None:
        """Handle activity changes."""
        await self._async_update_state()
        self.async_write_ha_state()

    @callback
    async def _async_check_inactivity(self, now) -> None:
        """Periodic inactivity check."""
        await self._async_update_state()
        self.async_write_ha_state()

    async def _async_update_state(self) -> None:
        """Update the inactivity warning status."""
        now = dt_util.now()
        
        # Get last activity times
        last_times = {}
        activity_types = ["outside", "walk", "play", "activity"]
        
        for activity_type in activity_types:
            entity_id = f"input_datetime.{self._dog_name}_last_{activity_type}"
            state = self.hass.states.get(entity_id)
            
            if state and state.state not in ["unknown", "unavailable"]:
                try:
                    last_time = datetime.fromisoformat(state.state.replace("Z", "+00:00"))
                    if last_time.tzinfo is None:
                        last_time = dt_util.as_local(last_time)
                    
                    hours_since = (now - last_time).total_seconds() / 3600
                    last_times[activity_type] = {
                        "time": last_time,
                        "hours_since": hours_since
                    }
                except ValueError:
                    continue
        
        # Check for inactivity thresholds
        warnings = []
        max_hours_since = 0
        
        # Check critical activities
        if "outside" in last_times:
            hours_since_outside = last_times["outside"]["hours_since"]
            max_hours_since = max(max_hours_since, hours_since_outside)
            
            if hours_since_outside > HEALTH_THRESHOLDS["max_hours_without_outside"]:
                warnings.append({
                    "type": "outside",
                    "description": f"Seit {hours_since_outside:.1f}h nicht draußen",
                    "severity": "high" if hours_since_outside > 12 else "medium"
                })
        
        # Check general activity
        if "activity" in last_times:
            hours_since_activity = last_times["activity"]["hours_since"]
            max_hours_since = max(max_hours_since, hours_since_activity)
            
            if hours_since_activity > 6:  # 6 hours without any activity
                warnings.append({
                    "type": "general",
                    "description": f"Seit {hours_since_activity:.1f}h keine Aktivität",
                    "severity": "medium"
                })
        
        has_warning = len(warnings) > 0
        self._attr_is_on = has_warning
        
        # Determine overall severity
        severities = [w["severity"] for w in warnings]
        if "high" in severities:
            overall_severity = "high"
        elif "medium" in severities:
            overall_severity = "medium"
        else:
            overall_severity = "low"
        
        self._attr_extra_state_attributes = {
            "warnings": warnings,
            "last_activity_times": {k: v["time"].isoformat() for k, v in last_times.items()},
            "hours_since_last_activity": {k: v["hours_since"] for k, v in last_times.items()},
            "max_hours_inactive": max_hours_since,
            "overall_severity": overall_severity,
            "total_warnings": len(warnings),
            "last_checked": now.isoformat(),
        }


class HundesystemMedicationDueBinarySensor(HundesystemBinarySensorBase):
    """Binary sensor for medication due reminders."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry, dog_name: str) -> None:
        """Initialize the medication due binary sensor."""
        super().__init__(hass, config_entry, dog_name, "medication_due")
        self._attr_icon = ICONS["medication"]
        self._attr_device_class = BinarySensorDeviceClass.PROBLEM

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Track medication entities
        medication_entities = [
            f"input_datetime.{self._dog_name}_medication_time",
            f"input_boolean.{self._dog_name}_medication_given",
            f"input_text.{self._dog_name}_medication_notes",
        ]
        
        async_track_state_change_event(
            self.hass, medication_entities, self._async_medication_changed
        )
        
        # Check every 15 minutes for medication due
        async_track_time_interval(
            self.hass, self._async_check_medication, timedelta(minutes=15)
        )
        
        await self._async_update_state()

    @callback
    async def _async_medication_changed(self, event) -> None:
        """Handle medication changes."""
        await self._async_update_state()
        self.async_write_ha_state()

    @callback
    async def _async_check_medication(self, now) -> None:
        """Periodic medication check."""
        await self._async_update_state()
        self.async_write_ha_state()

    async def _async_update_state(self) -> None:
        """Update the medication due status."""
        # Check if medication was already given today
        given_state = self.hass.states.get(f"input_boolean.{self._dog_name}_medication_given")
        medication_given = given_state.state == "on" if given_state else False
        
        if medication_given:
            self._attr_is_on = False
            self._attr_extra_state_attributes = {
                "medication_given": True,
                "due": False,
                "last_updated": datetime.now().isoformat(),
            }
            return
        
        # Check scheduled medication time
        time_state = self.hass.states.get(f"input_datetime.{self._dog_name}_medication_time")
        
        if not time_state or time_state.state in ["unknown", "unavailable"]:
            self._attr_is_on = False
            self._attr_extra_state_attributes = {
                "medication_given": False,
                "scheduled": False,
                "due": False,
                "last_updated": datetime.now().isoformat(),
            }
            return
        
        try:
            scheduled_time = datetime.strptime(time_state.state, "%H:%M:%S").time()
            current_time = datetime.now().time()
            
            # Medication is due if current time is past scheduled time
            is_due = current_time >= scheduled_time
            
            # Calculate how overdue (if overdue)
            minutes_overdue = 0
            if is_due:
                current_datetime = datetime.combine(datetime.now().date(), current_time)
                scheduled_datetime = datetime.combine(datetime.now().date(), scheduled_time)
                minutes_overdue = int((current_datetime - scheduled_datetime).total_seconds() / 60)
            
            self._attr_is_on = is_due
            
            # Determine urgency
            if minutes_overdue > 120:  # More than 2 hours late
                urgency = "critical"
            elif minutes_overdue > 60:  # More than 1 hour late
                urgency = "high"
            elif minutes_overdue > 0:  # Overdue
                urgency = "medium"
            else:
                urgency = "low"
            
            # Get medication notes
            notes_state = self.hass.states.get(f"input_text.{self._dog_name}_medication_notes")
            notes = notes_state.state if notes_state else ""
            
            self._attr_extra_state_attributes = {
                "medication_given": False,
                "scheduled": True,
                "scheduled_time": scheduled_time.strftime("%H:%M"),
                "due": is_due,
                "minutes_overdue": minutes_overdue if is_due else 0,
                "urgency": urgency,
                "notes": notes,
                "last_updated": datetime.now().isoformat(),
            }
        
        except ValueError:
            self._attr_is_on = False
            self._attr_extra_state_attributes = {
                "medication_given": False,
                "scheduled": False,
                "due": False,
                "error": "Invalid time format",
                "last_updated": datetime.now().isoformat(),
            }


class HundesystemVetAppointmentReminderBinarySensor(HundesystemBinarySensorBase):
    """Binary sensor for vet appointment reminders."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry, dog_name: str) -> None:
        """Initialize the vet appointment reminder binary sensor."""
        super().__init__(hass, config_entry, dog_name, "vet_appointment_reminder")
        self._attr_icon = ICONS["vet"]

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Track vet appointment entities
        vet_entities = [
            f"input_datetime.{self._dog_name}_next_vet_appointment",
            f"input_datetime.{self._dog_name}_next_vaccination",
        ]
        
        async_track_state_change_event(
            self.hass, vet_entities, self._async_vet_changed
        )
        
        # Check daily for upcoming appointments
        async_track_time_interval(
            self.hass, self._async_check_appointments, timedelta(hours=6)
        )
        
        await self._async_update_state()

    @callback
    async def _async_vet_changed(self, event) -> None:
        """Handle vet appointment changes."""
        await self._async_update_state()
        self.async_write_ha_state()

    @callback
    async def _async_check_appointments(self, now) -> None:
        """Periodic appointment check."""
        await self._async_update_state()
        self.async_write_ha_state()

    async def _async_update_state(self) -> None:
        """Update the vet appointment reminder status."""
        now = dt_util.now()
        reminders = []
        
        # Check next vet appointment
        vet_state = self.hass.states.get(f"input_datetime.{self._dog_name}_next_vet_appointment")
        if vet_state and vet_state.state not in ["unknown", "unavailable"]:
            try:
                next_vet = datetime.fromisoformat(vet_state.state.replace("Z", "+00:00"))
                if next_vet.tzinfo is None:
                    next_vet = dt_util.as_local(next_vet)
                
                time_until = next_vet - now
                days_until = time_until.days
                
                if days_until <= 7:  # Remind within a week
                    if days_until == 0:
                        reminder_text = "Tierarzttermin heute"
                        urgency = "critical"
                    elif days_until == 1:
                        reminder_text = "Tierarzttermin morgen"
                        urgency = "high"
                    elif days_until <= 3:
                        reminder_text = f"Tierarzttermin in {days_until} Tagen"
                        urgency = "medium"
                    else:
                        reminder_text = f"Tierarzttermin in {days_until} Tagen"
                        urgency = "low"
                    
                    reminders.append({
                        "type": "appointment",
                        "text": reminder_text,
                        "date": next_vet.isoformat(),
                        "days_until": days_until,
                        "urgency": urgency
                    })
            except ValueError:
                pass
        
        # Check next vaccination
        vaccination_state = self.hass.states.get(f"input_datetime.{self._dog_name}_next_vaccination")
        if vaccination_state and vaccination_state.state not in ["unknown", "unavailable"]:
            try:
                next_vaccination = datetime.fromisoformat(vaccination_state.state.replace("Z", "+00:00"))
                if next_vaccination.tzinfo is None:
                    next_vaccination = dt_util.as_local(next_vaccination)
                
                time_until = next_vaccination - now
                days_until = time_until.days
                
                if days_until <= 14:  # Remind within two weeks
                    if days_until == 0:
                        reminder_text = "Impfung heute fällig"
                        urgency = "critical"
                    elif days_until <= 3:
                        reminder_text = f"Impfung in {days_until} Tagen fällig"
                        urgency = "high"
                    elif days_until <= 7:
                        reminder_text = f"Impfung in {days_until} Tagen fällig"
                        urgency = "medium"
                    else:
                        reminder_text = f"Impfung in {days_until} Tagen fällig"
                        urgency = "low"
                    
                    reminders.append({
                        "type": "vaccination",
                        "text": reminder_text,
                        "date": next_vaccination.isoformat(),
                        "days_until": days_until,
                        "urgency": urgency
                    })
            except ValueError:
                pass
        
        has_reminders = len(reminders) > 0
        self._attr_is_on = has_reminders
        
        # Determine highest urgency
        urgencies = [r["urgency"] for r in reminders]
        if "critical" in urgencies:
            overall_urgency = "critical"
        elif "high" in urgencies:
            overall_urgency = "high"
        elif "medium" in urgencies:
            overall_urgency = "medium"
        else:
            overall_urgency = "low"
        
        self._attr_extra_state_attributes = {
            "reminders": reminders,
            "total_reminders": len(reminders),
            "overall_urgency": overall_urgency,
            "next_appointment": reminders[0] if reminders else None,
            "last_checked": now.isoformat(),
        }


class HundesystemWeatherAlertBinarySensor(HundesystemBinarySensorBase):
    """Binary sensor for weather-based alerts."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry, dog_name: str) -> None:
        """Initialize the weather alert binary sensor."""
        super().__init__(hass, config_entry, dog_name, "weather_alert")
        self._attr_icon = "mdi:weather-partly-cloudy"

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Track weather and settings
        weather_entities = [
            f"input_boolean.{self._dog_name}_weather_alerts",
            f"input_select.{self._dog_name}_weather_preference",
        ]
        
        # Also track weather entity if available
        weather_entities.extend([
            "weather.home",  # Common weather entity
            "sensor.temperature",
            "sensor.humidity",
        ])
        
        async_track_state_change_event(
            self.hass, weather_entities, self._async_weather_changed
        )
        
        # Check weather every hour
        async_track_time_interval(
            self.hass, self._async_check_weather, timedelta(hours=1)
        )
        
        await self._async_update_state()

    @callback
    async def _async_weather_changed(self, event) -> None:
        """Handle weather changes."""
        await self._async_update_state()
        self.async_write_ha_state()

    @callback
    async def _async_check_weather(self, now) -> None:
        """Periodic weather check."""
        await self._async_update_state()
        self.async_write_ha_state()

    async def _async_update_state(self) -> None:
        """Update the weather alert status."""
        # Check if weather alerts are enabled
        alerts_enabled_state = self.hass.states.get(f"input_boolean.{self._dog_name}_weather_alerts")
        alerts_enabled = alerts_enabled_state.state == "on" if alerts_enabled_state else False
        
        if not alerts_enabled:
            self._attr_is_on = False
            self._attr_extra_state_attributes = {
                "alerts_enabled": False,
                "last_updated": datetime.now().isoformat(),
            }
            return
        
        # Get weather preference
        preference_state = self.hass.states.get(f"input_select.{self._dog_name}_weather_preference")
        weather_preference = preference_state.state if preference_state else "Alle Wetter"
        
        # Check current weather conditions
        weather_alerts = []
        
        # Check temperature
        temp_state = self.hass.states.get("sensor.temperature")
        if temp_state and temp_state.state not in ["unknown", "unavailable"]:
            try:
                temperature = float(temp_state.state)
                
                if temperature > 30:
                    weather_alerts.append({
                        "type": "hot",
                        "message": f"Sehr heiß ({temperature}°C) - Kürzere Spaziergänge empfohlen",
                        "severity": "medium"
                    })
                elif temperature < -5:
                    weather_alerts.append({
                        "type": "cold",
                        "message": f"Sehr kalt ({temperature}°C) - Pfoten schützen",
                        "severity": "medium"
                    })
            except ValueError:
                pass
        
        # Check weather entity if available
        weather_state = self.hass.states.get("weather.home")
        if weather_state and weather_state.state not in ["unknown", "unavailable"]:
            current_condition = weather_state.state.lower()
            
            # Check for problematic conditions based on preference
            if weather_preference != "Alle Wetter":
                if current_condition in ["rainy", "pouring"] and "Regen" not in weather_preference:
                    weather_alerts.append({
                        "type": "rain",
                        "message": "Regen - Möglicherweise nicht ideal für Spaziergänge",
                        "severity": "low"
                    })
                elif current_condition in ["snowy", "snowy-rainy"] and "Schnee" not in weather_preference:
                    weather_alerts.append({
                        "type": "snow",
                        "message": "Schnee - Pfoten nach dem Spaziergang säubern",
                        "severity": "medium"
                    })
                elif current_condition in ["windy", "windy-variant"]:
                    weather_alerts.append({
                        "type": "wind",
                        "message": "Starker Wind - Vorsicht bei ängstlichen Hunden",
                        "severity": "low"
                    })
        
        has_alerts = len(weather_alerts) > 0
        self._attr_is_on = has_alerts
        
        # Determine overall severity
        severities = [alert["severity"] for alert in weather_alerts]
        if "high" in severities:
            overall_severity = "high"
        elif "medium" in severities:
            overall_severity = "medium"
        else:
            overall_severity = "low"
        
        self._attr_extra_state_attributes = {
            "alerts_enabled": True,
            "weather_preference": weather_preference,
            "current_alerts": weather_alerts,
            "total_alerts": len(weather_alerts),
            "overall_severity": overall_severity,
            "recommendations": [alert["message"] for alert in weather_alerts],
            "last_updated": datetime.now().isoformat(),
        }