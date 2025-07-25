"""Config flow for Hundesystem integration - FIXED IMPORTS."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_ENTITY_ID
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.selector import selector  # FIXED IMPORT
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry

from .const import (
    DOMAIN,
    CONF_DOG_NAME,
    CONF_PUSH_DEVICES,
    CONF_PERSON_TRACKING,
    CONF_CREATE_DASHBOARD,
    CONF_DOOR_SENSOR,
    DEFAULT_DOG_NAME,
    DEFAULT_PERSON_TRACKING,
    DEFAULT_CREATE_DASHBOARD,
)

_LOGGER = logging.getLogger(__name__)


class CannotConnect(Exception):
    """Error to indicate we cannot connect."""


class InvalidDogName(Exception):
    """Error to indicate there is invalid dog name."""


class AlreadyConfigured(Exception):
    """Error to indicate dog is already configured."""


class TooManyDogs(Exception):
    """Error to indicate too many dogs are configured."""


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.
    
    Data has the keys from DATA_SCHEMA with values provided by the user.
    """
    dog_name = data[CONF_DOG_NAME].strip().lower()
    
    # Validate dog name
    if not dog_name or len(dog_name) < 2:
        raise InvalidDogName
    
    if not dog_name.replace('_', '').replace('-', '').isalnum():
        raise InvalidDogName
    
    # Check if already configured
    existing_entries = hass.config_entries.async_entries(DOMAIN)
    if len(existing_entries) >= 5:  # Max 5 dogs
        raise TooManyDogs
    
    for entry in existing_entries:
        if entry.data.get(CONF_DOG_NAME, "").lower() == dog_name:
            raise AlreadyConfigured

    # Return info that you want to store in the config entry.
    return {
        CONF_DOG_NAME: dog_name,
        CONF_PUSH_DEVICES: data.get(CONF_PUSH_DEVICES, []),
        CONF_PERSON_TRACKING: data.get(CONF_PERSON_TRACKING, DEFAULT_PERSON_TRACKING),
        CONF_CREATE_DASHBOARD: data.get(CONF_CREATE_DASHBOARD, DEFAULT_CREATE_DASHBOARD),
        CONF_DOOR_SENSOR: data.get(CONF_DOOR_SENSOR, ""),
    }


@config_entries.HANDLERS.register(DOMAIN)
class HundesystemConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
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
                info = await validate_input(self.hass, user_input)
                
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
                # Validate door sensor if provided
                door_sensor = user_input.get(CONF_DOOR_SENSOR, "")
                if door_sensor:
                    # Check if entity exists
                    entity_registry = async_get_entity_registry(self.hass)
                    if not entity_registry.async_get(door_sensor):
                        state = self.hass.states.get(door_sensor)
                        if not state:
                            errors["door_sensor"] = "entity_not_found"
                
                if not errors:
                    # Update data and create entry
                    self._data.update(user_input)
                    
                    return self.async_create_entry(
                        title=f"Hundesystem - {self._data[CONF_DOG_NAME].title()}",
                        data=self._data
                    )
                    
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception in advanced step")
                errors["base"] = "unknown"

        # Get door sensors
        door_sensors = await self._get_door_sensors()

        advanced_schema = vol.Schema({
            vol.Optional(CONF_DOOR_SENSOR, default=""): selector({
                "entity": {
                    "domain": "binary_sensor",
                    "device_class": "door"
                }
            }) if door_sensors else cv.string,
        })

        return self.async_show_form(
            step_id="advanced",
            data_schema=advanced_schema,
            errors=errors,
            description_placeholders={
                "door_sensor_info": "Optional: Türsensor für automatische Erkennung"
            }
        )

    async def _get_notify_services(self) -> list[str]:
        """Get available notify services."""
        try:
            services = []
            
            # Get all notify services
            notify_services = self.hass.services.async_services().get("notify", {})
            
            for service_name in notify_services:
                if service_name != "persistent_notification":
                    display_name = service_name.replace("_", " ").title()
                    services.append({
                        "value": f"notify.{service_name}",
                        "label": display_name
                    })
            
            # Add mobile app services if available
            mobile_services = [s for s in notify_services if s.startswith("mobile_app_")]
            for service in mobile_services:
                device_name = service.replace("mobile_app_", "").replace("_", " ").title()
                services.append({
                    "value": f"notify.{service}",
                    "label": f"📱 {device_name}"
                })
            
            return services if services else [{"value": "", "label": "Keine Benachrichtigungsdienste verfügbar"}]
            
        except Exception as e:
            _LOGGER.error("Error getting notify services: %s", e)
            return [{"value": "", "label": "Fehler beim Laden der Dienste"}]

    async def _get_door_sensors(self) -> list[str]:
        """Get available door sensors."""
        try:
            door_sensors = []
            
            # Get entity registry
            entity_registry = async_get_entity_registry(self.hass)
            
            # Find binary sensors with door device class
            for entity in entity_registry.entities.values():
                if (entity.domain == "binary_sensor" and 
                    entity.device_class == "door" and 
                    not entity.disabled_by):
                    
                    state = self.hass.states.get(entity.entity_id)
                    if state:
                        friendly_name = state.attributes.get("friendly_name", entity.entity_id)
                        door_sensors.append({
                            "value": entity.entity_id,
                            "label": friendly_name
                        })
            
            # Also check current states for door sensors
            for entity_id, state in self.hass.states.async_all():
                if (entity_id.startswith("binary_sensor.") and 
                    state.attributes.get("device_class") == "door"):
                    
                    # Avoid duplicates
                    if not any(sensor["value"] == entity_id for sensor in door_sensors):
                        friendly_name = state.attributes.get("friendly_name", entity_id)
                        door_sensors.append({
                            "value": entity_id,
                            "label": friendly_name
                        })
            
            return door_sensors if door_sensors else [{"value": "", "label": "Keine Türsensoren gefunden"}]
            
        except Exception as e:
            _LOGGER.error("Error getting door sensors: %s", e)
            return [{"value": "", "label": "Fehler beim Laden der Sensoren"}]

    def _get_existing_dogs_list(self) -> str:
        """Get list of existing configured dogs."""
        try:
            existing_entries = self.hass.config_entries.async_entries(DOMAIN)
            if not existing_entries:
                return "Noch keine Hunde konfiguriert"
            
            dog_names = [entry.data.get(CONF_DOG_NAME, "Unbekannt").title() 
                        for entry in existing_entries]
            
            return f"Bereits konfiguriert: {', '.join(dog_names)}"
            
        except Exception as e:
            _LOGGER.error("Error getting existing dogs: %s", e)
            return "Fehler beim Laden vorhandener Konfigurationen"

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> HundesystemOptionsFlow:
        """Get the options flow for this handler."""
        return HundesystemOptionsFlow(config_entry)


class HundesystemOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Hundesystem."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                # Validate options
                door_sensor = user_input.get(CONF_DOOR_SENSOR, "")
                if door_sensor:
                    # Check if entity exists
                    entity_registry = async_get_entity_registry(self.hass)
                    if not entity_registry.async_get(door_sensor):
                        state = self.hass.states.get(door_sensor)
                        if not state:
                            errors["door_sensor"] = "entity_not_found"

                if not errors:
                    return self.async_create_entry(title="", data=user_input)

            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception in options flow")
                errors["base"] = "unknown"

        # Get current configuration
        current_config = {**self.config_entry.data, **self.config_entry.options}
        
        # Get available services and sensors
        notify_services = await self._get_notify_services()
        door_sensors = await self._get_door_sensors()

        options_schema = vol.Schema({
            vol.Optional(
                CONF_PUSH_DEVICES,
                default=current_config.get(CONF_PUSH_DEVICES, [])
            ): selector({
                "select": {
                    "options": notify_services,
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
                default=current_config.get(CONF_DOOR_SENSOR, "")
            ): selector({
                "entity": {
                    "domain": "binary_sensor",
                    "device_class": "door"
                }
            }) if door_sensors else cv.string,
        })

        return self.async_show_form(
            step_id="init",
            data_schema=options_schema,
            errors=errors,
            description_placeholders={
                "dog_name": self.config_entry.data.get(CONF_DOG_NAME, "").title()
            }
        )

    async def _get_notify_services(self) -> list[str]:
        """Get available notify services."""
        try:
            services = []
            
            # Get all notify services
            notify_services = self.hass.services.async_services().get("notify", {})
            
            for service_name in notify_services:
                if service_name != "persistent_notification":
                    display_name = service_name.replace("_", " ").title()
                    services.append({
                        "value": f"notify.{service_name}",
                        "label": display_name
                    })
            
            return services if services else [{"value": "", "label": "Keine Benachrichtigungsdienste verfügbar"}]
            
        except Exception as e:
            _LOGGER.error("Error getting notify services in options: %s", e)
            return [{"value": "", "label": "Fehler beim Laden der Dienste"}]

    async def _get_door_sensors(self) -> list[str]:
        """Get available door sensors."""
        try:
            door_sensors = []
            
            # Get entity registry
            entity_registry = async_get_entity_registry(self.hass)
            
            # Find binary sensors with door device class
            for entity in entity_registry.entities.values():
                if (entity.domain == "binary_sensor" and 
                    entity.device_class == "door" and 
                    not entity.disabled_by):
                    
                    state = self.hass.states.get(entity.entity_id)
                    if state:
                        friendly_name = state.attributes.get("friendly_name", entity.entity_id)
                        door_sensors.append({
                            "value": entity.entity_id,
                            "label": friendly_name
                        })
            
            return door_sensors if door_sensors else [{"value": "", "label": "Keine Türsensoren gefunden"}]
            
        except Exception as e:
            _LOGGER.error("Error getting door sensors in options: %s", e)
            return [{"value": "", "label": "Fehler beim Laden der Sensoren"}]
