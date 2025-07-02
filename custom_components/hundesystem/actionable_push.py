from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.event import async_track_event
from homeassistant.util import slugify

from .activity_logger import async_log_activity
from .notification_handler import send_push_notification

DOMAIN = "hundesystem"

@callback
def setup_actionable_notifications(hass: HomeAssistant):
    """Registriere Listener für mobile Push-Aktionen."""

    @callback
    async def handle_push_action(event):
        data = event.data
        action = data.get("action")
        dog_name = data.get("dog_name") or "Hund"
        dog_id = slugify(dog_name)

        if action == "DOG_WENT_OUT":
            await async_log_activity(hass, dog_name, "walk")

            # Folgefrage: Geschäft erledigt?
            await send_push_notification(
                hass,
                dog_name,
                "Hat {} sein Geschäft gemacht?".format(dog_name),
                actions=[
                    {"action": "DOG_POTTY_YES", "title": "Ja"},
                    {"action": "DOG_POTTY_NO", "title": "Nein"},
                ],
                tag="potty_confirm_" + dog_id
            )

        elif action == "DOG_POTTY_YES":
            await async_log_activity(hass, dog_name, "potty")

        elif action == "DOG_POTTY_NO":
            # optional: kein Logging, aber Log-Eintrag möglich
            pass

    hass.bus.async_listen("mobile_app_notification_action", handle_push_action)
