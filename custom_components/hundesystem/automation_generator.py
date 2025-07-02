from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.util import slugify
from homeassistant.helpers.service import async_prepare_call_from_config

import logging

_LOGGER = logging.getLogger(__name__)
DOMAIN = "hundesystem"

AUTOMATION_TEMPLATE = {{
    "no_walk": {{
        "alias": "Hundesystem - Kein Gassi bis 18 Uhr",
        "trigger": [{{"platform": "time", "at": "18:00:00"}}],
        "condition": [
            {{"condition": "numeric_state", "entity_id": "counter.walk_{{dog_id}}", "below": 1}}
        ],
        "action": [
            {{
                "service": "notify.{{notify_target}}",
                "data": {{
                    "title": "🐕 Gassi-Erinnerung",
                    "message": "{{dog_name}} war heute noch nicht draußen!"
                }}
            }}
        ],
        "mode": "single",
    }},
    "no_feeding": {{
        "alias": "Hundesystem - Nicht gefüttert bis 10 Uhr",
        "trigger": [{{"platform": "time", "at": "10:00:00"}}],
        "condition": [
            {{"condition": "numeric_state", "entity_id": "counter.feeding_{{dog_id}}", "below": 1}}
        ],
        "action": [
            {{
                "service": "notify.{{notify_target}}",
                "data": {{
                    "title": "🍽️ Fütterungserinnerung",
                    "message": "{{dog_name}} hat heute noch nichts gefressen."
                }}
            }}
        ],
        "mode": "single",
    }},
}}

async def async_generate_automations(hass: HomeAssistant, dog_name: str, notify_target: str):
    dog_id = slugify(dog_name)
    for key, cfg in AUTOMATION_TEMPLATE.items():
        rendered = str(cfg)
        rendered = rendered.replace("{{dog_name}}", dog_name)
        rendered = rendered.replace("{{dog_id}}", dog_id)
        rendered = rendered.replace("{{notify_target}}", notify_target)
        try:
            automation = eval(rendered)
            await hass.services.async_call("automation", "reload")
            _LOGGER.info("Automationsvorlage '%s' vorbereitet für %s", key, dog_name)
        except Exception as e:
            _LOGGER.error("Fehler beim Generieren der Automation: %s", e)
