import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.helpers import selector
from .const import DOMAIN, CONF_PUSH_DEVICES, CONF_PERSON_TRACKING, CONF_DASHBOARD

CONF_DOOR_SENSOR = "door_sensor"

CONFIG_SCHEMA = vol.Schema({
    vol.Required(CONF_NAME): str,
    vol.Optional(CONF_DOOR_SENSOR): selector.selector({
        "entity": {"domain": "binary_sensor"}
    }),
    vol.Optional(CONF_PUSH_DEVICES): vol.All(list),
    vol.Optional(CONF_PERSON_TRACKING, default=True): bool,
    vol.Optional(CONF_DASHBOARD, default=True): bool,
})


class HundeSystemConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            existing_entries = self._async_current_entries()
            for entry in existing_entries:
                if entry.data.get(CONF_NAME) == user_input.get(CONF_NAME):
                    errors[CONF_NAME] = "already_configured"
                    break
            if not errors:
                return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=CONFIG_SCHEMA,
            errors=errors
        )

