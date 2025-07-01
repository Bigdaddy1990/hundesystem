from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_registry import async_get
from homeassistant.helpers import device_registry as dr

async def send_push_notification(
    hass: HomeAssistant,
    title: str,
    message: str,
    push_devices: list[str],
    use_person_tracking: bool
):
    notified = False

    if use_person_tracking:
        person_entities = [
            e.entity_id
            for e in hass.states.async_all("person")
            if e.state == "home"
        ]

        for person in person_entities:
            # Beispiel: notify.mobile_app_rene_pixel6
            person_name = person.split(".")[1]
            notify_entity = f"notify.mobile_app_{person_name}"

            if hass.services.has_service("notify", f"mobile_app_{person_name}"):
                await hass.services.async_call("notify", f"mobile_app_{person_name}", {
                    "title": title,
                    "message": message
                })
                notified = True

    # Fallback, wenn niemand zuhause oder person.* unzuverlässig
    if not notified and push_devices:
        for device in push_devices:
            if hass.services.has_service("notify", device):
                await hass.services.async_call("notify", device, {
                    "title": title,
                    "message": message
                })
