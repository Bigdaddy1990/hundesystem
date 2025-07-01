# custom_components/hundesystem/automations.py
from homeassistant.core import HomeAssistant
from datetime import timedelta

FEEDING_TYPES = ["morning", "lunch", "evening", "snack"]

async def async_setup_automations(hass: HomeAssistant, name: str, push_devices: list[str], use_persons: bool):
    for f_type in FEEDING_TYPES:
        bool_id = f"input_boolean.{name}_feeding_{f_type}"
        counter_id = f"counter.{name}_feeding_{f_type}"

        # Beispiel: Rückfrage bei Nichtfütterung um 10:00 Uhr (für Frühstück)
        if f_type == "morning":
            hass.services.async_call(
                "automation", "trigger", {
                    "entity_id": f"automation.{name}_{f_type}_reminder"
                }
            )

            # Anlegen der Automation (vereinfacht):
            hass.states.async_set(f"automation.{name}_{f_type}_reminder", "on", {
                "friendly_name": f"{f_type.capitalize()} Feeding Reminder",
                "trigger": {
                    "platform": "time",
                    "at": "10:00:00"
                },
                "condition": [
                    {"condition": "state", "entity_id": bool_id, "state": "off"}
                ],
                "action": [
                    {
                        "service": "notify.mobile_app_" + push_devices[0],
                        "data": {
                            "title": "🐶 Erinnerung",
                            "message": f"{name} wurde noch nicht gefüttert ({f_type})!",
                        }
                    }
                ]
            })

        # Optional: Counter erhöhen bei Änderung
        hass.helpers.event.async_track_state_change(
            bool_id,
            lambda *args: hass.services.async_call(
                "counter", "increment", {"entity_id": counter_id}
            ) if args[2].state == "on" else None
        )
