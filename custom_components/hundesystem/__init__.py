import logging
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import ConfigType

from .dashboard import create_dashboard_for_dog
from .setup_helpers import async_create_helpers_for_dog
from .activity_logger import async_log_activity
from .notification_handler import send_push_notification

_LOGGER = logging.getLogger(__name__)
DOMAIN = "hundesystem"

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    async def handle_create_dashboard(call: ServiceCall) -> None:
        dog_name = call.data.get("dog_name")
        await create_dashboard_for_dog(hass, dog_name)

    async def handle_setup_helpers(call: ServiceCall) -> None:
        dog_name = call.data.get("dog_name")
        dog_id = dog_name.lower().replace(" ", "_")
        await async_create_helpers_for_dog(hass, dog_id)

    async def handle_log_activity(call: ServiceCall) -> None:
        dog_name = call.data.get("dog_name")
        activity = call.data.get("activity_type")
        await async_log_activity(hass, dog_name, activity)

    async def handle_send_notification(call: ServiceCall) -> None:
        dog_name = call.data.get("dog_name")
        message = call.data.get("message")
        await send_push_notification(hass, dog_name, message)

    hass.services.async_register(DOMAIN, "create_dashboard", handle_create_dashboard)
    hass.services.async_register(DOMAIN, "setup_helpers", handle_setup_helpers)
    hass.services.async_register(DOMAIN, "log_activity", handle_log_activity)
    hass.services.async_register(DOMAIN, "send_notification", handle_send_notification)

    async def handle_generate_stats(call: ServiceCall) -> None:
        dog_name = call.data.get("dog_name")
        dog_id = dog_name.lower().replace(" ", "_")
        _LOGGER.info("Statistiksensoren für %s registriert", dog_id)
        # Hinweis: Utility Meter-Sensoren werden über sensor.yaml oder Dashboard erwartet
        # Diese Funktion kann erweitert werden, um dynamisch zu registrieren
    hass.services.async_register(DOMAIN, "generate_stat_sensors", handle_generate_stats)

    async def handle_generate_automations(call: ServiceCall) -> None:
        dog_name = call.data.get("dog_name")
        notify_target = call.data.get("notify_target")
        from .automation_generator import async_generate_automations
        await async_generate_automations(hass, dog_name, notify_target)

    hass.services.async_register(DOMAIN, "generate_automations", handle_generate_automations)



    _LOGGER.info("Hundesystem Services geladen.")
    setup_actionable_notifications(hass)
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return await async_setup(hass, {})

from .actionable_push import setup_actionable_notifications
