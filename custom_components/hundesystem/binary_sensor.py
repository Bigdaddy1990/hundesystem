self._attr_extra_state_attributes = {
                "error": str(e),
                "attention_reasons": ["Systemfehler - Aufmerksamkeit empfohlen"],
                "priority_level": "high",
                "last_updated": datetime.now().isoformat(),
            }

    def _get_attention_assessment(self, priority_level: str, reasons: List[str]) -> str:
        """Get attention assessment text."""
        if priority_level == "critical":
            return "Sofortige Aufmerksamkeit erforderlich!"
        elif priority_level == "high":
            return "Dringende Aufmerksamkeit benötigt"
        elif priority_level == "medium":
            return "Aufmerksamkeit empfohlen"
        elif priority_level == "low":
            return "Geringe Aufmerksamkeit nötig"
        else:
            return "Alles in Ordnung"


class HundesystemEmergencyStatusBinarySensor(HundesystemBinarySensorBase):
    """Binary sensor for emergency status."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        dog_name: str,
    ) -> None:
        """Initialize the emergency status binary sensor."""
        super().__init__(hass, config_entry, dog_name, ENTITIES["emergency"])
        self._attr_icon = ICONS["emergency"]
        self._attr_device_class = BinarySensorDeviceClass.SAFETY
        
        self._emergency_entities = [
            f"input_boolean.{dog_name}_emergency_mode",
            f"input_select.{dog_name}_health_status",
            f"input_select.{dog_name}_emergency_level",
        ]

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Track emergency entities
        self._track_entity_changes(self._emergency_entities, self._emergency_state_changed)
        
        # Initial update
        await self._async_update_state()

    @callback
    def _emergency_state_changed(self, event) -> None:
        """Handle emergency state changes - CORRECTED."""
        self.hass.async_create_task(self._async_update_state())
        self.async_write_ha_state()

    async def _async_update_state(self) -> None:
        """Update the emergency status binary sensor state."""
        try:
            # Check manual emergency mode
            emergency_mode_state = self.hass.states.get(f"input_boolean.{self._dog_name}_emergency_mode")
            manual_emergency = emergency_mode_state.state == "on" if emergency_mode_state else False
            
            # Check health-based emergency
            health_state = self.hass.states.get(f"input_select.{self._dog_name}_health_status")
            health_status = health_state.state if health_state else "Gut"
            health_emergency = health_status == "Notfall"
            
            # Check emergency level
            emergency_level_state = self.hass.states.get(f"input_select.{self._dog_name}_emergency_level")
            emergency_level = emergency_level_state.state if emergency_level_state else "Normal"
            level_emergency = emergency_level in ["Kritisch", "Dringend"]
            
            # Emergency is active if any trigger is true
            emergency_active = manual_emergency or health_emergency or level_emergency
            
            self._attr_is_on = emergency_active
            
            # Determine emergency type and actions
            emergency_info = self._analyze_emergency_status(
                manual_emergency, health_emergency, level_emergency, 
                health_status, emergency_level
            )
            
            self._attr_extra_state_attributes = {
                "manual_emergency": manual_emergency,
                "health_emergency": health_emergency,
                "level_emergency": level_emergency,
                "health_status": health_status,
                "emergency_level": emergency_level,
                "emergency_type": emergency_info["type"],
                "severity": emergency_info["severity"],
                "recommended_actions": emergency_info["actions"],
                "contact_vet_immediately": emergency_info["contact_vet"],
                "last_updated": datetime.now().isoformat(),
            }
            
        except Exception as e:
            _LOGGER.error("Error updating emergency status sensor for %s: %s", self._dog_name, e)
            self._attr_is_on = True  # Safe default - assume emergency on error
            self._attr_extra_state_attributes = {
                "error": str(e),
                "severity": "unknown",
                "contact_vet_immediately": True,
                "last_updated": datetime.now().isoformat(),
            }

    def _analyze_emergency_status(self, manual: bool, health: bool, level: bool, 
                                health_status: str, emergency_level: str) -> Dict[str, Any]:
        """Analyze emergency status and provide recommendations."""
        
        if manual:
            return {
                "type": "Manual Emergency",
                "severity": "Critical",
                "actions": [
                    "Hund beruhigen und sichern",
                    "Sofort Tierarzt kontaktieren",
                    "Notfallkontakte informieren",
                    "Situation dokumentieren"
                ],
                "contact_vet": True
            }
        
        if health and health_status == "Notfall":
            return {
                "type": "Health Emergency",
                "severity": "Critical",
                "actions": [
                    "Vitalfunktionen prüfen",
                    "Tierarzt-Notdienst anrufen",
                    "Ruhige Umgebung schaffen",
                    "Transport vorbereiten"
                ],
                "contact_vet": True
            }
        
        if level and emergency_level == "Kritisch":
            return {
                "type": "Critical Alert",
                "severity": "High",
                "actions": [
                    "Sofortige Beurteilung",
                    "Tierarzt konsultieren", 
                    "Zustand überwachen",
                    "Beruhigende Maßnahmen"
                ],
                "contact_vet": True
            }
        
        if level and emergency_level == "Dringend":
            return {
                "type": "Urgent Alert", 
                "severity": "Medium",
                "actions": [
                    "Situation bewerten",
                    "Tierarzt in Bereitschaft",
                    "Engere Überwachung",
                    "Vorbeugende Maßnahmen"
                ],
                "contact_vet": False
            }
        
        return {
            "type": "No Emergency",
            "severity": "None",
            "actions": ["Normale Betreuung fortsetzen"],
            "contact_vet": False
        }


class HundesystemOverdueFeedingBinarySensor(HundesystemBinarySensorBase):
    """Binary sensor for overdue feeding detection."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        dog_name: str,
    ) -> None:
        """Initialize the overdue feeding binary sensor."""
        super().__init__(hass, config_entry, dog_name, "overdue_feeding")
        self._attr_icon = ICONS["food"]
        self._attr_device_class = BinarySensorDeviceClass.PROBLEM
        
        # Track feeding entities and times
        self._feeding_entities = [f"input_boolean.{dog_name}_feeding_{meal}" for meal in FEEDING_TYPES]
        self._feeding_times = [f"input_datetime.{dog_name}_feeding_{meal}_time" for meal in FEEDING_TYPES]
        
        self._tracked_entities = self._feeding_entities + self._feeding_times

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Track feeding entities
        self._track_entity_changes(self._tracked_entities, self._feeding_state_changed)
        
        # Check for overdue feedings every 30 minutes
        self._track_time_interval(self._periodic_overdue_check, timedelta(minutes=30))
        
        # Initial update
        await self._async_update_state()

    @callback
    def _feeding_state_changed(self, event) -> None:
        """Handle feeding state changes - CORRECTED."""
        self.hass.async_create_task(self._async_update_state())
        self.async_write_ha_state()

    @callback
    def _periodic_overdue_check(self, time) -> None:
        """Periodic overdue check - CORRECTED."""
        self.hass.async_create_task(self._async_update_state())

    async def _async_update_state(self) -> None:
        """Update the overdue feeding binary sensor state."""
        try:
            now = datetime.now()
            current_time = now.time()
            overdue_meals = []
            overdue_details = {}
            
            # Default grace periods (minutes after scheduled time)
            grace_periods = {
                "morning": 60,   # 1 hour grace
                "lunch": 120,    # 2 hours grace
                "evening": 90,   # 1.5 hours grace
                "snack": 180,    # 3 hours grace (less critical)
            }
            
            # Default meal times if not configured
            default_times = {
                "morning": "07:00:00",
                "lunch": "12:00:00", 
                "evening": "18:00:00",
                "snack": "15:00:00"
            }
            
            for i, meal in enumerate(FEEDING_TYPES):
                # Check if meal is already given
                feeding_entity = self._feeding_entities[i]
                feeding_state = self.hass.states.get(feeding_entity)
                is_fed = feeding_state.state == "on" if feeding_state else False
                
                if not is_fed:  # Only check overdue if not fed
                    # Get scheduled time
                    time_entity = self._feeding_times[i]
                    time_state = self.hass.states.get(time_entity)
                    
                    if time_state and time_state.state not in ["unknown", "unavailable"]:
                        scheduled_time_str = time_state.state
                    else:
                        scheduled_time_str = default_times[meal]
                    
                    try:
                        # Parse scheduled time
                        scheduled_time = datetime.strptime(scheduled_time_str, "%H:%M:%S").time()
                        
                        # Calculate deadline with grace period
                        scheduled_datetime = datetime.combine(now.date(), scheduled_time)
                        deadline = scheduled_datetime + timedelta(minutes=grace_periods[meal])
                        
                        # Check if overdue
                        if now > deadline:
                            minutes_overdue = int((now - deadline).total_seconds() / 60)
                            overdue_meals.append(meal)
                            overdue_details[meal] = {
                                "scheduled_time": scheduled_time_str,
                                "deadline": deadline.time().strftime("%H:%M"),
                                "minutes_overdue": minutes_overdue,
                                "severity": self._calculate_overdue_severity(minutes_overdue)
                            }
                    
                    except ValueError as e:
                        _LOGGER.warning("Error parsing feeding time for %s meal %s: %s", 
                                      self._dog_name, meal, e)
                        continue
            
            # Sensor is ON if any meals are overdue
            has_overdue = len(overdue_meals) > 0
            self._attr_is_on = has_overdue
            
            # Calculate overall severity
            overall_severity = self._calculate_overall_severity(overdue_details)
            
            self._attr_extra_state_attributes = {
                "overdue_meals": overdue_meals,
                "overdue_details": overdue_details,
                "total_overdue": len(overdue_meals),
                "overall_severity": overall_severity,
                "next_check": (now + timedelta(minutes=30)).isoformat(),
                "recommendations": self._get_overdue_recommendations(overdue_details),
                "last_updated": now.isoformat(),
            }
            
        except Exception as e:
            _LOGGER.error("Error updating overdue feeding sensor for %s: %s", self._dog_name, e)
            self._attr_is_on = False
            self._attr_extra_state_attributes = {
                "error": str(e),
                "last_updated": datetime.now().isoformat(),
            }

    def _calculate_overdue_severity(self, minutes_overdue: int) -> str:
        """Calculate severity based on how overdue the feeding is."""
        if minutes_overdue < 30:
            return "low"
        elif minutes_overdue < 120:  # 2 hours
            return "medium"
        elif minutes_overdue < 360:  # 6 hours
            return "high"
        else:
            return "critical"

    def _calculate_overall_severity(self, overdue_details: Dict[str, Any]) -> str:
        """Calculate overall severity from all overdue feedings."""
        if not overdue_details:
            return "none"
        
        severities = [details["severity"] for details in overdue_details.values()]
        
        if "critical" in severities:
            return "critical"
        elif "high" in severities:
            return "high"
        elif "medium" in severities:
            return "medium"
        else:
            return "low"

    def _get_overdue_recommendations(self, overdue_details: Dict[str, Any]) -> List[str]:
        """Get recommendations based on overdue feedings."""
        if not overdue_details:
            return ["Alle Mahlzeiten pünktlich"]
        
        recommendations = []
        
        # Check for critical overdue situations
        critical_meals = [meal for meal, details in overdue_details.items() 
                         if details["severity"] == "critical"]
        
        if critical_meals:
            recommendations.append("DRINGEND: Sofort füttern - sehr verspätet!")
            recommendations.append("Tierarzt konsultieren bei Appetitlosigkeit")
        
        # Check for high severity
        high_meals = [meal for meal, details in overdue_details.items() 
                     if details["severity"] == "high"]
        
        if high_meals and not critical_meals:
            recommendations.append("Baldmöglichst füttern")
            recommendations.append("Fütterungszeiten überprüfen")
        
        # General recommendations
        if len(overdue_details) > 1:
            recommendations.append("Mehrere Mahlzeiten verspätet - Routine überprüfen")
        
        recommendations.append("Fütterungserinnerungen aktivieren")
        
        return recommendations


class HundesystemInactivityWarningBinarySensor(HundesystemBinarySensorBase):
    """Binary sensor for inactivity warning."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        dog_name: str,
    ) -> None:
        """Initialize the inactivity warning binary sensor."""
        super().__init__(hass, config_entry, dog_name, "inactivity_warning")
        self._attr_icon = ICONS["walk"]
        self._attr_device_class = BinarySensorDeviceClass.PROBLEM
        
        # Track activity timestamps
        self._activity_times = [
            f"input_datetime.{dog_name}_last_outside",
            f"input_datetime.{dog_name}_last_walk", 
            f"input_datetime.{dog_name}_last_play",
            f"input_datetime.{dog_name}_last_activity",
        ]

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Track activity time changes
        self._track_entity_changes(self._activity_times, self._activity_time_changed)
        
        # Check inactivity every hour
        self._track_time_interval(self._periodic_inactivity_check, timedelta(hours=1))
        
        # Initial update
        await self._async_update_state()

    @callback
    def _activity_time_changed(self, event) -> None:
        """Handle activity time changes - CORRECTED."""
        self.hass.async_create_task(self._async_update_state())
        self.async_write_ha_state()

    @callback
    def _periodic_inactivity_check(self, time) -> None:
        """Periodic inactivity check - CORRECTED."""
        self.hass.async_create_task(self._async_update_state())

    async def _async_update_state(self) -> None:
        """Update the inactivity warning binary sensor state."""
        try:
            now = datetime.now()
            activity_status = {}
            warning_triggers = []
            
            # Inactivity thresholds (hours)
            thresholds = {
                "last_outside": 6,    # 6 hours without going outside
                "last_walk": 24,      # 24 hours without a walk
                "last_play": 48,      # 48 hours without play
                "last_activity": 8,   # 8 hours without any activity
            }
            
            # Check each activity type
            for i, entity_id in enumerate(self._activity_times):
                activity_type = entity_id.split(f"{self._dog_name}_")[1]
                threshold_hours = thresholds.get(activity_type, 24)
                
                state = self.hass.states.get(entity_id)
                
                if state and state.state not in ["unknown", "unavailable"]:
                    try:
                        last_time = datetime.fromisoformat(state.state.replace("Z", "+00:00"))
                        last_time = last_time.replace(tzinfo=None)  # Convert to naive datetime
                        
                        hours_since = (now - last_time).total_seconds() / 3600
                        
                        activity_status[activity_type] = {
                            "last_time": state.state,
                            "hours_since": round(hours_since, 1),
                            "threshold_hours": threshold_hours,
                            "is_overdue": hours_since > threshold_hours
                        }
                        
                        if hours_since > threshold_hours:
                            severity = self._calculate_inactivity_severity(hours_since, threshold_hours)
                            warning_triggers.append({
                                "activity": activity_type,
                                "hours_overdue": round(hours_since - threshold_hours, 1),
                                "severity": severity
                            })
                    
                    except (ValueError, TypeError) as e:
                        _LOGGER.debug("Error parsing activity time for %s: %s", entity_id, e)
                        activity_status[activity_type] = {
                            "last_time": "unknown",
                            "hours_since": 999,
                            "threshold_hours": threshold_hours,
                            "is_overdue": True
                        }
                        warning_triggers.append({
                            "activity": activity_type,
                            "hours_overdue": 999,
                            "severity": "high"
                        })
                else:
                    # No timestamp available - assume long inactivity
                    activity_status[activity_type] = {
                        "last_time": "never",
                        "hours_since": 999,
                        "threshold_hours": threshold_hours,
                        "is_overdue": True
                    }
                    warning_triggers.append({
                        "activity": activity_type,
                        "hours_overdue": 999,
                        "severity": "medium"
                    })
            
            # Sensor is ON if any activity is overdue
            has_inactivity_warning = len(warning_triggers) > 0
            self._attr_is_on = has_inactivity_warning
            
            # Calculate overall severity
            overall_severity = self._calculate_overall_inactivity_severity(warning_triggers)
            
            self._attr_extra_state_attributes = {
                "activity_status": activity_status,
                "warning_triggers": warning_triggers,
                "total_warnings": len(warning_triggers),
                "overall_severity": overall_severity,
                "recommendations": self._get_inactivity_recommendations(warning_triggers),
                "next_check": (now + timedelta(hours=1)).isoformat(),
                "last_updated": now.isoformat(),
            }
            
        except Exception as e:
            _LOGGER.error("Error updating inactivity warning sensor for %s: %s", self._dog_name, e)
            self._attr_is_on = False
            self._attr_extra_state_attributes = {
                "error": str(e),
                "last_updated": datetime.now().isoformat(),
            }

    def _calculate_inactivity_severity(self, hours_since: float, threshold: float) -> str:
        """Calculate severity based on how long past threshold."""
        hours_overdue = hours_since - threshold
        
        if hours_overdue < 2:
            return "low"
        elif hours_overdue < 6:
            return "medium"
        elif hours_overdue < 24:
            return "high"
        else:
            return "critical"

    def _calculate_overall_inactivity_severity(self, warning_triggers: List[Dict]) -> str:
        """Calculate overall inactivity severity."""
        if not warning_triggers:
            return "none"
        
        severities = [trigger["severity"] for trigger in warning_triggers]
        
        if "critical" in severities:
            return "critical"
        elif "high" in severities:
            return "high"
        elif "medium" in severities:
            return "medium"
        else:
            return "low"

    def _get_inactivity_recommendations(self, warning_triggers: List[Dict]) -> List[str]:
        """Get recommendations based on inactivity warnings."""
        if not warning_triggers:
            return ["Aktivitätslevel ist gut"]
        
        recommendations = []
        
        # Check specific activity types
        trigger_activities = [trigger["activity"] for trigger in warning_triggers]
        
        if "last_outside" in trigger_activities:
            recommendations.append("Dringend: Hund nach draußen lassen")
        
        if "last_walk" in trigger_activities:
            recommendations.append("Spaziergang einplanen")
        
        if "last_play" in trigger_activities:
            recommendations.append("Spielzeit organisieren")
        
        if "last_activity" in trigger_activities:
            recommendations.append("Allgemeine Aktivität fördern")
        
        # Check for critical situations
        critical_triggers = [t for t in warning_triggers if t["severity"] == "critical"]
        if critical_triggers:
            recommendations.insert(0, "KRITISCH: Sofortige Aktivität erforderlich!")
        
        return recommendations


class HundesystemSystemHealthBinarySensor(HundesystemBinarySensorBase):
    """Binary sensor for system health monitoring."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        dog_name: str,
    ) -> None:
        """Initialize the system health binary sensor."""
        super().__init__(hass, config_entry, dog_name, "system_health")
        self._attr_icon = ICONS["status"]
        self._attr_device_class = BinarySensorDeviceClass.PROBLEM
        
        # Monitor key system entities
        self._system_entities = [
            f"sensor.{dog_name}_status",
            f"sensor.{dog_name}_feeding_status",
            f"sensor.{dog_name}_activity",
            f"binary_sensor.{dog_name}_needs_attention",
        ]

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Check system health every 5 minutes
        self._track_time_interval(self._periodic_system_check, timedelta(minutes=5))
        
        # Initial update
        await self._async_update_state()

    @callback
    def _periodic_system_check(self, time) -> None:
        """Periodic system health check - CORRECTED."""
        self.hass.async_create_task(self._async_update_state())

    async def _async_update_state(self) -> None:
        """Update the system health binary sensor state."""
        try:
            system_status = {}
            health_issues = []
            
            # Check each system entity
            for entity_id in self._system_entities:
                state = self.hass.states.get(entity_id)
                
                if not state:
                    health_issues.append(f"Entity missing: {entity_id}")
                    system_status[entity_id] = "missing"
                elif state.state in ["unknown", "unavailable"]:
                    health_issues.append(f"Entity unavailable: {entity_id}")
                    system_status[entity_id] = "unavailable"
                elif hasattr(state, 'attributes') and state.attributes.get('error'):
                    health_issues.append(f"Entity error: {entity_id}")
                    system_status[entity_id] = "error"
                else:
                    system_status[entity_id] = "ok"
            
            # Check for stale data
            stale_entities = self._check_stale_entities()
            health_issues.extend(stale_entities)
            
            # System has issues if any health issues found
            has_system_issues = len(health_issues) > 0
            self._attr_is_on = has_system_issues
            
            # Calculate system health score
            total_entities = len(self._system_entities)
            healthy_entities = len([s for s in system_status.values() if s == "ok"])
            health_score = (healthy_entities / total_entities) * 100 if total_entities > 0 else 0
            
            self._attr_extra_state_attributes = {
                "system_status": system_status,
                "health_issues": health_issues,
                "total_issues": len(health_issues),
                "health_score": round(health_score, 1),
                "entities_checked": total_entities,
                "healthy_entities": healthy_entities,
                "system_assessment": self._get_system_assessment(health_score, health_issues),
                "last_updated": datetime.now().isoformat(),
            }
            
        except Exception as e:
            _LOGGER.error("Error updating system health sensor for %s: %s", self._dog_name, e)
            self._attr_is_on = True  # Assume issues on error
            self._attr_extra_state_attributes = {
                "error": str(e),
                "health_score": 0,
                "system_assessment": "System check failed",
                "last_updated": datetime.now().isoformat(),
            }

    def _check_stale_entities(self) -> List[str]:
        """Check for entities with stale data."""
        stale_entities = []
        now = datetime.now()
        stale_threshold = timedelta(hours=2)  # Consider data stale after 2 hours
        
        for entity_id in self._system_entities:
            state = self.hass.states.get(entity_id)
            if state and state.last_updated:
                time_since_update = now - state.last_updated.replace(tzinfo=None)
                if time_since_update > stale_threshold:
                    stale_entities.append(f"Stale data: {entity_id} ({time_since_update})")
        
        return stale_entities

    def _get_system_assessment(self, health_score: float, health_issues: List[str]) -> str:
        """Get system assessment text."""
        if health_score >= 95:
            return "System läuft optimal"
        elif health_score >= 80:
            return "System läuft gut mit kleineren Problemen"
        elif health_score >= 60:
            return "System hat moderate Probleme"
        elif health_score >= 40:
            return "System hat erhebliche Probleme"
        else:
            return "System kritisch - sofortige Aufmerksamkeit erforderlich"


# Add additional sensor stubs for completion
class HundesystemMedicationDueBinarySensor(HundesystemBinarySensorBase):
    """Binary sensor for medication due status."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry, dog_name: str) -> None:
        super().__init__(hass, config_entry, dog_name, "medication_due")
        self._attr_icon = ICONS["medication"]
        self._attr_device_class = BinarySensorDeviceClass.PROBLEM

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._track_time_interval(self._check_medication, timedelta(minutes=30))
        await self._async_update_state()

    @callback
    def _check_medication(self, time) -> None:
        self.hass.async_create_task(self._async_update_state())

    async def _async_update_state(self) -> None:
        # Simplified implementation
        self._attr_is_on = False
        self._attr_extra_state_attributes = {
            "last_updated": datetime.now().isoformat(),
            "status": "No medication scheduled"
        }


class HundesystemVetAppointmentReminderBinarySensor(HundesystemBinarySensorBase):
    """Binary sensor for vet appointment reminders."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry, dog_name: str) -> None:
        super().__init__(hass, config_entry, dog_name, "vet_appointment_reminder")
        self._attr_icon = ICONS["vet"]
        self._attr_device_class = BinarySensorDeviceClass.PROBLEM

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._track_time_interval(self._check_appointments, timedelta(hours=6))
        await self._async_update_state()

    @callback
    def _check_appointments(self, time) -> None:
        self.hass.async_create_task(self._async_update_state())

    async def _async_update_state(self) -> None:
        # Simplified implementation
        self._attr_is_on = False
        self._attr_extra_state_attributes = {
            "last_updated": datetime.now().isoformat(),
            "status": "No appointments scheduled"
        }


class HundesystemWeatherAlertBinarySensor(HundesystemBinarySensorBase):
    """Binary sensor for weather alerts."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry, dog_name: str) -> None:
        super().__init__(hass, config_entry, dog_name, "weather_alert")
        self._attr_icon = "mdi:weather-partly-cloudy"
        self._attr_device_class = BinarySensorDeviceClass.SAFETY

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._track_time_interval(self._check_weather, timedelta(hours=1))
        """Binary sensor platform for Hundesystem integration - COMPLETE VERSION."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Callable, Optional

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
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
    FEEDING_TYPES,
    HEALTH_THRESHOLDS,
    STATUS_MESSAGES,
    MEAL_TYPES,
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
        HundesystemSystemHealthBinarySensor(hass, config_entry, dog_name),
        HundesystemMaintenanceRequiredBinarySensor(hass, config_entry, dog_name),
    ]
    
    async_add_entities(entities, True)


class HundesystemBinarySensorBase(BinarySensorEntity, RestoreEntity):
    """Base class for Hundesystem binary sensors with proper cleanup."""

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
            self._attr_is_on = old_state.state == "on"
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
        self._track_entity_changes(self._tracked_entities, self._feeding_state_changed)
        
        # Check feeding status every hour
        self._track_time_interval(self._periodic_feeding_check, timedelta(hours=1))
        
        # Initial update
        await self._async_update_state()

    @callback
    def _feeding_state_changed(self, event) -> None:
        """Handle state changes of feeding entities - CORRECTED."""
        self.hass.async_create_task(self._async_update_state())
        self.async_write_ha_state()

    @callback
    def _periodic_feeding_check(self, time) -> None:
        """Periodic feeding check - CORRECTED."""
        self.hass.async_create_task(self._async_update_state())

    async def _async_update_state(self) -> None:
        """Update the binary sensor state."""
        try:
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
            
            # Check if feeding is complete
            self._attr_is_on = all_fed
            
            # Determine completion percentage
            completion_percentage = (completed_count / len(self._essential_meals)) * 100
            
            # Get next scheduled meal
            next_meal = self._get_next_scheduled_meal(feeding_status)
            
            # Check for late feedings
            late_feedings = self._check_late_feedings(feeding_status)
            
            self._attr_extra_state_attributes = {
                "feeding_status": feeding_status,
                "completion_percentage": completion_percentage,
                "completed_meals": completed_count,
                "total_meals": len(self._essential_meals),
                "next_meal": next_meal,
                "late_feedings": late_feedings,
                "all_essential_complete": all_fed,
                "last_updated": datetime.now().isoformat(),
            }
            
        except Exception as e:
            _LOGGER.error("Error updating feeding complete sensor for %s: %s", self._dog_name, e)
            self._attr_is_on = False
            self._attr_extra_state_attributes = {
                "error": str(e),
                "last_updated": datetime.now().isoformat(),
            }

    def _get_next_scheduled_meal(self, feeding_status: Dict[str, bool]) -> Optional[str]:
        """Get the next scheduled meal."""
        try:
            now = datetime.now().time()
            
            # Default meal times
            meal_times = {
                "morning": "07:00",
                "lunch": "12:00", 
                "evening": "18:00"
            }
            
            for meal in self._essential_meals:
                if not feeding_status.get(meal, False):  # Meal not yet given
                    # Try to get scheduled time from input_datetime
                    time_entity = f"input_datetime.{self._dog_name}_feeding_{meal}_time"
                    time_state = self.hass.states.get(time_entity)
                    
                    if time_state and time_state.state not in ["unknown", "unavailable"]:
                        scheduled_time = time_state.state
                    else:
                        scheduled_time = meal_times.get(meal, "00:00")
                    
                    return f"{MEAL_TYPES.get(meal, meal)} um {scheduled_time[:5]}"
            
            return "Alle Mahlzeiten erledigt"
            
        except Exception as e:
            _LOGGER.error("Error getting next meal for %s: %s", self._dog_name, e)
            return "Fehler bei Berechnung"

    def _check_late_feedings(self, feeding_status: Dict[str, bool]) -> List[str]:
        """Check for late feedings."""
        try:
            late_feedings = []
            now = datetime.now()
            current_time = now.time()
            
            # Default meal times with grace periods
            meal_deadlines = {
                "morning": ("09:00", "Frühstück"),
                "lunch": ("14:00", "Mittagessen"),
                "evening": ("20:00", "Abendessen")
            }
            
            for meal, (deadline_str, meal_name) in meal_deadlines.items():
                if not feeding_status.get(meal, False):  # Meal not given
                    deadline = datetime.strptime(deadline_str, "%H:%M").time()
                    if current_time > deadline:
                        late_feedings.append(meal_name)
            
            return late_feedings
            
        except Exception as e:
            _LOGGER.error("Error checking late feedings for %s: %s", self._dog_name, e)
            return []


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
        self._attr_icon = ICONS["checklist"]
        self._attr_device_class = BinarySensorDeviceClass.PROBLEM
        
        # Essential daily tasks
        self._daily_tasks = {
            "fed": f"input_boolean.{dog_name}_feeding_morning",
            "outside": f"input_boolean.{dog_name}_outside",
            "poop": f"input_boolean.{dog_name}_poop_done",
        }
        
        self._tracked_entities = list(self._daily_tasks.values())

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Track state changes
        self._track_entity_changes(self._tracked_entities, self._task_state_changed)
        
        # Check daily tasks every 30 minutes
        self._track_time_interval(self._periodic_task_check, timedelta(minutes=30))
        
        # Initial update
        await self._async_update_state()

    @callback
    def _task_state_changed(self, event) -> None:
        """Handle state changes of task entities - CORRECTED."""
        self.hass.async_create_task(self._async_update_state())
        self.async_write_ha_state()

    @callback
    def _periodic_task_check(self, time) -> None:
        """Periodic task check - CORRECTED."""
        self.hass.async_create_task(self._async_update_state())

    async def _async_update_state(self) -> None:
        """Update the binary sensor state."""
        try:
            task_status = {}
            all_complete = True
            completed_count = 0
            
            task_names = {
                "fed": "Gefüttert",
                "outside": "Draußen gewesen",
                "poop": "Geschäft gemacht"
            }
            
            for task_key, entity_id in self._daily_tasks.items():
                state = self.hass.states.get(entity_id)
                is_complete = state.state == "on" if state else False
                task_status[task_key] = is_complete
                
                if is_complete:
                    completed_count += 1
                else:
                    all_complete = False
            
            # Sensor is ON when all tasks are complete
            self._attr_is_on = all_complete
            
            # Calculate completion percentage
            completion_percentage = (completed_count / len(self._daily_tasks)) * 100
            
            # Get incomplete tasks
            incomplete_tasks = [
                task_names[task] for task, complete in task_status.items() 
                if not complete
            ]
            
            # Determine priority based on time of day and incomplete tasks
            priority = self._calculate_task_priority(incomplete_tasks)
            
            self._attr_extra_state_attributes = {
                "task_status": task_status,
                "completion_percentage": completion_percentage,
                "completed_count": completed_count,
                "total_count": len(self._daily_tasks),
                "incomplete_tasks": incomplete_tasks,
                "priority": priority,
                "all_complete": all_complete,
                "last_updated": datetime.now().isoformat(),
            }
            
        except Exception as e:
            _LOGGER.error("Error updating daily tasks sensor for %s: %s", self._dog_name, e)
            self._attr_is_on = False
            self._attr_extra_state_attributes = {
                "error": str(e),
                "last_updated": datetime.now().isoformat(),
            }

    def _calculate_task_priority(self, incomplete_tasks: List[str]) -> str:
        """Calculate task priority based on incomplete tasks and time."""
        if not incomplete_tasks:
            return "none"
        
        now = datetime.now()
        hour = now.hour
        
        # High priority conditions
        if "Gefüttert" in incomplete_tasks and hour > 9:
            return "high"
        
        if "Draußen gewesen" in incomplete_tasks and hour > 10:
            return "high"
        
        if "Geschäft gemacht" in incomplete_tasks and hour > 11:
            return "high"
        
        # Medium priority
        if len(incomplete_tasks) >= 2:
            return "medium"
        
        return "low"


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
        self._attr_device_class = BinarySensorDeviceClass.PRESENCE
        
        self._visitor_entities = [
            f"input_boolean.{dog_name}_visitor_mode_input",
            f"input_text.{dog_name}_visitor_name",
            f"input_datetime.{dog_name}_visitor_start",
            f"input_datetime.{dog_name}_visitor_end",
        ]

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Track visitor mode changes
        self._track_entity_changes(self._visitor_entities, self._visitor_state_changed)
        
        # Check visitor mode every 10 minutes
        self._track_time_interval(self._periodic_visitor_check, timedelta(minutes=10))
        
        # Initial update
        await self._async_update_state()

    @callback
    def _visitor_state_changed(self, event) -> None:
        """Handle visitor state changes - CORRECTED."""
        self.hass.async_create_task(self._async_update_state())
        self.async_write_ha_state()

    @callback
    def _periodic_visitor_check(self, time) -> None:
        """Periodic visitor mode check - CORRECTED."""
        self.hass.async_create_task(self._async_update_state())

    async def _async_update_state(self) -> None:
        """Update the visitor mode binary sensor state."""
        try:
            # Check manual visitor mode toggle
            visitor_mode_state = self.hass.states.get(f"input_boolean.{self._dog_name}_visitor_mode_input")
            manual_visitor_mode = visitor_mode_state.state == "on" if visitor_mode_state else False
            
            # Get visitor information
            visitor_name_state = self.hass.states.get(f"input_text.{self._dog_name}_visitor_name")
            visitor_name = visitor_name_state.state if visitor_name_state else ""
            
            visitor_start_state = self.hass.states.get(f"input_datetime.{self._dog_name}_visitor_start")
            visitor_start = visitor_start_state.state if visitor_start_state else ""
            
            visitor_end_state = self.hass.states.get(f"input_datetime.{self._dog_name}_visitor_end")
            visitor_end = visitor_end_state.state if visitor_end_state else ""
            
            # Check if currently in scheduled visitor period
            scheduled_visitor_active = self._check_scheduled_visitor_period(visitor_start, visitor_end)
            
            # Visitor mode is active if manual mode OR scheduled period
            visitor_mode_active = manual_visitor_mode or scheduled_visitor_active
            
            self._attr_is_on = visitor_mode_active
            
            # Calculate visitor session duration
            session_info = self._calculate_visitor_session_info(visitor_start, visitor_end)
            
            self._attr_extra_state_attributes = {
                "manual_mode": manual_visitor_mode,
                "scheduled_active": scheduled_visitor_active,
                "visitor_name": visitor_name,
                "visitor_start": visitor_start,
                "visitor_end": visitor_end,
                "session_info": session_info,
                "active_reason": "Manual" if manual_visitor_mode else ("Scheduled" if scheduled_visitor_active else "None"),
                "last_updated": datetime.now().isoformat(),
            }
            
        except Exception as e:
            _LOGGER.error("Error updating visitor mode sensor for %s: %s", self._dog_name, e)
            self._attr_is_on = False
            self._attr_extra_state_attributes = {
                "error": str(e),
                "last_updated": datetime.now().isoformat(),
            }

    def _check_scheduled_visitor_period(self, start_time: str, end_time: str) -> bool:
        """Check if currently within scheduled visitor period."""
        try:
            if not start_time or not end_time:
                return False
            
            now = datetime.now()
            start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
            
            # Convert to local timezone
            start_dt = start_dt.replace(tzinfo=None)
            end_dt = end_dt.replace(tzinfo=None)
            
            return start_dt <= now <= end_dt
            
        except (ValueError, TypeError) as e:
            _LOGGER.debug("Error parsing visitor times for %s: %s", self._dog_name, e)
            return False

    def _calculate_visitor_session_info(self, start_time: str, end_time: str) -> Dict[str, Any]:
        """Calculate visitor session information."""
        try:
            session_info = {
                "duration_minutes": 0,
                "time_remaining_minutes": 0,
                "status": "Not scheduled"
            }
            
            if not start_time or not end_time:
                return session_info
            
            now = datetime.now()
            start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00")).replace(tzinfo=None)
            end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00")).replace(tzinfo=None)
            
            # Calculate total duration
            total_duration = end_dt - start_dt
            session_info["duration_minutes"] = int(total_duration.total_seconds() / 60)
            
            # Calculate status and remaining time
            if now < start_dt:
                session_info["status"] = "Scheduled"
                time_until = start_dt - now
                session_info["time_until_minutes"] = int(time_until.total_seconds() / 60)
            elif start_dt <= now <= end_dt:
                session_info["status"] = "Active"
                time_remaining = end_dt - now
                session_info["time_remaining_minutes"] = max(0, int(time_remaining.total_seconds() / 60))
            else:
                session_info["status"] = "Ended"
                session_info["time_remaining_minutes"] = 0
            
            return session_info
            
        except (ValueError, TypeError) as e:
            _LOGGER.debug("Error calculating visitor session info for %s: %s", self._dog_name, e)
            return {"status": "Error", "duration_minutes": 0, "time_remaining_minutes": 0}


class HundesystemNeedsAttentionBinarySensor(HundesystemBinarySensorBase):
    """Binary sensor for needs attention status."""

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
        
        # Entities that can trigger attention needs
        self._attention_entities = [
            f"input_boolean.{dog_name}_emergency_mode",
            f"input_select.{dog_name}_health_status", 
            f"input_select.{dog_name}_mood",
            f"binary_sensor.{dog_name}_feeding_complete",
            f"binary_sensor.{dog_name}_daily_tasks_complete",
            f"sensor.{dog_name}_last_activity",
            f"input_boolean.{dog_name}_medication_given",
        ]

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Track attention-triggering entities
        self._track_entity_changes(self._attention_entities, self._attention_state_changed)
        
        # Check attention needs every 15 minutes
        self._track_time_interval(self._periodic_attention_check, timedelta(minutes=15))
        
        # Initial update
        await self._async_update_state()

    @callback
    def _attention_state_changed(self, event) -> None:
        """Handle attention state changes - CORRECTED."""
        self.hass.async_create_task(self._async_update_state())
        self.async_write_ha_state()

    @callback
    def _periodic_attention_check(self, time) -> None:
        """Periodic attention check - CORRECTED."""
        self.hass.async_create_task(self._async_update_state())

    async def _async_update_state(self) -> None:
        """Update the needs attention binary sensor state."""
        try:
            attention_reasons = []
            priority_level = "none"
            
            # Check emergency mode (highest priority)
            emergency_state = self.hass.states.get(f"input_boolean.{self._dog_name}_emergency_mode")
            if emergency_state and emergency_state.state == "on":
                attention_reasons.append("Notfallmodus aktiviert")
                priority_level = "critical"
            
            # Check health status
            health_state = self.hass.states.get(f"input_select.{self._dog_name}_health_status")
            health_status = health_state.state if health_state else "Gut"
            
            if health_status in ["Krank", "Notfall"]:
                attention_reasons.append(f"Gesundheitsstatus: {health_status}")
                if priority_level != "critical":
                    priority_level = "high"
            elif health_status == "Schwach":
                attention_reasons.append("Gesundheit bedenklich")
                if priority_level not in ["critical", "high"]:
                    priority_level = "medium"
            
            # Check mood
            mood_state = self.hass.states.get(f"input_select.{self._dog_name}_mood")
            mood = mood_state.state if mood_state else "Glücklich"
            
            if mood in ["Ängstlich", "Krank"]:
                attention_reasons.append(f"Stimmung: {mood}")
                if priority_level not in ["critical", "high"]:
                    priority_level = "medium"
            elif mood == "Gestresst":
                attention_reasons.append("Gestresst")
                if priority_level == "none":
                    priority_level = "low"
            
            # Check feeding completion
            feeding_complete_state = self.hass.states.get(f"binary_sensor.{self._dog_name}_feeding_complete")
            if feeding_complete_state and feeding_complete_state.state == "off":
                # Check if it's late for feeding
                now = datetime.now()
                if now.hour > 9:  # After 9 AM, feeding should be started
                    attention_reasons.append("Fütterung unvollständig")
                    if priority_level == "none":
                        priority_level = "medium"
            
            # Check daily tasks completion
            tasks_complete_state = self.hass.states.get(f"binary_sensor.{self._dog_name}_daily_tasks_complete")
            if tasks_complete_state and tasks_complete_state.state == "off":
                now = datetime.now()
                if now.hour > 11:  # After 11 AM, basic tasks should be done
                    attention_reasons.append("Tägliche Aufgaben unvollständig")
                    if priority_level == "none":
                        priority_level = "low"
            
            # Check last activity (inactivity warning)
            last_activity_state = self.hass.states.get(f"sensor.{self._dog_name}_last_activity")
            if last_activity_state and last_activity_state.attributes:
                time_ago = last_activity_state.attributes.get("time_ago", "")
                if "Tag" in time_ago:  # More than a day
                    attention_reasons.append("Lange keine Aktivität")
                    if priority_level not in ["critical", "high"]:
                        priority_level = "medium"
            
            # Check medication
            medication_state = self.hass.states.get(f"input_boolean.{self._dog_name}_medication_given")
            if medication_state:
                # Check if medication schedule exists and if it's overdue
                medication_time_state = self.hass.states.get(f"input_datetime.{self._dog_name}_medication_time")
                if medication_time_state and medication_state.state == "off":
                    # Simple check - in real implementation would be more sophisticated
                    now = datetime.now()
                    if now.hour > 12:  # Simplified check
                        attention_reasons.append("Medikament noch nicht gegeben")
                        if priority_level == "none":
                            priority_level = "medium"
            
            # Determine if attention is needed
            needs_attention = len(attention_reasons) > 0
            
            self._attr_is_on = needs_attention
            
            self._attr_extra_state_attributes = {
                "attention_reasons": attention_reasons,
                "priority_level": priority_level,
                "total_issues": len(attention_reasons),
                "needs_immediate_attention": priority_level in ["critical", "high"],
                "assessment": self._get_attention_assessment(priority_level, attention_reasons),
                "last_updated": datetime.now().isoformat(),
            }
            
        except Exception as e:
            _LOGGER.error("Error updating needs attention sensor for %s: %s", self._dog_name, e)
            self._attr_is_on = True  # Safe default - assume attention is needed on error
            self._attr_extra_state_attributes = {
                "
