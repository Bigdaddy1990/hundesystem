"""Button platform for Hundesystem."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from homeassistant.components.button import ButtonEntity, ButtonDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo

from .const import (
    DOMAIN,
    CONF_DOG_NAME,
    ICONS,
    ENTITIES,
    SERVICE_DAILY_RESET,
    SERVICE_TRIGGER_FEEDING_REMINDER,
    SERVICE_TEST_NOTIFICATION,
    SERVICE_EMERGENCY_CONTACT,
    SERVICE_LOG_ACTIVITY,
    SERVICE_SET_VISITOR_MODE,
    MEAL_TYPES,
    ACTIVITY_TYPES,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Hundesystem buttons."""
    dog_name = config_entry.data[CONF_DOG_NAME]
    
    buttons = [
        # Basic control buttons
        HundesystemResetButton(hass, config_entry, dog_name),
        HundesystemFeedingReminderButton(hass, config_entry, dog_name),
        HundesystemTestNotificationButton(hass, config_entry, dog_name),
        
        # Quick action buttons
        HundesystemQuickOutsideButton(hass, config_entry, dog_name),
        HundesystemQuickFeedingButton(hass, config_entry, dog_name),
        HundesystemQuickPoopButton(hass, config_entry, dog_name),
        
        # Activity logging buttons
        HundesystemLogWalkButton(hass, config_entry, dog_name),
        HundesystemLogPlayButton(hass, config_entry, dog_name),
        HundesystemLogTrainingButton(hass, config_entry, dog_name),
        
        # Emergency and visitor buttons
        HundesystemEmergencyButton(hass, config_entry, dog_name),
        HundesystemVisitorModeToggleButton(hass, config_entry, dog_name),
        
        # Health and medication buttons
        HundesystemMedicationGivenButton(hass, config_entry, dog_name),
        HundesystemHealthCheckButton(hass, config_entry, dog_name),
        
        # Feeding specific buttons
        HundesystemMorningFeedingButton(hass, config_entry, dog_name),
        HundesystemLunchFeedingButton(hass, config_entry, dog_name),
        HundesystemEveningFeedingButton(hass, config_entry, dog_name),
        HundesystemSnackButton(hass, config_entry, dog_name),
    ]
    
    async_add_entities(buttons)


class HundesystemBaseButton(ButtonEntity):
    """Base class for Hundesystem buttons."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        dog_name: str,
        button_type: str,
    ) -> None:
        """Initialize the button."""
        self.hass = hass
        self._config_entry = config_entry
        self._dog_name = dog_name
        self._button_type = button_type
        self._attr_unique_id = f"{DOMAIN}_{dog_name}_{button_type}"
        self._attr_name = f"{dog_name.title()} {button_type.replace('_', ' ').title()}"
        
    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._dog_name)},
            name=f"Hundesystem {self._dog_name.title()}",
            manufacturer="Hundesystem",
            model="Dog Management System",
            sw_version="2.0.0",
        )


class HundesystemResetButton(HundesystemBaseButton):
    """Button to reset daily statistics."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        dog_name: str,
    ) -> None:
        """Initialize the reset button."""
        super().__init__(hass, config_entry, dog_name, ENTITIES["daily_reset_button"])
        self._attr_icon = ICONS["reset"]
        self._attr_device_class = ButtonDeviceClass.RESTART

    async def async_press(self) -> None:
        """Handle the button press."""
        try:
            await self.hass.services.async_call(
                DOMAIN, 
                SERVICE_DAILY_RESET,
                {"dog_name": self._dog_name},
                blocking=True
            )
            _LOGGER.info("Daily reset executed for %s", self._dog_name)
        except Exception as e:
            _LOGGER.error("Failed to execute daily reset for %s: %s", self._dog_name, e)


class HundesystemFeedingReminderButton(HundesystemBaseButton):
    """Button to trigger feeding reminder."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        dog_name: str,
    ) -> None:
        """Initialize the feeding reminder button."""
        super().__init__(hass, config_entry, dog_name, ENTITIES["feeding_reminder_button"])
        self._attr_icon = ICONS["bell"]

    async def async_press(self) -> None:
        """Handle the button press."""
        try:
            # Determine appropriate meal type based on current time
            current_hour = datetime.now().hour
            
            if 6 <= current_hour < 11:
                meal_type = "morning"
            elif 11 <= current_hour < 15:
                meal_type = "lunch"
            elif 17 <= current_hour < 21:
                meal_type = "evening"
            else:
                meal_type = "snack"
            
            await self.hass.services.async_call(
                DOMAIN,
                SERVICE_TRIGGER_FEEDING_REMINDER,
                {
                    "meal_type": meal_type,
                    "dog_name": self._dog_name,
                    "message": f"🐶 Zeit für {MEAL_TYPES[meal_type]} für {self._dog_name.title()}!"
                },
                blocking=True
            )
            _LOGGER.info("Feeding reminder sent for %s (%s)", self._dog_name, meal_type)
        except Exception as e:
            _LOGGER.error("Failed to send feeding reminder for %s: %s", self._dog_name, e)


class HundesystemTestNotificationButton(HundesystemBaseButton):
    """Button to test notifications."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        dog_name: str,
    ) -> None:
        """Initialize the test notification button."""
        super().__init__(hass, config_entry, dog_name, ENTITIES["test_notification_button"])
        self._attr_icon = ICONS["test"]

    async def async_press(self) -> None:
        """Handle the button press."""
        try:
            await self.hass.services.async_call(
                DOMAIN,
                SERVICE_TEST_NOTIFICATION,
                {"dog_name": self._dog_name},
                blocking=True
            )
            _LOGGER.info("Test notification sent for %s", self._dog_name)
        except Exception as e:
            _LOGGER.error("Failed to send test notification for %s: %s", self._dog_name, e)


class HundesystemQuickOutsideButton(HundesystemBaseButton):
    """Button for quick outside action."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        dog_name: str,
    ) -> None:
        """Initialize the quick outside button."""
        super().__init__(hass, config_entry, dog_name, ENTITIES["quick_outside_button"])
        self._attr_icon = ICONS["outside"]

    async def async_press(self) -> None:
        """Handle the button press."""
        try:
            # Toggle outside status
            outside_entity = f"input_boolean.{self._dog_name}_outside"
            await self.hass.services.async_call(
                "input_boolean", "toggle",
                {"entity_id": outside_entity},
                blocking=True
            )
            
            # Increment outside counter
            counter_entity = f"counter.{self._dog_name}_outside_count"
            await self.hass.services.async_call(
                "counter", "increment",
                {"entity_id": counter_entity},
                blocking=True
            )
            
            # Update last outside datetime
            datetime_entity = f"input_datetime.{self._dog_name}_last_outside"
            if self.hass.states.get(datetime_entity):
                await self.hass.services.async_call(
                    "input_datetime", "set_datetime",
                    {
                        "entity_id": datetime_entity,
                        "datetime": datetime.now().isoformat()
                    },
                    blocking=True
                )
            
            _LOGGER.info("Quick outside action executed for %s", self._dog_name)
        except Exception as e:
            _LOGGER.error("Failed to execute quick outside action for %s: %s", self._dog_name, e)


class HundesystemQuickFeedingButton(HundesystemBaseButton):
    """Button for quick feeding action."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        dog_name: str,
    ) -> None:
        """Initialize the quick feeding button."""
        super().__init__(hass, config_entry, dog_name, ENTITIES["quick_feeding_button"])
        self._attr_icon = ICONS["food"]

    async def async_press(self) -> None:
        """Handle the button press."""
        try:
            # Determine current meal based on time
            current_hour = datetime.now().hour
            
            if 6 <= current_hour < 11:
                meal = "morning"
            elif 11 <= current_hour < 15:
                meal = "lunch"
            elif 17 <= current_hour < 21:
                meal = "evening"
            else:
                meal = "snack"
            
            # Set feeding status
            feeding_entity = f"input_boolean.{self._dog_name}_feeding_{meal}"
            await self.hass.services.async_call(
                "input_boolean", "turn_on",
                {"entity_id": feeding_entity},
                blocking=True
            )
            
            # Increment feeding counter
            counter_entity = f"counter.{self._dog_name}_feeding_{meal}_count"
            await self.hass.services.async_call(
                "counter", "increment",
                {"entity_id": counter_entity},
                blocking=True
            )
            
            # Update last feeding datetime
            datetime_entity = f"input_datetime.{self._dog_name}_last_feeding_{meal}"
            if self.hass.states.get(datetime_entity):
                await self.hass.services.async_call(
                    "input_datetime", "set_datetime",
                    {
                        "entity_id": datetime_entity,
                        "datetime": datetime.now().isoformat()
                    },
                    blocking=True
                )
            
            _LOGGER.info("Quick feeding (%s) executed for %s", meal, self._dog_name)
        except Exception as e:
            _LOGGER.error("Failed to execute quick feeding for %s: %s", self._dog_name, e)


class HundesystemQuickPoopButton(HundesystemBaseButton):
    """Button for quick poop action."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        dog_name: str,
    ) -> None:
        """Initialize the quick poop button."""
        super().__init__(hass, config_entry, dog_name, "quick_poop_button")
        self._attr_icon = ICONS["poop"]

    async def async_press(self) -> None:
        """Handle the button press."""
        try:
            # Set poop status
            poop_entity = f"input_boolean.{self._dog_name}_poop_done"
            await self.hass.services.async_call(
                "input_boolean", "turn_on",
                {"entity_id": poop_entity},
                blocking=True
            )
            
            # Increment poop counter
            counter_entity = f"counter.{self._dog_name}_poop_count"
            await self.hass.services.async_call(
                "counter", "increment",
                {"entity_id": counter_entity},
                blocking=True
            )
            
            # Update last poop datetime
            datetime_entity = f"input_datetime.{self._dog_name}_last_poop"
            if self.hass.states.get(datetime_entity):
                await self.hass.services.async_call(
                    "input_datetime", "set_datetime",
                    {
                        "entity_id": datetime_entity,
                        "datetime": datetime.now().isoformat()
                    },
                    blocking=True
                )
            
            _LOGGER.info("Quick poop action executed for %s", self._dog_name)
        except Exception as e:
            _LOGGER.error("Failed to execute quick poop action for %s: %s", self._dog_name, e)


class HundesystemLogWalkButton(HundesystemBaseButton):
    """Button to log a walk activity."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        dog_name: str,
    ) -> None:
        """Initialize the log walk button."""
        super().__init__(hass, config_entry, dog_name, "log_walk_button")
        self._attr_icon = ICONS["walk"]

    async def async_press(self) -> None:
        """Handle the button press."""
        try:
            await self.hass.services.async_call(
                DOMAIN,
                SERVICE_LOG_ACTIVITY,
                {
                    "activity_type": "walk",
                    "dog_name": self._dog_name,
                    "notes": "Spaziergang per Schnellbutton geloggt"
                },
                blocking=True
            )
            _LOGGER.info("Walk activity logged for %s", self._dog_name)
        except Exception as e:
            _LOGGER.error("Failed to log walk activity for %s: %s", self._dog_name, e)


class HundesystemLogPlayButton(HundesystemBaseButton):
    """Button to log a play activity."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        dog_name: str,
    ) -> None:
        """Initialize the log play button."""
        super().__init__(hass, config_entry, dog_name, "log_play_button")
        self._attr_icon = ICONS["play"]

    async def async_press(self) -> None:
        """Handle the button press."""
        try:
            await self.hass.services.async_call(
                DOMAIN,
                SERVICE_LOG_ACTIVITY,
                {
                    "activity_type": "play",
                    "dog_name": self._dog_name,
                    "notes": "Spielzeit per Schnellbutton geloggt"
                },
                blocking=True
            )
            _LOGGER.info("Play activity logged for %s", self._dog_name)
        except Exception as e:
            _LOGGER.error("Failed to log play activity for %s: %s", self._dog_name, e)


class HundesystemLogTrainingButton(HundesystemBaseButton):
    """Button to log a training activity."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        dog_name: str,
    ) -> None:
        """Initialize the log training button."""
        super().__init__(hass, config_entry, dog_name, "log_training_button")
        self._attr_icon = ICONS["training"]

    async def async_press(self) -> None:
        """Handle the button press."""
        try:
            await self.hass.services.async_call(
                DOMAIN,
                SERVICE_LOG_ACTIVITY,
                {
                    "activity_type": "training",
                    "dog_name": self._dog_name,
                    "notes": "Training per Schnellbutton geloggt"
                },
                blocking=True
            )
            _LOGGER.info("Training activity logged for %s", self._dog_name)
        except Exception as e:
            _LOGGER.error("Failed to log training activity for %s: %s", self._dog_name, e)


class HundesystemEmergencyButton(HundesystemBaseButton):
    """Button for emergency activation."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        dog_name: str,
    ) -> None:
        """Initialize the emergency button."""
        super().__init__(hass, config_entry, dog_name, ENTITIES["emergency_button"])
        self._attr_icon = ICONS["emergency"]
        self._attr_device_class = ButtonDeviceClass.RESTART

    async def async_press(self) -> None:
        """Handle the button press."""
        try:
            # Toggle emergency mode
            emergency_entity = f"input_boolean.{self._dog_name}_emergency_mode"
            await self.hass.services.async_call(
                "input_boolean", "toggle",
                {"entity_id": emergency_entity},
                blocking=True
            )
            
            # Send emergency notification
            await self.hass.services.async_call(
                DOMAIN,
                SERVICE_EMERGENCY_CONTACT,
                {
                    "emergency_type": "other",
                    "message": f"Notfallmodus für {self._dog_name.title()} wurde aktiviert",
                    "dog_name": self._dog_name
                },
                blocking=True
            )
            
            _LOGGER.warning("Emergency mode toggled for %s", self._dog_name)
        except Exception as e:
            _LOGGER.error("Failed to handle emergency for %s: %s", self._dog_name, e)


class HundesystemVisitorModeToggleButton(HundesystemBaseButton):
    """Button to toggle visitor mode."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        dog_name: str,
    ) -> None:
        """Initialize the visitor mode toggle button."""
        super().__init__(hass, config_entry, dog_name, "visitor_mode_toggle_button")
        self._attr_icon = ICONS["visitor"]

    async def async_press(self) -> None:
        """Handle the button press."""
        try:
            # Check current visitor mode status
            visitor_entity = f"input_boolean.{self._dog_name}_visitor_mode_input"
            current_state = self.hass.states.get(visitor_entity)
            
            if current_state:
                new_state = not (current_state.state == "on")
                
                await self.hass.services.async_call(
                    DOMAIN,
                    SERVICE_SET_VISITOR_MODE,
                    {
                        "enabled": new_state,
                        "dog_name": self._dog_name,
                        "visitor_name": "Schnellbutton" if new_state else ""
                    },
                    blocking=True
                )
                
                _LOGGER.info("Visitor mode %s for %s", "enabled" if new_state else "disabled", self._dog_name)
        except Exception as e:
            _LOGGER.error("Failed to toggle visitor mode for %s: %s", self._dog_name, e)


class HundesystemMedicationGivenButton(HundesystemBaseButton):
    """Button to mark medication as given."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        dog_name: str,
    ) -> None:
        """Initialize the medication given button."""
        super().__init__(hass, config_entry, dog_name, "medication_given_button")
        self._attr_icon = ICONS["medication"]

    async def async_press(self) -> None:
        """Handle the button press."""
        try:
            # Set medication given status
            medication_entity = f"input_boolean.{self._dog_name}_medication_given"
            await self.hass.services.async_call(
                "input_boolean", "turn_on",
                {"entity_id": medication_entity},
                blocking=True
            )
            
            # Increment medication counter
            counter_entity = f"counter.{self._dog_name}_medication_count"
            if self.hass.states.get(counter_entity):
                await self.hass.services.async_call(
                    "counter", "increment",
                    {"entity_id": counter_entity},
                    blocking=True
                )
            
            _LOGGER.info("Medication marked as given for %s", self._dog_name)
        except Exception as e:
            _LOGGER.error("Failed to mark medication as given for %s: %s", self._dog_name, e)


class HundesystemHealthCheckButton(HundesystemBaseButton):
    """Button to trigger a health check."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        dog_name: str,
    ) -> None:
        """Initialize the health check button."""
        super().__init__(hass, config_entry, dog_name, "health_check_button")
        self._attr_icon = ICONS["health"]

    async def async_press(self) -> None:
        """Handle the button press."""
        try:
            # Perform basic health check
            health_observations = []
            
            # Check feeding status
            feeding_complete_state = self.hass.states.get(f"binary_sensor.{self._dog_name}_feeding_complete")
            if feeding_complete_state and feeding_complete_state.state == "on":
                health_observations.append("Fütterung vollständig")
            else:
                health_observations.append("Fütterung unvollständig")
            
            # Check activity status
            outside_state = self.hass.states.get(f"input_boolean.{self._dog_name}_outside")
            if outside_state and outside_state.state == "on":
                health_observations.append("War heute draußen")
            else:
                health_observations.append("War noch nicht draußen")
            
            # Get current health status
            health_status_state = self.hass.states.get(f"input_select.{self._dog_name}_health_status")
            current_health = health_status_state.state if health_status_state else "Gut"
            health_observations.append(f"Gesundheitsstatus: {current_health}")
            
            # Create health check summary
            health_summary = f"Gesundheitscheck für {self._dog_name.title()}: " + "; ".join(health_observations)
            
            # Update health notes
            health_notes_entity = f"input_text.{self._dog_name}_health_notes"
            if self.hass.states.get(health_notes_entity):
                timestamp = datetime.now().strftime("%d.%m. %H:%M")
                await self.hass.services.async_call(
                    "input_text", "set_value",
                    {
                        "entity_id": health_notes_entity,
                        "value": f"[{timestamp}] {health_summary}"
                    },
                    blocking=True
                )
            
            _LOGGER.info("Health check completed for %s", self._dog_name)
        except Exception as e:
            _LOGGER.error("Failed to perform health check for %s: %s", self._dog_name, e)


# Specific feeding buttons
class HundesystemMorningFeedingButton(HundesystemBaseButton):
    """Button for morning feeding."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        dog_name: str,
    ) -> None:
        """Initialize the morning feeding button."""
        super().__init__(hass, config_entry, dog_name, "morning_feeding_button")
        self._attr_icon = ICONS["morning"]

    async def async_press(self) -> None:
        """Handle the button press."""
        await self._handle_feeding("morning")

    async def _handle_feeding(self, meal_type: str) -> None:
        """Handle feeding action for specific meal."""
        try:
            # Set feeding status
            feeding_entity = f"input_boolean.{self._dog_name}_feeding_{meal_type}"
            await self.hass.services.async_call(
                "input_boolean", "turn_on",
                {"entity_id": feeding_entity},
                blocking=True
            )
            
            # Increment counter
            counter_entity = f"counter.{self._dog_name}_feeding_{meal_type}_count"
            await self.hass.services.async_call(
                "counter", "increment",
                {"entity_id": counter_entity},
                blocking=True
            )
            
            # Update datetime
            datetime_entity = f"input_datetime.{self._dog_name}_last_feeding_{meal_type}"
            if self.hass.states.get(datetime_entity):
                await self.hass.services.async_call(
                    "input_datetime", "set_datetime",
                    {
                        "entity_id": datetime_entity,
                        "datetime": datetime.now().isoformat()
                    },
                    blocking=True
                )
            
            _LOGGER.info("%s feeding executed for %s", meal_type, self._dog_name)
        except Exception as e:
            _LOGGER.error("Failed to execute %s feeding for %s: %s", meal_type, self._dog_name, e)


class HundesystemLunchFeedingButton(HundesystemMorningFeedingButton):
    """Button for lunch feeding."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        dog_name: str,
    ) -> None:
        """Initialize the lunch feeding button."""
        super().__init__(hass, config_entry, dog_name)
        self._button_type = "lunch_feeding_button"
        self._attr_unique_id = f"{DOMAIN}_{dog_name}_lunch_feeding_button"
        self._attr_name = f"{dog_name.title()} Lunch Feeding Button"
        self._attr_icon = ICONS["lunch"]

    async def async_press(self) -> None:
        """Handle the button press."""
        await self._handle_feeding("lunch")


class HundesystemEveningFeedingButton(HundesystemMorningFeedingButton):
    """Button for evening feeding."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        dog_name: str,
    ) -> None:
        """Initialize the evening feeding button."""
        super().__init__(hass, config_entry, dog_name)
        self._button_type = "evening_feeding_button"
        self._attr_unique_id = f"{DOMAIN}_{dog_name}_evening_feeding_button"
        self._attr_name = f"{dog_name.title()} Evening Feeding Button"
        self._attr_icon = ICONS["evening"]

    async def async_press(self) -> None:
        """Handle the button press."""
        await self._handle_feeding("evening")


class HundesystemSnackButton(HundesystemMorningFeedingButton):
    """Button for snack/treat feeding."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        dog_name: str,
    ) -> None:
        """Initialize the snack button."""
        super().__init__(hass, config_entry, dog_name)
        self._button_type = "snack_button"
        self._attr_unique_id = f"{DOMAIN}_{dog_name}_snack_button"
        self._attr_name = f"{dog_name.title()} Snack Button"
        self._attr_icon = ICONS["snack"]

    async def async_press(self) -> None:
        """Handle the button press."""
        await self._handle_feeding("snack")