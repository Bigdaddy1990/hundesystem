"""Config flow for Hundesystem integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
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
    DEFAULT_DOG_NAME,
    DEFAULT_CREATE_DASHBOARD,
    DEFAULT_PERSON_TRACKING,
)

_LOGGER = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Hundesystem."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                await self._validate_input(user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=f"Hundesystem - {user_input[CONF_DOG_NAME].title()}",
                    data=user_input,
                )

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
                "push_devices": "Benachrichtigungsgeräte für Erinnerungen",
                "person_tracking": "Erweiterte Personenverfolgung aktivieren",
                "create_dashboard": "Automatisches Dashboard erstellen"
            }
        )

    async def _validate_input(self, user_input: dict[str, Any]) -> dict[str, Any]:
        """Validate the user input allows us to connect."""
        
        # Validate dog name
        dog_name = user_input[CONF_DOG_NAME].lower().strip()
        if not dog_name:
            raise InvalidAuth("Dog name cannot be empty")
        
        if not dog_name.isalpha():
            raise InvalidAuth("Dog name should only contain letters")
        
        # Check if integration already exists for this dog
        existing_entries = self._async_current_entries()
        for entry in existing_entries:
            if entry.data.get(CONF_DOG_NAME, "").lower() == dog_name:
                raise InvalidAuth(f"Integration for '{dog_name}' already exists")
        
        # Validate notify services
        push_devices = user_input.get(CONF_PUSH_DEVICES, [])
        if push_devices:
            available_services = await self._get_notify_services()
            for device in push_devices:
                if device not in [service["value"] for service in available_services]:
                    raise CannotConnect(f"Notify service '{device}' not available")
        
        # Normalize dog name
        user_input[CONF_DOG_NAME] = dog_name
        
        return user_input

    async def _get_notify_services(self) -> list[dict[str, str]]:
        """Get available notify services."""
        services = []
        
        try:
            # Get all notify services
            notify_services = self.hass.services.async_services().get("notify", {})
            
            for service_name in notify_services.keys():
                if service_name != "notify":  # Skip the base notify service
                    services.append({
                        "value": service_name,
                        "label": service_name.replace("_", " ").title()
                    })
            
            # Add some common services if not present
            common_services = [
                {"value": "mobile_app", "label": "Mobile App"},
                {"value": "persistent_notification", "label": "Persistent Notification"}
            ]
            
            for common in common_services:
                if not any(s["value"] == common["value"] for s in services):
                    services.append(common)
            
        except Exception as err:
            _LOGGER.warning("Could not get notify services: %s", err)
            # Fallback services
            services = [
                {"value": "persistent_notification", "label": "Persistent Notification"}
            ]
        
        return services

    @staticmethod
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
