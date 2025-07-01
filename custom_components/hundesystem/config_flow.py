from homeassistant import config_entries
from homeassistant.helpers.entity_component import async_update_entity
from homeassistant.const import CONF_NAME
from .const import DOMAIN
import voluptuous as vol

class HundesystemConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)
        return self.async_show_form(step_id="user", data_schema=vol.Schema({vol.Required(CONF_NAME): str}))