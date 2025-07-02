import logging

_LOGGER = logging.getLogger(__name__)
DOMAIN = "hundesystem"

async def async_setup(hass, config):
    from .sensor import async_setup_statistics
    from .automation_generator import async_generate_automations
    from .actionable_push import setup_actionable_notifications

    def handle_generate_stats(call):
        dog_name = call.data.get("dog_name")
        hass.async_create_task(async_setup_statistics(hass, dog_name))

    def handle_generate_automations(call):
        dog_name = call.data.get("dog_name")
        notify_target = call.data.get("notify_target")
        hass.async_create_task(async_generate_automations(hass, dog_name, notify_target))

    setup_actionable_notifications(hass)

    hass.services.async_register(DOMAIN, "generate_stat_sensors", handle_generate_stats)
    hass.services.async_register(DOMAIN, "generate_automations", handle_generate_automations)

    _LOGGER.info("Hundesystem erfolgreich eingerichtet")
    return True
