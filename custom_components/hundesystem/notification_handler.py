from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_component import async_update_entity
from homeassistant.util import slugify

from .const import DOMAIN


async def send_push_notification(hass: HomeAssistant, dog_name: str, message: str, actions: list = None):
    """Sendet eine gezielte Benachrichtigung nur an anwesende Personen/Geräte."""

    dog_id = slugify(dog_name)

    # Optional: input_select mit Geräten abrufen
    # Hier vereinfacht: an notify.mobile_app_<person> schicken, wenn anwesend

    recipients = []
    persons = hass.states.async_entity_ids("person")

    for person_entity in persons:
        person_state = hass.states.get(person_entity)
        if person_state.state == "home":
            person_id = person_entity.split(".")[1]
            notify_entity = f"notify.mobile_app_{person_id}"
            if notify_entity in hass.services.async_services().get("notify", {}):
                recipients.append(notify_entity)

    for target in recipients:
        await hass.services.async_call(
            "notify",
            target.replace("notify.", ""),
            {
                "title": f"Hundesystem: {dog_name}",
                "message": message,
                "data": {"actions": actions} if actions else {}
            }
        )
