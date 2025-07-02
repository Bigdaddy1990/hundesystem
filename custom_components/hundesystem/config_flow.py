"""Config flow for Hundesystem integration."""
from __future__ import annotations

import logging
import re
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.selector import selector

from .const import (
    DOMAIN,
    CONF_DOG_NAME,
    CONF_PUSH_DEVICES,
    CONF_PERSON_TRACKING,
    CONF_CREATE_DASHBOARD,
    CONF_DOOR_SENSOR,
    CONF_FEEDING_TIMES,
    CONF_RESET_TIME,
    DEFAULT_DOG_NAME,
    DEFAULT_CREATE_DASHBOARD,
    DEFAULT_PERSON_TRACKING,
    DEFAULT_RESET_TIME,
    DEFAULT_FEEDING_TIMES,
    DOG_NAME_PATTERN,
    MAX_DOGS,
)

_LOGGER = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Hundesystem."""

    VERSION = 1
    
    def __init__(self):
        """Initialize the config flow."""
        self._errors = {}
        self._data = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await self._validate_input(user_input)
                
                # Set unique ID to prevent duplicates
                await self.async_set_unique_id(info[CONF_DOG_NAME])
                self._abort_if_unique_id_configured()
                
                # Store basic info and proceed to advanced settings
                self._data.update(info)
                return await self.async_step_advanced()
                
            except AlreadyConfigured:
                errors["base"] = "already_configured"
            except InvalidDogName:
                errors["dog_name"] = "invalid_dog_name"
            except TooManyDogs:
                errors["base"] = "too_many_dogs"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        # Get available notify services
        notify_services = await self._get_notify_services()

        data_schema = vol.Schema({
            vol.Required(CONF_DOG_NAME, default=DEFAULT_DOG_NAME): cv.string,
            vol.Optional(CONF_PUSH_DEVICES, default=[]): selector({
                "select": {
                    "options": notify_services,
                    "multiple": True,
                    "mode": "dropdown"
                }
            }),
            vol.Optional(CONF_PERSON_TRACKING, default=DEFAULT_PERSON_TRACKING): cv.boolean,
            vol.Optional(CONF_CREATE_DASHBOARD, default=DEFAULT_CREATE_DASHBOARD): cv.boolean,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "dog_name": "Name für Ihren Hund (z.B. 'Rex', 'Bella')",
                "existing_dogs": self._get_existing_dogs_list()
            }
        )

    async def async_step_advanced(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle advanced configuration step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                # Validate advanced settings
                await self._validate_advanced_input(user_input)
                
                # Merge with basic data
                self._data.update(user_input)
                return await self.async_step_feeding_schedule()
                
            except InvalidSensor:
                errors["door_sensor"] = "invalid_sensor"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception in advanced step")
                errors["base"] = "unknown"

        # Get available binary sensors for door detection
        door_sensors = await self._get_door_sensors()

        data_schema = vol.Schema({
            vol.Optional(CONF_DOOR_SENSOR): selector({
                "entity": {
                    "filter": {
                        "domain": "binary_sensor"
                    }
                }
            }),
            vol.Optional(CONF_RESET_TIME, default=DEFAULT_RESET_TIME): selector({
                "time": {}
            }),
            vol.Optional("enable_health_monitoring", default=True): cv.boolean,
            vol.Optional("enable_weather_integration", default=False): cv.boolean,
            vol.Optional("enable_visitor_mode", default=True): cv.boolean,
            vol.Optional("enable_emergency_features", default=True): cv.boolean,
        })

        return self.async_show_form(
            step_id="advanced",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "door_sensors_count": str(len(door_sensors))
            }
        )

    async def async_step_feeding_schedule(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle feeding schedule configuration."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                # Validate feeding times
                await self._validate_feeding_times(user_input)
                
                # Merge with existing data
                self._data.update(user_input)
                return await self.async_step_contacts()
                
            except InvalidTime:
                errors["base"] = "invalid_feeding_times"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception in feeding schedule step")
                errors["base"] = "unknown"

        data_schema = vol.Schema({
            vol.Optional("morning_time", default=DEFAULT_FEEDING_TIMES["morning"]): selector({
                "time": {}
            }),
            vol.Optional("lunch_time", default=DEFAULT_FEEDING_TIMES["lunch"]): selector({
                "time": {}
            }),
            vol.Optional("evening_time", default=DEFAULT_FEEDING_TIMES["evening"]): selector({
                "time": {}
            }),
            vol.Optional("snack_time", default=DEFAULT_FEEDING_TIMES["snack"]): selector({
                "time": {}
            }),
            vol.Optional("enable_feeding_reminders", default=True): cv.boolean,
            vol.Optional("auto_increment_counters", default=True): cv.boolean,
            vol.Optional("strict_feeding_schedule", default=False): cv.boolean,
        })

        return self.async_show_form(
            step_id="feeding_schedule",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "dog_name": self._data[CONF_DOG_NAME].title()
            }
        )

    async def async_step_contacts(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle emergency contacts configuration."""
        if user_input is not None:
            # Merge all data and create entry
            self._data.update(user_input)
            
            return self.async_create_entry(
                title=f"Hundesystem - {self._data[CONF_DOG_NAME].title()}",
                data=self._data,
            )

        data_schema = vol.Schema({
            vol.Optional("emergency_contact_name"): cv.string,
            vol.Optional("emergency_contact_phone"): cv.string,
            vol.Optional("vet_name"): cv.string,
            vol.Optional("vet_phone"): cv.string,
            vol.Optional("vet_address"): cv.string,
            vol.Optional("backup_contact_name"): cv.string,
            vol.Optional("backup_contact_phone"): cv.string,
            vol.Optional("microchip_id"): cv.string,
            vol.Optional("insurance_company"): cv.string,
            vol.Optional("insurance_number"): cv.string,
        })

        return self.async_show_form(
            step_id="contacts",
            data_schema=data_schema,
            description_placeholders={
                "dog_name": self._data[CONF_DOG_NAME].title()
            }
        )

    async def _validate_input(self, user_input: dict[str, Any]) -> dict[str, Any]:
        """Validate the user input allows us to connect."""
        
        # Check number of existing dogs
        existing_entries = self._async_current_entries()
        if len(existing_entries) >= MAX_DOGS:
            raise TooManyDogs(f"Maximum of {MAX_DOGS} dogs allowed")
        
        # Validate and normalize dog name
        dog_name = user_input[CONF_DOG_NAME].lower().strip()
        
        if not dog_name:
            raise InvalidDogName("Dog name cannot be empty")
        
        if not re.match(DOG_NAME_PATTERN, dog_name):
            raise InvalidDogName("Dog name must start with a letter and contain only letters, numbers, and underscores")
        
        if len(dog_name) > 20:
            raise InvalidDogName("Dog name must be 20 characters or less")
        
        # Check if dog already exists
        for entry in existing_entries:
            if entry.data.get(CONF_DOG_NAME, "").lower() == dog_name:
                raise AlreadyConfigured(f"Dog '{dog_name}' is already configured")
        
        # Validate notify services
        push_devices = user_input.get(CONF_PUSH_DEVICES, [])
        if push_devices:
            available_services = await self._get_notify_services()
            available_service_values = [service["value"] for service in available_services]
            
            for device in push_devices:
                if device not in available_service_values:
                    raise CannotConnect(f"Notify service '{device}' not available")
        
        # Return normalized data
        return {
            CONF_DOG_NAME: dog_name,
            CONF_PUSH_DEVICES: push_devices,
            CONF_PERSON_TRACKING: user_input.get(CONF_PERSON_TRACKING, DEFAULT_PERSON_TRACKING),
            CONF_CREATE_DASHBOARD: user_input.get(CONF_CREATE_DASHBOARD, DEFAULT_CREATE_DASHBOARD),
        }

    async def _validate_advanced_input(self, user_input: dict[str, Any]) -> None:
        """Validate advanced configuration input."""
        
        # Validate door sensor if provided
        door_sensor = user_input.get(CONF_DOOR_SENSOR)
        if door_sensor:
            state = self.hass.states.get(door_sensor)
            if not state:
                raise InvalidSensor(f"Sensor '{door_sensor}' not found")
            
            if not door_sensor.startswith("binary_sensor."):
                raise InvalidSensor("Door sensor must be a binary sensor")
        
        # Validate reset time
        reset_time = user_input.get(CONF_RESET_TIME, DEFAULT_RESET_TIME)
        try:
            # Parse time to validate format
            import datetime
            datetime.datetime.strptime(reset_time, "%H:%M:%S")
        except ValueError:
            raise InvalidTime("Invalid reset time format")

    async def _validate_feeding_times(self, user_input: dict[str, Any]) -> None:
        """Validate feeding schedule times."""
        import datetime
        
        times = []
        for meal in ["morning", "lunch", "evening", "snack"]:
            time_key = f"{meal}_time"
            if time_key in user_input:
                try:
                    time_obj = datetime.datetime.strptime(user_input[time_key], "%H:%M:%S")
                    times.append((meal, time_obj))
                except ValueError:
                    raise InvalidTime(f"Invalid time format for {meal}")
        
        # Check that times are in logical order (optional warning)
        times.sort(key=lambda x: x[1])
        expected_order = ["morning", "lunch", "snack", "evening"]
        actual_order = [meal for meal, _ in times]
        
        if actual_order != [m for m in expected_order if m in actual_order]:
            _LOGGER.warning("Feeding times might not be in logical order: %s", actual_order)

    async def _get_notify_services(self) -> list[dict[str, str]]:
        """Get available notify services."""
        services = []
        
        try:
            # Get all notify services
            notify_services = self.hass.services.async_services().get("notify", {})
            
            for service_name in notify_services.keys():
                if service_name != "notify":  # Skip the base notify service
                    # Create human readable label
                    label = service_name.replace("_", " ").title()
                    if service_name.startswith("mobile_app_"):
                        person_name = service_name.replace("mobile_app_", "").title()
                        label = f"Mobile App - {person_name}"
                    elif service_name == "persistent_notification":
                        label = "Persistent Notification"
                    
                    services.append({
                        "value": service_name,
                        "label": label
                    })
            
            # Add some common services if not present
            common_services = [
                {"value": "persistent_notification", "label": "Persistent Notification"},
                {"value": "telegram", "label": "Telegram"},
                {"value": "pushbullet", "label": "Pushbullet"},
                {"value": "discord", "label": "Discord"},
            ]
            
            for common in common_services:
                if not any(s["value"] == common["value"] for s in services):
                    # Only add if the service actually exists
                    if self.hass.services.has_service("notify", common["value"]):
                        services.append(common)
            
        except Exception as err:
            _LOGGER.warning("Could not get notify services: %s", err)
            # Fallback services
            services = [
                {"value": "persistent_notification", "label": "Persistent Notification"}
            ]
        
        return sorted(services, key=lambda x: x["label"])

    async def _get_door_sensors(self) -> list[dict[str, str]]:
        """Get available door/window binary sensors."""
        sensors = []
        
        try:
            for entity_id in self.hass.states.async_entity_ids("binary_sensor"):
                state = self.hass.states.get(entity_id)
                if state:
                    # Look for door, window, opening sensors
                    device_class = state.attributes.get("device_class", "").lower()
                    friendly_name = state.attributes.get("friendly_name", entity_id)
                    
                    if (device_class in ["door", "window", "opening"] or
                        any(keyword in entity_id.lower() for keyword in ["door", "window", "tuer", "fenster"]) or
                        any(keyword in friendly_name.lower() for keyword in ["door", "window", "tür", "fenster"])):
                        
                        sensors.append({
                            "value": entity_id,
                            "label": friendly_name
                        })
        except Exception as err:
            _LOGGER.warning("Could not get door sensors: %s", err)
        
        return sorted(sensors, key=lambda x: x["label"])

    def _get_existing_dogs_list(self) -> str:
        """Get list of existing configured dogs."""
        existing_entries = self._async_current_entries()
        if not existing_entries:
            return "Keine Hunde konfiguriert"
        
        dog_names = [entry.data.get(CONF_DOG_NAME, "").title() for entry in existing_entries]
        return f"Existierende Hunde: {', '.join(dog_names)}"

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Hundesystem."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Get current configuration
        current_config = self.config_entry.data
        dog_name = current_config.get(CONF_DOG_NAME, "")

        data_schema = vol.Schema({
            vol.Optional(
                CONF_PUSH_DEVICES,
                default=current_config.get(CONF_PUSH_DEVICES, [])
            ): selector({
                "select": {
                    "options": await self._get_notify_services(),
                    "multiple": True,
                    "mode": "dropdown"
                }
            }),
            vol.Optional(
                CONF_PERSON_TRACKING,
                default=current_config.get(CONF_PERSON_TRACKING, DEFAULT_PERSON_TRACKING)
            ): cv.boolean,
            vol.Optional(
                CONF_CREATE_DASHBOARD,
                default=current_config.get(CONF_CREATE_DASHBOARD, DEFAULT_CREATE_DASHBOARD)
            ): cv.boolean,
            vol.Optional(
                CONF_DOOR_SENSOR,
                default=current_config.get(CONF_DOOR_SENSOR)
            ): selector({
                "entity": {
                    "filter": {
                        "domain": "binary_sensor"
                    }
                }
            }),
            vol.Optional(
                CONF_RESET_TIME,
                default=current_config.get(CONF_RESET_TIME, DEFAULT_RESET_TIME)
            ): selector({
                "time": {}
            }),
        })

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
            description_placeholders={
                "dog_name": dog_name.title()
            }
        )

    async def _get_notify_services(self) -> list[dict[str, str]]:
        """Get available notify services for options."""
        # Reuse the same method from ConfigFlow
        config_flow = ConfigFlow()
        config_flow.hass = self.hass
        return await config_flow._get_notify_services()


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidDogName(HomeAssistantError):
    """Error to indicate invalid dog name."""


class AlreadyConfigured(HomeAssistantError):
    """Error to indicate dog is already configured."""


class TooManyDogs(HomeAssistantError):
    """Error to indicate too many dogs configured."""


class InvalidSensor(HomeAssistantError):
    """Error to indicate invalid sensor."""


class InvalidTime(HomeAssistantError):
    """Error to indicate invalid time format."""