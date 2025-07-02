from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import entity_registry as er
from homeassistant.components.notify import async_get_notifier
import logging

_LOGGER = logging.getLogger(__name__)

DOMAIN = "hundesystem"

async def handle_send_notification(call: ServiceCall):
    hass: HomeAssistant = call.hass
    dog_name = call.data.get("dog_name")
    title = call.data.get("title", f"{dog_name}: Rückfrage")
    message = call.data.get("message", "War der Hund draußen?")
    target_devices = call.data.get("targets", [])
    person_ids = call.data.get("persons", [])

    notify_targets = set()

    # Dynamische Empfängerwahl
    for person_id in person_ids:
        entity_id = f"person.{person_id}"
        state = hass.states.get(entity_id)
        if state and state.state == "home":
            device = hass.states.get(f"input_text.notify_device_{person_id}")
            if device:
                notify_targets.add(device.state)

    # Manuelle Targets hinzufügen
    notify_targets.update(target_devices)

    if not notify_targets:
        _LOGGER.warning("Keine gültigen Notify-Ziele gefunden")
        return

    # Actionable Notification-Daten
    actions = call.data.get("actions", [
        {"action": "yes", "title": "Ja"},
        {"action": "no", "title": "Nein"}
    ])
    data = {
        "actions": actions,
        "tag": f"{dog_name}_frage",
        "group": f"hundesystem_{dog_name}",
        "clickAction": "/lovelace/hundesystem"
    }

    for notify_target in notify_targets:
        await hass.services.async_call(
            "notify",
            notify_target,
            {
                "title": title,
                "message": message,
                "data": data
            },
            blocking=False,
        )

def setup_actionable_notifications(hass: HomeAssistant):
    hass.services.async_register(DOMAIN, "send_notification", handle_send_notification)
