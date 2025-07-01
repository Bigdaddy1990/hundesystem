import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.device_registry import async_get as async_get_device_registry
from homeassistant.const import CONF_NAME

from .const import DOMAIN, CONF_SENSOR_TUER, CONF_HUNDELISTE, CONF_PUSH_GERAETE, CONF_MAHLZEITEN
from .helpers.helper_creator import get_all_door_sensors, get_all_push_devices, get_all_persons

_LOGGER = logging.getLogger(__name__)


class HundesystemConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            return self.async_create_entry(title="Hundesystem", data=user_input)

        sensors = await get_all_door_sensors(self.hass)
        personen = await get_all_persons(self.hass)
        push_devices = await get_all_push_devices(self.hass)

        schema = vol.Schema({
            vol.Required(CONF_SENSOR_TUER): vol.In(sensors),
            vol.Optional(CONF_HUNDELISTE): str,
            vol.Optional(CONF_PUSH_GERAETE): vol.In(push_devices),
            vol.Optional(CONF_MAHLZEITEN, default=["frühstück", "abendessen"]): vol.All([str])
        })

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
