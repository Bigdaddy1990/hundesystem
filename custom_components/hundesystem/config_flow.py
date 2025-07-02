"""Config flow for Hundesystem integration."""
import voluptuous as vol
import logging

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.helpers.selector import selector
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN, CONF_PUSH_DEVICES, CONF_PERSON_TRACKING, CONF_DASHBOARD

_LOGGER = logging.getLogger(__name__)

class HundeSystemConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Hundesystem."""
    
    VERSION = 1
    
    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        
        if user_input is not None:
            # Validate and normalize name
            name = user_input[CONF_NAME].lower().strip()
            name = "".join(c for c in name if c.isalnum() or c == "_")
            
            if not name:
                errors["name"] = "invalid_name"
            else:
                # Check if already configured
                await self.async_set_unique_id(name)
                self._abort_if_unique_id_configured()
                
                user_input[CONF_NAME] = name
                return self.async_create_entry(
                    title=f"Hundesystem - {name.title()}", 
                    data=user_input
                )
        
        # Build form schema
        schema = vol.Schema({
            vol.Required(CONF_NAME, default="rex"): str,
            vol.Optional(CONF_PUSH_DEVICES, default=[]): selector({
                "entity": {
                    "multiple": True,
                    "filter": {
                        "domain": "notify"
                    }
                }
            }),
            vol.Optional(CONF_PERSON_TRACKING, default=True): bool,
            vol.Optional(CONF_DASHBOARD, default=True): bool,
        })
        
        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "name": "rex"
            }
        )