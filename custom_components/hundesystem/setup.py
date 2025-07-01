import asyncio
from homeassistant.core import HomeAssistant

async def async_setup_entry(hass: HomeAssistant, entry):
    await hass.async_add_executor_job(create_helpers, hass)
    return True

def create_helpers(hass):
    # Erstellung aller input_boolean, counter etc.
    pass  # Vollständige Logik eingebettet in reale Version
