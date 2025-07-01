import logging

_LOGGER = logging.getLogger(__name__)

async def notify_if_person_home(hass, title, message, push_devices):
    for dev in push_devices:
        if dev.startswith("notify.") and dev in hass.services.async_services().get("notify", {}):
            _LOGGER.debug(f"Sending push to: {dev}")
            await hass.services.async_call("notify", dev.replace("notify.", ""), {
                "title": title,
                "message": message
            })
