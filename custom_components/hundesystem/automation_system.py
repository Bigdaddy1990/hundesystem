"""Automation system for Hundesystem integration - SMART DOG CARE."""
from __future__ import annotations

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable

from homeassistant.core import HomeAssistant, callback, Event, State
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_interval
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.components.automation import AutomationEntity
from homeassistant.helpers.script import Script
from homeassistant.helpers.template import Template

from .const import (
    DOMAIN,
    CONF_DOG_NAME,
    ICONS,
    ENTITIES,
    FEEDING_TYPES,
    MEAL_TYPES,
    STATUS_MESSAGES,
    HEALTH_THRESHOLDS,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Hundesystem automations based on a config entry."""
    dog_name = config_entry.data[CONF_DOG_NAME]
    
    # Create automation manager
    automation_manager = HundesystemAutomationManager(hass, config_entry, dog_name)
    
    # Initialize all automations
    await automation_manager.async_setup()
    
    # Register automation manager as a single entity for management
    async_add_entities([automation_manager], True)


class HundesystemAutomationManager(RestoreEntity):
    """Central automation manager for the Hundesystem."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        dog_name: str,
    ) -> None:
        """Initialize the automation manager."""
        self.hass = hass
        self._config_entry = config_entry
        self._dog_name = dog_name
        self._attr_unique_id = f"{DOMAIN}_{dog_name}_automation_manager"
        self._attr_name = f"{dog_name.title()} Automation Manager"
        self._attr_icon = ICONS["automation"]
        
        # Track all automation listeners for cleanup
        self._listeners: List[Callable[[], None]] = []
        self._automation_registry: Dict[str, Dict[str, Any]] = {}
        
        # Automation state tracking
        self._feeding_automation_active = True
        self._activity_automation_active = True
        self._health_automation_active = True
        self._emergency_automation_active = True
        
        # Statistics
        self._automation_stats = {
            "total_triggers": 0,
            "feeding_triggers": 0,
            "activity_triggers": 0,
            "health_triggers": 0,
            "emergency_triggers": 0,
            "last_trigger": None,
        }

    async def async_setup(self) -> None:
        """Set up all automations."""
        try:
            _LOGGER.info("Setting up Hundesystem automations for %s", self._dog_name)
            
            # Setup different automation categories
            await self._setup_feeding_automations()
            await self._setup_activity_automations()
            await self._setup_health_automations()
            await self._setup_emergency_automations()
            await self._setup_visitor_automations()
            await self._setup_maintenance_automations()
            
            # Setup periodic checks
            self._setup_periodic_automations()
            
            _LOGGER.info("Successfully set up %d automations for %s", 
                        len(self._automation_registry), self._dog_name)
            
        except Exception as e:
            _LOGGER.error("Error setting up automations for %s: %s", self._dog_name, e)
            raise

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Restore previous state
        if (old_state := await self.async_get_last_state()) is not None:
            if old_state.attributes:
                self._automation_stats = old_state.attributes.get("automation_stats", self._automation_stats)

    async def async_will_remove_from_hass(self) -> None:
        """Clean up when entity is removed."""
        # Remove all automation listeners
        for remove_listener in self._listeners:
            try:
                remove_listener()
            except Exception as e:
                _LOGGER.warning("Error removing automation listener: %s", e)
        self._listeners.clear()
        
        _LOGGER.info("Cleaned up %d automation listeners for %s", 
                    len(self._listeners), self._dog_name)
        
        await super().async_will_remove_from_hass()

    @property
    def state(self) -> str:
        """Return the state of the automation manager."""
        active_count = sum([
            self._feeding_automation_active,
            self._activity_automation_active,
            self._health_automation_active,
            self._emergency_automation_active,
        ])
        
        if active_count == 4:
            return "all_active"
        elif active_count > 0:
            return "partially_active"
        else:
            return "inactive"

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return extra state attributes."""
        return {
            "automation_registry": list(self._automation_registry.keys()),
            "total_automations": len(self._automation_registry),
            "feeding_automation_active": self._feeding_automation_active,
            "activity_automation_active": self._activity_automation_active,
            "health_automation_active": self._health_automation_active,
            "emergency_automation_active": self._emergency_automation_active,
            "automation_stats": self._automation_stats,
            "last_updated": datetime.now().isoformat(),
        }

    async def _setup_feeding_automations(self) -> None:
        """Set up feeding-related automations."""
        
        # Automation: Feeding reminder based on scheduled times
        feeding_reminder_entities = [f"input_datetime.{self._dog_name}_feeding_{meal}_time" for meal in FEEDING_TYPES]
        feeding_status_entities = [f"input_boolean.{self._dog_name}_feeding_{meal}" for meal in FEEDING_TYPES]
        
        def create_feeding_automation(meal_type: str):
            @callback
            def feeding_reminder_trigger(event: Event) -> None:
                """Trigger feeding reminder automation."""
                self.hass.async_create_task(
                    self._handle_feeding_reminder(meal_type, event)
                )
            return feeding_reminder_trigger
        
        # Set up feeding reminders for each meal
        for meal in FEEDING_TYPES:
            automation_id = f"feeding_reminder_{meal}"
            
            # Track scheduled time changes
            time_entity = f"input_datetime.{self._dog_name}_feeding_{meal}_time"
            status_entity = f"input_boolean.{self._dog_name}_feeding_{meal}"
            
            # Register automation
            self._automation_registry[automation_id] = {
                "type": "feeding",
                "meal_type": meal,
                "trigger_entities": [time_entity, status_entity],
                "description": f"Feeding reminder for {MEAL_TYPES.get(meal, meal)}",
                "active": True,
            }
            
            # Set up state change tracking
            remove_listener = async_track_state_change_event(
                self.hass, [time_entity, status_entity], 
                create_feeding_automation(meal)
            )
            self._listeners.append(remove_listener)
        
        # Automation: Overdue feeding alert
        overdue_entities = [f"binary_sensor.{self._dog_name}_overdue_feeding"]
        
        @callback
        def overdue_feeding_trigger(event: Event) -> None:
            """Trigger overdue feeding automation."""
            self.hass.async_create_task(self._handle_overdue_feeding(event))
        
        if overdue_entities[0]:  # Check if entity exists
            remove_listener = async_track_state_change_event(
                self.hass, overdue_entities, overdue_feeding_trigger
            )
            self._listeners.append(remove_listener)
            
            self._automation_registry["overdue_feeding_alert"] = {
                "type": "feeding",
                "trigger_entities": overdue_entities,
                "description": "Alert for overdue feedings",
                "active": True,
            }

    async def _setup_activity_automations(self) -> None:
        """Set up activity-related automations."""
        
        # Automation: Inactivity warning
        inactivity_entities = [f"binary_sensor.{self._dog_name}_inactivity_warning"]
        
        @callback
        def inactivity_trigger(event: Event) -> None:
            """Trigger inactivity automation."""
            self.hass.async_create_task(self._handle_inactivity_warning(event))
        
        remove_listener = async_track_state_change_event(
            self.hass, inactivity_entities, inactivity_trigger
        )
        self._listeners.append(remove_listener)
        
        self._automation_registry["inactivity_warning"] = {
            "type": "activity",
            "trigger_entities": inactivity_entities,
            "description": "Warning for extended inactivity",
            "active": True,
        }
        
        # Automation: Activity milestone celebrations
        activity_counters = [
            f"counter.{self._dog_name}_walk_count",
            f"counter.{self._dog_name}_play_count",
            f"counter.{self._dog_name}_training_count",
        ]
        
        @callback
        def activity_milestone_trigger(event: Event) -> None:
            """Trigger activity milestone automation."""
            self.hass.async_create_task(self._handle_activity_milestone(event))
        
        remove_listener = async_track_state_change_event(
            self.hass, activity_counters, activity_milestone_trigger
        )
        self._listeners.append(remove_listener)
        
        self._automation_registry["activity_milestones"] = {
            "type": "activity",
            "trigger_entities": activity_counters,
            "description": "Celebrate activity milestones",
            "active": True,
        }

    async def _setup_health_automations(self) -> None:
        """Set up health-related automations."""
        
        # Automation: Health status changes
        health_entities = [
            f"input_select.{self._dog_name}_health_status",
            f"input_select.{self._dog_name}_mood",
            f"sensor.{self._dog_name}_health_score",
        ]
        
        @callback
        def health_status_trigger(event: Event) -> None:
            """Trigger health status automation."""
            self.hass.async_create_task(self._handle_health_status_change(event))
        
        remove_listener = async_track_state_change_event(
            self.hass, health_entities, health_status_trigger
        )
        self._listeners.append(remove_listener)
        
        self._automation_registry["health_monitoring"] = {
            "type": "health",
            "trigger_entities": health_entities,
            "description": "Monitor health status changes",
            "active": True,
        }
        
        # Automation: Medication reminders
        medication_entities = [
            f"input_boolean.{self._dog_name}_medication_given",
            f"input_datetime.{self._dog_name}_medication_time",
        ]
        
        @callback
        def medication_reminder_trigger(event: Event) -> None:
            """Trigger medication reminder automation."""
            self.hass.async_create_task(self._handle_medication_reminder(event))
        
        remove_listener = async_track_state_change_event(
            self.hass, medication_entities, medication_reminder_trigger
        )
        self._listeners.append(remove_listener)
        
        self._automation_registry["medication_reminders"] = {
            "type": "health",
            "trigger_entities": medication_entities,
            "description": "Medication reminder system",
            "active": True,
        }

    async def _setup_emergency_automations(self) -> None:
        """Set up emergency-related automations."""
        
        # Automation: Emergency mode activation
        emergency_entities = [
            f"input_boolean.{self._dog_name}_emergency_mode",
            f"binary_sensor.{self._dog_name}_emergency_status",
        ]
        
        @callback
        def emergency_trigger(event: Event) -> None:
            """Trigger emergency automation."""
            self.hass.async_create_task(self._handle_emergency_activation(event))
        
        remove_listener = async_track_state_change_event(
            self.hass, emergency_entities, emergency_trigger
        )
        self._listeners.append(remove_listener)
        
        self._automation_registry["emergency_response"] = {
            "type": "emergency",
            "trigger_entities": emergency_entities,
            "description": "Emergency response system",
            "active": True,
        }
        
        # Automation: Needs attention alerts
        attention_entities = [f"binary_sensor.{self._dog_name}_needs_attention"]
        
        @callback
        def attention_trigger(event: Event) -> None:
            """Trigger attention needed automation."""
            self.hass.async_create_task(self._handle_attention_needed(event))
        
        remove_listener = async_track_state_change_event(
            self.hass, attention_entities, attention_trigger
        )
        self._listeners.append(remove_listener)
        
        self._automation_registry["attention_alerts"] = {
            "type": "emergency",
            "trigger_entities": attention_entities,
            "description": "Attention needed alert system",
            "active": True,
        }

    async def _setup_visitor_automations(self) -> None:
        """Set up visitor-related automations."""
        
        # Automation: Visitor mode management
        visitor_entities = [
            f"input_boolean.{self._dog_name}_visitor_mode_input",
            f"binary_sensor.{self._dog_name}_visitor_mode",
        ]
        
        @callback
        def visitor_mode_trigger(event: Event) -> None:
            """Trigger visitor mode automation."""
            self.hass.async_create_task(self._handle_visitor_mode_change(event))
        
        remove_listener = async_track_state_change_event(
            self.hass, visitor_entities, visitor_mode_trigger
        )
        self._listeners.append(remove_listener)
        
        self._automation_registry["visitor_management"] = {
            "type": "visitor",
            "trigger_entities": visitor_entities,
            "description": "Visitor mode management",
            "active": True,
        }

    async def _setup_maintenance_automations(self) -> None:
        """Set up maintenance-related automations."""
        
        # Automation: Daily summary generation
        @callback
        def daily_summary_trigger(time) -> None:
            """Trigger daily summary automation."""
            self.hass.async_create_task(self._handle_daily_summary())
        
        # Generate daily summary at 23:30
        remove_listener = async_track_time_interval(
            self.hass, daily_summary_trigger, timedelta(days=1)
        )
        self._listeners.append(remove_listener)
        
        self._automation_registry["daily_summary"] = {
            "type": "maintenance",
            "trigger_entities": [],
            "description": "Daily summary generation",
            "active": True,
        }

    def _setup_periodic_automations(self) -> None:
        """Set up periodic check automations."""
        
        # Periodic system health check every 30 minutes
        @callback
        def system_health_check(time) -> None:
            """Periodic system health check."""
            self.hass.async_create_task(self._handle_system_health_check())
        
        remove_listener = async_track_time_interval(
            self.hass, system_health_check, timedelta(minutes=30)
        )
        self._listeners.append(remove_listener)
        
        self._automation_registry["system_health_check"] = {
            "type": "maintenance",
            "trigger_entities": [],
            "description": "Periodic system health monitoring",
            "active": True,
        }

    # AUTOMATION HANDLERS
    
    async def _handle_feeding_reminder(self, meal_type: str, event: Event) -> None:
        """Handle feeding reminder automation."""
        try:
            self._update_stats("feeding_triggers")
            
            # Check if meal is already given
            status_entity = f"input_boolean.{self._dog_name}_feeding_{meal_type}"
            status_state = self.hass.states.get(status_entity)
            
            if status_state and status_state.state == "on":
                # Meal already given, no reminder needed
                return
            
            # Get scheduled time
            time_entity = f"input_datetime.{self._dog_name}_feeding_{meal_type}_time"
            time_state = self.hass.states.get(time_entity)
            
            if not time_state or time_state.state in ["unknown", "unavailable"]:
                return
            
            scheduled_time = time_state.state
            meal_name = MEAL_TYPES.get(meal_type, meal_type)
            
            # Check if it's time for reminder (30 minutes before scheduled time)
            now = datetime.now()
            try:
                scheduled_dt = datetime.strptime(scheduled_time, "%H:%M:%S")
                scheduled_today = now.replace(
                    hour=scheduled_dt.hour, 
                    minute=scheduled_dt.minute, 
                    second=0, 
                    microsecond=0
                )
                
                reminder_time = scheduled_today - timedelta(minutes=30)
                
                # Send reminder if within 5 minutes of reminder time
                time_diff = abs((now - reminder_time).total_seconds())
                
                if time_diff <= 300:  # Within 5 minutes
                    await self._send_feeding_reminder(meal_name, scheduled_time)
                
            except ValueError as e:
                _LOGGER.warning("Error parsing feeding time for %s: %s", meal_type, e)
                
        except Exception as e:
            _LOGGER.error("Error in feeding reminder automation for %s: %s", self._dog_name, e)

    async def _handle_overdue_feeding(self, event: Event) -> None:
        """Handle overdue feeding automation."""
        try:
            self._update_stats("feeding_triggers")
            
            entity_id = event.data.get("entity_id")
            new_state = event.data.get("new_state")
            
            if not new_state or new_state.state != "on":
                return
            
            # Get overdue feeding details
            if new_state.attributes:
                overdue_meals = new_state.attributes.get("overdue_meals", [])
                overall_severity = new_state.attributes.get("overall_severity", "low")
                
                if overdue_meals:
                    await self._send_overdue_feeding_alert(overdue_meals, overall_severity)
                    
        except Exception as e:
            _LOGGER.error("Error in overdue feeding automation for %s: %s", self._dog_name, e)

    async def _handle_inactivity_warning(self, event: Event) -> None:
        """Handle inactivity warning automation."""
        try:
            self._update_stats("activity_triggers")
            
            new_state = event.data.get("new_state")
            
            if not new_state or new_state.state != "on":
                return
            
            # Get inactivity details
            if new_state.attributes:
                warning_triggers = new_state.attributes.get("warning_triggers", [])
                overall_severity = new_state.attributes.get("overall_severity", "low")
                
                if warning_triggers:
                    await self._send_inactivity_alert(warning_triggers, overall_severity)
                    
        except Exception as e:
            _LOGGER.error("Error in inactivity warning automation for %s: %s", self._dog_name, e)

    async def _handle_activity_milestone(self, event: Event) -> None:
        """Handle activity milestone automation."""
        try:
            self._update_stats("activity_triggers")
            
            entity_id = event.data.get("entity_id")
            new_state = event.data.get("new_state")
            
            if not new_state:
                return
            
            try:
                count = int(new_state.state)
                
                # Check for milestone achievements (5, 10, 25, 50, 100)
                milestones = [5, 10, 25, 50, 100]
                
                for milestone in milestones:
                    if count == milestone:
                        activity_type = self._extract_activity_type(entity_id)
                        await self._send_milestone_celebration(activity_type, milestone)
                        break
                        
            except ValueError:
                pass  # Not a numeric state
                
        except Exception as e:
            _LOGGER.error("Error in activity milestone automation for %s: %s", self._dog_name, e)

    async def _handle_health_status_change(self, event: Event) -> None:
        """Handle health status change automation."""
        try:
            self._update_stats("health_triggers")
            
            entity_id = event.data.get("entity_id")
            new_state = event.data.get("new_state")
            old_state = event.data.get("old_state")
            
            if not new_state or not old_state:
                return
            
            # Check for health deterioration
            if "health_status" in entity_id:
                await self._handle_health_status_specific_change(new_state.state, old_state.state)
            elif "mood" in entity_id:
                await self._handle_mood_change(new_state.state, old_state.state)
            elif "health_score" in entity_id:
                await self._handle_health_score_change(new_state.state, old_state.state)
                
        except Exception as e:
            _LOGGER.error("Error in health status automation for %s: %s", self._dog_name, e)

    async def _handle_emergency_activation(self, event: Event) -> None:
        """Handle emergency activation automation."""
        try:
            self._update_stats("emergency_triggers")
            
            new_state = event.data.get("new_state")
            
            if not new_state or new_state.state != "on":
                return
            
            # Emergency activated - immediate response
            await self._execute_emergency_protocol()
            
        except Exception as e:
            _LOGGER.error("Error in emergency activation automation for %s: %s", self._dog_name, e)

    async def _handle_attention_needed(self, event: Event) -> None:
        """Handle attention needed automation."""
        try:
            self._update_stats("emergency_triggers")
            
            new_state = event.data.get("new_state")
            
            if not new_state or new_state.state != "on":
                return
            
            # Get attention details
            if new_state.attributes:
                priority_level = new_state.attributes.get("priority_level", "low")
                attention_reasons = new_state.attributes.get("attention_reasons", [])
                
                await self._send_attention_alert(priority_level, attention_reasons)
                
        except Exception as e:
            _LOGGER.error("Error in attention needed automation for %s: %s", self._dog_name, e)

    async def _handle_visitor_mode_change(self, event: Event) -> None:
        """Handle visitor mode change automation."""
        try:
            new_state = event.data.get("new_state")
            
            if not new_state:
                return
            
            if new_state.state == "on":
                # Visitor mode activated
                visitor_name = ""
                if new_state.attributes:
                    visitor_name = new_state.attributes.get("visitor_name", "")
                
                await self._send_visitor_mode_notification(True, visitor_name)
            else:
                # Visitor mode deactivated
                await self._send_visitor_mode_notification(False, "")
                
        except Exception as e:
            _LOGGER.error("Error in visitor mode automation for %s: %s", self._dog_name, e)

    async def _handle_daily_summary(self) -> None:
        """Handle daily summary generation."""
        try:
            # Get daily summary data
            summary_sensor = self.hass.states.get(f"sensor.{self._dog_name}_daily_summary")
            
            if summary_sensor and summary_sensor.attributes:
                daily_rating = summary_sensor.attributes.get("daily_rating", "Unbekannt")
                overall_score = float(summary_sensor.state) if summary_sensor.state.replace('.', '').isdigit() else 0
                recommendations = summary_sensor.attributes.get("recommendations", [])
                
                await self._send_daily_summary_notification(daily_rating, overall_score, recommendations)
                
        except Exception as e:
            _LOGGER.error("Error in daily summary automation for %s: %s", self._dog_name, e)

    async def _handle_system_health_check(self) -> None:
        """Handle periodic system health check."""
        try:
            # Check system health sensor
            health_sensor = self.hass.states.get(f"binary_sensor.{self._dog_name}_system_health")
            
            if health_sensor and health_sensor.state == "on":  # System has issues
                if health_sensor.attributes:
                    health_issues = health_sensor.attributes.get("health_issues", [])
                    health_score = health_sensor.attributes.get("health_score", 0)
                    
                    if health_score < 80:  # Only alert for significant issues
                        await self._send_system_health_alert(health_issues, health_score)
                        
        except Exception as e:
            _LOGGER.error("Error in system health check automation for %s: %s", self._dog_name, e)

    # NOTIFICATION HELPERS
    
    async def _send_feeding_reminder(self, meal_name: str, scheduled_time: str) -> None:
        """Send feeding reminder notification."""
        try:
            await self.hass.services.async_call(
                "persistent_notification", "create",
                {
                    "title": f"🍽️ Fütterung - {self._dog_name.title()}",
                    "message": f"Erinnerung: {meal_name} ist für {scheduled_time[:5]} geplant",
                    "notification_id": f"feeding_reminder_{self._dog_name}_{meal_name.lower()}",
                }
            )
        except Exception as e:
            _LOGGER.error("Error sending feeding reminder: %s", e)

    async def _send_overdue_feeding_alert(self, overdue_meals: List[str], severity: str) -> None:
        """Send overdue feeding alert."""
        try:
            severity_icons = {
                "low": "⏰",
                "medium": "