from homeassistant.core import HomeAssistant
from homeassistant.components.lovelace.dashboard import async_create_dashboard

DOMAIN = "hundesystem"

def generate_dashboard_config(dog_name: str, visitor: bool = False) -> dict:
    """Generate a grouped dashboard configuration for a specific dog."""
    dog_id = dog_name.lower().replace(" ", "_")
    badge = " (Besuchshund)" if visitor else ""

    return {
        "title": f"Hund: {dog_name}",
        "views": [
            {
                "title": f"{dog_name}{badge}",
                "path": dog_id,
                "theme": "default",
                "type": "custom:masonry",
                "cards": [
                    {
                        "type": "custom:mushroom-title-card",
                        "title": f"Status für {dog_name}{badge}",
                        "subtitle": f"Gassi, Futter, Aktivität",
                        "badge_color": "red" if visitor else "green"
                    },
                    {
                        "type": "custom:mushroom-entity-card",
                        "entity": f"sensor.walks_today_{dog_id}",
                        "name": "Gassi heute",
                        "layout": "horizontal",
                        "fill_container": True
                    },
                    {
                        "type": "custom:mushroom-entity-card",
                        "entity": f"sensor.feeding_today_{dog_id}",
                        "name": "Fütterung heute",
                        "layout": "horizontal",
                        "fill_container": True
                    },
                    {
                        "type": "custom:mushroom-entity-card",
                        "entity": f"sensor.potty_today_{dog_id}",
                        "name": "Geschäft heute",
                        "layout": "horizontal",
                        "fill_container": True
                    },
                    {
                        "type": "custom:mushroom-entity-card",
                        "entity": f"input_text.last_activity_{dog_id}",
                        "name": "Letzte Aktivität",
                        "icon": "mdi:history",
                        "layout": "horizontal",
                        "fill_container": True
                    },
                    {
                        "type": "custom:mushroom-button-card",
                        "entity": f"button.quick_feeding_button_{dog_id}",
                        "name": "Jetzt füttern",
                        "icon": "mdi:dog",
                        "tap_action": {
                            "action": "call-service",
                            "service": "hundesystem.log_activity",
                            "service_data": {
                                "dog_name": dog_name,
                                "activity_type": "feeding"
                            }
                        },
                        "fill_container": True
                    }
                ]
            }
        ]
    }

async def create_dashboard_for_dog(hass: HomeAssistant, dog_name: str) -> None:
    """Create and register a dashboard for a specific dog."""
    dog_id = dog_name.lower().replace(" ", "_")
    visitor_entity = f"input_boolean.visitor_mode_{dog_id}"
    visitor = hass.states.get(visitor_entity).state == "on" if hass.states.get(visitor_entity) else False

    config = generate_dashboard_config(dog_name, visitor)
    url_path = f"{dog_id}-dashboard"
    await async_create_dashboard(
        hass=hass,
        title=config["title"],
        config=config,
        url_path=url_path,
        require_admin=False,
    )
